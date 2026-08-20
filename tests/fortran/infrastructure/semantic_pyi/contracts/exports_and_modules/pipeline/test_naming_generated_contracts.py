"""Generated `.pyi` package fixtures for naming and dispatch wrapper inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
    source_contract_case,
)

CONTRACT_ROOT = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "visibility" / "contracts"
CASES = (source_contract_case(CONTRACT_ROOT, "fnaming_f90.f90"),)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_naming_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
