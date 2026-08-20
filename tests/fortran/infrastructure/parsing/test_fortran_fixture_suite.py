import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file


def parse_fortran_modules(source, filename=None):
    return parse_fortran_file(source, filename=filename).modules


_TESTS_DIR = Path(__file__).parent / "fixtures"
_FIXTURES_DIR = _TESTS_DIR
_SOURCE_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
_UPDATE_GOLDENS = os.getenv("FORTRAN_PARSER_UPDATE_GOLDENS", "0") == "1"


def _has_direct_expected_json(fixture: Path) -> bool:
    return (_FIXTURES_DIR / fixture.relative_to(_TESTS_DIR)).with_suffix(".json").exists()


def _source_json_relpaths(root: Path) -> set[Path]:
    return {
        path.relative_to(root).with_suffix(".json")
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in _SOURCE_SUFFIXES
    }


def _fixture_json_relpaths(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*.json") if path.is_file()}


_GOLDEN_FIXTURES = sorted(
    f
    for f in (_TESTS_DIR / "general").glob("*")
    if f.is_file() and f.suffix.lower() in _SOURCE_SUFFIXES and (_UPDATE_GOLDENS or _has_direct_expected_json(f))
)


def _expected_json_for_fixture(fixture: Path) -> Path:
    rel = fixture.relative_to(_TESTS_DIR)
    direct = (_FIXTURES_DIR / rel).with_suffix(".json")
    if direct.exists():
        return direct
    return _FIXTURES_DIR / "general" / (fixture.stem + ".json")


def _load_expected(expected_path: Path):
    with expected_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _strip_parent_fields(value):
    if isinstance(value, dict):
        return {k: _strip_parent_fields(v) for k, v in value.items() if k != "parent"}
    if isinstance(value, list):
        return [_strip_parent_fields(v) for v in value]
    return value


def _to_dict(value):
    return _strip_parent_fields(asdict(value))


def _dump_expected(path: Path, parsed: dict) -> None:
    payload = parsed
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_fixture_comparison(fixture: Path, *, filename_for_parser: str, expected_path: Path) -> None:
    source = fixture.read_text(encoding="utf-8")
    assert source.strip(), f"Fixture is empty: {filename_for_parser}"

    parsed = _to_dict(parse_fortran_file(source, filename=filename_for_parser))

    if _UPDATE_GOLDENS:
        _dump_expected(expected_path, parsed)
        return

    expected = _load_expected(expected_path)
    assert parsed == expected, f"FortranFile mismatch for {fixture.name}"


def test_fortran_fixture_golden_suite_has_fixtures():
    assert _GOLDEN_FIXTURES, f"No fixtures found in {_TESTS_DIR}"


@pytest.mark.parametrize(
    ("data_root", "fixture_subdir"),
    [
        pytest.param(_TESTS_DIR / "general", "general", id="general-general"),
        pytest.param(_TESTS_DIR / "errors", "errors", id="errors/parser-errors"),
    ],
)
def test_fortran_parser_fixtures_match_data_files_one_to_one(data_root, fixture_subdir):
    fixture_root = _FIXTURES_DIR / fixture_subdir

    expected = _source_json_relpaths(data_root)
    actual = _fixture_json_relpaths(fixture_root)

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    if not _UPDATE_GOLDENS:
        assert not missing, f"Missing parser JSON fixtures for {fixture_subdir}: {missing[:20]}"
    assert not extra, f"Parser JSON fixtures without matching data files in {fixture_subdir}: {extra[:20]}"


@pytest.mark.parametrize("fixture", _GOLDEN_FIXTURES, ids=lambda f: f.name)
def test_fortran_fixture_golden_suite(fixture):
    _run_fixture_comparison(
        fixture,
        filename_for_parser=fixture.name,
        expected_path=_expected_json_for_fixture(fixture),
    )
