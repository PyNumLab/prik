"""Fail closed when the reviewed MINPACK surface or explicit tests drift."""

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
TEST_ROOT = Path(__file__).parent
TEST_MODULES = ("test_diagnostics.py", "test_linear_algebra.py", "test_solvers.py")


def _test_functions() -> dict[str, tuple[Path, ast.FunctionDef]]:
    """Collect uniquely named top-level routine tests from this reviewed suite."""
    functions: dict[str, tuple[Path, ast.FunctionDef]] = {}
    for filename in TEST_MODULES:
        path = TEST_ROOT / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                assert node.name not in functions, f"duplicate explicit test name: {node.name}"
                functions[node.name] = (path, node)
    return functions


def test_every_public_minpack_routine_has_one_visible_numerical_test():
    functions = _test_functions()
    assert len(ALL_ROUTINES) == len(set(ALL_ROUTINES))
    assert set(ALL_ROUTINES) == PRIK_TESTED_ROUTINES
    assert UNSUPPORTED_ROUTINES == {}

    for routine, test_name in EXPLICIT_TEST_NAMES.items():
        path, node = functions[test_name]
        source = ast.get_source_segment(path.read_text(encoding="utf-8"), node)
        assert source is not None
        assert routine in source, f"{test_name} does not visibly exercise {routine}"
        assert "minpack" in source, f"{test_name} does not visibly invoke MINPACK"


def test_inventory_groups_cover_the_generated_public_surface_once(minpack):
    grouped = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
    exported = {name for name in dir(minpack) if not name.startswith("_")}

    assert grouped == ALL_ROUTINES
    assert len(grouped) == len(set(grouped))
    assert exported == {*ALL_ROUTINES, "dpmpar"}
