"""Generated semantic-contract evidence for the primitive scalar fixture."""

from pathlib import Path

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
)


FEATURE_ROOT = Path(__file__).parents[1]
FIXTURES = FEATURE_ROOT / "end_to_end" / "fixtures"
CASE = GeneratedContractCase(
    name="fscalar_kinds_f90",
    inputs=(FIXTURES / "fscalar_kinds_f90.f90",),
    expected_package=FIXTURES / "contracts" / "fscalar_kinds_f90",
)


def test_generated_primitive_scalar_contract_matches_reviewed_package(tmp_path: Path):
    assert_generated_contract_matches_fixture(CASE, tmp_path)
