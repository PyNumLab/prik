"""Reviewed generated semantic `.pyi` package for Fortran enumerations."""

from pathlib import Path

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CASE = GeneratedContractCase(
    name="fenums_f90",
    inputs=(FIXTURES / "native" / "fenums_f90.f90",),
    expected_package=FIXTURES / "contracts" / "fenums_f90",
)


def test_generated_enum_contract_matches_reviewed_package(tmp_path: Path):
    assert_generated_contract_matches_fixture(CASE, tmp_path)
