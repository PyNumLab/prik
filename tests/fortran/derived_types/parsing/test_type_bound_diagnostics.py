"""Tests split by stable ownership concept from `test_source_form_and_diagnostics_regressions.py`."""

import pytest
from prik.parsers.fortran import FortranParseError
from prik.parsers.fortran.models import FortranDerivedType
from prik.parsers.fortran.parser import FortranParser


def test_malformed_type_bound_declaration_diagnostic_preserves_public_metadata():
    parser = FortranParser()
    dtype = FortranDerivedType("state_t")

    with pytest.raises(FortranParseError) as error:
        parser._parse_derived_type_contains_line(
            "FINAL :: 123",
            dtype,
            filename="type_bound_contract.f90",
            lineno=9,
            source_line="FINAL :: 123",
        )

    assert error.value.base_message == "Unsupported or malformed type-bound declaration in type 'state_t': FINAL :: 123"
    assert error.value.filename == "type_bound_contract.f90"
    assert error.value.line_number == 9
    assert error.value.source_line == "FINAL :: 123"
    assert error.value.code == "PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION"
