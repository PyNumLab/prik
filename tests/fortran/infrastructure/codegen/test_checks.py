"""Behavior of the advisory code-generation reviewer."""

from __future__ import annotations

from pathlib import Path

import pytest

from prik.codegen.checks import (
    WrapperCodegenCheckConfig,
    check_codegen_paths,
)

_OVERSIZED_FUNCTION = """
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
"""

_EMITTER_WITH_MISSING_HANDLERS = """
from prik.codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    PRIMARY_REGISTRY = {"item": "_emit_item"}
    SECONDARY_DISPATCHER = {"item": {"value": "_emit_item_value"}}
"""

_EMITTER_CALLING_THE_PRINTER = """
from prik.codegen import ClassVisitor

class DemoEmitter(ClassVisitor):
    HANDLER_REGISTRY = {"item": "_emit_item"}

    def _emit_item(self, node):
        return self.printer.doprint(node)
"""

# Within the default limits for an ordinary function, but over the stricter
# recommendation for an emitter's `_convert_*` handler.
_BRANCHY_EMITTER_HANDLER = """
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
"""

_SMALL_LIMITS = WrapperCodegenCheckConfig(max_complexity=3, max_statements=4, max_nesting=2)


@pytest.mark.parametrize(
    ("source", "config", "expected_codes"),
    [
        pytest.param("def build_plan():\n    return None\n", _SMALL_LIMITS, {"module-function"}, id="module_function"),
        pytest.param("class WrapperPlanner:\n    pass\n", _SMALL_LIMITS, {"visitor-class"}, id="non_visitor_class"),
        pytest.param(
            _OVERSIZED_FUNCTION,
            _SMALL_LIMITS,
            {"complexity", "statement-count", "nesting-depth"},
            id="complexity_statement_and_nesting_limits",
        ),
        pytest.param(
            _EMITTER_WITH_MISSING_HANDLERS,
            _SMALL_LIMITS,
            {"registry-missing-handler"},
            id="missing_primary_and_secondary_registry_handlers",
        ),
        pytest.param(
            _EMITTER_CALLING_THE_PRINTER, _SMALL_LIMITS, {"handler-printer-call"}, id="printer_call_from_handler"
        ),
        pytest.param(_BRANCHY_EMITTER_HANDLER, None, {"complexity"}, id="stricter_default_for_emitter_handlers"),
    ],
)
def test_reviewer_reports_advisory_violations(
    tmp_path: Path, source: str, config: WrapperCodegenCheckConfig | None, expected_codes: set[str]
):
    path = tmp_path / "reviewed.py"
    path.write_text(source, encoding="utf-8")

    violations = check_codegen_paths([path]) if config is None else check_codegen_paths([path], config=config)

    assert expected_codes <= {violation.code for violation in violations}
