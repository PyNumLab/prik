"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    ProjectionMapping,
    SCALAR_STORAGE_CATEGORY,
    array_contract,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)
from x2py.semantics.metadata import PROJECTED_OUTPUT_METADATA


def test_optional_argument():
    source = """
module opt_mod

contains

subroutine solve(A, tol)

    real(8), intent(in) :: A(:, :)
    real(8), intent(in), optional :: tol

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "solve")

    tol = func.arguments[1]

    assert tol.optional is True


def test_optional_without_intent_uses_visible_conservative_replacement_projection():
    source = """
module no_intent_optional_mod
contains
subroutine adjust(value)
    integer(4), optional :: value
end subroutine adjust
end module no_intent_optional_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    function = get_function(module, "adjust")
    value = function.arguments[0]

    assert value.optional is True
    assert value.metadata[PROJECTED_OUTPUT_METADATA] is True
    assert function.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]


def test_optional_scalar_output_remains_visible_scalar_storage():
    source = """
module opt_out_mod
contains
subroutine maybe_status(status)
    integer(4), intent(out), optional :: status
end subroutine maybe_status
end module opt_out_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))

    func = get_function(smod, "maybe_status")
    status = func.arguments[0]

    assert status.optional is True
    assert array_contract(status.semantic_type).category == SCALAR_STORAGE_CATEGORY
    assert func.projection == [
        ProjectionMapping(
            python_name="status",
            native_name="status",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]


def test_optional_allocatable_output_remains_visible():
    source = """
module opt_alloc_out_mod
contains
subroutine maybe_values(values)
    real(8), allocatable, intent(out), optional :: values(:)
end subroutine maybe_values
end module opt_alloc_out_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))

    func = get_function(smod, "maybe_values")
    values = func.arguments[0]

    assert values.optional is True
    assert array_contract(values.semantic_type).allocatable is True
    assert func.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]


def test_pointer_array_output_visibility_follows_intent_and_optional_presence():
    source = """
module pointer_output_mod
contains
subroutine create_values(values)
    real(8), pointer, intent(out) :: values(:)
end subroutine create_values

subroutine maybe_create_values(values)
    real(8), pointer, optional, intent(out) :: values(:)
end subroutine maybe_create_values

subroutine replace_values(values)
    real(8), pointer, intent(inout) :: values(:)
end subroutine replace_values
end module pointer_output_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    create = get_function(smod, "create_values")
    maybe_create = get_function(smod, "maybe_create_values")
    replace = get_function(smod, "replace_values")

    assert create.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert create.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=None,
            result_position=0,
        )
    ]
    assert maybe_create.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]
    assert replace.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=0,
        )
    ]


def test_optional_scalar_derived_output_stays_visible_without_result_projection():
    source = """
module outputs
type :: point
    real(8) :: x
end type point
contains
subroutine fill(value)
    type(point), intent(out), optional :: value
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
