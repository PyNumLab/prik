"""Render Fortran parser results and diagnostics for command-line inspection.

``main`` is reached through ``python3 -m prik.parsers.fortran``. Its default
route parses paths and formats parser-owned reports; JSON is the same result in
a machine-readable shape. The explicit ``--semantics`` and ``--pyi`` options
cross into semantic conversion and printing for inspection, rather than adding
meaning to the parser itself. Read the report-building helpers before CLI
argument handling when changing presentation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path

from prik.parsers.fortran.models import FortranParseError
from prik.parsers.fortran.parser import FortranParser


_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _diagnostic_color_enabled(*, disabled: bool) -> bool:
    if disabled:
        return False
    return "NO_COLOR" not in os.environ


def _to_dict_no_parent(obj):
    """Convert dataclass-based parse models into JSON-serializable dicts.

    The `FortranDerivedType.extends` field may contain a parent object reference.
    To keep JSON acyclic and stable for goldens, we drop any `parent`-like
    back-reference fields during serialization.
    """
    if is_dataclass(obj):
        out = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            if f.name == "parent" and not isinstance(value, str | type(None)):
                continue
            out[f.name] = _to_dict_no_parent(value)
        return out
    if isinstance(obj, list):
        return [_to_dict_no_parent(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_dict_no_parent(v) for k, v in obj.items()}
    return obj


def _collect_extensions(path: Path) -> list[Path]:
    """Recursively collect Fortran source files under a directory."""
    exts = {".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08"}
    return sorted(p for p in path.rglob("*") if p.suffix.lower() in exts)


def _parse_paths(paths: list[str]) -> dict[str, dict]:
    """Parse one or more files/directories into a per-file report structure."""
    out: dict[str, dict] = {}
    parser = FortranParser()
    expanded: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            expanded.extend(_collect_extensions(p))
        else:
            expanded.append(p)

    for p in sorted(set(expanded)):
        code = p.read_text(encoding="utf-8")
        parsed = parser.parse_file(code, filename=str(p))
        out[str(p)] = {
            "signatures": [_to_dict_no_parent(s) for s in parsed.procedures],
            "types": [_to_dict_no_parent(t) for t in parsed.derived_types],
            "modules": [_to_dict_no_parent(m) for m in parsed.modules],
            "submodules": [_to_dict_no_parent(m) for m in parsed.submodules],
            "programs": [_to_dict_no_parent(m) for m in parsed.programs],
            "block_data": [_to_dict_no_parent(m) for m in parsed.block_data_units],
        }
    return out


def _semantic_report(paths: list[str]) -> dict[str, dict]:
    """Generate semantic IR and pyi text per parsed file."""
    from prik.semantics.fortran2ir import fortran_module_to_semantic_module
    from prik.printers import emit_module

    parsed = _parse_paths(paths)
    semantic_out: dict[str, dict] = {}
    parser = FortranParser()

    for fname in parsed:
        code = Path(fname).read_text(encoding="utf-8")
        fobj = parser.parse_file(code, filename=fname)
        modules = [fortran_module_to_semantic_module(m) for m in fobj.modules]
        semantic_out[fname] = {
            "semantic_modules": [asdict(m) for m in modules],
            "pyi": "\n\n".join(emit_module(m) for m in modules).strip(),
        }

    return semantic_out


def _format_pyi_report(semantic_report: dict[str, dict]) -> str:
    lines: list[str] = []
    for fname, payload in semantic_report.items():
        lines.append(f"File: {fname}")
        pyi = payload.get("pyi", "")
        lines.append(pyi if pyi else "<no module declarations found>")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_var_type(var: dict) -> str:
    base = var.get("base_type", "unknown")
    kind = var.get("kind")
    rank = var.get("rank", 0)
    if base == "derived" and kind:
        base_repr = f"type({kind})"
    elif kind:
        base_repr = f"{base}({kind})"
    else:
        base_repr = base
    return f"{base_repr}[{rank}]"


def _limit_items(items: list[dict], print_limit: int | None) -> tuple[list[dict], int]:
    if print_limit is None:
        return items, 0
    visible_items = items[:print_limit]
    return visible_items, len(items) - len(visible_items)


def _format_variable_lines(variables: list[dict], *, indent: str, print_limit: int | None) -> list[str]:
    """Format variable declarations for optional verbose parse output."""
    if not variables:
        return []

    visible_variables, hidden = _limit_items(variables, print_limit)
    lines = [f"{indent}Variables: {len(variables)}"]
    for var in visible_variables:
        lines.append(f"{indent}  - {var['name']}:{_format_var_type(var)}")

    if hidden > 0:
        lines.append(f"{indent}  ... {hidden} more variables")

    return lines


def _format_report(
    report: dict[str, dict],
    *,
    show_vars: bool = False,
    print_limit: int | None = None,
) -> str:
    """Format the per-file parse report as a stable, human-readable tree."""
    lines: list[str] = []
    for fname, parsed in report.items():
        lines.append(f"File: {fname}")
        free_procedures = [s for s in parsed["signatures"] if s.get("module") is None]

        if free_procedures:
            lines.append(f"  Procedures: {len(free_procedures)}")
            visible_procedures, hidden = _limit_items(free_procedures, print_limit)
            for s in visible_procedures:
                args = ", ".join(f"{a['name']}:{_format_var_type(a)}" for a in s["arguments"])
                result_txt = f" -> {_format_var_type(s['result'])}" if s.get("result") else ""
                lines.append(f"    - {s['kind']} {s['name']}({args}){result_txt}")
            if hidden > 0:
                lines.append(f"    ... {hidden} more procedures")

        if parsed["types"]:
            lines.append(f"  Derived types: {len(parsed['types'])}")
            visible_types, hidden = _limit_items(parsed["types"], print_limit)
            for t in visible_types:
                lines.append(f"    - type {t['name']} (fields={len(t['fields'])}, methods={len(t['methods'])})")
            if hidden > 0:
                lines.append(f"    ... {hidden} more derived types")

        if parsed["modules"]:
            lines.append(f"  Modules: {len(parsed['modules'])}")
            visible_modules, hidden_modules = _limit_items(parsed["modules"], print_limit)
            for mod in visible_modules:
                lines.append(f"    - module {mod['name']} (vars={len(mod['variables'])}, uses={len(mod['uses'])})")
                if show_vars:
                    lines.extend(_format_variable_lines(mod["variables"], indent="      ", print_limit=print_limit))
                if mod.get("derived_types"):
                    lines.append(f"      Derived types: {len(mod['derived_types'])}")
                    visible_types, hidden = _limit_items(mod["derived_types"], print_limit)
                    for t in visible_types:
                        lines.append(
                            f"        - type {t['name']} (fields={len(t['fields'])}, methods={len(t['methods'])})"
                        )
                        if t.get("fields"):
                            lines.append(f"          Fields: {len(t['fields'])}")
                            visible_fields, hidden_fields = _limit_items(t["fields"], print_limit)
                            for field in visible_fields:
                                lines.append(f"            - {field['name']}:{_format_var_type(field)}")
                            if hidden_fields > 0:
                                lines.append(f"            ... {hidden_fields} more fields")
                    if hidden > 0:
                        lines.append(f"        ... {hidden} more derived types")
                if mod.get("procedures"):
                    lines.append(f"      Procedures: {len(mod['procedures'])}")
                    visible_procedures, hidden = _limit_items(mod["procedures"], print_limit)
                    for s in visible_procedures:
                        args = ", ".join(f"{a['name']}:{_format_var_type(a)}" for a in s["arguments"])
                        result_txt = f" -> {_format_var_type(s['result'])}" if s.get("result") else ""
                        lines.append(f"        - {s['kind']} {s['name']}({args}){result_txt}")
                    if hidden > 0:
                        lines.append(f"        ... {hidden} more procedures")
            if hidden_modules > 0:
                lines.append(f"    ... {hidden_modules} more modules")

        if parsed.get("submodules"):
            lines.append(f"  Submodules: {len(parsed['submodules'])}")
            visible_submodules, hidden_submodules = _limit_items(parsed["submodules"], print_limit)
            for submod in visible_submodules:
                parent = (
                    submod["parent"] if submod.get("ancestor") is None else f"{submod['ancestor']}:{submod['parent']}"
                )
                lines.append(
                    f"    - submodule {submod['name']} (parent={parent}, vars={len(submod['variables'])}, uses={len(submod['uses'])})"
                )
                if show_vars:
                    lines.extend(_format_variable_lines(submod["variables"], indent="      ", print_limit=print_limit))
                if submod.get("procedures"):
                    lines.append(f"      Procedures: {len(submod['procedures'])}")
                    visible_procedures, hidden = _limit_items(submod["procedures"], print_limit)
                    for proc in visible_procedures:
                        args = ", ".join(f"{a['name']}:{_format_var_type(a)}" for a in proc["arguments"])
                        result_txt = f" -> {_format_var_type(proc['result'])}" if proc.get("result") else ""
                        lines.append(f"        - {proc['kind']} {proc['name']}({args}){result_txt}")
                    if hidden > 0:
                        lines.append(f"        ... {hidden} more procedures")
            if hidden_submodules > 0:
                lines.append(f"    ... {hidden_submodules} more submodules")

        if parsed.get("programs"):
            lines.append(f"  Programs: {len(parsed['programs'])}")
            visible_programs, hidden_programs = _limit_items(parsed["programs"], print_limit)
            for prog in visible_programs:
                lines.append(f"    - program {prog['name']} (vars={len(prog['variables'])}, uses={len(prog['uses'])})")
                if show_vars:
                    lines.extend(_format_variable_lines(prog["variables"], indent="      ", print_limit=print_limit))
            if hidden_programs > 0:
                lines.append(f"    ... {hidden_programs} more programs")

        if parsed.get("block_data"):
            lines.append(f"  Block data: {len(parsed['block_data'])}")
            visible_blocks, hidden_blocks = _limit_items(parsed["block_data"], print_limit)
            for block in visible_blocks:
                name = block["name"] or "<unnamed>"
                lines.append(f"    - block data {name} (vars={len(block['variables'])})")
                if show_vars:
                    lines.extend(_format_variable_lines(block["variables"], indent="      ", print_limit=print_limit))
            if hidden_blocks > 0:
                lines.append(f"    ... {hidden_blocks} more block data units")

        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    """CLI entrypoint for `python -m prik.parsers.fortran` and `prik.parsers.fortran.cli`.

    The CLI supports:
    - parsing one or more paths (files and/or directories)
    - printing a human-readable report, or JSON
    - optionally writing the JSON report to a file
    """
    parser = argparse.ArgumentParser(description="Parse Fortran files and print a human-readable report or JSON.")
    parser.add_argument("paths", nargs="+", help="Fortran file(s) or directory path(s)")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument(
        "--semantics", action="store_true", help="Generate semantic IR models from parsed Fortran modules"
    )
    parser.add_argument(
        "--pyi", action="store_true", help="Print the generated Python .pyi content from semantic models"
    )
    parser.add_argument(
        "--show-vars",
        action="store_true",
        help="Include module, submodule, program, and block-data variables in the human-readable parse report.",
    )
    parser.add_argument(
        "--print-limit",
        type=int,
        metavar="N",
        help="Show at most N items per repeated section in the human-readable parse report.",
    )
    parser.add_argument(
        "--vars-limit",
        type=int,
        metavar="N",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--json-out", type=Path, help="Write JSON report to this file")
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color in parse diagnostics. Diagnostics are colored by default when available.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Re-raise parser errors so Python prints a traceback for parser debugging. "
        "Can also be enabled with FORTRAN_PARSER_DEBUG=1.",
    )
    args = parser.parse_args()

    print_limit = args.print_limit if args.print_limit is not None else args.vars_limit
    if print_limit is not None and print_limit < 0:
        parser.error("--print-limit must be >= 0")

    try:
        report = _parse_paths(args.paths)
        semantic = _semantic_report(args.paths) if (args.semantics or args.pyi) else None
    except FortranParseError as exc:
        if args.debug or _env_flag("FORTRAN_PARSER_DEBUG"):
            raise
        print(
            exc.format_diagnostic(color=_diagnostic_color_enabled(disabled=args.no_color), debug=False), file=sys.stderr
        )
        return 1

    payload = report
    if semantic is not None:
        payload = semantic

    if args.json_out:
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2))
    elif args.pyi:
        print(_format_pyi_report(semantic or {}))
    elif args.semantics:
        print(json.dumps(payload, indent=2))
    else:
        print(_format_report(report, show_vars=args.show_vars or args.vars_limit is not None, print_limit=print_limit))

    return 0


def _direct_example() -> None:
    """Render one in-memory parser result using the normal report formatter."""

    parsed = FortranParser().parse_file(
        """\
module geometry
contains
  real function norm(value)
    real, intent(in) :: value
    norm = abs(value)
  end function norm
end module geometry
""",
        filename="geometry.f90",
    )
    report = {
        "geometry.f90": {
            "signatures": [_to_dict_no_parent(item) for item in parsed.procedures],
            "types": [_to_dict_no_parent(item) for item in parsed.derived_types],
            "modules": [_to_dict_no_parent(item) for item in parsed.modules],
            "submodules": [_to_dict_no_parent(item) for item in parsed.submodules],
            "programs": [_to_dict_no_parent(item) for item in parsed.programs],
            "block_data": [_to_dict_no_parent(item) for item in parsed.block_data_units],
        }
    }
    print(_format_report(report, print_limit=2))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _direct_example()
    else:
        raise SystemExit(main())
