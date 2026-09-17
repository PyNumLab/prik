"""A character constant reaches Python holding the characters it declares.

Fortran doubles a quote to hold one, so `'don''t'` is five characters. Python
reads that same spelling as two literals written side by side and joins them,
which silently drops the quote. Both the generated contract and the built
extension therefore decode the Fortran literal rather than hand its text to a
Python reader.
"""

from pathlib import Path

import pytest

from prik.pipeline.build import build_fortran_extension
from tests.fortran._support.wrapper_build import _generate_checked_pyi_contract, _import_from_build_dir

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = """\
module quoting_mod
  implicit none
  character(len=5), parameter :: word = 'don''t'
  character(len=3), parameter :: pair = "a""b"
  character(len=4), parameter :: plain = 'abcd'
end module quoting_mod
"""


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Build the quoting source once for the read-only checks."""
    tmp_path = tmp_path_factory.mktemp("character_quoting")
    source = tmp_path / "quoting.f90"
    source.write_text(SOURCE, encoding="utf-8")
    result = build_fortran_extension(source, output_dir=tmp_path / "build", output_name="quoting_api")
    return _import_from_build_dir(result.module_name, result.output_dir)


def test_a_doubled_quote_reaches_python_as_one_quote(built):
    """Each constant holds exactly the characters its declared length counts."""
    assert built.quoting_mod.word == "don't"
    assert built.quoting_mod.pair == 'a"b'
    assert built.quoting_mod.plain == "abcd"


def test_a_generated_contract_states_the_declared_characters(tmp_path: Path):
    """The contract publishes the same value the extension returns."""
    source = tmp_path / "quoting.f90"
    source.write_text(SOURCE, encoding="utf-8")
    contracts = tmp_path / "contracts"

    _generate_checked_pyi_contract(source, contracts, None)
    contract = (contracts / "quoting_mod.pyi").read_text(encoding="utf-8")

    assert 'word: Final[String[5]] = "don\'t"' in contract
    assert "pair: Final[String[3]] = 'a\"b'" in contract
    assert "plain: Final[String[4]] = 'abcd'" in contract
