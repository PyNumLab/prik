"""Extract parser-level intrinsic kind metadata from Fortran type specifications.

This module operates after the declaration parser has separated an intrinsic
base type from its parenthesized type specifier.  It preserves the syntax that
later parser and semantic stages need; it does not evaluate kind expressions or
make semantic datatype decisions.
"""

from __future__ import annotations

from prik.parsers.fortran.utils import split_csv


def extract_kind_from_type_spec(base_type: str, type_spec: str) -> str | None:
    """Return the parser-facing kind metadata encoded in one type specifier.

    Use this after declaration parsing has identified an intrinsic ``base_type``
    and isolated its parenthesized ``type_spec``.  Positional specs such as
    ``(8)`` and named ``kind=...`` specs return their kind expression.  For
    ``character`` declarations with ``len=...``, the complete inner spec is
    preserved because parser models carry character length and kind together.

    The function only extracts syntax: nested expressions remain unchanged and
    unsupported or empty forms return ``None`` for the caller to handle.
    """

    # Stage 1: normalize the already-isolated parenthesized specifier.
    if not type_spec:
        return None
    inside = type_spec[1:-1].strip()
    if not inside:
        return None

    # Stage 2: split only top-level comma-separated keyword arguments.
    items = split_csv(inside)
    keywords: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if sep:
            keywords[key.strip().lower()] = value.strip()

    # Stage 3: apply the parser's intrinsic-type metadata rules.
    if base_type == "character" and "len" in keywords:
        return inside
    if "kind" in keywords:
        return keywords["kind"]
    if len(items) == 1 and "=" not in items[0]:
        return items[0].strip()
    return None


if __name__ == "__main__":
    examples = [
        ("integer", "(4)"),
        ("real", "(kind=selected_real_kind(15, 307))"),
        ("character", "(len=16, kind=c_char)"),
    ]

    for base_type, type_spec in examples:
        print(f"{base_type}{type_spec} -> {extract_kind_from_type_spec(base_type, type_spec)}")
