"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


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
