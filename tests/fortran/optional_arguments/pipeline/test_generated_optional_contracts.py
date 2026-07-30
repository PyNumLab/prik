"""Reviewed generated contracts for optional Fortran arguments."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CONTRACT_ROOT = FIXTURES / "contracts"
CASES = (
    GeneratedContractCase(
        "foptional_fixed",
        (FIXTURES / "foptional_fixed.f",),
        CONTRACT_ROOT / "foptional_fixed",
    ),
    GeneratedContractCase(
        "foptional_f90",
        (FIXTURES / "foptional_f90.f90",),
        CONTRACT_ROOT / "foptional_f90",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_optional_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)
