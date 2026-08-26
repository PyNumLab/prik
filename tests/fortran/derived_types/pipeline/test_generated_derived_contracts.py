"""Reviewed generated contracts for derived-type feature subjects."""

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
CASES = tuple(
    GeneratedContractCase(
        name,
        (FIXTURES / "native" / f"{name}.f90",),
        CONTRACT_ROOT / name,
    )
    for name in (
        "fbind_c_derived_layout_f90",
        "fborrowed_finalizer_f90",
        "fclasses_f90",
        "fconstructors_f90",
        "fderived_boundary_f90",
        "finheritance_f90",
    )
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_derived_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)
