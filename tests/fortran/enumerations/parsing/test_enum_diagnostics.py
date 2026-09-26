"""Public diagnostics for invalid enum specification units."""

import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


@pytest.mark.parametrize(
    ("invalid_line", "message"),
    [
        pytest.param(
            "enumerator :: valid = 1, 2invalid",
            "Invalid Fortran syntax in enum specification part: enumerator :: valid = 1, 2invalid",
            id="malformed-enumerator",
        ),
        pytest.param(
            "integer :: invalid",
            "Invalid Fortran syntax in enum specification part: integer :: invalid",
            id="declaration-statement",
        ),
        pytest.param(
            "interface invalid",
            "Invalid Fortran syntax in enum specification part: interface invalid",
            id="nested-interface",
        ),
        pytest.param(
            "type :: nested\n    end type nested",
            "Invalid Fortran syntax in enum '<unnamed>' specification part: type :: nested",
            id="nested-program-unit",
        ),
    ],
)
def test_enum_diagnostic_reports_the_first_invalid_line_after_a_valid_enumerator(invalid_line: str, message: str):
    """The diagnostic names the offending line and its location, not the enum as a whole."""
    with pytest.raises(FortranParseError) as error:
        parse_fortran_file(
            f"""
module enum_contract
  enum, bind(c)
    enumerator :: valid = 1
    {invalid_line}
  end enum
end module enum_contract
""",
            filename="enum_contract.f90",
        )

    assert error.value.base_message == message
    assert error.value.filename == "enum_contract.f90"
    assert error.value.line_number == 5
    assert error.value.source_line.strip() == invalid_line.splitlines()[0]
    assert error.value.code == "PARSE_INVALID_SYNTAX"


def test_enum_accepts_preprocessed_linemarkers_before_enumerators():
    """A compiler preprocessor's line marker is provenance, not an enum statement."""
    parsed = parse_fortran_file(
        'module m\n  enum, bind(c)\n# 8 "generated.f90"\n    enumerator :: ready = 1\n  end enum\nend module m\n',
        filename="generated.f90",
    )

    assert [(item.name, item.value) for item in parsed.modules[0].enums[0].enumerators] == [("ready", "1")]
