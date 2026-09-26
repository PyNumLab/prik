import json
from pathlib import Path

import pytest

from tests.fortran._support.fixture_outputs import parse_fixture
from tests.fortran._support.paths import PARSER_FIXTURE_ROOT as TESTS_DIR
from tests.fortran._support.fixture_conversion import FORTRAN_FIXTURES
from tests.fortran._support.fixture_outputs import (
    semantic_payload_for_fixture,
    semantics_fixture_path,
)


def _iter_semantic_types(node):
    if isinstance(node, dict):
        if "semantic_type" in node:
            yield node["semantic_type"]
        if "return_type" in node and node["return_type"] is not None:
            yield node["return_type"]
        for value in node.values():
            yield from _iter_semantic_types(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_semantic_types(item)


@pytest.mark.parametrize(
    "fixture",
    FORTRAN_FIXTURES,
    ids=lambda p: str(p.relative_to(TESTS_DIR)),
)
def test_semantic_model_fixture_suite(fixture: Path):
    parse_fixture(fixture)
    expected_path = semantics_fixture_path(fixture)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    payload = semantic_payload_for_fixture(fixture)

    assert payload == expected
    unknown = [
        semantic_type
        for semantic_type in _iter_semantic_types(payload)
        if semantic_type.get("name") == "Unknown" or semantic_type.get("dtype") == "Unknown"
    ]
    assert not unknown, f"Unknown semantic types: {unknown[:20]}"
