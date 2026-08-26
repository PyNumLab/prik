"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.models import ProjectionMapping
from tests.fortran._support.semantic_conversion import get_function
from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


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


ASSUMED_INTENT_SOURCE = """
module legacy
  type :: pt
    real(8) :: x = 0.0d0
  end type pt
contains
subroutine touch(count, item, values, label, declared)
    integer(4) :: count
    type(pt) :: item
    real(8) :: values(:)
    character(len=4) :: label
    integer(4), intent(inout) :: declared
    count = count + 1
    item%x = item%x + 1.0d0
    values = values * 2.0d0
    label = "zzzz"
    declared = declared + 1
end subroutine touch
end module legacy
"""


def _touch_result_names(*, assume_intent_in_scalars):
    smod = fortran_module_to_semantic_module(
        parse_fortran_source(ASSUMED_INTENT_SOURCE),
        assume_intent_in_scalars=assume_intent_in_scalars,
    )
    touch = get_function(smod, "touch")
    return [mapping.native_name for mapping in touch.projection if mapping.result_position is not None]


def test_undeclared_intent_scalar_projects_a_replacement_result_by_default():
    """Primitive and character scalars share one conservative default."""
    assert _touch_result_names(assume_intent_in_scalars=False) == ["count", "label", "declared"]


def test_assumed_scalar_intent_drops_only_the_undeclared_scalar_results():
    """The assumption reaches undeclared scalars, primitive and character alike.

    A declared ``intent(inout)`` scalar keeps its replacement result, and
    arrays and derived-type objects were never projected as results, so their
    in-place contract is unchanged either way.
    """
    assert _touch_result_names(assume_intent_in_scalars=True) == ["declared"]


def test_assumed_scalar_intent_leaves_undeclared_non_scalars_writable():
    smod = fortran_module_to_semantic_module(
        parse_fortran_source(ASSUMED_INTENT_SOURCE),
        assume_intent_in_scalars=True,
    )
    arguments = {argument.name: argument for argument in get_function(smod, "touch").arguments}

    assert arguments["count"].semantic_type.ownership.mutable is False
    assert arguments["item"].semantic_type.ownership.mutable is True
    assert arguments["values"].semantic_type.ownership.mutable is True
