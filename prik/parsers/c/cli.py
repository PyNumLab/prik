from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .models import CFile, CMacro, CParseError, CSourceLocation, c_model_to_dict
from .parser import CParser


_C_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _diagnostic_color_enabled(*, disabled: bool) -> bool:
    return not disabled and "NO_COLOR" not in os.environ


def _collect_c_extensions(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in _C_SOURCE_SUFFIXES)


def expand_c_paths(paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            expanded.extend(_collect_c_extensions(p))
        else:
            expanded.append(p)
    return sorted(set(expanded))


def attach_preprocessing_recipe(parsed: CFile, preprocessing_recipe: dict[str, Any] | None) -> None:
    """Attach compiler recipe side-channel facts to a parsed C file."""

    parsed.preprocessing_recipe = preprocessing_recipe
    if not preprocessing_recipe:
        return
    existing = {
        (
            macro.name,
            macro.source_location.filename if macro.source_location else None,
            macro.source_location.line if macro.source_location else None,
        )
        for macro in parsed.macros
    }
    for item in preprocessing_recipe.get("macros") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        location = CSourceLocation(
            filename=item.get("path") if isinstance(item.get("path"), str) else None,
            line=item.get("line") if isinstance(item.get("line"), int) else None,
            column=1,
        )
        key = (name, location.filename, location.line)
        if key in existing:
            continue
        parsed.macros.append(
            CMacro(
                name=name,
                value=item.get("value") if isinstance(item.get("value"), str) else None,
                function_like=bool(item.get("function_like")),
                source_location=location,
            )
        )
        existing.add(key)


def parse_c_report(
    paths: list[str],
    *,
    include_dirs: Sequence[str | Path] | None = None,
    preprocessing: str = "raw",
    source_loader: Callable[[Path], str | tuple[str, dict[str, Any] | None]] | None = None,
) -> dict[str, dict]:
    out: dict[str, dict] = {}
    parser = CParser()
    for p in expand_c_paths(paths):
        if source_loader is None:
            parsed = parser.parse_file(
                p,
                filename=str(p),
                include_dirs=include_dirs,
                preprocessing=preprocessing,
            )
        else:
            loaded = source_loader(p)
            source, preprocessing_recipe = loaded if isinstance(loaded, tuple) else (loaded, None)
            parsed = parser.parse_file(
                source,
                filename=str(p),
                include_dirs=include_dirs,
                preprocessing=preprocessing,
            )
            attach_preprocessing_recipe(parsed, preprocessing_recipe)
        out[str(p)] = c_model_to_dict(parsed)
    return out


def _label_items(items: list[object], *, keys: tuple[str, ...], fallback: str) -> list[str]:
    names: list[str] = []
    for index, item in enumerate(items, start=1):
        label = None
        if isinstance(item, dict):
            for key in keys:
                value = item.get(key)
                if isinstance(value, str) and value:
                    label = value
                    break
        names.append(label or f"{fallback} {index}")
    return names


def _named_items(items: list[object], *, fallback: str) -> list[str]:
    return _label_items(items, keys=("name", "reference", "anonymous_id"), fallback=fallback)


def _include_items(items: list[object]) -> list[str]:
    return _label_items(items, keys=("path", "name", "source", "filename"), fallback="include")


def _diagnostic_items(items: list[object]) -> list[str]:
    names: list[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            names.append(f"diagnostic {index}")
            continue
        code = item.get("code")
        severity = item.get("severity")
        message = item.get("message")
        parts = [part for part in (severity, code, message) if isinstance(part, str) and part]
        names.append(": ".join(parts) if parts else f"diagnostic {index}")
    return names


def _append_limited_items(lines: list[str], title: str, names: list[str], print_limit: int | None) -> None:
    lines.append(f"  {title}: {len(names)}")
    if print_limit is None:
        return
    for name in names[:print_limit]:
        lines.append(f"    - {name}")
    remaining = len(names) - min(len(names), print_limit)
    if remaining:
        lines.append(f"    ... {remaining} more {title.lower()}")


def format_c_report(report: dict[str, dict], *, print_limit: int | None = None) -> str:
    lines: list[str] = []
    for fname, parsed in report.items():
        lines.append(f"File: {fname}")
        lines.append(f"  Language: {parsed.get('language', 'c')}")
        _append_limited_items(
            lines, "Functions", _named_items(parsed.get("functions") or [], fallback="function"), print_limit
        )
        _append_limited_items(
            lines, "Structs", _named_items(parsed.get("structs") or [], fallback="struct"), print_limit
        )
        _append_limited_items(lines, "Unions", _named_items(parsed.get("unions") or [], fallback="union"), print_limit)
        _append_limited_items(lines, "Enums", _named_items(parsed.get("enums") or [], fallback="enum"), print_limit)
        _append_limited_items(
            lines, "Typedefs", _named_items(parsed.get("typedefs") or [], fallback="typedef"), print_limit
        )
        _append_limited_items(
            lines, "Variables", _named_items(parsed.get("variables") or [], fallback="variable"), print_limit
        )
        _append_limited_items(lines, "Macros", _named_items(parsed.get("macros") or [], fallback="macro"), print_limit)
        _append_limited_items(lines, "Includes", _include_items(parsed.get("includes") or []), print_limit)
        _append_limited_items(lines, "Diagnostics", _diagnostic_items(parsed.get("diagnostics") or []), print_limit)
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C parser CLI for the implemented C subset.")
    parser.add_argument("paths", nargs="+", help="C source/header file(s) or directory path(s)")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--out", type=str, help="Write parser JSON to a file")
    parser.add_argument(
        "--print-limit",
        type=int,
        metavar="N",
        help="Show at most N items per repeated section in the human-readable parse report.",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color in parse diagnostics")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Re-raise parser errors so Python prints a traceback for parser debugging.",
    )
    args = parser.parse_args(argv)
    if args.print_limit is not None and args.print_limit < 0:
        parser.error("--print-limit must be >= 0")

    try:
        payload = parse_c_report(args.paths)
    except CParseError as exc:
        if args.debug or _env_flag("C_PARSER_DEBUG"):
            raise
        print(
            exc.format_diagnostic(color=_diagnostic_color_enabled(disabled=args.no_color), debug=False), file=sys.stderr
        )
        return 1
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 0

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_c_report(payload, print_limit=args.print_limit))
    return 0


__all__ = (
    "CFile",
    "expand_c_paths",
    "format_c_report",
    "main",
    "parse_c_report",
)
