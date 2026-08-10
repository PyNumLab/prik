"""Public diagnostics for invalid enum specification units."""

import pytest

from prik import FortranParseError, parse_fortran_file
from prik.parsers.fortran.parser import FortranParser
from tests.fortran._support.parser_regressions import _unit


def test_enum_diagnostic_reports_first_invalid_line_after_valid_enumerator():
    with pytest.raises(FortranParseError) as error:
        parse_fortran_file(
            """
module enum_contract
  enum, bind(c)
    enumerator :: valid = 1
    integer :: invalid
  end enum
end module enum_contract
""",
            filename="enum_contract.f90",
        )

    assert error.value.base_message == "Invalid Fortran syntax in enum specification part: integer :: invalid"
    assert error.value.filename == "enum_contract.f90"
    assert error.value.line_number == 5
    assert error.value.source_line.strip() == "integer :: invalid"
    assert error.value.code == "PARSE_INVALID_SYNTAX"


def test_enum_diagnostic_rejects_nested_program_unit_with_source_metadata():
    with pytest.raises(FortranParseError) as error:
        parse_fortran_file(
            """
module enum_contract
  enum, bind(c)
    type :: nested
    end type nested
  end enum
end module enum_contract
""",
            filename="nested_enum_contract.f90",
        )

    assert error.value.base_message == "Invalid Fortran syntax in enum '<unnamed>' specification part: type :: nested"
    assert error.value.filename == "nested_enum_contract.f90"
    assert error.value.line_number == 4
    assert error.value.source_line.strip() == "type :: nested"
    assert error.value.code == "PARSE_INVALID_SYNTAX"


def test_enum_validator_skips_preprocessed_linemarkers_before_enumerators():
    parser = FortranParser()
    unit = _unit(
        "enum",
        None,
        "enum, bind(c)",
        '# 8 "generated.f90"',
        "enumerator :: ready = 1",
        "end enum",
    )

    parser._helper_validate_enum_unit(unit, filename="generated.f90")
