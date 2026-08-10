"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.semantic_conversion import get_function
from prik import parse_fortran_file as parse_fortran_source


def test_scalar_character_inout_is_projected_as_replacement_return():
    parsed = parse_fortran_source(
        """
module chars
contains
  subroutine normalize(name)
    character(len=8), intent(inout) :: name
  end subroutine normalize
end module chars
"""
    )

    func = get_function(fortran_module_to_semantic_module(parsed), "normalize")
    mapping = func.projection[0]

    assert func.arguments[0].semantic_type.name == "String"
    assert mapping.python_position == 0
    assert mapping.native_position == 0
    assert mapping.result_position == 0
