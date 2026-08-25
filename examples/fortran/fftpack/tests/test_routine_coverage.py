"""Fail closed when the reviewed FFTPACK transform surface or tests drift."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ..routine_inventory import (
    ALL_ROUTINES,
    EXPLICIT_TEST_NAMES,
    PRIK_TESTED_ROUTINES,
    ROUTINE_GROUPS,
    UNSUPPORTED_ROUTINES,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
TEST_FILE = Path(__file__).with_name("test_transforms.py")


def _test_functions() -> dict[str, ast.FunctionDef]:
    """Return the explicitly named public-routine tests in this suite."""
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"), filename=str(TEST_FILE))
    return {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def test_every_public_fftpack_routine_has_one_visible_numerical_test():
    functions = _test_functions()
    assert len(ALL_ROUTINES) == len(set(ALL_ROUTINES))
    assert set(ALL_ROUTINES) == PRIK_TESTED_ROUTINES
    assert UNSUPPORTED_ROUTINES == {}

    source_text = TEST_FILE.read_text(encoding="utf-8")
    for routine, test_name in EXPLICIT_TEST_NAMES.items():
        source = ast.get_source_segment(source_text, functions[test_name])
        assert source is not None
        assert routine in source, f"{test_name} does not visibly exercise {routine}"
        assert "fftpack" in source, f"{test_name} does not visibly invoke FFTPACK"


def test_inventory_groups_cover_each_generated_public_routine_once(fftpack):
    grouped = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
    exported = {name for name in dir(fftpack) if not name.startswith("_")}

    assert grouped == ALL_ROUTINES
    assert len(grouped) == len(set(grouped))
    assert exported == set(ALL_ROUTINES)
