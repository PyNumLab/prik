from pathlib import Path

import pytest

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.printers import emit_module

from tests.fortran._support.fixture_outputs import (
    PARSER_FIXTURE_ROOT as TESTS_DIR,
    parse_fixture,
)
from tests.fortran._support.fixture_conversion import FORTRAN_FIXTURES


def test_pyi_printer_fixture_suite_has_fixtures():
    assert FORTRAN_FIXTURES, "No final general Fortran parser fixtures found"


@pytest.mark.parametrize(
    "fixture",
    FORTRAN_FIXTURES,
    ids=lambda p: str(p.relative_to(TESTS_DIR)),
)
def test_pyi_printer_conversion_smoke(fixture: Path):
    parsed = parse_fixture(fixture)

    for module in parsed.modules:
        semantic_module = fortran_module_to_semantic_module(module)
        emit_module(semantic_module)
