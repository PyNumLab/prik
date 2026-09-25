"""Read one C input the way every C route parses it.

A build, ``prik generate``, and a parse report all parse a C path here, so the
same preprocessing, include directories, and recipe provenance apply to each.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prik.parsers.c.models import CFile, CMacro, CSourceLocation
from prik.parsers.c.parser import CParser
from prik.preprocessing import PreprocessingConfig, run_compiler_preprocessor_with_recipe


def parse_c_source(path: Path | str, preprocessing: PreprocessingConfig, *, parser: CParser | None = None) -> CFile:
    """Parse one C input under ``preprocessing``.

    Compiler preprocessing expands the input first and attaches its recipe,
    which include exposure reads to keep an included header's declarations
    out of the input's own. Otherwise the text is parsed as written.
    """
    parser = parser or CParser()
    source_path = Path(path)
    if not preprocessing.uses_compiler:
        return parser.parse_file(
            source_path,
            filename=str(source_path),
            include_dirs=preprocessing.include_dirs,
            preprocessing="raw",
        )
    source, recipe = run_compiler_preprocessor_with_recipe(source_path, language="c", config=preprocessing)
    parsed = parser.parse_file(
        source,
        filename=str(source_path),
        include_dirs=preprocessing.include_dirs,
        preprocessing="compiler",
    )
    attach_preprocessing_recipe(parsed, recipe.to_dict())
    return parsed


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
