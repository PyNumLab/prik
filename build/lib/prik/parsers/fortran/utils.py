from __future__ import annotations


def detect_source_form(code: str, filename: str | None = None) -> str:
    """Detect whether a source looks like fixed-form or free-form Fortran.

    Resolution order:
    - If ``filename`` is provided, decide based on its suffix (most reliable).
    - Otherwise, use a small heuristic on the first ~20 lines to detect the
      fixed-form continuation column (column 6).

    Returns
    -------
    str
        ``"fixed"`` or ``"free"``.
    """
    if filename:
        lowered = filename.lower()
        if lowered.endswith((".f", ".for", ".ftn", ".f77")):
            return "fixed"
        if lowered.endswith((".f90", ".f95", ".f03", ".f08")):
            return "free"

    for line in code.splitlines()[:20]:
        if len(line) >= 6 and line[:5].strip() == "" and line[5:6].strip():
            return "fixed"
    return "free"


def split_csv(text: str | None) -> list[str]:
    """Split a comma-separated list while respecting parenthesis nesting.

    This is used for things that *look* like CSV in Fortran but may contain
    parenthesized expressions, e.g.:

    - argument lists: ``sub(x, y)``
    - attribute lists: ``dimension(n, m), contiguous``
    - shape lists: ``a(1:n, 0:m)``

    Only commas at parenthesis depth 0 are treated as separators.
    """
    if not text:
        return []
    out, cur, depth = [], [], 0
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]" and depth > 0:
            depth -= 1
        if ch == "," and depth == 0:
            piece = "".join(cur).strip()
            if piece:
                out.append(piece)
            cur = []
            continue
        cur.append(ch)
    piece = "".join(cur).strip()
    if piece:
        out.append(piece)
    return out
