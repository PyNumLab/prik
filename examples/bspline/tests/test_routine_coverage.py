"""Fail closed when the reviewed BSPLINE-FORTRAN surface or tests drift."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ..routine_inventory import (
    ALL_OBJECT_EXPORTS,
    ALL_PROCEDURAL_EXPORTS,
    ALL_PROCEDURAL_ROUTINES,
    EXPLICIT_PROCEDURAL_TEST_NAMES,
    PRIK_TESTED_PROCEDURAL_ROUTINES,
    PROCEDURAL_ROUTINE_GROUPS,
    UNSUPPORTED_PROCEDURAL_ROUTINES,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
TEST_FILE = Path(__file__).with_name("test_procedural_api.py")


def _test_functions() -> dict[str, ast.FunctionDef]:
    """Return the explicitly named public-routine tests in this suite."""
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"), filename=str(TEST_FILE))
    return {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def test_every_public_procedural_routine_has_one_visible_numerical_test():
    functions = _test_functions()
    source_text = TEST_FILE.read_text(encoding="utf-8")

    assert len(ALL_PROCEDURAL_ROUTINES) == len(set(ALL_PROCEDURAL_ROUTINES))
    assert set(ALL_PROCEDURAL_ROUTINES) == PRIK_TESTED_PROCEDURAL_ROUTINES
    assert UNSUPPORTED_PROCEDURAL_ROUTINES == {}

    for routine, test_name in EXPLICIT_PROCEDURAL_TEST_NAMES.items():
        source = ast.get_source_segment(source_text, functions[test_name])
        assert source is not None
        assert f"bspline_sub.{routine}" in source, f"{test_name} does not visibly invoke {routine}"


def test_inventory_groups_cover_each_generated_public_export_once(bspline_oo, bspline_sub):
    grouped = tuple(routine for group in PROCEDURAL_ROUTINE_GROUPS.values() for routine in group)
    object_exports = {name for name in dir(bspline_oo) if not name.startswith("_")}
    procedural_exports = {name for name in dir(bspline_sub) if not name.startswith("_")}

    assert grouped == ALL_PROCEDURAL_ROUTINES
    assert len(grouped) == len(set(grouped))
    assert object_exports == set(ALL_OBJECT_EXPORTS)
    assert procedural_exports == set(ALL_PROCEDURAL_EXPORTS)
