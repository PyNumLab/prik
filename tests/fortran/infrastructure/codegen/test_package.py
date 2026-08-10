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
    printers = CODEGEN_ROOT / "printers"

    assert (printers / "pyi_printer.py").is_file()
    assert (printers / "source_printers.py").is_file()


def test_backend_generators_do_not_import_each_other():
    binding_imports = _imported_modules(CODEGEN_ROOT / "c" / "binding.py")
    bridge_imports = _imported_modules(CODEGEN_ROOT / "fortran" / "bridge.py")

    assert not _imports_under(binding_imports, "prik.codegen.fortran")
    assert not _imports_under(bridge_imports, "prik.codegen.c")


def test_wrapper_build_pipeline_imports_canonical_generator():
    imports = _imported_modules(SOURCE_ROOT / "pipeline" / "build.py")

    assert _imports_under(imports, "prik.codegen")
