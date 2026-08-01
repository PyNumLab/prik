"""Declaration parsing, interfaces, and less common scope edges."""

import pytest

from prik import FortranParseError, parse_fortran_file


def test_derived_type_field_default_initializers_are_preserved():
    code = """
module init_mod
  type :: state
    integer :: count = 7
    logical :: enabled = .true.
  end type state
end module init_mod
"""

    dtype = parse_fortran_file(code).modules[0].derived_types[0]
    fields = {field.name: field for field in dtype.fields}

    assert fields["count"].value == "7"
    assert fields["count"].symbolic_value == "7"
    assert fields["enabled"].value == "1"
    assert fields["enabled"].symbolic_value == ".true."


def test_malformed_type_bound_declaration_raises():
    code = """
module bad_binding_mod
  type :: t
  contains
    procedure broken_binding
  end type t
end module bad_binding_mod
"""

    with pytest.raises(FortranParseError, match="Unsupported or malformed type-bound declaration"):
        parse_fortran_file(code, filename="bad_binding.f90")


def test_bind_c_derived_type_attribute_and_component_order_are_preserved():
    code = """
module bind_c_type_mod
  use iso_c_binding
  type, bind(C) :: sample
    real(c_double) :: x
    integer(c_int) :: tag
    logical(c_bool) :: active
  end type sample
end module bind_c_type_mod
"""

    dtype = parse_fortran_file(code, filename="bind_c_type.f90").modules[0].derived_types[0]

    assert dtype.attributes == ["bind(c)"]
    assert [field.name for field in dtype.fields] == ["x", "tag", "active"]
