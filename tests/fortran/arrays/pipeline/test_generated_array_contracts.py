"""Generated `.pyi` package fixture for the source-only array wrapper input.

Every other array contract fixture is compared with a freshly generated
contract by the generated-`.pyi` lane of the end-to-end test that replays it.
"""

from __future__ import annotations

from pathlib import Path

from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "end_to_end" / "fixtures"


def test_fmath_arrays_f90_generated_pyi_contract_matches_fixture(tmp_path: Path):
    source = FIXTURE_ROOT / "native" / "fmath_arrays_f90.f90"
    case = GeneratedContractCase(
        name=source.stem,
        inputs=(source,),
        expected_package=FIXTURE_ROOT / "contracts" / source.stem,
    )

    assert_generated_contract_matches_fixture(case, tmp_path)
