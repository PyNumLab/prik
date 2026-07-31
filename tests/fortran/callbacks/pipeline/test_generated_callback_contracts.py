"""Generated `.pyi` package fixtures for callback wrapper inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CASES = tuple(
    GeneratedContractCase(
        name=name,
        inputs=(FIXTURES / f"{name}.f90",),
        expected_package=FIXTURES / "contracts" / name,
    )
    for name in ("fcallback_all_f90", "fcallback_array_f90", "fcallback_scalar_f90")
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_callback_generated_pyi_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
