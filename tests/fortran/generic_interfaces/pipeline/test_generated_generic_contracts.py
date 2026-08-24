"""Reviewed generated contracts for generics and defined operators."""

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
        "foverloads_f90",
        (FIXTURES / "native" / "foverloads_f90.f90",),
        CONTRACT_ROOT / "foverloads_f90",
    ),
    GeneratedContractCase(
        "foverloads_fixed",
        (FIXTURES / "native" / "foverloads_fixed.f",),
        CONTRACT_ROOT / "foverloads_fixed",
    ),
    GeneratedContractCase(
        "foperators_f90",
        (FIXTURES / "native" / "foperators_f90.f90",),
        CONTRACT_ROOT / "foperators_f90",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_generic_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)
