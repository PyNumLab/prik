"""Generated `.pyi` package fixtures for direct source-build inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FEATURE_ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = FEATURE_ROOT / "end_to_end" / "fixtures" / "native"
CONTRACT_ROOT = Path(__file__).parent / "fixtures" / "generated_contracts" / "source_builds"
CASES = (
    GeneratedContractCase("fdefault_output", (NATIVE_ROOT / "fdefault_output.f",), CONTRACT_ROOT / "fdefault_output"),
    GeneratedContractCase(
        "fruntime_abi_f90",
        (NATIVE_ROOT / "fruntime_abi_f90.f90",),
        CONTRACT_ROOT / "fruntime_abi_f90",
    ),
    GeneratedContractCase("verbose_api", (NATIVE_ROOT / "verbose_api.f90",), CONTRACT_ROOT / "verbose_api"),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_source_build_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
