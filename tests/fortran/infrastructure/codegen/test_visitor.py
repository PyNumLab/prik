"""Tests for the isolated wrapper-codegen visitor protocol."""

from __future__ import annotations

import pytest

from prik.codegen import ClassVisitor, UnsupportedWrapperCodegenNodeError


class BaseNode:
    """Base node used to prove MRO dispatch."""


class ChildNode(BaseNode):
    """Child node that should use the most specific available handler."""


class GrandchildNode(ChildNode):
    """Node whose nearest handler is its parent's."""


def test_class_visitor_dispatches_by_mro_and_rejects_unhandled_nodes():
    class Visitor(ClassVisitor):
        def _render_BaseNode(self, node):
            return ("base", type(node).__name__)

        def _render_ChildNode(self, node):
            return ("child", type(node).__name__)

    visitor = Visitor(method_prefix="_render")

    assert visitor.visit(BaseNode()) == ("base", "BaseNode")
    assert visitor.visit(ChildNode()) == ("child", "ChildNode")
    assert visitor.visit(GrandchildNode()) == ("child", "GrandchildNode")
    with pytest.raises(UnsupportedWrapperCodegenNodeError, match="_render") as exc_info:
        visitor.visit(object())
    assert "object" in str(exc_info.value)
