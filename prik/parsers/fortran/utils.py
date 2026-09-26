"""Grammar-neutral lexical helpers for the Fortran parser.

``split_csv`` separates only top-level comma lists after a caller has chosen
the relevant Fortran construct. It builds no parser models and interprets no
declarations; ``lexer.py`` and ``parser.py`` own those next steps. Which
source form a file uses is ``prik.preprocessing.languages.fortran_source_form``.
"""

from __future__ import annotations

from prik.utilities.declaration_expressions import split_top_level_expression


def split_csv(text: str | None) -> list[str]:
    """Split a comma-separated list while respecting nested expression syntax.

    This is used for things that *look* like CSV in Fortran but may contain
    parenthesized expressions, e.g.:

    - argument lists: ``sub(x, y)``
    - attribute lists: ``dimension(n, m), contiguous``
    - shape lists: ``a(1:n, 0:m)``

    Only commas outside brackets and quoted literals are separators.
    """
    if not text:
        return []
    return [piece for piece in split_top_level_expression(text, ",") if piece]
