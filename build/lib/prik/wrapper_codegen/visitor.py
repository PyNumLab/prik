"""Independent class-based visitor protocol for wrapper-plan generation."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("ClassVisitor", "UnsupportedWrapperCodegenNodeError")


@dataclass(frozen=True)
class UnsupportedWrapperCodegenNodeError(TypeError):
    """Raised when a wrapper-codegen visitor has no handler for a node."""

    visitor_type: type
    node_type: type
    method_prefix: str

    def __str__(self) -> str:
        return (
            f"{self.visitor_type.__name__} does not support {self.node_type.__name__} "
            f"with prefix {self.method_prefix!r}"
        )


class ClassVisitor:
    """Dispatch nodes through a deterministic ``<prefix>_<ClassName>`` protocol."""

    visitor_method_prefix = "_visit"

    def __init__(self, *, method_prefix: str | None = None):
        if method_prefix is not None:
            self.visitor_method_prefix = method_prefix

    def visit(self, node, *args, **kwargs):
        """Call the most specific handler for ``node``."""
        for node_type in type(node).__mro__:
            method = getattr(self, self._visitor_method_name(node_type), None)
            if method is not None:
                return method(node, *args, **kwargs)
        raise UnsupportedWrapperCodegenNodeError(type(self), type(node), self.visitor_method_prefix)

    def _visitor_method_name(self, node_type: type) -> str:
        """Return the handler method name for ``node_type``."""
        return f"{self.visitor_method_prefix}_{node_type.__name__}"
