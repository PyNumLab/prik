import json
import re
from pathlib import Path

_PARSER_DATA = Path(__file__).parent
_FCODE_DIR = _PARSER_DATA / "fixtures"
_ALLOWLIST_PATH = _FCODE_DIR / "json_sanity_allowlist.json"


def _is_external_argument(arg: dict) -> bool:
    """Return True for procedure/external arguments where base_type may be unresolved."""
    attrs = {str(a).lower() for a in (arg.get("attributes") or [])}
    return arg.get("base_type") == "procedure" or "external" in attrs


def _has_known_base_type(entry: dict) -> bool:
    return entry.get("base_type") not in (None, "", "unknown")


def _is_valid_rank(entry: dict) -> bool:
    rank = entry.get("rank")
    return isinstance(rank, int) and rank >= 0


def _has_non_empty_name(entry: dict) -> bool:
    name = entry.get("name")
    return isinstance(name, str) and bool(name.strip())


def _split_dim_bounds(dim: str) -> tuple[str | None, str | None]:
    """Return the parser-normalized lower/upper bounds for a shape token."""
    part = dim.strip()
    if not part:
        return None, None
    if ":" not in part:
        return "1", part
    lower, upper = part.split(":", 1)
    return lower.strip() or None, upper.strip() or None


def _bounds_from_shape(shape: list[str]) -> tuple[list[str | None], list[str | None]]:
    lower_bounds = []
    upper_bounds = []
    for dim in shape:
        lower, upper = _split_dim_bounds(dim)
        lower_bounds.append(lower)
        upper_bounds.append(upper)
    return lower_bounds, upper_bounds


def _has_valid_bounds(entry: dict) -> bool:
    """Validate optional lower/upper bound metadata against rank and shape."""
    rank = entry.get("rank")
    shape = entry.get("shape")
    lbound = entry.get("lbound")
    ubound = entry.get("ubound")

    if not isinstance(rank, int) or rank < 0:
        return False

    if rank == 0:
        return lbound in (None, []) and ubound in (None, [])

    if lbound is not None and (not isinstance(lbound, list) or len(lbound) != rank):
        return False
    if ubound is not None and (not isinstance(ubound, list) or len(ubound) != rank):
        return False

    if isinstance(shape, list) and lbound is not None and ubound is not None:
        expected_lbound, expected_ubound = _bounds_from_shape(shape)
        return lbound == expected_lbound and ubound == expected_ubound

    return True


def _split_top_level_csv(text: str) -> list[str]:
    parts = []
    current = []
    depth = 0
    quote: str | None = None
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char in "([":
            depth += 1
        elif char in ")]" and depth:
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def _is_literal_json_parameter_value(value) -> bool:
    """Return True only for evaluated/literal parameter values in JSON output."""
    if isinstance(value, bool):
        return True
    if isinstance(value, int | float):
        return True
    if value is None:
        return False

    text = str(value).strip()
    if not text:
        return False
    if re.fullmatch(r"[+-]?\d+(?:\.\d*)?(?:[deDE][+-]?\d+)?", text):
        return True
    if re.fullmatch(r"\.(?:true|false)\.", text, re.IGNORECASE):
        return True
    if re.fullmatch(r"(['\"]).*\1", text):
        return True
    if text.startswith("[") and text.endswith("]"):
        return all(_is_literal_json_parameter_value(part) for part in _split_top_level_csv(text[1:-1]))
    if text.startswith("(/") and text.endswith("/)"):
        return all(_is_literal_json_parameter_value(part) for part in _split_top_level_csv(text[2:-2]))
    if text.startswith("(") and text.endswith(")"):
        parts = _split_top_level_csv(text[1:-1])
        return len(parts) == 2 and all(_is_literal_json_parameter_value(part) for part in parts)
    return False


def _is_valid_shape_info(entry: dict) -> bool:
    """Enforce non-ambiguous shape metadata with clear scalar/array exception rules.

    Rule: rank must match the shape metadata.
    - scalar (rank == 0): `shape`, `dimensions`, `lbound`, and `ubound` may be
      omitted/None/[] only.
    - array  (rank > 0): `shape`, `dimensions`, `lbound`, and `ubound` can be
      omitted for legacy fixtures, but if present they must be lists. Present
      bounds must match rank, and when `shape` is available they must match the
      parser-normalized lower/upper bounds for each dimension.
    """
    rank = entry.get("rank")
    shape = entry.get("shape")
    dimensions = entry.get("dimensions")

    if not isinstance(rank, int) or rank < 0:
        return False

    if rank == 0:
        return shape in (None, []) and dimensions in (None, []) and _has_valid_bounds(entry)

    return (
        (shape is None or isinstance(shape, list))
        and (dimensions is None or isinstance(dimensions, list))
        and _has_valid_bounds(entry)
    )


def _load_fixture_payload(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"signatures": data, "types": []}
    return {"signatures": data.get("signatures", []), "types": data.get("types", [])}


def _iter_typed_entries(node):
    if isinstance(node, dict):
        if "base_type" in node:
            yield node
        for value in node.values():
            yield from _iter_typed_entries(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_typed_entries(item)


def test_fortran_json_fixtures_are_valid_json():
    for path in _FCODE_DIR.rglob("*.json"):
        if path.name.endswith("_errors.json"):
            continue
        with path.open("r", encoding="utf-8") as f:
            json.load(f)


def test_fortran_json_fixtures_have_sane_types():
    with _ALLOWLIST_PATH.open("r", encoding="utf-8") as f:
        allowlist = {
            (item["file"], item["kind"], item["owner"], item["name"])
            for item in json.load(f)["allowed_unknown_base_types"]
        }

    unknown_entries = []
    invalid_rank_entries = []
    duplicate_argument_entries = []
    invalid_name_entries = []
    invalid_shape_entries = []
    invalid_kind_entries = []
    invalid_parameter_value_entries = []

    for path in _FCODE_DIR.rglob("*.json"):
        if path.name.endswith("_errors.json") or path.name == _ALLOWLIST_PATH.name:
            continue

        with path.open("r", encoding="utf-8") as f:
            raw_payload = json.load(f)
        payload = _load_fixture_payload(path)
        relpath = str(path.relative_to(_FCODE_DIR))
        if relpath.startswith("general/"):
            relpath = relpath[len("general/") :]
        for entry in _iter_typed_entries(raw_payload):
            if "kind" not in entry or entry.get("kind") is None:
                invalid_kind_entries.append((relpath, entry.get("base_type"), entry.get("name")))
            if entry.get("is_parameter"):
                value = entry.get("value")
                symbolic_value = entry.get("symbolic_value")
                if value is None and symbolic_value in (None, ""):
                    invalid_parameter_value_entries.append(
                        (relpath, entry.get("name"), "missing value and symbolic_value")
                    )
                if value is not None and not _is_literal_json_parameter_value(value):
                    invalid_parameter_value_entries.append((relpath, entry.get("name"), value))

        for sig in payload["signatures"]:
            arg_names = []
            for arg in sig.get("arguments", []):
                arg_name = arg.get("name")
                arg_names.append(arg_name)

                if not _has_non_empty_name(arg):
                    invalid_name_entries.append((relpath, "argument", sig.get("name"), arg_name))

                if not _is_valid_rank(arg):
                    invalid_rank_entries.append((relpath, "argument", sig.get("name"), arg_name, arg.get("rank")))

                if not _is_valid_shape_info(arg):
                    invalid_shape_entries.append(
                        (
                            relpath,
                            "argument",
                            sig.get("name"),
                            arg_name,
                            arg.get("rank"),
                            arg.get("shape"),
                            arg.get("dimensions"),
                        )
                    )

                if not _has_known_base_type(arg) and not _is_external_argument(arg):
                    unknown_entries.append((relpath, "argument", sig.get("name"), arg.get("name")))

            if len(arg_names) != len(set(arg_names)):
                duplicate_argument_entries.append((relpath, sig.get("name")))

            for var_name, var in sig.get("variables", {}).items():
                if not _has_non_empty_name(var):
                    invalid_name_entries.append((relpath, "variable", sig.get("name"), var_name))

                if not _is_valid_rank(var):
                    invalid_rank_entries.append((relpath, "variable", sig.get("name"), var_name, var.get("rank")))

                if not _is_valid_shape_info(var):
                    invalid_shape_entries.append(
                        (
                            relpath,
                            "variable",
                            sig.get("name"),
                            var_name,
                            var.get("rank"),
                            var.get("shape"),
                            var.get("dimensions"),
                        )
                    )

                if not _has_known_base_type(var):
                    unknown_entries.append((relpath, "variable", sig.get("name"), var_name))

        for dtype in payload["types"]:
            for field in dtype.get("fields", []):
                if not _has_non_empty_name(field):
                    invalid_name_entries.append((relpath, "field", dtype.get("name"), field.get("name")))

                if not _is_valid_rank(field):
                    invalid_rank_entries.append(
                        (relpath, "field", dtype.get("name"), field.get("name"), field.get("rank"))
                    )

                if not _is_valid_shape_info(field):
                    invalid_shape_entries.append(
                        (
                            relpath,
                            "field",
                            dtype.get("name"),
                            field.get("name"),
                            field.get("rank"),
                            field.get("shape"),
                            field.get("dimensions"),
                        )
                    )

                if not _has_known_base_type(field):
                    unknown_entries.append((relpath, "field", dtype.get("name"), field.get("name")))

    unexpected = sorted(e for e in unknown_entries if e not in allowlist)
    stale_allowlist = sorted(e for e in allowlist if e not in set(unknown_entries))

    assert not unexpected, f"Unexpected unknown base_type entries: {unexpected[:20]}"
    assert not stale_allowlist, f"Stale allowlist entries: {stale_allowlist[:20]}"
    assert not invalid_rank_entries, f"Invalid rank entries: {invalid_rank_entries[:20]}"
    assert not invalid_name_entries, f"Invalid empty/missing names: {invalid_name_entries[:20]}"
    assert not invalid_shape_entries, f"Invalid shape/dimensions metadata: {invalid_shape_entries[:20]}"
    assert not invalid_kind_entries, f"Missing/null kind entries: {invalid_kind_entries[:20]}"
    assert not invalid_parameter_value_entries, f"Invalid parameter values: {invalid_parameter_value_entries[:20]}"
    assert not duplicate_argument_entries, f"Duplicate argument names in signatures: {duplicate_argument_entries[:20]}"
