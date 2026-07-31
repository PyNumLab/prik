"""Focused regression contracts for the Fortran parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from x2py.parsers.fortran.models import FortranArgument, FortranDerivedType, FortranModule, FortranProcedureSignature

from x2py.parsers.fortran.parser import (
    FortranParser,
    SourceUnit,
    _ParserScope,
    _SOURCE_UNIT_TYPES,
    _UnitParts,
    parse_fortran_project,
)

from x2py import FortranParseError, parse_fortran_file


def _lines(*values: str) -> list[tuple[str, int, str]]:
    return [(value, lineno, value) for lineno, value in enumerate(values, start=1)]


def _unit(kind: str, name: str | None, *values: str) -> SourceUnit:
    lines = _lines(*values)
    return _SOURCE_UNIT_TYPES[kind](kind=kind, name=name, lines=lines, start_line=1, end_line=len(lines))


def _empty_unit(kind: str, name: str | None, start_line: int | None, end_line: int | None) -> SourceUnit:
    return _SOURCE_UNIT_TYPES[kind](kind, name, [], start_line, end_line)


__all__ = (
    "FortranArgument",
    "FortranDerivedType",
    "FortranModule",
    "FortranParseError",
    "FortranParser",
    "FortranProcedureSignature",
    "Path",
    "_ParserScope",
    "_UnitParts",
    "_empty_unit",
    "_lines",
    "_unit",
    "parse_fortran_file",
    "parse_fortran_project",
    "pytest",
)
