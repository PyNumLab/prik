"""Generated `.pyi` package fixtures for runtime-behavior wrapper inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
    source_contract_case,
)

CONTRACT_ROOT = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "runtime" / "contracts"
CASES = (
    source_contract_case(CONTRACT_ROOT, "fopenmp_runtime_f90.f90"),
    source_contract_case(CONTRACT_ROOT, "fruntime_recursion_f90.f90"),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_runtime_behavior_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
