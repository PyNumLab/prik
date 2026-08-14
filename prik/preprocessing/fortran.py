"""Expand native Fortran textual includes before parsing.

Compiler preprocessing and provenance collection live in
``prik.preprocessing.source``.  This module owns the Fortran-specific pass that
expands native ``INCLUDE`` statements left in the compiler-expanded stream.
It preserves generated-to-original line mappings and reports missing files or
cycles without making parser or semantic decisions.

The sole public operation, :func:`expand_native_fortran_includes`, returns
parser input together with dependency, mapping, and diagnostic records. Read
that function first; the private helpers resolve paths and maintain the
generated-line provenance it returns.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from prik.preprocessing.source import (
    DependencyKind,
    IncludedFile,
    PreprocessingConfig,
    PreprocessingDiagnostic,
    SourceMapping,
    _exposure_for,
    _parse_linemarker,
    parse_linemarker_mappings,
)


_FORTRAN_INCLUDE_RE = re.compile(
    r"^\s*include\s*(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)\s*$",
    re.IGNORECASE,
)


def _mapping_for_generated_line(
    mappings: Sequence[SourceMapping], generated_line: int, fallback: Path
) -> SourceMapping:
    """Return a generated-line mapping or construct the established root fallback."""
    for mapping in mappings:
        if mapping.generated_line == generated_line:
            return mapping
    return SourceMapping(
        generated_line=generated_line,
        original_path=str(fallback),
        original_line=generated_line,
        include_stack=[str(fallback)],
    )


def _resolve_fortran_include(target: str, including_file: str, include_dirs: Sequence[str]) -> Path | None:
    """Find a native Fortran include beside its source before configured paths.

    Filesystem lookup errors on one candidate do not prevent checking later
    include directories. The first existing regular file wins.
    """
    candidates = [Path(including_file).parent / target]
    candidates.extend(Path(include_dir) / target for include_dir in include_dirs)
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _line_marker(line: int, path: str, flag: int | None = None) -> str:
    """Render one escaped GCC-style line marker for expanded Fortran source."""
    escaped = path.replace("\\", "\\\\").replace('"', '\\"')
    suffix = f" {flag}" if flag is not None else ""
    return f'# {line} "{escaped}"{suffix}'


def expand_native_fortran_includes(
    source: str,
    *,
    root_path: Path,
    include_dirs: Sequence[str],
    config: PreprocessingConfig | None = None,
) -> tuple[str, list[IncludedFile], list[SourceMapping], list[PreprocessingDiagnostic]]:
    """Expand native Fortran ``INCLUDE`` statements after compiler preprocessing.

    Use this for a Fortran source stream that may still contain textual
    ``include "file.inc"`` statements. The return value contains expanded
    parser input, discovered include edges, generated-to-original mappings, and
    recoverable diagnostics. Missing files and cycles are recorded while later
    source lines continue to be emitted; :func:`preprocess_source` promotes
    error diagnostics after it records the complete result.

    Relative includes resolve beside the including file before configured
    include directories. Repeated non-cyclic includes are expanded repeatedly
    and retain their separate dependency edges.
    """

    config = config or PreprocessingConfig()
    diagnostics: list[PreprocessingDiagnostic] = []
    included_files: list[IncludedFile] = []
    generated_mappings: list[SourceMapping] = []
    line_counter = 0

    def emit_line(line: str, mapping: SourceMapping, out: list[str]) -> None:
        """Append one output line and its corresponding generated-line mapping.

        ``line_counter`` is shared across recursive expansions so mappings
        retain output order even when included text contributes many lines.
        """
        nonlocal line_counter
        out.append(line)
        line_counter += 1
        generated_mappings.append(
            SourceMapping(
                generated_line=line_counter,
                original_path=mapping.original_path,
                original_line=mapping.original_line,
                include_stack=list(mapping.include_stack),
            )
        )

    def expand_text(text: str, current_file: Path, stack: list[Path]) -> list[str]:
        """Recursively replace include lines in one source fragment.

        ``stack`` contains resolved paths currently being expanded and is used
        only for cycle detection. The function appends diagnostics instead of
        raising so siblings and following source survive independent failures.
        """
        out: list[str] = []
        mappings = parse_linemarker_mappings(text, filename=str(current_file))
        mapping_by_line = {mapping.generated_line: mapping for mapping in mappings}
        for generated_line, line in enumerate(text.splitlines(), start=1):
            marker = _parse_linemarker(line)
            if marker is not None:
                mapping = _mapping_for_generated_line(mappings, generated_line, current_file)
                emit_line(line, mapping, out)
                continue
            mapping = mapping_by_line.get(generated_line) or SourceMapping(
                generated_line=generated_line,
                original_path=str(current_file),
                original_line=generated_line,
                include_stack=[str(path) for path in stack],
            )
            match = _FORTRAN_INCLUDE_RE.match(line)
            if match is None:
                emit_line(line, mapping, out)
                continue

            target = match.group("path")
            resolved = _resolve_fortran_include(target, mapping.original_path, include_dirs)
            if resolved is None:
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_NOT_FOUND",
                        message=f'Fortran INCLUDE file "{target}" was not found',
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue
            try:
                resolved_abs = resolved.resolve()
            except OSError:
                resolved_abs = resolved.absolute()
            if resolved_abs in stack:
                cycle = " -> ".join(str(path) for path in [*stack, resolved_abs])
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_CYCLE",
                        message=f"Fortran INCLUDE cycle detected: {cycle}",
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue

            kind: DependencyKind = "project"
            included_files.append(
                IncludedFile(
                    path=str(resolved_abs),
                    included_by=mapping.original_path,
                    include_line=mapping.original_line,
                    mechanism="fortran_include",
                    dependency_kind=kind,
                    exposure=_exposure_for(str(resolved_abs), kind, config),
                )
            )
            emit_line(_line_marker(1, str(resolved_abs), 1), mapping, out)
            try:
                include_text = resolved.read_text(encoding="utf-8")
            except OSError as exc:
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_NOT_FOUND",
                        message=f'Fortran INCLUDE file "{target}" could not be read: {exc}',
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue
            out.extend(expand_text(include_text, resolved_abs, [*stack, resolved_abs]))
            emit_line(_line_marker(mapping.original_line + 1, mapping.original_path, 2), mapping, out)
        return out

    root_abs = root_path.resolve() if root_path.exists() else root_path.absolute()
    expanded_lines = expand_text(source, root_abs, [root_abs])
    return (
        "\n".join(expanded_lines) + ("\n" if source.endswith("\n") else ""),
        included_files,
        generated_mappings,
        diagnostics,
    )


__all__ = ("expand_native_fortran_includes",)


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        source_path = Path(directory) / "geometry.f90"
        include_path = Path(directory) / "dimensions.inc"
        source = "module geometry\ninclude 'dimensions.inc'\nend module geometry\n"
        source_path.write_text(source, encoding="utf-8")
        include_path.write_text("integer, parameter :: dimensions = 3\n", encoding="utf-8")

        expanded, dependencies, mappings, diagnostics = expand_native_fortran_includes(
            source,
            root_path=source_path,
            include_dirs=(),
        )
        parser_lines = tuple(line for line in expanded.splitlines() if not line.lstrip().startswith("#"))

        print("Expanded parser input:")
        print("\n".join(parser_lines))
        print(f"Native include dependencies: {len(dependencies)}")
        print(f"Generated source mappings: {len(mappings)}")
        print(f"Diagnostics: {len(diagnostics)}")
