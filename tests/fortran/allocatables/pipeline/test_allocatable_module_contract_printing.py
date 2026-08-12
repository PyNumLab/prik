"""Generated and reparsed allocatable module and field declarations."""

from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


def _generate_pyi(source: str) -> str:
    return emit_module(fortran_module_to_semantic_module(parse_fortran_source(source)))


def test_emit_and_load_allocatable_module_variable_declaration():
    source = """
module alloc_view_mod
  real(8), allocatable, target :: values(:)
  type :: box
    real(8), allocatable :: field(:)
  end type box
end module alloc_view_mod
"""
    code = _generate_pyi(source)

    assert "values: Annotated[Allocatable[Float64[:]], Aliased]" in code
    assert "field: Allocatable[Float64[:]]" in code

    loaded = parse_pyi_text(code, module_name="alloc_view_mod")
    assert [variable.name for variable in loaded.variables] == ["values"]
    assert loaded.variables[0].semantic_type.storage.array.allocatable is True
    assert loaded.variables[0].semantic_type.metadata["aliased"] is True
    assert loaded.classes[0].fields[0].semantic_type.storage.array.allocatable is True
    assert "aliased" not in loaded.classes[0].fields[0].semantic_type.metadata
