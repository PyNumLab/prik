"""C parser error fixture and diagnostic golden regression tests."""

import json
import os
from pathlib import Path

import pytest


_C_ROOT = Path(__file__).resolve().parents[1]
_ERRORS_DIR = _C_ROOT / "fixtures" / "native" / "errors" / "parser"
_EXPECTED_ERRORS_DIR = _C_ROOT / "fixtures" / "parser" / "fixtures" / "errors"
_SOURCE_SUFFIXES = {".c", ".h", ".i"}


def _expected_path_for_fixture(fixture: Path) -> Path:
    return _EXPECTED_ERRORS_DIR / f"{fixture.name}.json"


def _load_expected_error(expected_path: Path) -> dict:
    return json.loads(expected_path.read_text(encoding="utf-8"))


def _dump_expected_error(path: Path, error_type: str, exc, parser: str) -> None:
    payload = {
        "parser": parser,
        "error_type": error_type,
        "message_contains": [exc.base_message],
        "diagnostic_contains": [
            f"error[{exc.code}]",
            exc.base_message,
            exc.source_line.strip() if exc.source_line else "",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _update_mode_enabled() -> bool:
    return os.getenv("C_PARSER_UPDATE_GOLDENS", "0") == "1"


def test_c_error_fixture_suite_has_fixtures():
    fixtures = [path for path in _ERRORS_DIR.glob("*") if path.suffix.lower() in _SOURCE_SUFFIXES]
    assert fixtures, "No C parser error fixtures found in tests/c/fixtures/native/errors/parser"


def test_c_error_fixtures_have_matching_expected_json():
    fixture_outputs = {f"{path.name}.json" for path in _ERRORS_DIR.glob("*") if path.suffix.lower() in _SOURCE_SUFFIXES}
    expected_outputs = {path.name for path in _EXPECTED_ERRORS_DIR.glob("*.json")}

    assert not sorted(fixture_outputs - expected_outputs)
    assert not sorted(expected_outputs - fixture_outputs)


def test_c_error_fixture_suite_reports_expected_diagnostics():
    from x2py.parsers.c import CParseError, parse_c_file

    for fixture in sorted(_ERRORS_DIR.glob("*")):
        if fixture.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        expected_path = _expected_path_for_fixture(fixture)
        source = fixture.read_text(encoding="utf-8")

        if _update_mode_enabled():
            try:
                parse_c_file(source, filename=fixture.name)
                raise AssertionError(f"Expected CParseError from {fixture.name} but no error was raised")
            except CParseError as exc:
                _dump_expected_error(expected_path, "CParseError", exc, "parse_c_file")
            continue

        expected = _load_expected_error(expected_path)
        assert expected["parser"] == "parse_c_file"
        assert expected["error_type"] == "CParseError"
        with pytest.raises(CParseError) as exc_info:
            parse_c_file(source, filename=fixture.name)

        for fragment in expected["message_contains"]:
            assert fragment in str(exc_info.value)
        diagnostic = exc_info.value.format_diagnostic(color=False)
        for fragment in expected.get("diagnostic_contains", []):
            if fragment:
                assert fragment in diagnostic
