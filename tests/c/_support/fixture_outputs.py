"""C fixture parsing, semantic conversion, and `.pyi` generation helpers."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from prik.parsers.c import CParser
from prik.parsers.c.cli import attach_preprocessing_recipe
from prik.preprocessing import PreprocessingConfig, preprocess_source
from prik.semantics.c2ir import c_project_to_semantic_module
from prik.printers import emit_module
from tests.c._support.paths import C_DATA_DIR, C_ROOT


GENERAL_C_DIR = C_DATA_DIR / "general"
C_PYI_FIXTURE_DIR = C_ROOT / "fixtures" / "pyi" / "general"
C_SOURCE_SUFFIXES = {".c", ".h", ".i"}
C_SOURCE_ORDER = {".c": 0, ".h": 1, ".i": 2}


def _c_fixture_sort_key(path: Path) -> tuple[int, str]:
    return (C_SOURCE_ORDER.get(path.suffix.lower(), 99), path.as_posix())


def iter_general_c_fixture_projects() -> list[tuple[Path, list[Path]]]:
    grouped: dict[Path, list[Path]] = {}
    for path in sorted(GENERAL_C_DIR.iterdir(), key=_c_fixture_sort_key):
        if path.is_file() and path.suffix.lower() in C_SOURCE_SUFFIXES:
            grouped.setdefault(Path(path.stem), []).append(path)
    return [(project_key, sorted(paths, key=_c_fixture_sort_key)) for project_key, paths in sorted(grouped.items())]


def parse_c_fixture_project(paths: list[Path]):
    compiler = shutil.which("cc")
    if compiler is None:
        raise RuntimeError("C fixture preprocessing requires cc")

    parser = CParser()
    parsed_files = {}
    root_paths = {str(path.resolve()) for path in paths}
    with TemporaryDirectory() as tmp_dir:
        system_include_dir = Path(tmp_dir)
        (system_include_dir / "stddef.h").write_text("", encoding="utf-8")
        (system_include_dir / "stdbool.h").write_text(
            "#define bool _Bool\n#define true 1\n#define false 0\n",
            encoding="utf-8",
        )
        (system_include_dir / "math.h").write_text("", encoding="utf-8")
        config = PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            include_dirs=sorted({str(path.parent) for path in paths}),
            compiler_args=["-dD", f"-isystem{system_include_dir}"],
        )
        for path in sorted(paths, key=_c_fixture_sort_key):
            preprocessed = preprocess_source(path, language="c", config=config)
            recipe = dict(preprocessed.recipe)
            recipe["macros"] = [item for item in recipe["macros"] if item.get("path") in root_paths]
            filename = path.relative_to(C_DATA_DIR).as_posix()
            parsed = parser.parse_file(
                preprocessed.source,
                filename=filename,
                preprocessing="compiler",
            )
            attach_preprocessing_recipe(parsed, recipe)
            parsed_files[filename] = parsed
    return parser._assemble_project(parsed_files)


def c_semantic_module_for_fixture_project(project_key: Path, paths: list[Path]):
    return c_project_to_semantic_module(
        parse_c_fixture_project(paths),
        name=project_key.as_posix().replace("/", "_"),
    )


def c_pyi_text_for_fixture_project(project_key: Path, paths: list[Path]) -> str:
    return emit_module(c_semantic_module_for_fixture_project(project_key, paths)).strip()


def c_pyi_fixture_path(project_key: Path) -> Path:
    return (C_PYI_FIXTURE_DIR / project_key).with_suffix(".pyi")


__all__ = (
    "C_PYI_FIXTURE_DIR",
    "c_pyi_fixture_path",
    "c_pyi_text_for_fixture_project",
    "iter_general_c_fixture_projects",
)
