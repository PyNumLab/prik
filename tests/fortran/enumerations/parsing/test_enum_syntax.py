"""Supported Fortran enum syntax."""

from prik.parsers.fortran import parse_fortran_file


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
