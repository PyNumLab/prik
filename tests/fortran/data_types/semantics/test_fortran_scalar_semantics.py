"""Fortran scalar kinds, target storage facts, and semantic type mapping."""

import pytest
import re
from prik.parsers.fortran.models import (
    FortranFile,
    FortranVariable,
)
from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    collect_fortran_type_storage_requirements,
    fortran_type_storage_expression,
)
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_intrinsic_builtin_kinds_map_to_semantic_types():
    converter = FortranToIRConverter()
    cases = [
        ("integer", None, "Int32"),
        ("integer", "1", "Int8"),
        ("integer", "2", "Int16"),
        ("integer", "4", "Int32"),
        ("integer", "8", "Int64"),
        ("integer", "int8", "Int8"),
        ("integer", "int16", "Int16"),
        ("integer", "int32", "Int32"),
        ("integer", "int64", "Int64"),
        ("integer", "c_signed_char", "Int8"),
        ("integer", "c_short", "Int16"),
        ("integer", "c_int", "Int32"),
        ("integer", "c_long_long", "Int64"),
        ("integer", "c_int8_t", "Int8"),
        ("integer", "c_int16_t", "Int16"),
        ("integer", "c_int32_t", "Int32"),
        ("integer", "c_int64_t", "Int64"),
        ("real", None, "Float32"),
        ("real", "4", "Float32"),
        ("real", "8", "Float64"),
        ("real", "real32", "Float32"),
        ("real", "real64", "Float64"),
        ("real", "c_float", "Float32"),
        ("real", "c_double", "Float64"),
        ("real", "kind(1.0e0)", "Float32"),
        ("real", "kind(1.0d0)", "Float64"),
        ("complex", None, "Complex64"),
        ("complex", "4", "Complex64"),
        ("complex", "8", "Complex128"),
        ("complex", "real32", "Complex64"),
        ("complex", "real64", "Complex128"),
        ("complex", "c_float_complex", "Complex64"),
        ("complex", "c_double_complex", "Complex128"),
        ("logical", None, "Bool"),
        ("logical", "c_bool", "Bool"),
        ("character", None, "String"),
        ("character", "1", "String"),
        ("character", "c_char", "String"),
        ("character", "len=12, kind=c_char", "String"),
        ("procedure", "f_iface", "Procedure"),
    ]

    for base_type, kind, expected in cases:
        variable = FortranVariable(name=f"{base_type}_{kind or 'default'}", base_type=base_type, kind=kind)
        assert converter.visit(variable, as_type=True).name == expected


def test_unsupported_intrinsic_widths_fail_in_semantic_conversion():
    cases = (
        ("real", "16", "real(kind=16)"),
        ("real", "real128", "real(kind=real128)"),
        ("real", "kind(1.0q0)", "real(kind=16)"),
        ("complex", "16", "complex(kind=16)"),
        ("complex", "real128", "complex(kind=real128)"),
        ("logical", "8", "logical(kind=8)"),
    )

    for base_type, kind, message in cases:
        variable = FortranVariable(name="value", base_type=base_type, kind=kind)
        with pytest.raises(ValueError, match=re.escape(message)):
            FortranToIRConverter().visit(variable, as_type=True)


def test_fortran2ir_uses_compiler_probed_storage_facts_and_preserves_provenance():
    fact = {
        "base_type": "real",
        "kind": None,
        "bits": 64,
        "expression": "storage_size(real(0.0))",
    }
    semantic_type = FortranToIRConverter(type_facts={("real", None): fact}).visit(
        FortranVariable(name="value", base_type="real"),
        as_type=True,
    )

    assert semantic_type.name == "Float64"
    assert semantic_type.dtype == "Float64"
    assert semantic_type.metadata["fortran_type_fact"] == fact
    assert semantic_type.metadata["fortran_type_fact_source"] == "compiler_probe"

    logical_fact = {
        "base_type": "logical",
        "kind": "1",
        "bits": 8,
        "expression": "storage_size(logical(.false.,kind=1))",
    }
    logical_type = FortranToIRConverter(type_facts={("logical", "1"): logical_fact}).visit(
        FortranVariable(name="flag", base_type="logical", kind="1")
    )

    assert logical_type.name == "Bool8"
    assert logical_type.metadata["fortran_type_fact"] == logical_fact


@pytest.mark.parametrize(
    ("bits", "expected"),
    [(8, "Bool8"), (16, "Bool16"), (32, "Bool32"), (64, "Bool64")],
)
def test_fortran2ir_maps_probed_logical_storage_to_language_neutral_boolean_widths(bits, expected):
    fact = {
        "base_type": "logical",
        "kind": str(bits // 8),
        "bits": bits,
        "expression": f"storage_size(logical(.false.,kind={bits // 8}))",
    }

    semantic_type = FortranToIRConverter(type_facts={("logical", str(bits // 8)): fact}).visit(
        FortranVariable(name="flag", base_type="logical", kind=str(bits // 8))
    )

    assert semantic_type.name == expected
    assert semantic_type.dtype == expected


def test_fortran2ir_rejects_compiler_storage_without_semantic_dtype():
    fact = {
        "base_type": "integer",
        "kind": None,
        "bits": 48,
        "expression": "storage_size(int(0))",
    }

    with pytest.raises(ValueError, match="integer uses 48-bit storage"):
        FortranToIRConverter(type_facts={("integer", None): fact}).visit(
            FortranVariable(name="value", base_type="integer")
        )


def test_compiler_probed_unknown_storage_widths_fail_in_semantic_conversion():
    facts = (
        {"base_type": "real", "kind": "3", "bits": 24},
        {"base_type": "complex", "kind": "3", "bits": 96},
        {"base_type": "integer", "kind": "6", "bits": 48},
    )
    for fact in facts:
        with pytest.raises(ValueError, match="Unsupported Fortran target storage"):
            FortranToIRConverter(type_facts={(fact["base_type"], fact["kind"]): fact}).visit(
                FortranVariable(name="value", base_type=fact["base_type"], kind=fact["kind"])
            )


def test_fortran_storage_requirements_follow_resolved_kinds_and_actual_source_types():
    parsed = FortranFile(
        variables=[
            FortranVariable(name="default_real", base_type="real"),
            FortranVariable(name="selected", base_type="real", kind="rk"),
            FortranVariable(name="flag", base_type="logical", kind="8"),
            FortranVariable(name="text", base_type="character", kind="len=12, kind=c_char"),
        ]
    )

    assert fortran_type_storage_expression("complex", "8") == "storage_size(cmplx(0.0,kind=8))"
    requirements = collect_fortran_type_storage_requirements(parsed, compile_time_values={"rk": 8})
    assert {(item["base_type"], item["kind"], item["expression"]) for item in requirements} == {
        ("real", None, "storage_size(real(0.0))"),
        ("real", "8", "storage_size(real(0.0,kind=8))"),
        ("logical", "8", "storage_size(logical(.false.,kind=8))"),
    }


def test_legacy_fortran_storage_uses_fixed_star_widths_and_probes_double_types():
    parsed = parse_fortran_source(
        """
subroutine legacy(c8, c16, dp, dc, label, explicit_kind)
  complex*8 c8
  complex*16 c16
  double precision dp
  double complex dc
  character*8 label
  character(kind=1) explicit_kind
end subroutine legacy
""",
        filename="legacy_types.f90",
    )
    args = {arg.name: arg for arg in parsed.procedures[0].arguments}
    converter = FortranToIRConverter()

    assert converter.visit(args["c8"], as_type=True).name == "Complex64"
    assert converter.visit(args["c16"], as_type=True).name == "Complex128"
    assert converter.visit(args["c16"], as_type=True).metadata["fortran_type_fact_source"] == "legacy_star_storage"

    requirements = collect_fortran_type_storage_requirements(parsed)
    assert {(item["base_type"], item["kind"], item["expression"]) for item in requirements} == {
        ("real", "kind(1.0d0)", "storage_size(real(0.0,kind=kind(1.0d0)))"),
        ("complex", "kind(1.0d0)", "storage_size(cmplx(0.0,kind=kind(1.0d0)))"),
    }
