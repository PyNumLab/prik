"""Optional presence keeps an output dummy visible so the caller can omit it."""

import pytest

from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.metadata import SCALAR_STORAGE_CATEGORY
from prik.semantics.models import ProjectionMapping
from tests.fortran._support.semantic_conversion import array_contract, get_function


@pytest.mark.parametrize(
    ("declaration", "python_position", "result_position"),
    [
        ("integer(4), optional :: value", 0, 0),
        ("integer(4), intent(out), optional :: value", 0, 0),
        ("real(8), allocatable, intent(out), optional :: value(:)", 0, 0),
        ("real(8), pointer, intent(out) :: value(:)", None, 0),
        ("real(8), pointer, optional, intent(out) :: value(:)", 0, 0),
        ("real(8), pointer, intent(inout) :: value(:)", 0, None),
        ("type(point), intent(out), optional :: value", 0, None),
    ],
    ids=[
        "optional-without-intent-conservative-replacement",
        "optional-scalar-output-visible-storage",
        "optional-allocatable-output-visible",
        "required-pointer-output-hidden",
        "optional-pointer-output-visible",
        "pointer-inout-visible-without-result",
        "optional-derived-output-visible-without-result",
    ],
)
def test_optional_output_visibility_follows_intent_and_presence(declaration, python_position, result_position):
    """A required output can be produced for the caller, so it leaves the signature.

    An optional one must stay a visible argument, because only the caller can
    say whether it is present; its result slot follows the object kind.
    """
    source = f"""
module optional_outputs
type :: point
    real(8) :: x
end type point
contains
subroutine update(value)
    {declaration}
end subroutine update
end module optional_outputs
"""

    update = get_function(fortran_module_to_semantic_module(parse_fortran_source(source)), "update")

    assert update.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=python_position,
            result_position=result_position,
        )
    ]
    if declaration == "integer(4), intent(out), optional :: value":
        # The caller lends rank-zero storage the procedure may fill.
        assert array_contract(update.arguments[0].semantic_type).category == SCALAR_STORAGE_CATEGORY
