"""Parse `.pyi` text into Python AST.

Semantic interpretation belongs to `prik.semantics.pyi2ir`; this module stays
small so the `.pyi` pipeline mirrors native source parsing:
parser -> semantic IR converter -> semantic policy completion.
"""

from __future__ import annotations

import ast
from pathlib import Path

__all__ = ("parse_pyi_file", "parse_pyi_text")


def parse_pyi_text(source: str, *, filename: str = "<pyi>") -> ast.Module:
    """Parse semantic `.pyi` source text into a Python AST module."""

    return ast.parse(source or "\n", filename=filename)


def parse_pyi_file(path: str | Path, *, encoding: str = "utf-8") -> ast.Module:
    """Read one `.pyi` file and parse it into a Python AST module."""

    pyi_path = Path(path)
    return parse_pyi_text(pyi_path.read_text(encoding=encoding), filename=str(pyi_path))
