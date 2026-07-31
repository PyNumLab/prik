"""Generated `.pyi` package fixtures for scalar wrapper inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
    source_contract_case,
)

DATA_TYPE_CONTRACTS = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "baseline" / "contracts"
ARRAY_CONTRACTS = Path(__file__).parents[2] / "arrays" / "end_to_end" / "fixtures" / "baseline" / "contracts"
CASES = (
    source_contract_case(DATA_TYPE_CONTRACTS, "fbind_value_f90.f90"),
    source_contract_case(DATA_TYPE_CONTRACTS, "fmath.f"),
    source_contract_case(ARRAY_CONTRACTS, "fmath_arrays.f"),
    source_contract_case(ARRAY_CONTRACTS, "fmath_arrays_f90.f90"),
    source_contract_case(DATA_TYPE_CONTRACTS, "fmath_f90.f90"),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_scalar_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
