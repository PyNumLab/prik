"""Every parser fixture emits a contract that reloads and prints back unchanged."""

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.policy.exports import complete_python_export_policy
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.fixture_conversion import FORTRAN_FIXTURES
from tests.fortran._support.fixture_outputs import parse_fixture
from tests.fortran._support.paths import PARSER_FIXTURE_ROOT as TESTS_DIR


@pytest.mark.parametrize(
    "fixture",
    FORTRAN_FIXTURES,
    ids=lambda p: str(p.relative_to(TESTS_DIR)),
)
def test_pyi_printer_conversion_smoke(fixture: Path):
    parsed = parse_fixture(fixture)

    for module in parsed.modules:
        semantic_module = fortran_module_to_semantic_module(module)
        complete_python_export_policy(semantic_module)
        code = emit_module(semantic_module)
        assert emit_module(pyi_text_to_semantic_module(code, module_name=semantic_module.name)) == code
