"""Temporary cross-stage golden contracts for maintainability refactoring.

Refresh the reviewed baselines with::

    REFACTORING_UPDATE_GOLDENS=1 python3 -m pytest -q \
        tests/fortran/infrastructure/codegen/test_refactoring_goldens.py

Remove this module and its fixture directory after the focused permanent suite
subsumes the refactoring evidence.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import pytest

from prik import parse_fortran_project
from prik.codegen import WrapperCodeGenerator, WrapperPlanner
from prik.codegen.printers import emit_module_stubs
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.policy_completion import complete_semantic_policies


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "refactoring_goldens"
_NATIVE_DIR = _FIXTURE_DIR / "native"
_UPDATE_GOLDENS = os.getenv("REFACTORING_UPDATE_GOLDENS", "0") == "1"


@dataclass(frozen=True)
class _RefactoringGoldenOutputs:
    """Store the four stable stage outputs protected during refactoring."""

    parser_json: str
    semantic_pyi: str
    fortran_bridge: str
    c_binding: str


def _strip_parent_fields(value):
    """Remove recursive parser parent links before deterministic JSON emission."""
    if isinstance(value, dict):
        return {_stable_parser_path(key): _strip_parent_fields(item) for key, item in value.items() if key != "parent"}
    if isinstance(value, list):
        return [_strip_parent_fields(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_parent_fields(item) for item in value)
    if isinstance(value, set):
        return [_strip_parent_fields(item) for item in sorted(value, key=repr)]
    return _stable_parser_path(value)


def _stable_parser_path(value):
    """Replace checkout-specific fixture prefixes with stable relative names."""
    if not isinstance(value, str):
        return value
    prefix = str(_NATIVE_DIR.resolve()) + os.sep
    return value.replace(prefix, "")


def _rendered_source(artifacts, suffix: str) -> str:
    """Return the unique generated source carrying the requested suffix."""
    matches = [source.text for source in artifacts.sources if source.path.suffix == suffix]
    assert len(matches) == 1, f"Expected one generated {suffix} source, found {len(matches)}"
    return matches[0]


@pytest.fixture(scope="module")
def refactoring_golden_outputs() -> _RefactoringGoldenOutputs:
    """Run the complete source-to-wrapper pipeline once for all golden checks."""
    parsed = parse_fortran_project(_NATIVE_DIR)
    parser_json = json.dumps(_strip_parent_fields(asdict(parsed)), indent=2) + "\n"

    semantic_modules = fortran_project_to_semantic_modules(parsed)
    assert [module.name for module in semantic_modules] == ["refactoring_goldens"]
    semantic_pyi = (
        emit_module_stubs(
            semantic_modules,
            normalize_fortran_public_names=True,
        )["refactoring_goldens"]
        + "\n"
    )

    complete_semantic_policies(semantic_modules)
    plan = WrapperPlanner().build(semantic_modules[0])
    artifacts = WrapperCodeGenerator().generate(plan)

    return _RefactoringGoldenOutputs(
        parser_json=parser_json,
        semantic_pyi=semantic_pyi,
        fortran_bridge=_rendered_source(artifacts, ".f90"),
        c_binding=_rendered_source(artifacts, ".c"),
    )


def _assert_matches_golden(filename: str, actual: str) -> None:
    """Compare one output byte-for-byte, optionally refreshing its baseline."""
    expected_path = _FIXTURE_DIR / filename
    if _UPDATE_GOLDENS:
        expected_path.write_text(actual, encoding="utf-8")
    assert actual == expected_path.read_text(encoding="utf-8")


def test_parser_json_matches_refactoring_golden(refactoring_golden_outputs):
    _assert_matches_golden("parser.json", refactoring_golden_outputs.parser_json)


def test_semantic_pyi_matches_refactoring_golden(refactoring_golden_outputs):
    _assert_matches_golden("contract.pyi.golden", refactoring_golden_outputs.semantic_pyi)


def test_fortran_bridge_matches_refactoring_golden(refactoring_golden_outputs):
    _assert_matches_golden("bridge.f90", refactoring_golden_outputs.fortran_bridge)


def test_c_binding_matches_refactoring_golden(refactoring_golden_outputs):
    _assert_matches_golden("binding.c", refactoring_golden_outputs.c_binding)
