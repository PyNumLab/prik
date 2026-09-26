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


def test_character_constants_hold_their_declared_characters_in_extension_and_contract(tmp_path: Path):
    """Each constant holds exactly the characters its declared length counts.

    A doubled quote is one quote, a literal's kind is a type fact rather than
    part of the value, and the generated contract publishes the same value the
    built extension returns.
    """
    source = tmp_path / "quoting.f90"
    source.write_text(SOURCE, encoding="utf-8")
    result = build_fortran_extension(source, output_dir=tmp_path / "build", output_name="quoting_api")
    built = _import_from_build_dir(result.module_name, result.output_dir)

    expected = {
        "word": "don't",
        "pair": 'a"b',
        "plain": "abcd",
        "tagged": "abc",
        "numbered": "xyz",
        "tagged_quote": "don't",
    }
    assert {name: getattr(built.quoting_mod, name) for name in expected} == expected

    contracts = tmp_path / "contracts"
    _generate_checked_pyi_contract(source, contracts, None)
    contract = (contracts / "quoting_mod.pyi").read_text(encoding="utf-8")

    assert 'word: Final[String[5]] = "don\'t"' in contract
    assert "pair: Final[String[3]] = 'a\"b'" in contract
    assert "plain: Final[String[4]] = 'abcd'" in contract
    assert "tagged: Final[String[3]] = 'abc'" in contract
    assert "numbered: Final[String[3]] = 'xyz'" in contract
    assert 'tagged_quote: Final[String[5]] = "don\'t"' in contract
