"""Every general Fortran fixture parses to its reviewed JSON golden.

Set ``FORTRAN_PARSER_UPDATE_GOLDENS=1`` to rewrite the goldens from the
current parser, then review the diff.
"""

import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file

_GENERAL_DIR = Path(__file__).parent / "fixtures" / "general"
_SOURCE_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
_UPDATE_GOLDENS = os.getenv("FORTRAN_PARSER_UPDATE_GOLDENS", "0") == "1"

_GOLDEN_FIXTURES = sorted(
    path for path in _GENERAL_DIR.iterdir() if path.is_file() and path.suffix.lower() in _SOURCE_SUFFIXES
)


def _strip_parent_fields(value):
    if isinstance(value, dict):
        return {k: _strip_parent_fields(v) for k, v in value.items() if k != "parent"}
    if isinstance(value, list):
        return [_strip_parent_fields(v) for v in value]
    return value


def _to_dict(value):
    """Return one parsed file as the golden records it.

    The golden is JSON, where a tuple and a list are the same array, so the
    parsed model is compared in that form rather than as Python objects.
    """
    return json.loads(json.dumps(_strip_parent_fields(asdict(value))))


@pytest.mark.parametrize("fixture", _GOLDEN_FIXTURES, ids=lambda f: f.name)
def test_fortran_fixture_golden_suite(fixture):
    parsed = _to_dict(parse_fortran_file(fixture.read_text(encoding="utf-8"), filename=fixture.name))
    expected_path = fixture.with_suffix(".json")

    if _UPDATE_GOLDENS:
        expected_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        return

    assert parsed == json.loads(expected_path.read_text(encoding="utf-8")), f"FortranFile mismatch for {fixture.name}"
