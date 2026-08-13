"""Behavior of the advisory code-generation reviewer."""

from __future__ import annotations

from pathlib import Path

from prik.codegen.checks import (
    WrapperCodegenCheckConfig,
    check_codegen_paths,
)


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


def test_reviewer_reports_module_level_production_functions(tmp_path: Path):
    codes = _check_source(tmp_path, "def build_plan():\n    return None\n")

    assert "module-function" in codes


def test_reviewer_recommends_visitor_based_production_classes(tmp_path: Path):
    codes = _check_source(tmp_path, "class WrapperPlanner:\n    pass\n")

    assert "visitor-class" in codes


def test_reviewer_reports_complexity_statement_and_nesting_limits(tmp_path: Path):
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


def test_reviewer_uses_stricter_recommendations_for_emitter_handlers(tmp_path: Path):
    path = _write_module(
        tmp_path,
        "strict.py",
        """
from prik.codegen import ClassVisitor

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

    violations = check_codegen_paths([path])

    assert "complexity" in {violation.code for violation in violations}


def test_reviewer_reports_missing_primary_and_secondary_registry_handlers(tmp_path: Path):
    codes = _check_source(
        tmp_path,
        """
from prik.codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    PRIMARY_REGISTRY = {"item": "_emit_item"}
    SECONDARY_DISPATCHER = {"item": {"value": "_emit_item_value"}}
""",
    )

    assert "registry-missing-handler" in codes


def test_reviewer_reports_printer_calls_from_handlers(tmp_path: Path):
    codes = _check_source(
        tmp_path,
        """
from prik.codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    HANDLER_REGISTRY = {"item": "_emit_item"}

    def _emit_item(self, node):
        return self.printer.doprint(node)
""",
    )

    assert "handler-printer-call" in codes
