"""Focused regression contracts for the Fortran parser."""

from __future__ import annotations


from prik.parsers.fortran.parser import (
    SourceUnit,
    _SourceUnitScanner,
)


def _lines(*values: str) -> list[tuple[str, int, str]]:
    return [(value, lineno, value) for lineno, value in enumerate(values, start=1)]


def _unit(kind: str, name: str | None, *values: str) -> SourceUnit:
    lines = _lines(*values)
    return _SourceUnitScanner()._build_source_unit(
        kind,
        name,
        lines,
        parent_region=None,
        filename=None,
    )
