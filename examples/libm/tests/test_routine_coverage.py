"""Fail closed when the reviewed libm surface or its tests drift."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

from ..routine_inventory import (
    ALL_ROUTINES,
    EXPLICIT_TEST_NAMES,
    PRIK_TESTED_ROUTINES,
    ROUTINE_GROUPS,
    UNSUPPORTED_ROUTINES,
)

pytestmark = pytest.mark.real_library
TEST_FILES = tuple(sorted(path for path in Path(__file__).parent.glob("test_*.py") if path != Path(__file__)))


def _test_sources() -> dict[str, str]:
    """Return the source text of every explicitly named public-routine test."""
    sources: dict[str, str] = {}
    for path in TEST_FILES:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                segment = ast.get_source_segment(text, node)
                assert segment is not None
                sources[node.name] = segment
    return sources


def test_every_reviewed_libm_routine_has_one_visible_numerical_test():
    sources = _test_sources()
    assert len(ALL_ROUTINES) == len(set(ALL_ROUTINES))
    assert set(ALL_ROUTINES) == PRIK_TESTED_ROUTINES
    assert UNSUPPORTED_ROUTINES == {}

    for routine, test_name in EXPLICIT_TEST_NAMES.items():
        source = sources[test_name]
        assert f"libm.{routine}(" in source, f"{test_name} does not visibly invoke {routine}"


def test_inventory_groups_cover_each_exported_routine_once(libm):
    grouped = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
    exported = {name for name in dir(libm) if not name.startswith("_")}

    assert grouped == ALL_ROUTINES
    assert len(grouped) == len(set(grouped))
    assert exported == set(ALL_ROUTINES)


def test_build_generated_the_target_contract_from_the_math_h_allowlist():
    contract = Path(os.environ["LIBM_BUILD_ROOT"]) / "prik/contract/libm_api.pyi"
    tree = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    generated = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

    assert generated == set(ALL_ROUTINES)


def test_reviewed_export_file_matches_the_inventory():
    export_file = Path(__file__).parents[1] / "iso_c99_routines.txt"
    selected = tuple(
        line.split("#", 1)[0].strip()
        for line in export_file.read_text(encoding="utf-8").splitlines()
        if line.split("#", 1)[0].strip()
    )

    assert selected == ALL_ROUTINES


def test_built_surface_is_positional_only(libm):
    with pytest.raises(TypeError, match="keyword"):
        libm.atan2(arg0=1.0, arg1=2.0)
