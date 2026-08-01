import json
import os
from pathlib import Path

import pytest

from prik import FortranParseError, parse_fortran_file


def parse_fortran_procedures(source, filename=None):
    return parse_fortran_file(source, filename=filename).procedures


def parse_fortran_types(source, filename=None):
    return parse_fortran_file(source, filename=filename).derived_types


def parse_fortran_modules(source, filename=None):
    return parse_fortran_file(source, filename=filename).modules


_ERRORS_DIR = Path(__file__).parent / "fixtures" / "errors"
_EXPECTED_ERRORS_DIR = _ERRORS_DIR
_PARSER_MAP = {
    "parse_fortran_procedures": parse_fortran_procedures,
    "parse_fortran_types": parse_fortran_types,
    "parse_fortran_modules": parse_fortran_modules,
}
_ERROR_FIXTURES = sorted(
    f
    for f in _ERRORS_DIR.glob("*")
    if f.is_file() and f.suffix.lower() in {".f", ".f90", ".f95", ".f03", ".f08", ".f77", ".for", ".ftn"}
)


def _load_expected_error(expected_path: Path) -> dict:
    with expected_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _dump_expected_error(path: Path, error_type: str, exc: FortranParseError, parser: str) -> None:
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
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_error_fixture(fixture: Path, *, filename_for_parser: str, expected_path: Path) -> None:
    source = fixture.read_text(encoding="utf-8")
    assert source.strip(), f"Error fixture is empty: {filename_for_parser}"

    update_mode = os.getenv("FORTRAN_PARSER_UPDATE_GOLDENS", "0") == "1"

    if update_mode:
        expected = _load_expected_error(expected_path)
        parser_name = expected.get("parser", "parse_fortran_procedures")
        parser_fn = _PARSER_MAP[parser_name]
        try:
            parser_fn(source, filename=filename_for_parser)
            raise AssertionError(f"Expected FortranParseError from {fixture.name} but no error was raised")
        except FortranParseError as exc:
            _dump_expected_error(expected_path, "FortranParseError", exc, parser_name)
        return

    expected = _load_expected_error(expected_path)
    parser_name = expected["parser"]
    parser_fn = _PARSER_MAP[parser_name]
    error_type = expected["error_type"]
    message_contains = expected["message_contains"]
    diagnostic_contains = expected.get("diagnostic_contains", [])

    assert error_type == "FortranParseError", f"Unknown error_type '{error_type}' in {expected_path.name}"

    with pytest.raises(FortranParseError) as exc_info:
        parser_fn(source, filename=filename_for_parser)

    err_msg = str(exc_info.value)
    for fragment in message_contains:
        assert fragment in err_msg, (
            f"Expected fragment {fragment!r} not found in error message for {fixture.name}.\nGot: {err_msg!r}"
        )

    diagnostic = exc_info.value.format_diagnostic(color=False)
    for fragment in diagnostic_contains:
        if not fragment:
            continue
        assert fragment in diagnostic, (
            f"Expected diagnostic fragment {fragment!r} not found for {fixture.name}.\nGot: {diagnostic!r}"
        )


def test_fortran_error_fixture_suite_has_fixtures():
    assert _ERROR_FIXTURES, f"No parser error fixtures found in {_ERRORS_DIR}"


@pytest.mark.parametrize("fixture", _ERROR_FIXTURES, ids=lambda f: f.name)
def test_fortran_error_fixture_suite(fixture):
    _run_error_fixture(
        fixture,
        filename_for_parser=fixture.name,
        expected_path=_EXPECTED_ERRORS_DIR / f"{fixture.stem}.json",
    )
