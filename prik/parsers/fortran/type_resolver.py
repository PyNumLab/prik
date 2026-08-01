from __future__ import annotations

from .utils import split_csv


def extract_kind_from_type_spec(base_type: str, type_spec: str) -> str | None:
    if not type_spec:
        return None
    inside = type_spec[1:-1].strip()
    if not inside:
        return None

    items = split_csv(inside)
    keywords = {}
    for item in items:
        key, sep, value = item.partition("=")
        if sep:
            keywords[key.strip().lower()] = value.strip()

    if base_type == "character" and "len" in keywords:
        return inside
    if "kind" in keywords:
        return keywords["kind"]
    if len(items) == 1 and "=" not in items[0]:
        return items[0].strip()
    return None
