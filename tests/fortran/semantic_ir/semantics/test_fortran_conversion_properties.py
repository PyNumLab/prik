"""Tests split by stable ownership concept from `test_c_conversion_properties.py`."""

from tests.fortran._support.semantic_properties import (
    asdict,
    fortran_file_to_semantic_modules,
    fortran_scalar_subroutines,
    given,
    parse_fortran_file,
    pytest,
)


@pytest.mark.property
@given(fortran_scalar_subroutines())
def test_generated_fortran_ast_to_semantic_ir_is_deterministic(case):
    source, expected_parameters = case

    first = fortran_file_to_semantic_modules(
        parse_fortran_file(source, filename="generated.f90"),
        standalone_module_name="generated",
    )[0]
    second = fortran_file_to_semantic_modules(
        parse_fortran_file(source, filename="generated.f90"),
        standalone_module_name="generated",
    )[0]

    assert asdict(first) == asdict(second)
    assert len(first.functions) == 1
    function = first.functions[0]
    assert [(arg.name, arg.semantic_type.name) for arg in function.arguments] == expected_parameters
