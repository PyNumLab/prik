import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


# ---------------------------------------------------------------------------
# FortranParseError attributes
# ---------------------------------------------------------------------------


def test_star_kind_in_derived_type_field_is_parsed():
    code = """
module m
  type :: t
    real*8 :: x
  end type t
end module m
"""
    field = parse_fortran_file(code, filename="bad.f90").modules[0].derived_types[0].fields[0]
    assert field.base_type == "real"
    assert field.kind == "8"


def test_unknown_type_in_derived_type_field_raises_parse_error():
    code = """
module m
  type :: t
    weirdtype :: x
  end type t
end module m
"""
    with pytest.raises(FortranParseError, match="Unknown or unsupported datatype"):
        parse_fortran_file(code, filename="bad.f90")


def test_duplicate_field_in_derived_type_raises_parse_error():
    code = """
module m
  type :: point
    real :: x
    integer :: x
  end type point
end module m
"""
    with pytest.raises(FortranParseError, match="Duplicate field"):
        parse_fortran_file(code, filename="dup_field.f90")
