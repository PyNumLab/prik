"""Build-local f2py intent overlays for caller-owned scalar storage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import re


_FIXED_FORM_SUFFIXES = frozenset({".f", ".for", ".f77", ".ftn"})


def prepare_f2py_intent_sources(
    sources: Sequence[Path],
    workdir: Path,
    inout_arguments: Mapping[str, tuple[str, ...]],
) -> tuple[Path, ...]:
    """Copy selected sources and add f2py-only ``intent(inout)`` directives."""
    overlay_root = workdir / "f2py-intent-sources"
    prepared: list[Path] = []
    for source in sources:
        arguments = inout_arguments.get(source.stem.lower())
        if arguments is None:
            prepared.append(source)
            continue

        overlay_root.mkdir(parents=True, exist_ok=True)
        target = overlay_root / source.name
        target.write_text(_with_inout_directive(source, arguments), encoding="utf-8")
        prepared.append(target)
    return tuple(prepared)


def _with_inout_directive(source: Path, arguments: tuple[str, ...]) -> str:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    declaration = re.compile(rf"^\s*subroutine\s+{re.escape(source.stem)}\s*\(", re.IGNORECASE)
    matches = [index for index, line in enumerate(lines) if declaration.match(line)]
    if len(matches) != 1:
        raise ValueError(f"expected one SUBROUTINE declaration for {source.stem}, found {len(matches)}")

    insertion_index = _statement_end(lines, matches[0], fixed_form=source.suffix.lower() in _FIXED_FORM_SUFFIXES)
    prefix = "Cf2py" if source.suffix.lower() in _FIXED_FORM_SUFFIXES else "!f2py"
    directive = f"{prefix} intent(inout) {', '.join(arguments)}\n"
    lines.insert(insertion_index, directive)
    return "".join(lines)


def _statement_end(lines: list[str], start: int, *, fixed_form: bool) -> int:
    index = start + 1
    if fixed_form:
        while index < len(lines) and len(lines[index]) > 5 and lines[index][5] not in {" ", "0", "\n", "\r"}:
            index += 1
        return index

    while index < len(lines) and lines[index - 1].rstrip().endswith("&"):
        index += 1
    return index
