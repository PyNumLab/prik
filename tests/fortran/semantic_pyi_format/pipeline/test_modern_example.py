from pathlib import Path

from prik import parse_fortran_file
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.codegen.printers import emit_module


def test_modern_fortran_example_pyi_snapshot():
    fixture = (
        Path(__file__).resolve().parents[2]
        / "source_parsing"
        / "parsing"
        / "fixtures"
        / "general"
        / "modern_pyi_example.f90"
    )
    expected_fixture = Path(__file__).parent / "fixtures" / "modern_math_physics.pyi"
    source = fixture.read_text(encoding="utf-8")

    parsed = parse_fortran_file(source, filename=str(fixture.name))
    modules = [fortran_module_to_semantic_module(m) for m in parsed.modules]
    pyi = "\n\n".join(emit_module(m) for m in modules).strip()

    assert pyi == expected_fixture.read_text(encoding="utf-8").strip()


def test_pyi_visibility_private_public_markers():
    source = """
module visibility_mod
  implicit none
  private
  public :: pub_proc, visible_t

  type :: visible_t
     integer :: a
     integer :: b
  end type visible_t

  type :: hidden_t
     integer :: z
  end type hidden_t

contains
  subroutine pub_proc(x)
    integer, intent(in) :: x
  end subroutine pub_proc

  subroutine hidden_proc(x)
    integer, intent(in) :: x
  end subroutine hidden_proc
end module visibility_mod
"""
    parsed = parse_fortran_file(source, filename="visibility_mod.f90")
    pyi = emit_module(fortran_module_to_semantic_module(parsed.modules[0])).strip()

    assert "a: Int32" in pyi
    assert "b: Int32" in pyi
    assert "class hidden_t:" not in pyi
    assert "def pub_proc(" in pyi
    assert "def hidden_proc(" not in pyi
