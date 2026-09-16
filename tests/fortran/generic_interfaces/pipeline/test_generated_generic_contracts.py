"""Reviewed generated contracts for generics and defined operators."""

from __future__ import annotations

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.generated_contracts import (
    GeneratedContractCase,
    assert_generated_contract_matches_fixture,
    contract_case_id,
)

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
CONTRACT_ROOT = FIXTURES / "contracts"
CASES = (
    GeneratedContractCase(
        "foverloads_f90",
        (FIXTURES / "native" / "foverloads_f90.f90",),
        CONTRACT_ROOT / "foverloads_f90",
    ),
    GeneratedContractCase(
        "foverloads_fixed",
        (FIXTURES / "native" / "foverloads_fixed.f",),
        CONTRACT_ROOT / "foverloads_fixed",
    ),
    GeneratedContractCase(
        "foperators_f90",
        (FIXTURES / "native" / "foperators_f90.f90",),
        CONTRACT_ROOT / "foperators_f90",
    ),
)


@pytest.mark.parametrize("case", CASES, ids=contract_case_id)
def test_generated_generic_contract_matches_fixture(
    case: GeneratedContractCase,
    tmp_path: Path,
):
    assert_generated_contract_matches_fixture(case, tmp_path)


def test_overload_names_its_specific_as_the_contract_declares_it():
    """An overload target names a declaration this contract holds.

    A specific whose Fortran spelling carries capitals is declared under its
    Python name, so the overload naming it is written the same way; the source
    spelling would name no declaration in the contract at all.
    """
    source = """
module powalg_mod
implicit none
private
public :: qradd
interface qradd
module procedure qradd_Rdiag
end interface qradd
contains
subroutine qradd_Rdiag(x)
real(8), intent(inout) :: x
end subroutine qradd_Rdiag
end module powalg_mod
"""

    code = emit_module(
        fortran_module_to_semantic_module(parse_fortran_source(source)),
        normalize_public_names=True,
    )

    assert "def qradd_rdiag(" in code
    assert '@overload("qradd_rdiag")' in code
    assert "qradd_Rdiag" not in code
