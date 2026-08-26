"""Reviewed generated contract for the allocatable end-to-end subject."""

from pathlib import Path

import pytest

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CASES = tuple(
    GeneratedContractCase(
        name,
        (FIXTURES / "native" / f"{name}.f90",),
        FIXTURES / "contracts" / name,
    )
    for name in ("fallocatable_views_f90", "fscalar_allocatables_f90")
)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_generated_allocatable_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)
