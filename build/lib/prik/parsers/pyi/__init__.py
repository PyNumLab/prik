"""Parser entrypoints for semantic `.pyi` contracts."""

from .parser import parse_pyi_file, parse_pyi_text

__all__ = ("parse_pyi_file", "parse_pyi_text")
