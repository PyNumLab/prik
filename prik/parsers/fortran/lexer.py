from __future__ import annotations

from .utils import detect_source_form


def strip_comment(line: str, form: str) -> str:
    """Remove comments from a single source line.

    - **Fixed form**: lines starting with ``c``, ``C``, ``*`` or ``!`` in column 1
      are treated as full-line comments.
    - **Free form**: ``!`` starts an inline comment *unless* it occurs inside a
      quoted string literal (single or double quotes).
    """
    omp = line.lstrip()
    omp_lower = omp.lower()
    if omp_lower.startswith("!$omp"):
        return omp
    if form == "fixed" and line[:5].lower() in {"c$omp", "*$omp"}:
        return "!$omp" + line[5:]
    if line.lstrip().startswith("#"):
        return line
    if form == "fixed" and line and line[0] in ("c", "C", "*", "!"):
        return ""
    in_string = False
    quote = ""
    out = []
    for c in line:
        if c in ('"', "'"):
            if in_string and c == quote:
                in_string = False
                quote = ""
            elif not in_string:
                in_string = True
                quote = c
            out.append(c)
            continue
        if c == "!" and not in_string:
            break
        out.append(c)
    return "".join(out)


def preprocess_lines(code: str, filename: str | None = None) -> list[tuple[str, int, str]]:
    """Preprocess Fortran source into parse-ready logical lines.

    This is the lexer/preprocessing stage used by all parsing entrypoints.
    It performs:

    - **Source-form detection** (fixed vs free) via `detect_source_form`.
    - **Comment stripping** (including fixed-form comment-line rules).
    - **Continuation folding**:
      - fixed-form: continuation in column 6 (1-based)
      - free-form: trailing ``&`` and optional leading ``&`` on the next line

    Returns a list of ``(logical_line, original_line_number, original_source_line)``
    tuples so downstream parsers can raise `FortranParseError` with accurate
    location context even after folding.
    """
    form = detect_source_form(code, filename)
    raw_lines = code.splitlines()
    raw = [
        (strip_comment(raw_line.rstrip("\n"), form), i + 1, raw_line.rstrip("\n"))
        for i, raw_line in enumerate(raw_lines)
    ]

    folded: list[tuple[str, int, str]] = []
    pending = ""
    pending_lineno = 0
    pending_raw = ""
    continuing = False
    for stripped_line, lineno, original_line in raw:
        if form == "fixed":
            if stripped_line.lstrip().lower().startswith("!$omp"):
                if pending:
                    folded.append((pending, pending_lineno, pending_raw))
                    pending = ""
                    pending_lineno = 0
                    pending_raw = ""
                    continuing = False
                folded.append((stripped_line.strip(), lineno, original_line))
                continue
            cont = len(stripped_line) >= 6 and stripped_line[5:6].strip() != ""
            text = stripped_line[6:] if len(stripped_line) > 6 else ""
            if not text.strip() and not continuing:
                continue
            if cont and pending:
                pending += " " + text.strip()
                continuing = False
                continue
            if pending:
                folded.append((pending, pending_lineno, pending_raw))
            pending = text.strip()
            pending_lineno = lineno
            pending_raw = original_line
            continuing = False
            continue

        line = stripped_line.rstrip()
        if not line and not continuing:
            continue
        starts_with_amp = line.lstrip().startswith("&")
        if starts_with_amp:
            line = line.lstrip()[1:].lstrip()
        if continuing:
            pending += line
        else:
            pending = line
            pending_lineno = lineno
            pending_raw = original_line
        if pending.endswith("&"):
            pending = pending[:-1].rstrip()
            continuing = True
            continue
        folded.append((pending, pending_lineno, pending_raw))
        pending = ""
        pending_lineno = 0
        pending_raw = ""
        continuing = False

    if pending:
        folded.append((pending, pending_lineno, pending_raw))
    return folded
