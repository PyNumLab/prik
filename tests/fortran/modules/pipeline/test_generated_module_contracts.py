"""Reviewed generated contracts for ordinary module state."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

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


def test_non_intrinsic_module_with_an_intrinsic_name_is_imported_and_reexported(tmp_path: Path):
    """A facade re-export from a user ``iso_fortran_env`` reaches the contract as an import."""
    user_module = tmp_path / "user_env.f90"
    user_module.write_text(
        "module iso_fortran_env\n  implicit none\n  integer :: my_value = 7\nend module iso_fortran_env\n",
        encoding="utf-8",
    )
    facade = tmp_path / "facade.f90"
    facade.write_text(
        "module facade\n  use, non_intrinsic :: iso_fortran_env, only: my_value\n  implicit none\nend module facade\n",
        encoding="utf-8",
    )
    contract = tmp_path / "contract"
    subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--pyi", str(user_module), str(facade), "--out", str(contract)],
        check=True,
        capture_output=True,
        text=True,
    )

    text = (contract / "facade.pyi").read_text(encoding="utf-8")
    assert "from .iso_fortran_env import my_value" in text
    assert '"my_value"' in text
