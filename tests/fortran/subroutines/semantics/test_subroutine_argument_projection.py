"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    ProjectionMapping,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)
from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA


def test_primitive_scalar_inout_stays_visible_and_projects_replacement_return():
    source = """
module outputs
contains
subroutine scale_in_place(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
end subroutine scale_in_place
end module outputs
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    scale = get_function(smod, "scale_in_place")

    assert scale.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert scale.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=0,
        ),
        ProjectionMapping(
            python_name="factor",
            native_name="factor",
            native_position=1,
            python_position=1,
        ),
    ]


def test_ordinary_array_output_stays_visible_without_result_projection():
    source = """
module outputs
contains
subroutine fill(values)
    real(8), intent(out) :: values(:)
end subroutine fill
end module outputs
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    fill = get_function(smod, "fill")

    assert PROJECTED_OUTPUT_METADATA not in fill.arguments[0].metadata
    assert fill.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=0,
        )
    ]


def test_scalar_derived_output_stays_visible_without_result_projection():
    source = """
module outputs
type :: point
    real(8) :: x
end type point
contains
subroutine fill(value)
    type(point), intent(out) :: value
end subroutine fill
end module outputs
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    fill = get_function(smod, "fill")

    assert PROJECTED_OUTPUT_METADATA not in fill.arguments[0].metadata
    assert fill.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
        )
    ]
