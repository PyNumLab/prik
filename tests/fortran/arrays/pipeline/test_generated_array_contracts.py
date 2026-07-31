"""Generated `.pyi` package fixtures for array wrapper inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "end_to_end" / "fixtures"
CONTRACT_ROOT = FIXTURE_ROOT / "contracts"
CASES = tuple(
    GeneratedContractCase(
        name=source.stem,
        inputs=(source,),
        expected_package=CONTRACT_ROOT / source.stem,
    )
    for source in (
        FIXTURE_ROOT / "farray_contracts_f90.f90",
        FIXTURE_ROOT / "farray_results_f90.f90",
        FIXTURE_ROOT / "fassumed_rank_f90.f90",
        FIXTURE_ROOT / "multid_arrays.f90",
    )
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_array_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
