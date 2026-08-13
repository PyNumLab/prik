"""Internal code-generation package boundary contracts."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.fortran._support.wrapper_build import REPO_ROOT

CODEGEN_ROOT = REPO_ROOT / "prik" / "codegen"
PRINTERS_ROOT = REPO_ROOT / "prik" / "printers"
PLANNING_ROOT = REPO_ROOT / "prik" / "planning"
POLICY_ROOT = REPO_ROOT / "prik" / "policy"
SEMANTICS_ROOT = REPO_ROOT / "prik" / "semantics"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def _imports_under(imports: set[str], package: str) -> bool:
    return any(name == package or name.startswith(f"{package}.") for name in imports)


def _package_imports(root: Path) -> set[str]:
    return set().union(*(_imported_modules(path) for path in root.rglob("*.py")))


def test_backend_generators_do_not_import_each_other():
    binding_imports = _imported_modules(CODEGEN_ROOT / "c" / "binding.py")
    bridge_imports = _imported_modules(CODEGEN_ROOT / "fortran" / "bridge.py")

    assert not _imports_under(binding_imports, "prik.codegen.fortran")
    assert not _imports_under(bridge_imports, "prik.codegen.c")


def test_wrapper_stage_packages_follow_the_documented_dependency_direction():
    semantic_imports = _package_imports(SEMANTICS_ROOT)
    policy_imports = _package_imports(POLICY_ROOT)
    planning_imports = _package_imports(PLANNING_ROOT)
    codegen_imports = _package_imports(CODEGEN_ROOT)
    printer_imports = _package_imports(PRINTERS_ROOT)

    assert not _imports_under(semantic_imports, "prik.policy")
    assert not _imports_under(semantic_imports, "prik.planning")
    assert not _imports_under(semantic_imports, "prik.codegen")
    assert not _imports_under(policy_imports, "prik.planning")
    assert not _imports_under(policy_imports, "prik.codegen")
    assert not _imports_under(planning_imports, "prik.codegen")
    assert not _imports_under(codegen_imports, "prik.printers")
    assert not _imports_under(codegen_imports, "prik.pipeline")
    assert not _imports_under(printer_imports, "prik.policy")
    assert not _imports_under(printer_imports, "prik.planning")
    assert not _imports_under(printer_imports, "prik.pipeline")
