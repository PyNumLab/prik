"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    fortran_module_to_semantic_module,
)
from prik.semantics.models import ProjectionMapping
from tests.fortran._support.semantic_conversion import array_contract
from prik import parse_fortran_file as parse_fortran_source


def test_converter_preserves_allocatable_target_metadata():
    source = """
module alloc_target_mod
  real(8), allocatable, target :: values(:)
  type :: box
    real(8), allocatable :: field(:)
  end type box
end module alloc_target_mod
"""
    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    values = module.variables[0]
    assert values.name == "values"
    assert values.semantic_type.storage.array.allocatable is True
    assert values.semantic_type.metadata["aliased"] is True

    field = module.classes[0].fields[0]
    assert field.semantic_type.storage.array.allocatable is True
    assert "aliased" not in field.semantic_type.metadata


def test_allocatable_output_semantics_projects_a_hidden_descriptor_handle():
    source = """
module alloc_mod
contains
subroutine build(x)
    real(8), allocatable, intent(out) :: x(:)
end subroutine build
end module alloc_mod
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    function = module.functions[0]
    output = function.arguments[0]

    assert array_contract(output.semantic_type).allocatable is True
    assert function.projection == [
        ProjectionMapping(
            python_name="x",
            native_name="x",
            native_position=0,
            python_position=None,
            result_position=0,
        )
    ]
