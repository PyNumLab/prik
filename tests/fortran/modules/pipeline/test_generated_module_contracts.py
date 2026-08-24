"""Reviewed generated contracts for ordinary module state."""

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
        "fcommon_block_f90",
        (FIXTURES / "native" / "fcommon_block_f90.f90",),
        CONTRACT_ROOT / "fcommon_block_f90",
    ),
    GeneratedContractCase(
        "fmodule_vars_f90",
        (FIXTURES / "native" / "fmodule_vars_f90.f90",),
        CONTRACT_ROOT / "fmodule_vars_f90",
    ),
    GeneratedContractCase(
        "module_exports",
        (FIXTURES / "native" / "module_exports.f90",),
        CONTRACT_ROOT / "module_exports",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_module_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)
