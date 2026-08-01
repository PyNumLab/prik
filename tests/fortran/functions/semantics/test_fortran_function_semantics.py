"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    ProjectionMapping,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)
from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA


def test_missing_intent_scalar_uses_conservative_replacement_projection():
    source = """
real(4) function square(value) result(output)
    real(4) :: value
    output = value * value
end function square
"""

    smod = fortran_file_to_semantic_modules(parse_fortran_source(source))[0]
    square = get_function(smod, "square")

    assert square.arguments[0].semantic_type.storage.mutable is True
    assert square.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert square.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=1,
        )
    ]


def test_function_result():
    source = """
module func_mod

contains

function norm2(x) result(r)

    real(8), intent(in) :: x(:)

    real(8) :: r

end function

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "norm2")

    assert func.return_type is not None

    assert func.return_type.name == "Float64"
