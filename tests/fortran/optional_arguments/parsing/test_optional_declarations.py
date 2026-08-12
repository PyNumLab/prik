"""Fortran optional attributes survive free- and fixed-form parsing."""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"


@pytest.mark.parametrize(
    ("fixture_name", "procedure_name", "argument_name"),
    [
        ("foptional_f90.f90", "summarize", "scale"),
        ("foptional_fixed.f", "optional_scale", "factor"),
    ],
)
def test_optional_dummy_attribute_is_preserved(
    fixture_name: str,
    procedure_name: str,
    argument_name: str,
):
    source = FIXTURES.joinpath(fixture_name)
    parsed = parse_fortran_file(source.read_text(encoding="utf-8"), filename=str(source))
    procedures = [
        *parsed.procedures,
        *(procedure for module in parsed.modules for procedure in module.procedures),
    ]
    procedure = next(item for item in procedures if item.name == procedure_name)
    argument = next(item for item in procedure.arguments if item.name == argument_name)

    assert argument.optional is True
