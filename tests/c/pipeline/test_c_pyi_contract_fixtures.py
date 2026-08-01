"""C source-to-semantic-`.pyi` fixture contracts."""

from pathlib import Path

import pytest

from tests.c._support.fixture_outputs import (
    C_PYI_FIXTURE_DIR,
    c_pyi_fixture_path,
    c_pyi_text_for_fixture_project,
    iter_general_c_fixture_projects,
)
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.wrapper_codegen.printers import emit_module


C_FIXTURE_PROJECTS = iter_general_c_fixture_projects()


def test_c_pyi_fixture_suite_has_fixtures():
    assert C_FIXTURE_PROJECTS, "No C fixtures found in tests/c/fixtures/native/general"


def test_c_pyi_fixtures_match_general_c_projects_one_to_one():
    expected = {project_key.with_suffix(".pyi") for project_key, _fixtures in C_FIXTURE_PROJECTS}
    actual = {path.relative_to(C_PYI_FIXTURE_DIR) for path in C_PYI_FIXTURE_DIR.rglob("*.pyi") if path.is_file()}

    assert not sorted(expected - actual)
    assert not sorted(actual - expected)


def test_c_pyi_fixtures_do_not_contain_unknown_types():
    unknown_fixtures = [
        str(path.relative_to(C_PYI_FIXTURE_DIR))
        for path in C_PYI_FIXTURE_DIR.rglob("*.pyi")
        if "Unknown" in path.read_text(encoding="utf-8")
    ]

    assert not unknown_fixtures, f"Unknown semantic types in C .pyi fixtures: {unknown_fixtures[:20]}"


@pytest.mark.parametrize(
    ("project_key", "fixtures"),
    C_FIXTURE_PROJECTS,
    ids=[str(project_key) for project_key, _fixtures in C_FIXTURE_PROJECTS],
)
def test_c_pyi_fixture_suite(project_key: Path, fixtures: list[Path]):
    expected_path = c_pyi_fixture_path(project_key)
    expected = expected_path.read_text(encoding="utf-8").strip()

    assert c_pyi_text_for_fixture_project(project_key, fixtures) == expected


@pytest.mark.parametrize(
    "fixture",
    sorted(C_PYI_FIXTURE_DIR.rglob("*.pyi")),
    ids=lambda path: str(path.relative_to(C_PYI_FIXTURE_DIR)),
)
def test_c_pyi_fixtures_round_trip_through_semantic_ir(fixture: Path):
    expected = fixture.read_text(encoding="utf-8").strip()
    module = parse_pyi_text(
        expected,
        module_name=fixture.stem,
        filename=str(fixture),
        native_language="c",
    )

    assert module.name == fixture.stem
    assert emit_module(module).strip() == expected
