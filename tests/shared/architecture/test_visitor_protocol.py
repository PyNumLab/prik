"""Structural contract for the active parser, semantic, and wrapper visitors."""

from __future__ import annotations

import ast
import inspect

from tests.fortran._support.wrapper_build import REPO_ROOT
from prik.parsers.c.parser import CParser
from prik.parsers.fortran.parser import FortranParser, SourceUnit, _SOURCE_UNIT_TYPES
from prik.semantics.c2ir import CToIRConverter
from prik.semantics.fortran2ir import FortranToIRConverter, _FortranVariableContextVisitor
from prik.semantics.pyi2ir import _ClassBodyVisitor, _ModuleVisitor
from prik.utilities.visitor import ClassVisitor as SemanticClassVisitor
from prik.codegen.c.binding import CBindingGenerator
from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.codegen.planner import WrapperPlanner
from prik.codegen.printers import PyiPrinter
from prik.codegen.visitor import ClassVisitor as WrapperClassVisitor


SEMANTIC_VISITORS = (
    FortranParser,
    CToIRConverter,
    FortranToIRConverter,
    _FortranVariableContextVisitor,
    _ClassBodyVisitor,
    _ModuleVisitor,
    PyiPrinter,
)
WRAPPER_VISITORS = (
    WrapperPlanner,
    CBindingGenerator,
    FortranBridgeGenerator,
)
VISITOR_IMPLEMENTATION_PATHS = (
    REPO_ROOT / "prik" / "parsers" / "fortran" / "parser.py",
    REPO_ROOT / "prik" / "semantics" / "c2ir.py",
    REPO_ROOT / "prik" / "semantics" / "fortran2ir.py",
    REPO_ROOT / "prik" / "semantics" / "pyi2ir.py",
    REPO_ROOT / "prik" / "codegen" / "planner.py",
    REPO_ROOT / "prik" / "codegen" / "c" / "binding.py",
    REPO_ROOT / "prik" / "codegen" / "fortran" / "bridge.py",
    REPO_ROOT / "prik" / "codegen" / "printers" / "pyi_printer.py",
)


def test_active_model_visitors_use_their_owned_dispatch_protocol():
    assert all(issubclass(visitor, SemanticClassVisitor) for visitor in SEMANTIC_VISITORS)
    assert all(issubclass(visitor, WrapperClassVisitor) for visitor in WRAPPER_VISITORS)


def test_semantic_class_visitor_supports_configured_handler_prefix():
    class Node:
        pass

    class SpecificNode(Node):
        pass

    class ParserVisitor(SemanticClassVisitor):
        visitor_method_prefix = "_parse"

        @staticmethod
        def _parse_Node(node):
            return type(node).__name__

    assert ParserVisitor()._visit(SpecificNode()) == "SpecificNode"


def test_wrapper_class_visitor_supports_configured_handler_prefix():
    class Node:
        pass

    class SpecificNode(Node):
        pass

    class PlanVisitor(WrapperClassVisitor):
        @staticmethod
        def _plan_Node(node):
            return type(node).__name__

    assert PlanVisitor(method_prefix="_plan").visit(SpecificNode()) == "SpecificNode"


def test_active_visitor_handlers_use_configured_class_names():
    invalid = []
    lowercase_model_names = {"int", "str", "tuple"}
    for visitor in (*SEMANTIC_VISITORS, *WRAPPER_VISITORS):
        handler_prefix = f"{visitor.visitor_method_prefix}_"
        for name, _method in inspect.getmembers(visitor, predicate=inspect.isfunction):
            if name.startswith("visit_"):
                invalid.append(f"{visitor.__name__}.{name}")
            if name == "_visit_not_supported" or not name.startswith(handler_prefix):
                continue
            model_name = name.removeprefix(handler_prefix)
            if model_name[:1].islower() and model_name not in lowercase_model_names:
                invalid.append(f"{visitor.__name__}.{name}")
    assert not invalid, "Use configured <prefix>_<ClassName> handlers:\n" + "\n".join(invalid)


def test_parser_entrypoints_are_not_misnamed_as_visitors():
    invalid = [
        f"{parser.__name__}.{name}"
        for parser in (FortranParser, CParser)
        for name in vars(parser)
        if name.startswith("visit_")
    ]
    assert not invalid, "Source entrypoints must use parse_* names:\n" + "\n".join(invalid)


def test_fortran_source_unit_classes_have_matching_handlers():
    assert all(issubclass(unit_type, SourceUnit) for unit_type in _SOURCE_UNIT_TYPES.values())
    assert {
        kind: f"_visit_{unit_type.__name__}"
        for kind, unit_type in _SOURCE_UNIT_TYPES.items()
        if not hasattr(FortranParser, f"_visit_{unit_type.__name__}")
    } == {}


def test_visitors_do_not_reimplement_mro_dispatch():
    invalid = []
    for path in VISITOR_IMPLEMENTATION_PATHS:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {"__mro__", "mro"}:
                invalid.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not invalid, "Use the owned ClassVisitor instead of local MRO dispatch:\n" + "\n".join(invalid)
