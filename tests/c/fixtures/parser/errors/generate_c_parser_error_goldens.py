"""Generate/update golden files for C parser error fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from prik.parsers.c import CParseError, parse_c_file


_ERRORS_DIR = Path(__file__).resolve().parents[2] / "native" / "errors" / "parser"
_EXPECTED_ERRORS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "errors"
_SOURCE_SUFFIXES = {".c", ".h", ".i"}


def _serialize_error_fixture(fixture: Path) -> dict:
    source = fixture.read_text(encoding="utf-8")
    try:
        parse_c_file(source, filename=fixture.name)
    except CParseError as exc:
        return {
            "parser": "parse_c_file",
            "error_type": "CParseError",
            "message_contains": [exc.base_message],
            "diagnostic_contains": [
                f"error[{exc.code}]",
                exc.base_message,
                exc.source_line.strip() if exc.source_line else "",
            ],
        }
    raise SystemExit(
        f"ERROR: {fixture.name} did not raise CParseError; error fixture files must trigger a parse error."
    )


def _output_path_for_fixture(fixture: Path) -> Path:
    return _EXPECTED_ERRORS_DIR / f"{fixture.name}.json"


def main() -> None:
    requested = sys.argv[1:]
    if requested:
        fixtures = []
        for item in requested:
            fixture = Path(item)
            if not fixture.is_absolute():
                fixture = _ERRORS_DIR / fixture
            if fixture.suffix.lower() not in _SOURCE_SUFFIXES:
                raise SystemExit(f"C error fixtures must use .c, .h, or .i: {fixture}")
            fixtures.append(fixture)
    else:
        fixtures = sorted(
            fixture
            for fixture in _ERRORS_DIR.glob("*")
            if fixture.is_file() and fixture.suffix.lower() in _SOURCE_SUFFIXES
        )
    if not fixtures:
        raise SystemExit("No C parser error fixtures found")

    _EXPECTED_ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    for fixture in fixtures:
        if not fixture.exists():
            raise SystemExit(f"Fixture does not exist: {fixture}")
        payload = _serialize_error_fixture(fixture)
        out = _output_path_for_fixture(fixture)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"updated {out}")


if __name__ == "__main__":
    main()
