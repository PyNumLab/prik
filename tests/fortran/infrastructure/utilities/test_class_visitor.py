"""Behavioral contracts for the shared class-based visitor utility."""

import pytest

from prik.utilities.visitor import ClassVisitor


class BaseNode:
    """Base model used to prove fallback dispatch."""


class ChildNode(BaseNode):
    """More specific model used to prove MRO dispatch."""


def test_class_visitor_uses_the_most_specific_available_handler() -> None:
    class Visitor(ClassVisitor):
        @staticmethod
        def _visit_BaseNode(_node):
            return "base"

        @staticmethod
        def _visit_ChildNode(_node):
            return "child"

    assert Visitor()._visit(ChildNode()) == "child"


def test_class_visitor_falls_back_to_a_base_model_handler() -> None:
    class Visitor(ClassVisitor):
        @staticmethod
        def _visit_BaseNode(_node):
            return "base"

    assert Visitor()._visit(ChildNode()) == "base"


def test_class_visitor_supports_a_configured_handler_prefix() -> None:
    class ParserVisitor(ClassVisitor):
        visitor_method_prefix = "_parse"

        @staticmethod
        def _parse_BaseNode(node):
            return type(node).__name__

    assert ParserVisitor()._visit(ChildNode()) == "ChildNode"


def test_class_visitor_reports_an_unsupported_model() -> None:
    with pytest.raises(TypeError, match="Unsupported model for class visitor"):
        ClassVisitor()._visit(object())
