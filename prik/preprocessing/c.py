"""Collect safe raw-preprocessor metadata for the C parser.

This preprocessing-stage module deliberately does not expand macros or choose
conditional-compilation branches; compiler-backed expansion belongs to
``prik.preprocessing.source``. Before raw C grammar parsing, it normalizes
comments and continuations, records literal ``#include`` and ``#pragma`` facts,
and reports unresolved quoted includes without reading included source.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from prik.parsers.c.lexer import CLogicalRecord, NormalizedCSource, normalize_c_source
from prik.parsers.c.models import CDiagnostic, CInclude, CMacro, CRawDirective, CSourceLocation


# Raw directive recognition and the subset preserved as parser provenance.
_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*(?:"([^"]+)"|<([^>]+)>)')
_DIRECTIVE_RE = re.compile(r"^\s*#\s*([A-Za-z_]\w*)\b(.*)$")
_RAW_PROVENANCE_DIRECTIVES = {"pragma"}


@dataclass
class CPreprocessorMetadata:
    """Return raw directive facts collected before C declaration parsing.

    ``includes`` preserves literal include order, ``raw_directives`` retains
    supported provenance directives, and ``diagnostics`` records recoverable
    local-include lookup failures.  ``macros`` is retained for the parser model
    shape but raw collection never evaluates or creates macro definitions.
    """

    includes: list[CInclude] = field(default_factory=list)
    macros: list[CMacro] = field(default_factory=list)
    raw_directives: list[CRawDirective] = field(default_factory=list)
    diagnostics: list[CDiagnostic] = field(default_factory=list)


def _record_location(record: CLogicalRecord) -> CSourceLocation:
    """Build one directive location from a normalized logical source record.

    The returned location points at the original physical line and at the
    first ``#`` when available.  Records without original source text retain
    the established column-one fallback.
    """
    source_line = record.source_line
    column = 1
    if source_line is not None:
        marker = source_line.find("#")
        if marker >= 0:
            column = marker + 1
    return CSourceLocation(
        filename=record.filename,
        line=record.original_start_line,
        column=column,
        source_line=source_line,
    )


def _resolve_local_include(
    target: str,
    filename: str | None,
    include_dirs: Sequence[str | Path] | None,
) -> str | None:
    """Resolve one quoted include for metadata, without parsing the target.

    Candidates are checked beside ``filename`` first and then in ``include_dirs``
    in the supplied order.  The first regular file is returned as a string;
    filesystem errors are ignored so later include directories remain usable.
    """
    candidates: list[Path] = []
    if filename:
        candidates.append(Path(filename).parent / target)
    candidates.extend(Path(include_dir) / target for include_dir in include_dirs or ())

    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


def collect_preprocessor_metadata(
    source: str,
    filename: str | None = None,
    *,
    include_dirs: Sequence[str | Path] | None = None,
) -> CPreprocessorMetadata:
    """Collect safe raw-preprocessor facts from one C source string.

    Use this immediately before raw C grammar parsing.  The result preserves
    literal ``#include`` directives, ``#pragma`` provenance, and warnings for
    unresolved quoted includes; it neither expands macros nor reads includes.
    The C parser consumes these collections as file metadata, while directives
    requiring actual preprocessing are rejected elsewhere by the raw-mode
    guard.
    """

    # Stage 1: normalize comments and continuations while retaining locations.
    normalized = normalize_c_source(source, filename=filename)
    metadata = CPreprocessorMetadata()

    # Stage 2: retain directives that are safe parser provenance.
    for record in normalized.records:
        directive_match = _DIRECTIVE_RE.match(record.text)
        if directive_match:
            directive, argument = directive_match.groups()
            if directive in _RAW_PROVENANCE_DIRECTIVES:
                metadata.raw_directives.append(
                    CRawDirective(
                        directive=directive,
                        argument=argument.strip() or None,
                        source_location=_record_location(record),
                    )
                )
                continue

        # Stage 3: classify literal includes and report unresolved local paths.
        include_match = _INCLUDE_RE.match(record.text)
        if include_match:
            local_target, system_target = include_match.groups()
            target = local_target or system_target
            kind = "local" if local_target is not None else "system"
            resolved_path = _resolve_local_include(target, filename, include_dirs) if kind == "local" else None
            location = _record_location(record)
            metadata.includes.append(
                CInclude(
                    target=target,
                    kind=kind,
                    resolved_path=resolved_path,
                    source_location=location,
                )
            )
            if kind == "local" and resolved_path is None:
                metadata.diagnostics.append(
                    CDiagnostic(
                        code="C_UNRESOLVED_INCLUDE",
                        message=f'Could not resolve local include "{target}".',
                        severity="warning",
                        location=location,
                        unit_kind="include",
                        unit_name=target,
                    )
                )
            continue
    return metadata


__all__ = (
    "CPreprocessorMetadata",
    "NormalizedCSource",
    "collect_preprocessor_metadata",
    "normalize_c_source",
)


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    source = """\
#pragma once
#include "state.h"
#include <stddef.h>
"""

    metadata = collect_preprocessor_metadata(source)

    print(f"Raw directive: #{metadata.raw_directives[0].directive} {metadata.raw_directives[0].argument}")
    print("Includes: " + ", ".join(f"{include.kind} {include.target}" for include in metadata.includes))
    print(f"Diagnostic: {metadata.diagnostics[0].code}")

    with TemporaryDirectory() as directory:
        header_path = Path(directory) / "api.h"
        (header_path.parent / "state.h").write_text("struct state;\n", encoding="utf-8")
        resolved_metadata = collect_preprocessor_metadata(source, filename=str(header_path))

        print(
            f"Resolved include: {Path(resolved_metadata.includes[0].resolved_path).name} "
            f"(diagnostics: {len(resolved_metadata.diagnostics)})"
        )
