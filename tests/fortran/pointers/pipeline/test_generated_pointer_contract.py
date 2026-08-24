"""Generated `.pyi` parity for the pointer result fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CASES = (
    GeneratedContractCase(
        name="fpointers_f90",
        inputs=(FIXTURES / "native" / "fpointers_f90.f90",),
        expected_package=FIXTURES / "contracts" / "fpointers_f90",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_pointer_contract_matches_fixture(case: GeneratedContractCase, tmp_path: Path):
    assert_generated_contract_matches_fixture(case, tmp_path)
