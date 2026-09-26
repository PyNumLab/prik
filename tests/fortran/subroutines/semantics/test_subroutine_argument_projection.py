"""Fortran intent and object kind decide whether a dummy projects a replacement result."""

import pytest

from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA
from prik.semantics.models import ProjectionMapping
from tests.fortran._support.semantic_conversion import get_function


@pytest.mark.parametrize(
    ("declaration", "projects_result"),
    [
        ("real(8), intent(inout) :: value", True),
        ("real(8), intent(out) :: value(:)", False),
        ("type(point), intent(out) :: value", False),
    ],
    ids=[
        "primitive-scalar-inout-returns-replacement",
        "array-output-stays-caller-storage",
        "derived-output-stays-caller-object",
    ],
)
def test_output_dummies_stay_visible_and_only_primitive_scalars_project_a_result(
    declaration: str, projects_result: bool
):
    """A primitive scalar is immutable in Python, so its update returns as a result.

    Arrays and derived objects are caller-owned storage the native procedure
    writes in place, so they stay visible arguments without a result slot.
    """
    source = f"""
module outputs
type :: point
    real(8) :: x
end type point
contains
subroutine update(value, factor)
    {declaration}
    real(8), intent(in) :: factor
end subroutine update
end module outputs
"""

    update = get_function(fortran_module_to_semantic_module(parse_fortran_source(source)), "update")

    assert update.arguments[0].metadata.get(PROJECTED_OUTPUT_METADATA, False) is projects_result
    assert update.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=0 if projects_result else None,
        ),
        ProjectionMapping(python_name="factor", native_name="factor", native_position=1, python_position=1),
    ]
