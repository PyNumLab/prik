import json
from pathlib import Path

import pytest

from tests.fortran._support.fixture_conversion import FORTRAN_FIXTURES, TESTS_DIR, parse_fixture
from tests.fortran._support.fixture_outputs import (
    SEMANTICS_FIXTURE_DIR,
    semantic_payload_for_fixture,
    semantics_fixture_path,
)


def test_semantics_fixture_suite_has_fixtures():
    assert FORTRAN_FIXTURES, "No final general Fortran parser fixtures found"


def test_semantic_fixtures_match_fortran_data_one_to_one():
    expected = {path.with_suffix(".json").name for path in FORTRAN_FIXTURES}
    actual = {path.name for path in SEMANTICS_FIXTURE_DIR.glob("*.json")}

    assert not sorted(expected - actual)
    assert not sorted(actual - expected)


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

    assert semantic_payload_for_fixture(fixture) == expected


def test_semantic_fixtures_do_not_contain_unknown_types():
    unknown_types = []
    for path in SEMANTICS_FIXTURE_DIR.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for semantic_type in _iter_semantic_types(payload):
            if semantic_type.get("name") == "Unknown" or semantic_type.get("dtype") == "Unknown":
                unknown_types.append(path.name)

    assert not unknown_types, f"Unknown semantic types in fixtures: {unknown_types[:20]}"
