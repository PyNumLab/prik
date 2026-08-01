"""Supported Fortran enum syntax and rejected declaration forms."""

import pytest

from prik import FortranParseError, parse_fortran_file


def test_valid_enum_subunit_accepts_optional_separator_and_multiple_enumerators():
    parsed = parse_fortran_file(
        """
module enum_valid_mod
  enum, bind(c)
    enumerator first = -1
    enumerator :: second, third = 10, fourth
  end enum
end module enum_valid_mod
""",
        filename="valid_enum.f90",
    )

    module = parsed.modules[0]
    enum = module.enums[0]
    assert module.name == "enum_valid_mod"
    assert enum.bind_c is True
    assert [(item.name, item.value, item.symbolic_value) for item in enum.enumerators] == [
        ("first", "-1", "-1"),
        ("second", "0", None),
        ("third", "10", "10"),
        ("fourth", "11", None),
    ]


@pytest.mark.parametrize(
    "invalid_line",
    [
        "enumerator :: valid = 1, 2invalid",
        "integer :: invalid",
        "interface invalid",
    ],
)
def test_enum_subunit_rejects_malformed_lines_and_nested_units(invalid_line):
    code = f"""
module enum_invalid_mod
  enum, bind(c)
    {invalid_line}
  end enum
end module enum_invalid_mod
"""

    with pytest.raises(FortranParseError, match="Invalid Fortran syntax"):
        parse_fortran_file(code, filename="invalid_enum.f90")
