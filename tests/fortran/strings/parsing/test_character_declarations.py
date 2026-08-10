"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from prik import parse_fortran_file


def test_legacy_character_and_star_kind_declarations_from_inline_fortran():
    source = """
      subroutine label(name, x)
      character*(*) name
      real*8 x
      end
"""

    proc = parse_fortran_file(source, filename="label.f").procedures[0]

    assert proc.arguments[0].base_type == "character"
    assert proc.arguments[0].kind == "*"
    assert proc.arguments[1].base_type == "real"

    modern_proc = parse_fortran_file(
        """
subroutine modern_star(x)
  real*8 x
end subroutine modern_star
""",
        filename="modern_star.f90",
    ).procedures[0]
    assert modern_proc.arguments[0].base_type == "real"
    assert modern_proc.arguments[0].kind == "8"
