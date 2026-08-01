"""Shared class-based visitor dispatch for parser, semantics, and codegen models."""

from __future__ import annotations

__all__ = ("ClassVisitor",)


class ClassVisitor:
    """Dispatch model nodes through a configured ``<prefix>_<ClassName>`` protocol.

    Subclasses implement one handler per supported model class. Dispatch follows
    the model class MRO so a handler for a base model remains a deliberate
    fallback for its subclasses. The default handler prefix is ``_visit``;
    subclasses may set ``visitor_method_prefix`` to names such as ``_print`` or
    ``_parse`` while keeping the same dispatcher.
    """

    visitor_method_prefix = "_visit"

    def _visitor_method_name(self, node_type: type) -> str:
        """Return the handler name for ``node_type``."""
        return f"{self.visitor_method_prefix}_{node_type.__name__}"

    def _visit(self, node, *args, **kwargs):
        """Call the most specific configured handler for ``node``."""
        for node_type in type(node).__mro__:
            method_name = self._visitor_method_name(node_type)
            method = getattr(self, method_name, None)
            if method is None:
                continue
            if getattr(self, "_verbose", 0) > 2:
                print(f">>>> Calling {type(self).__name__}.{method_name}")
            return method(node, *args, **kwargs)
        return self._visit_not_supported(node)

    @staticmethod
    def _visit_not_supported(node):
        """Raise when no class visitor handles ``node``."""
        raise TypeError(f"Unsupported model for class visitor: {type(node)!r}")
