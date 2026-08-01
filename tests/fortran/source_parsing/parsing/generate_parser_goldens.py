"""Generate/update golden files for Fortran parser fixtures."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_FORTRAN_DIR = _FIXTURES_DIR


def _strip_parent_fields(value):
    if isinstance(value, dict):
        return {k: _strip_parent_fields(v) for k, v in value.items() if k != "parent"}
    if isinstance(value, list):
        return [_strip_parent_fields(v) for v in value]
    return value


def _parser_filename_for_fixture(fixture: Path) -> str:
    relpath = fixture.relative_to(_FORTRAN_DIR).as_posix()
    if relpath.startswith("general/"):
        return fixture.name
    return relpath


def _serialize_fixture(fixture: Path) -> dict:
    from prik import parse_fortran_file

    source = fixture.read_text(encoding="utf-8")
    parsed = parse_fortran_file(source, filename=_parser_filename_for_fixture(fixture))
    return _strip_parent_fields(asdict(parsed))


def _output_path_for_fixture(fixture: Path) -> Path:
    return (_FIXTURES_DIR / fixture.relative_to(_FORTRAN_DIR)).with_suffix(".json")


def main() -> None:
    _FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    requested = sys.argv[1:]
    if requested:
        fixtures = []
        for item in requested:
            p = Path(item)
            if not p.is_absolute():
                p = _FORTRAN_DIR / p
            if p.suffix.lower() not in (".f", ".for", ".ftn", ".f90", ".f95", ".f03", ".f08"):
                p = p.with_suffix(".f90")
            fixtures.append(p)
    else:
        fixtures = sorted(_FORTRAN_DIR.rglob("*.f*"))
    if not fixtures:
        raise SystemExit("No Fortran fixtures found")

    failures = []
    for fixture in fixtures:
        if not fixture.exists():
            raise SystemExit(f"Fixture does not exist: {fixture}")
        try:
            payload = _serialize_fixture(fixture)
            out = _output_path_for_fixture(fixture)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"updated {out}")
        except Exception as exc:
            failures.append((fixture, exc))

    if failures:
        for fixture, exc in failures:
            print(f"failed {fixture}: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
