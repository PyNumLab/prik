"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from prik.parsers.fortran import parse_fortran_file


def test_fixed_form_character_star_length_is_parsed():
    code = """
      subroutine xerbla(srname, info)
      character*(*) srname
      integer info
      end
"""
    sigs = parse_fortran_file(code, filename="legacy.f").procedures
    assert len(sigs) == 1
    assert sigs[0].arguments[0].base_type == "character"
    assert sigs[0].arguments[0].kind == "*"
