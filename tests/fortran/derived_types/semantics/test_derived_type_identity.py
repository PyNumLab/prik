"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from pathlib import Path

from prik.semantics.fortran2ir import (
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
)
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def test_procedure_local_derived_type_rename_uses_origin_type_identity():
    parsed = parse_fortran_source(
        """
module physics
contains
  subroutine move(p)
    use a_types, only: local_state => state
    type(local_state), intent(inout) :: p
  end subroutine move
end module physics
"""
    )

    module = fortran_module_to_semantic_module(parsed)
    state = get_function(module, "move").arguments[0].semantic_type

    assert state.name == "a_types.state"
    assert state.metadata["external_type_ref"] == {
        "name": "state",
        "local_name": "a_types.state",
        "origin_module": "a_types",
        "wrapped": False,
        "representation": "opaque",
        "import_scope": "procedure",
    }


def test_non_only_rename_does_not_choose_between_derived_type_routes():
    """An ambiguous name and a renamed-away name have no invented type owner."""
    source = NATIVE_FIXTURES / "non_only_rename_derived_type_routes.f90"
    parsed = parse_fortran_source(source.read_text(encoding="utf-8"), filename=source.name)
    modules = {module.name: module for module in fortran_file_to_semantic_modules(parsed)}

    type_x = get_function(modules["consumer"], "take_x").arguments[0].semantic_type
    type_y = get_function(modules["consumer"], "take_y").arguments[0].semantic_type

    assert type_x.name == "x"
    assert "external_type_ref" not in type_x.metadata
    assert type_y.name == "y"
    assert "external_type_ref" not in type_y.metadata


def test_unindexed_non_only_rename_does_not_resurrect_the_source_spelling():
    parsed = parse_fortran_source(
        """
module consumer
  use unavailable_types, x => y
contains
  subroutine take_x(value)
    type(x), intent(in) :: value
  end subroutine take_x
  subroutine take_y(value)
    type(y), intent(in) :: value
  end subroutine take_y
end module consumer
"""
    )
    module = fortran_module_to_semantic_module(parsed)

    type_x = get_function(module, "take_x").arguments[0].semantic_type
    type_y = get_function(module, "take_y").arguments[0].semantic_type

    assert type_x.metadata["external_type_ref"]["origin_module"] == "unavailable_types"
    assert type_x.metadata["external_type_ref"]["name"] == "y"
    assert "external_type_ref" not in type_y.metadata


def test_parsed_module_without_types_is_not_an_opaque_type_route():
    parsed = parse_fortran_source(
        """
module types_mod
  type :: point
    integer :: value
  end type point
end module types_mod

module constants_mod
  integer, parameter :: count = 1
end module constants_mod

module consumer
  use types_mod, only : point
  use constants_mod
contains
  subroutine take(value)
    type(point), intent(in) :: value
  end subroutine take
end module consumer
"""
    )
    modules = {module.name: module for module in fortran_file_to_semantic_modules(parsed)}

    point = get_function(modules["consumer"], "take").arguments[0].semantic_type

    assert point.metadata["external_type_ref"]["origin_module"] == "types_mod"
