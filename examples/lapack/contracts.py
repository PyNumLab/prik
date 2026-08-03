"""Helpers for LAPACK's generated root-only runtime contract."""

from __future__ import annotations

from pathlib import Path

from prik.pipeline.pyi import pyi_paths_to_semantic_modules


RUNTIME_EXCLUDED_IMPORTS = frozenset({"from . import LA_CONSTANTS\n", "from . import LA_XISNAN\n"})


def remove_internal_root_imports(entry: Path) -> Path:
    """Remove internal module imports from a generated LAPACK root contract."""
    lines = entry.read_text(encoding="utf-8").splitlines(keepends=True)
    entry.write_text(
        "".join(line for line in lines if line not in RUNTIME_EXCLUDED_IMPORTS),
        encoding="utf-8",
    )
    return entry


def root_function_names(package: Path) -> set[str]:
    """Return the generated callable names owned by the root contract."""
    modules = pyi_paths_to_semantic_modules([package])
    root = next(module for module in modules if module.name == "__init__")
    return {function.name for function in root.functions}
