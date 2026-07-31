"""Generated contract surface for allocatable outputs and results."""

from tests.fortran._support.semantic_conversion import (
    emit_module,
    fortran_module_to_semantic_module,
    parse_fortran_source,
)


def _generate_pyi(source: str) -> str:
    return emit_module(fortran_module_to_semantic_module(parse_fortran_source(source)))


def test_emit_allocatable():
    source = """
module alloc_mod

contains

subroutine build(x)

    real(8), allocatable, intent(out) :: x(:)

end subroutine

function make_values() result(x)

    real(8), allocatable :: x(:)

end function

end module
"""

    code = _generate_pyi(source)

    assert "Allocatable" in code
    assert "@native_call([Return('x', 0)])" in code
    assert "def build() -> Allocatable[Float64[:]]: ..." in code
    assert "def make_values() -> Allocatable[Float64[:]]: ..." in code
