"""Generated contract surface for optional allocatable outputs."""

from prik.codegen.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik import parse_fortran_file as parse_fortran_source


def _generate_pyi(source: str) -> str:
    return emit_module(fortran_module_to_semantic_module(parse_fortran_source(source)))


def test_emit_optional_allocatable_output_as_visible_argument():
    source = """
module opt_alloc_out_mod
contains
subroutine maybe_values(values)
    real(8), allocatable, intent(out), optional :: values(:)
end subroutine maybe_values
end module opt_alloc_out_mod
"""

    code = _generate_pyi(source)

    assert "Return('values'" not in code
    assert "values: Allocatable[Float64[:]] | None = ..." in code
    assert ') -> Returns["values", Allocatable[Float64[:]]] | None: ...' in code
