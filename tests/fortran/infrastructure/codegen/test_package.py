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


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    class ImportCollector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.imported: set[str] = set()

        def visit_If(self, node: ast.If) -> None:
            if _is_main_guard(node):
                for statement in node.orelse:
                    self.visit(statement)
                return
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            self.imported.update(alias.name for alias in node.names)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                self.imported.add(node.module)

    collector = ImportCollector()
    collector.visit(tree)
    return collector.imported


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
