"""Boundary tests for the isolated wrapper-codegen package."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path
import subprocess
import sys

from tests.fortran._support.wrapper_build import REPO_ROOT
from x2py.pipeline.wrapper_artifacts import GeneratedWrapperArtifacts
from x2py.wrapper_codegen.checks import (
    WrapperCodegenCheckConfig,
    check_wrapper_codegen_package,
    check_wrapper_codegen_paths,
)

SOURCE_ROOT = REPO_ROOT / "x2py"
WRAPPER_CODEGEN_ROOT = SOURCE_ROOT / "wrapper_codegen"


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
    violations = check_wrapper_codegen_paths(
        [path],
        config=WrapperCodegenCheckConfig(max_complexity=3, max_statements=4, max_nesting=2),
    )
    return {violation.code for violation in violations}


def test_canonical_printers_share_one_package():
    printers = WRAPPER_CODEGEN_ROOT / "printers"

    assert (printers / "pyi_printer.py").is_file()
    assert (printers / "source_printers.py").is_file()


def test_backend_generators_do_not_import_each_other():
    binding_imports = _imported_modules(WRAPPER_CODEGEN_ROOT / "c" / "binding.py")
    bridge_imports = _imported_modules(WRAPPER_CODEGEN_ROOT / "fortran" / "bridge.py")

    assert not _imports_under(binding_imports, "x2py.wrapper_codegen.fortran")
    assert not _imports_under(bridge_imports, "x2py.wrapper_codegen.c")


def test_wrapper_build_pipeline_imports_canonical_generator():
    imports = _imported_modules(SOURCE_ROOT / "pipeline" / "build.py")

    assert _imports_under(imports, "x2py.wrapper_codegen")


def test_wrapper_codegen_package_static_contracts_pass():
    assert check_wrapper_codegen_package(WRAPPER_CODEGEN_ROOT) == ()


def test_wrapper_codegen_checker_command_runs_the_package_checker():
    result = subprocess.run(
        [sys.executable, "tools/check_wrapper_codegen_complexity.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout


def test_checker_rejects_module_level_production_functions(tmp_path: Path):
    codes = _check_source(tmp_path, "def build_plan():\n    return None\n")

    assert "module-function" in codes


def test_checker_requires_visitor_based_production_classes(tmp_path: Path):
    codes = _check_source(tmp_path, "class WrapperPlanner:\n    pass\n")

    assert "visitor-class" in codes


def test_checker_enforces_complexity_statement_and_nesting_limits(tmp_path: Path):
    codes = _check_source(
        tmp_path,
        """
def oversized(value):
    first = value + 1
    second = first + 1
    third = second + 1
    fourth = third + 1
    if value:
        if first:
            if second:
                return third
    if value == 1:
        return first
    if value == 2:
        return second
    if value == 3:
        return third
    return fourth
""",
    )

    assert {"complexity", "statement-count", "nesting-depth"} <= codes


def test_checker_uses_strict_default_limits_for_emitter_handlers(tmp_path: Path):
    path = _write_module(
        tmp_path,
        "strict.py",
        """
from x2py.wrapper_codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    def _convert_item(self, value):
        if value == 1:
            return 1
        if value == 2:
            return 2
        if value == 3:
            return 3
        if value == 4:
            return 4
        if value == 5:
            return 5
        return 6
""",
    )

    violations = check_wrapper_codegen_paths([path])

    assert "complexity" in {violation.code for violation in violations}


def test_checker_rejects_missing_primary_and_secondary_registry_handlers(tmp_path: Path):
    codes = _check_source(
        tmp_path,
        """
from x2py.wrapper_codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    PRIMARY_REGISTRY = {"item": "_emit_item"}
    SECONDARY_DISPATCHER = {"item": {"value": "_emit_item_value"}}
""",
    )

    assert "registry-missing-handler" in codes


def test_checker_rejects_printer_calls_from_handlers(tmp_path: Path):
    codes = _check_source(
        tmp_path,
        """
from x2py.wrapper_codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    HANDLER_REGISTRY = {"item": "_emit_item"}

    def _emit_item(self, node):
        return self.printer.doprint(node)
""",
    )

    assert "handler-printer-call" in codes


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
