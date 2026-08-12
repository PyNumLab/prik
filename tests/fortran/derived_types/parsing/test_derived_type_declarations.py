"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from prik.parsers.fortran import parse_fortran_file


def test_derived_type_fields_and_methods_detection():
    code = """
module particle_mod
  type :: particle
    integer :: id
    real(kind=8), dimension(3) :: x
    type(vector), pointer :: velocity
  contains
    procedure :: move, reset
  end type particle
end module particle_mod
"""
    parsed = parse_fortran_file(code)
    types = parsed.modules[0].derived_types
    assert len(types) == 1
    t = types[0]
    assert t.name == "particle"
    assert t.module == "particle_mod"
    assert t.methods == ["move", "reset"]
    assert [f.name for f in t.fields] == ["id", "x", "velocity"]
    assert t.fields[1].shape == ["3"]
    assert t.fields[2].base_type == "derived"
    assert t.fields[2].kind == "vector"


def test_derived_type_extends_and_attributes():
    code = """
module m
  type :: base_t
  end type base_t
  type, extends(base_t), abstract :: child_t
    integer :: id
  contains
    procedure :: run
  end type child_t
end module m
"""
    dt = parse_fortran_file(code).modules[0].derived_types[1]
    assert dt.name == "child_t"
    assert dt.extends is not None
    assert getattr(dt.extends, "name", None) == "base_t"
    assert "abstract" in dt.attributes
