"""Tests split by stable ownership concept from `test_properties.py`."""

import pytest
from contextlib import suppress
from hypothesis import given
from prik.parsers.fortran import FortranParseError, parse_fortran_file
from prik.pipeline.pyi import emit_module_stubs
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from tests.fortran._support.parser_properties import (
    _FORTRAN_IDENTIFIER_STEMS,
    _FORTRAN_SCALAR_TYPES,
    _FUZZ_TEXT,
    fortran_subroutines,
)


@pytest.mark.property
@given(fortran_subroutines())
def test_generated_fortran_subroutines_preserve_argument_order(case):
    proc_name, arg_names, source = case

    parsed = parse_fortran_file(source, filename=f"{proc_name}.f90")

    assert parsed.diagnostics == []
    assert len(parsed.procedures) == 1
    procedure = parsed.procedures[0]
    assert procedure.name == proc_name
    assert [arg.name for arg in procedure.arguments] == arg_names


@pytest.mark.property
@given(fortran_subroutines())
def test_generated_fortran_subroutines_survive_case_changes(case):
    proc_name, arg_names, source = case

    parsed = parse_fortran_file(source.upper(), filename=f"{proc_name}.f90")

    assert parsed.diagnostics == []
    assert len(parsed.procedures) == 1
    procedure = parsed.procedures[0]
    assert procedure.name.lower() == proc_name
    assert [arg.name.lower() for arg in procedure.arguments] == arg_names


@pytest.mark.property
@given(fortran_subroutines())
def test_generated_fortran_subroutines_round_trip_through_pyi(case):
    proc_name, arg_names, source = case

    parsed = parse_fortran_file(source, filename=f"{proc_name}.f90")
    modules = fortran_file_to_semantic_modules(parsed, standalone_module_name="generated")
    stub = emit_module_stubs(modules)["generated"]
    reparsed = parse_pyi_text(stub, module_name="generated")

    assert len(reparsed.functions) == 1
    procedure = reparsed.functions[0]
    assert procedure.name == proc_name
    assert [arg.name for arg in procedure.arguments] == arg_names


@pytest.mark.property
@given(
    module_stem=_FORTRAN_IDENTIFIER_STEMS, procedure_stem=_FORTRAN_IDENTIFIER_STEMS, scalar_type=_FORTRAN_SCALAR_TYPES
)
def test_generated_fortran_modules_preserve_owned_declarations(module_stem, procedure_stem, scalar_type):
    module_name = f"mod_{module_stem}"
    procedure_name = f"proc_{procedure_stem}"
    source = (
        f"module {module_name}\n"
        f"  {scalar_type} :: state\n"
        "contains\n"
        f"  subroutine {procedure_name}(value)\n"
        f"    {scalar_type}, intent(in) :: value\n"
        f"  end subroutine {procedure_name}\n"
        f"end module {module_name}\n"
    )

    parsed = parse_fortran_file(source, filename=f"{module_name}.f90")

    assert parsed.diagnostics == []
    assert len(parsed.modules) == 1
    module = parsed.modules[0]
    assert module.name == module_name
    assert [(variable.name, variable.base_type) for variable in module.variables] == [("state", scalar_type)]
    assert [(procedure.name, procedure.module) for procedure in module.procedures] == [(procedure_name, module_name)]
    assert [(argument.name, argument.base_type) for argument in module.procedures[0].arguments] == [
        ("value", scalar_type)
    ]


@pytest.mark.fuzz
@given(_FUZZ_TEXT)
def test_fortran_parser_fuzz_fragments_only_raise_owned_errors(source):
    with suppress(FortranParseError):
        parse_fortran_file(source, filename="fuzz.f90")
