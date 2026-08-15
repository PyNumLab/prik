"""Compiled all-direct and selectively adapted scalar route evidence."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "routing"
CONTRACTS = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_scalar_all_direct_route_has_no_generated_fortran_artifact(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "scalar_direct_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {"scalar_direct_bind_c_f90_wrapper.c", "scalar_direct_bind_c_f90_wrapper.h"},
        CONTRACTS / "scalar_direct_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.renamed_add(np.int32(5)) == np.int32(9)
    assert module.reference_add(np.int32(5)) == np.int32(13)
    assert module.scale_output(np.float64(4.0)) == np.float64(10.0)
    assert bool(module.invert_flag(np.bool_(True))) is False
    assert module.optional_state() == np.int32(0)
    assert module.optional_state(None) == np.int32(0)
    assert module.optional_state(np.float64(1.0)) == np.int32(1)

    if pyi_parity_build_mode == "source":
        build_dir = tmp_path / "source_build"
        binding = (build_dir / "scalar_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "int32_t scalar_direct_add(int32_t value);" in binding
        assert "void scale_output(double value, double * output);" in binding
        assert not (build_dir / "bind_c_scalar_direct_bind_c_f90_wrapper.f90").exists()
        assert not (build_dir / "bind_c_scalar_direct_bind_c_f90_wrapper.o").exists()


def test_scalar_mixed_route_generates_only_the_ordinary_adapter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    source = FIXTURES / "native" / "scalar_mixed_bind_c_f90.f90"
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "bind_c_scalar_mixed_bind_c_f90_wrapper.f90",
            "scalar_mixed_bind_c_f90_wrapper.c",
            "scalar_mixed_bind_c_f90_wrapper.h",
        },
        CONTRACTS / "scalar_mixed_bind_c_f90",
        pyi_parity_build_mode,
    )

    assert module.direct_add(np.int32(5)) == np.int32(8)
    assert module.adapted_add(np.int32(5)) == np.int32(12)

    if pyi_parity_build_mode == "source":
        bridge = (
            (tmp_path / "source_build" / "bind_c_scalar_mixed_bind_c_f90_wrapper.f90")
            .read_text(encoding="utf-8")
            .casefold()
        )
        binding = (tmp_path / "source_build" / "scalar_mixed_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
        assert "bind_c_adapted_add" in bridge
        assert "native_adapted_add => adapted_add" in bridge
        assert "direct_add" not in bridge
        assert "int32_t scalar_mixed_direct_add(int32_t value);" in binding


def test_source_free_edited_contract_preserves_direct_symbol_scalars_and_boolean_validation(
    tmp_path: Path,
):
    source = (FIXTURES / "native" / "scalar_direct_bind_c_f90.f90").read_text(encoding="utf-8")
    contract = """
from prik.contracts import Bool8, Int32, bind, native_abi

@native_abi("c")
@bind("scalar_direct_add")
def edited_add(value: Int32) -> Int32: ...

@native_abi("c")
def invert_flag(value: Bool8) -> Bool8: ...
"""
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="scalar_direct_bind_c_f90",
        source_text=source,
        contract_text=contract,
    )

    assert module.edited_add(np.int32(5)) == np.int32(9)
    assert bool(module.invert_flag(np.bool_(True))) is False
    with pytest.raises(TypeError):
        module.invert_flag(1)

    assert {path.name for path in result.generated_sources} == {
        "scalar_direct_bind_c_f90_wrapper.c",
        "scalar_direct_bind_c_f90_wrapper.h",
    }
    binding = (result.output_dir / "scalar_direct_bind_c_f90_wrapper.c").read_text(encoding="utf-8")
    assert "int32_t scalar_direct_add(int32_t value);" in binding
    assert "result = scalar_direct_add(bound_value);" in binding
