"""Internal rendered-wrapper artifact handoff contracts."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from tests.fortran._support.wrapper_build import REPO_ROOT
from prik.pipeline.wrapper_artifacts import GeneratedWrapperArtifacts
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


def test_generated_wrapper_artifacts_keep_compile_and_link_ownership_out_of_the_handoff():
    artifacts = GeneratedWrapperArtifacts(
        module_name="demo",
        bridge_sources=(Path("bind_c_demo.f90"),),
        binding_sources=(Path("demo.c"),),
        header_files=(Path("demo.h"),),
        native_support_keys=("binding_support",),
    )

    assert artifacts.source_files == (Path("bind_c_demo.f90"), Path("demo.c"))
    assert artifacts.generated_files == (Path("bind_c_demo.f90"), Path("demo.c"), Path("demo.h"))
    assert artifacts.required_headers == ()
    assert {field.name for field in fields(GeneratedWrapperArtifacts)} == {
        "module_name",
        "bridge_sources",
        "binding_sources",
        "header_files",
        "native_support_keys",
        "required_headers",
    }
