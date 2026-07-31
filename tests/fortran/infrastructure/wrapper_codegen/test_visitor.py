"""Tests for the isolated wrapper-codegen visitor protocol."""

from __future__ import annotations

import pytest

from x2py.wrapper_codegen import ClassVisitor, UnsupportedWrapperCodegenNodeError


class BaseNode:
    """Base node used to prove MRO dispatch."""


class ChildNode(BaseNode):
    """Child node that should use the most specific available handler."""


class UnsupportedNode:
    """Node with no matching handler."""


def test_class_visitor_uses_mro_specific_handler():
    class Visitor(ClassVisitor):
        def _visit_BaseNode(self, node):
            return ("base", type(node).__name__)

        def _visit_ChildNode(self, node):
            return ("child", type(node).__name__)

    assert Visitor().visit(ChildNode()) == ("child", "ChildNode")


def test_class_visitor_falls_back_to_base_handler():
    class Visitor(ClassVisitor):
        def _visit_BaseNode(self, node):
            return ("base", type(node).__name__)

    assert Visitor().visit(ChildNode()) == ("base", "ChildNode")


def test_class_visitor_supports_configurable_prefix():
    class Visitor(ClassVisitor):
        def _render_BaseNode(self, node):
            return ("rendered", type(node).__name__)

    assert Visitor(method_prefix="_render").visit(BaseNode()) == ("rendered", "BaseNode")


def test_class_visitor_reports_unsupported_nodes():
    visitor = ClassVisitor()

    with pytest.raises(UnsupportedWrapperCodegenNodeError) as exc_info:
        visitor.visit(UnsupportedNode())

    assert "UnsupportedNode" in str(exc_info.value)
    assert "_visit" in str(exc_info.value)
