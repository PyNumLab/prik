from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from prik.preprocessing.languages import C_SOURCE_SUFFIXES, expand_source_paths
from prik.parsers.c.models import CFile, CParseError, c_model_to_dict
from prik.parsers.c.parser import CParser
from prik.parsers.c.sources import parse_c_source
from prik.preprocessing import PreprocessingConfig


_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _diagnostic_color_enabled(*, disabled: bool) -> bool:
    return not disabled and "NO_COLOR" not in os.environ


def expand_c_paths(paths: list[str]) -> list[Path]:
    """Return the C inputs the named files and directories hold, in the caller's order."""
    return list(expand_source_paths(paths, C_SOURCE_SUFFIXES))


def parse_c_report(
    paths: list[str],
    preprocessing: PreprocessingConfig | None = None,
) -> dict[str, dict]:
    """Parse each named C input and return its report, keyed by path."""
    preprocessing = preprocessing or PreprocessingConfig()
    parser = CParser()
    return {
        str(path): c_model_to_dict(parse_c_source(path, preprocessing, parser=parser)) for path in expand_c_paths(paths)
    }


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


def _direct_example() -> None:
    """Show the parser report boundary without reading a source file."""

    parsed = CParser().parse_file(
        "struct point { double x; double y; };\ndouble norm(struct point value);\n",
        filename="geometry.h",
    )
    print(format_c_report({"geometry.h": c_model_to_dict(parsed)}, print_limit=2))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _direct_example()
    else:
        raise SystemExit(main())
