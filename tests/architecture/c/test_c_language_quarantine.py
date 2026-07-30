"""Structural contracts for the mechanically quarantined C-input suite."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).parents[3]
C_ROOT = REPO_ROOT / "tests/c"
TEST_OWNERS = {
    "cli",
    "parsing",
    "pipeline",
    "preprocessing",
    "probes",
    "semantics",
}
SUPPORT_OWNERS = {"_support", "fixtures"}


def _test_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports.update(
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    return imports


def test_c_tree_has_only_named_test_and_support_owners() -> None:
    directories = {path.name for path in C_ROOT.iterdir() if path.is_dir() and path.name != "__pycache__"}
    assert directories == TEST_OWNERS | SUPPORT_OWNERS

    for module in C_ROOT.rglob("test_*.py"):
        relative = module.relative_to(C_ROOT)
        assert relative.parts[0] in TEST_OWNERS


def test_c_test_modules_use_only_c_owned_test_support() -> None:
    violations = []
    for module in C_ROOT.rglob("test_*.py"):
        for imported in _test_imports(module):
            if imported == "tests" or not imported.startswith("tests."):
                continue
            if imported != "tests.c" and not imported.startswith("tests.c."):
                violations.append(f"{module.relative_to(REPO_ROOT)}: {imported}")
    assert violations == []


def test_c_fixture_and_support_trees_do_not_collect_pytest_modules() -> None:
    assert list((C_ROOT / "_support").rglob("test_*.py")) == []
    assert list((C_ROOT / "fixtures").rglob("test_*.py")) == []
