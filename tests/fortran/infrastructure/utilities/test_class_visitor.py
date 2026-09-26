"""Behavioral contracts for the shared class-based visitor utility."""

import pytest

from prik.utilities.visitor import ClassVisitor


class BaseNode:
    """Base model used to prove fallback dispatch."""


class ChildNode(BaseNode):
    """More specific model used to prove MRO dispatch."""


class GrandchildNode(ChildNode):
    """Model whose nearest handler is its parent's."""


def test_class_visitor_dispatches_by_mro_and_rejects_unhandled_models() -> None:
    class ParserVisitor(ClassVisitor):
        visitor_method_prefix = "_parse"

        @staticmethod
        def _parse_BaseNode(node):
            return ("base", type(node).__name__)

        @staticmethod
        def _parse_ChildNode(node):
            return ("child", type(node).__name__)

    visitor = ParserVisitor()

    assert visitor._visit(BaseNode()) == ("base", "BaseNode")
    assert visitor._visit(ChildNode()) == ("child", "ChildNode")
    assert visitor._visit(GrandchildNode()) == ("child", "GrandchildNode")
    with pytest.raises(TypeError, match="Unsupported model for class visitor"):
        visitor._visit(object())
