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

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SOURCE = (NATIVE_FIXTURES / "fcharacter_constant_quoting.f90").read_text(encoding="utf-8")


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


def test_a_literal_states_its_kind_without_the_kind_joining_the_value(built):
    """A literal's kind is a type fact, so only its characters are the value."""
    assert built.quoting_mod.tagged == "abc"
    assert built.quoting_mod.numbered == "xyz"
    assert built.quoting_mod.tagged_quote == "don't"


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
    assert "tagged: Final[String[3]] = 'abc'" in contract
    assert "numbered: Final[String[3]] = 'xyz'" in contract
    assert 'tagged_quote: Final[String[5]] = "don\'t"' in contract
