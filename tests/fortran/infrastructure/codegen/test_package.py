"""Internal code-generation package boundary contracts."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.fortran._support.wrapper_build import REPO_ROOT
from prik.codegen.checks import (
    WrapperCodegenCheckConfig,
    check_codegen_paths,
)

SOURCE_ROOT = REPO_ROOT / "prik"
CODEGEN_ROOT = SOURCE_ROOT / "codegen"
PRINTERS_ROOT = SOURCE_ROOT / "printers"
PLANNING_ROOT = SOURCE_ROOT / "planning"
POLICY_ROOT = SOURCE_ROOT / "policy"
SEMANTICS_ROOT = SOURCE_ROOT / "semantics"


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


def _write_module(root: Path, relative_path: str, source: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _check_source(tmp_path: Path, source: str, *, filename: str = "bad.py") -> set[str]:
    path = _write_module(tmp_path, filename, source)
    violations = check_codegen_paths(
        [path],
        config=WrapperCodegenCheckConfig(max_complexity=3, max_statements=4, max_nesting=2),
    )
    return {violation.code for violation in violations}


def test_canonical_printers_share_one_package():
    assert (PRINTERS_ROOT / "c.py").is_file()
    assert (PRINTERS_ROOT / "fortran.py").is_file()
    assert (PRINTERS_ROOT / "pyi.py").is_file()


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


def test_wrapper_build_pipeline_imports_canonical_wrapper_stages():
    imports = _imported_modules(SOURCE_ROOT / "pipeline" / "build.py")
    wrapper_imports = _imported_modules(SOURCE_ROOT / "pipeline" / "wrapper.py")

    assert _imports_under(imports, "prik.policy")
    assert _imports_under(imports, "prik.planning")
    assert _imports_under(imports, "prik.pipeline.wrapper")
    assert _imports_under(wrapper_imports, "prik.codegen")
    assert _imports_under(wrapper_imports, "prik.printers")
