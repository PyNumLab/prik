"""Generate/update golden files for Fortran parser error fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def parse_fortran_procedures(source, filename=None):
    return _parse_fortran_file(source, filename=filename).procedures


def parse_fortran_types(source, filename=None):
    return _parse_fortran_file(source, filename=filename).derived_types


def parse_fortran_modules(source, filename=None):
    return _parse_fortran_file(source, filename=filename).modules


_ERRORS_DIR = Path(__file__).parent / "fixtures" / "errors"
_EXPECTED_ERRORS_DIR = _ERRORS_DIR
_PARSER_MAP = {
    "parse_fortran_procedures": parse_fortran_procedures,
    "parse_fortran_types": parse_fortran_types,
    "parse_fortran_modules": parse_fortran_modules,
}
_DEFAULT_PARSER = "parse_fortran_procedures"


def _parse_fortran_file(source, filename=None):
    from prik import parse_fortran_file

    return parse_fortran_file(source, filename=filename)


def _get_parser_for_fixture(fixture: Path) -> str:
    json_path = _EXPECTED_ERRORS_DIR / f"{fixture.stem}.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return data.get("parser", _DEFAULT_PARSER)
        except (json.JSONDecodeError, KeyError):
            pass
    return _DEFAULT_PARSER


def _serialize_error_fixture(fixture: Path) -> dict:
    from prik import FortranParseError

    source = fixture.read_text(encoding="utf-8")
    parser_name = _get_parser_for_fixture(fixture)
    parser_fn = _PARSER_MAP[parser_name]
    try:
        parser_fn(source, filename=fixture.name)
        raise SystemExit(
            f"ERROR: {fixture.name} did not raise FortranParseError — error fixture files must trigger a parse error."
        )
    except FortranParseError as exc:
        return {
            "parser": parser_name,
            "error_type": "FortranParseError",
            "message_contains": [exc.base_message],
            "diagnostic_contains": [
                f"error[{exc.code}]",
                exc.base_message,
                exc.source_line.strip() if exc.source_line else "",
            ],
        }


def main() -> None:
    _EXPECTED_ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    requested = sys.argv[1:]
    if requested:
        fixtures = []
        for item in requested:
            p = Path(item)
            if not p.is_absolute():
                p = _ERRORS_DIR / p
            fixtures.append(p)
    else:
        extensions = {".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08"}
        fixtures = sorted(f for f in _ERRORS_DIR.glob("*") if f.is_file() and f.suffix.lower() in extensions)
    if not fixtures:
        raise SystemExit("No Fortran error fixtures found")

    for fixture in fixtures:
        if not fixture.exists():
            raise SystemExit(f"Fixture does not exist: {fixture}")
        payload = _serialize_error_fixture(fixture)
        out = _EXPECTED_ERRORS_DIR / f"{fixture.stem}.json"
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"updated {out}")


if __name__ == "__main__":
    main()
