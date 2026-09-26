"""Declaration parsing, interfaces, and less common scope edges."""

import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


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


@pytest.mark.parametrize("declaration", ["procedure broken_binding", "FINAL :: 123"])
def test_malformed_type_bound_declaration_reports_its_location_and_code(declaration: str):
    code = f"""
module bad_binding_mod
  type :: t
  contains
    {declaration}
  end type t
end module bad_binding_mod
"""

    with pytest.raises(FortranParseError) as error:
        parse_fortran_file(code, filename="bad_binding.f90")

    assert error.value.base_message == f"Unsupported or malformed type-bound declaration in type 't': {declaration}"
    assert error.value.filename == "bad_binding.f90"
    assert error.value.line_number == 5
    assert error.value.source_line.strip() == declaration
    assert error.value.code == "PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION"
