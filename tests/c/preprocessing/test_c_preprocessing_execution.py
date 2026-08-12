"""Tests split by stable ownership concept from `test_cli.py`."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

import prik.preprocessing.source as preprocessing
from prik.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    run_compiler_preprocessor,
    run_compiler_preprocessor_with_recipe,
)


def test_preprocessing_module_direct_execution_example():
    repository_root = Path(__file__).parents[3]

    result = subprocess.run(
        [sys.executable, "prik/preprocessing/source.py"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == (
        "Before Fortran include expansion:\n"
        "module greeting\n"
        "include 'constants.inc'\n"
        "contains\n"
        "subroutine show_answer()\n"
        "print *, answer\n"
        "end subroutine show_answer\n"
        "end module greeting\n"
        "\n"
        "After Fortran include expansion:\n"
        "module greeting\n"
        "integer, parameter :: answer = 42\n"
        "contains\n"
        "subroutine show_answer()\n"
        "print *, answer\n"
        "end subroutine show_answer\n"
        "end module greeting\n"
        "Native includes: 1; diagnostics: 0\n"
        "\n"
        "Before C compiler preprocessing:\n"
        '#include "state.h"\n'
        "int state_id = STATE_ID;\n"
        "\n"
        "After C compiler preprocessing:\n"
        "int state_id = 42;\n"
    )


def test_run_compiler_preprocessor_success_and_failures(monkeypatch, tmp_path: Path):
    config = PreprocessingConfig(mode="compiler", compiler="cc")
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    calls = []

    def succeed(*args, **kwargs):
        calls.append((args, kwargs))
        return type("Done", (), {"returncode": 0, "stdout": "expanded", "stderr": ""})()

    monkeypatch.setattr(preprocessing.subprocess, "run", succeed)
    expanded, recipe = run_compiler_preprocessor_with_recipe(source, language="c", config=config)
    assert expanded == "expanded"
    assert recipe.compiler == "cc"
    assert run_compiler_preprocessor(source, language="c", config=config) == "expanded"
    assert calls == [
        (
            (["cc", "-E", "-x", "c", str(source)],),
            {"cwd": None, "capture_output": True, "text": True, "timeout": 60, "check": False},
        ),
        (
            (["cc", "-E", "-x", "c", str(source)],),
            {"cwd": None, "capture_output": True, "text": True, "timeout": 60, "check": False},
        ),
    ]

    def raise_oserror(*_args, **_kwargs):
        raise OSError("cannot start")

    monkeypatch.setattr(preprocessing.subprocess, "run", raise_oserror)
    with pytest.raises(PreprocessingError) as exc_info:
        run_compiler_preprocessor(source, language="c", config=config)
    assert str(exc_info.value) == "failed to run compiler preprocessor: cannot start"
    assert exc_info.value.category == "PREPROCESSOR_FAILED"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_FAILED",
            "message": "failed to run compiler preprocessor: cannot start",
            "severity": "error",
            "path": None,
            "line": None,
            "command": ["cc", "-E", "-x", "c", str(source)],
        }
    ]

    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 1, "stdout": "", "stderr": "bad option"})(),
    )
    with pytest.raises(PreprocessingError) as exc_info:
        run_compiler_preprocessor(source, language="c", config=config)
    assert str(exc_info.value) == "compiler preprocessing failed with exit code 1\nbad option"
    assert exc_info.value.category == "PREPROCESSOR_FAILED"
    assert [diagnostic.to_dict() for diagnostic in exc_info.value.diagnostics] == [
        {
            "category": "PREPROCESSOR_FAILED",
            "message": "bad option",
            "severity": "error",
            "path": None,
            "line": None,
            "command": ["cc", "-E", "-x", "c", str(source)],
        }
    ]


def test_preprocess_source_preserves_exact_success_metadata(monkeypatch, tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    expanded = f'# 1 "{source}"\n#define API 1\nint value;\n'
    monkeypatch.setattr(
        preprocessing.subprocess,
        "run",
        lambda *_args, **_kwargs: type("Done", (), {"returncode": 0, "stdout": expanded, "stderr": ""})(),
    )
    config = PreprocessingConfig(
        mode="compiler",
        compiler=str(tmp_path / "cc"),
        include_dirs=["include"],
        defines=["CLI=1"],
        undefs=["DEBUG"],
        std="c11",
        compiler_args=["-dD"],
    )

    result = preprocessing.preprocess_source(source, language="c", config=config)

    argv = [
        str(tmp_path / "cc"),
        "-E",
        "-x",
        "c",
        "-Iinclude",
        "-DCLI=1",
        "-UDEBUG",
        "-std=c11",
        "-dD",
        str(source),
    ]
    included_files = [
        {
            "path": str(source),
            "included_by": None,
            "include_line": None,
            "mechanism": "c_include",
            "dependency_kind": "root",
            "exposure": "public",
        }
    ]
    mappings = [
        {
            "generated_line": 2,
            "original_path": str(source),
            "original_line": 1,
            "include_stack": [str(source)],
        },
        {
            "generated_line": 3,
            "original_path": str(source),
            "original_line": 2,
            "include_stack": [str(source)],
        },
    ]
    macros = [
        {
            "name": "API",
            "value": "1",
            "function_like": False,
            "parameters": None,
            "path": str(source),
            "line": 1,
            "builtin": False,
        }
    ]
    recipe = {
        "language": "c",
        "compiler": str(tmp_path / "cc"),
        "mode": "compiler",
        "adapter": "gcc-compatible-c",
        "argv": argv,
        "cwd": None,
        "include_dirs": ["include"],
        "defines": ["CLI=1"],
        "undefs": ["DEBUG"],
        "standard": "c11",
        "std": "c11",
        "compiler_args": ["-dD"],
        "source_path": str(source),
        "source_file": str(source),
        "compile_commands": None,
        "compile_commands_entry": None,
        "command_template": None,
        "included_files": included_files,
        "source_mappings": mappings,
        "macros": macros,
        "diagnostics": [],
        "capabilities": {"dependency_output": True, "macro_dump": True, "linemarkers": True},
    }
    assert result.to_dict() == {
        "source": expanded,
        "recipe": recipe,
        "included_files": included_files,
        "source_mappings": mappings,
        "macros": macros,
        "diagnostics": [],
    }


def test_run_compiler_preprocessor_with_recipe_restores_sparse_recipe_defaults(monkeypatch, tmp_path: Path):
    source = tmp_path / "api.c"
    result = preprocessing.PreprocessResult(source="expanded\n", recipe={"language": "c"})
    monkeypatch.setattr(preprocessing, "preprocess_source", lambda *_args, **_kwargs: result)

    expanded, recipe = run_compiler_preprocessor_with_recipe(source, language="c", config=PreprocessingConfig())

    assert expanded == "expanded\n"
    assert recipe.mode == "compiler"
    assert recipe.adapter == "direct"


def test_preprocess_source_uses_compile_database_working_directory(monkeypatch, tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    compiler = tmp_path / "cc"
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps([{"directory": str(tmp_path), "file": str(source), "arguments": [str(compiler), str(source)]}]),
        encoding="utf-8",
    )
    calls = []

    def succeed(*args, **kwargs):
        calls.append((args, kwargs))
        return type("Done", (), {"returncode": 0, "stdout": "int api(void);\n", "stderr": ""})()

    monkeypatch.setattr(preprocessing.subprocess, "run", succeed)

    result = preprocessing.preprocess_source(
        source,
        language="c",
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
    )

    assert result.source == "int api(void);\n"
    assert result.source_mappings == [
        preprocessing.SourceMapping(
            generated_line=1,
            original_path=str(source),
            original_line=1,
            include_stack=[str(source)],
        )
    ]
    assert calls == [
        (
            ([str(compiler), "-E", str(source)],),
            {"cwd": str(tmp_path), "capture_output": True, "text": True, "timeout": 60, "check": False},
        )
    ]
