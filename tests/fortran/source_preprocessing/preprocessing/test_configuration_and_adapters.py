"""Tests split by stable ownership concept from `test_cli.py`."""

import json
from pathlib import Path

import pytest

import prik.pipeline.preprocessing as preprocessing
from prik.pipeline.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    build_direct_preprocess_invocation,
    build_preprocess_invocation,
    expand_native_fortran_includes,
    run_compiler_preprocessor_with_recipe,
    validate_macro_name,
)
from tests.fortran.source_preprocessing.preprocessing._support import _assert_preprocessing_error


def test_direct_fortran_preprocess_invocation_uses_exact_compiler_and_cpp(tmp_path: Path):
    source = tmp_path / "solver.F90"
    config = PreprocessingConfig(
        mode="compiler",
        compiler="/usr/bin/gfortran-12",
        include_dirs=["include"],
        defines=["USE_MPI"],
        undefs=["DEBUG"],
        std="f2018",
    )

    invocation = build_direct_preprocess_invocation(source, language="fortran", config=config)

    assert invocation == preprocessing.Invocation(
        argv=[
            "/usr/bin/gfortran-12",
            "-E",
            "-cpp",
            "-Iinclude",
            "-DUSE_MPI",
            "-UDEBUG",
            "-std=f2018",
            str(source),
        ],
        cwd=None,
        adapter="gnu-fortran",
        language="fortran",
        compiler="/usr/bin/gfortran-12",
        capabilities={"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )
    assert preprocessing.GNUFortranAdapter().name == "gnu-fortran"


def test_direct_fortran_preprocess_invocation_hints_unknown_suffix_language(tmp_path: Path):
    source = tmp_path / "solver.source"
    config = PreprocessingConfig(mode="compiler", compiler="/usr/bin/gfortran-12")

    invocation = build_direct_preprocess_invocation(source, language="fortran", config=config)

    assert invocation.argv == [
        "/usr/bin/gfortran-12",
        "-E",
        "-cpp",
        "-x",
        "f95-cpp-input",
        str(source),
    ]


def test_direct_flang_preprocess_invocation_suppresses_line_markers(tmp_path: Path):
    source = tmp_path / "solver.F90"
    config = PreprocessingConfig(
        mode="compiler",
        compiler="/opt/llvm/bin/flang-new",
        defines=["USE_MPI"],
    )

    invocation = build_direct_preprocess_invocation(source, language="fortran", config=config)

    assert invocation == preprocessing.Invocation(
        argv=[
            "/opt/llvm/bin/flang-new",
            "-E",
            "-cpp",
            "-P",
            "-DUSE_MPI",
            str(source),
        ],
        cwd=None,
        adapter="llvm-flang",
        language="fortran",
        compiler="/opt/llvm/bin/flang-new",
        capabilities={"dependency_output": False, "macro_dump": False, "linemarkers": False},
    )


def test_preprocessing_config_internal_macros_recipe_and_validation(tmp_path: Path):
    source = tmp_path / "source.F90"
    plain = PreprocessingConfig()
    selected = PreprocessingConfig(defines=["USE_MPI", "VALUE=3"], undefs=["DEBUG"])

    assert plain.uses_compiler is False
    assert plain.fortran_internal_recipe(source) is None
    assert selected.fortran_internal_recipe(source)["source_path"] == str(source)
    validate_macro_name("NAME", "--define")
    validate_macro_name("name", "--define")
    validate_macro_name("_NAME=value", "--define")
    validate_macro_name("_NAME=value=with=equals", "--define")
    with pytest.raises(PreprocessingError) as exc_info:
        validate_macro_name("=value", "--define")
    _assert_preprocessing_error(exc_info, message="--define requires a macro name before '='")
    with pytest.raises(PreprocessingError) as exc_info:
        validate_macro_name("", "--define")
    _assert_preprocessing_error(exc_info, message="--define requires a macro name")
    with pytest.raises(PreprocessingError) as exc_info:
        validate_macro_name("bad-name", "--define")
    _assert_preprocessing_error(
        exc_info,
        message="--define: invalid macro name 'bad-name'; must be a valid identifier",
    )


def test_preprocessing_error_default_category_and_diagnostics():
    diagnostic = preprocessing.PreprocessingDiagnostic(category="PREPROCESSOR_FAILED", message="bad")

    default_error = PreprocessingError("default")
    detailed_error = PreprocessingError("detailed", diagnostics=[diagnostic])

    assert default_error.category == "PREPROCESSOR_FAILED"
    assert default_error.diagnostics == []
    assert str(default_error) == "default"
    assert detailed_error.category == "PREPROCESSOR_FAILED"
    assert detailed_error.diagnostics == [diagnostic]
    assert str(detailed_error) == "detailed"


def test_recipe_round_trip_preserves_all_preprocessing_metadata(monkeypatch, tmp_path: Path):
    source = tmp_path / "solver.F90"
    included = preprocessing.IncludedFile(
        path=str(tmp_path / "decls.inc"),
        included_by=str(source),
        include_line=2,
        mechanism="fortran_include",
        exposure="private",
    )
    mapping = preprocessing.SourceMapping(
        generated_line=3,
        original_path=included.path,
        original_line=1,
        include_stack=[str(source), included.path],
    )
    macro = preprocessing.MacroDefinition(name="USE_MPI", value="1", path=str(source), line=1)
    diagnostic = preprocessing.PreprocessingDiagnostic(
        category="PROVENANCE_UNAVAILABLE",
        message="no markers",
        severity="warning",
        command=["vendor-fc", "--expand"],
    )
    config = PreprocessingConfig(
        mode="compiler",
        include_dirs=["include"],
        defines=["USE_MPI=1"],
        undefs=["DEBUG"],
        std="f2018",
        compiler_args=["--dialect=strict"],
        command_template="{compiler} --expand {source}",
    )
    invocation = preprocessing.Invocation(
        argv=["vendor-fc", "--expand", str(source)],
        cwd=str(tmp_path),
        adapter="command-template",
        language="fortran",
        compiler="vendor-fc",
        compile_commands=str(tmp_path / "compile_commands.json"),
        compile_commands_entry={"directory": str(tmp_path), "file": str(source)},
        capabilities={"dependency_output": False, "macro_dump": False, "linemarkers": False},
    )
    result = preprocessing.PreprocessResult(
        source="expanded\n",
        recipe={},
        included_files=[included],
        source_mappings=[mapping],
        macros=[macro],
        diagnostics=[diagnostic],
    )
    expected = {
        "language": "fortran",
        "compiler": "vendor-fc",
        "mode": "compiler",
        "adapter": "command-template",
        "argv": ["vendor-fc", "--expand", str(source)],
        "cwd": str(tmp_path),
        "include_dirs": ["include"],
        "defines": ["USE_MPI=1"],
        "undefs": ["DEBUG"],
        "standard": "f2018",
        "std": "f2018",
        "compiler_args": ["--dialect=strict"],
        "source_path": str(source),
        "source_file": str(source),
        "compile_commands": str(tmp_path / "compile_commands.json"),
        "compile_commands_entry": {"directory": str(tmp_path), "file": str(source)},
        "command_template": "{compiler} --expand {source}",
        "included_files": [included.to_dict()],
        "source_mappings": [mapping.to_dict()],
        "macros": [macro.to_dict()],
        "diagnostics": [diagnostic.to_dict()],
        "capabilities": {"dependency_output": False, "macro_dump": False, "linemarkers": False},
    }

    recipe = preprocessing._recipe_from_invocation(source, "fortran", config, invocation, result)
    assert recipe.to_dict() == expected

    result.recipe = expected
    monkeypatch.setattr(preprocessing, "preprocess_source", lambda *_args, **_kwargs: result)
    expanded, restored = run_compiler_preprocessor_with_recipe(source, language="fortran", config=config)
    assert expanded == "expanded\n"
    assert restored.to_dict() == expected


def test_build_preprocess_invocation_supports_fortran_compile_database(tmp_path: Path):
    source = tmp_path / "solver.F90"
    source.write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")
    compiler = tmp_path / "toolchains" / "gfortran-13"
    compiler.parent.mkdir()
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [
                {
                    "directory": str(tmp_path),
                    "file": str(source),
                    "arguments": [
                        str(compiler),
                        "-Iproject/include",
                        "-cpp",
                        "-c",
                        str(source),
                        "-o",
                        "solver.o",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    invocation = build_preprocess_invocation(
        source,
        language="fortran",
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
    )

    assert invocation == preprocessing.Invocation(
        argv=[
            str(compiler),
            "-E",
            "-cpp",
            "-Iproject/include",
            "-cpp",
            str(source),
        ],
        cwd=str(tmp_path),
        adapter="gnu-fortran",
        language="fortran",
        compiler=str(compiler),
        compile_commands=str(database),
        compile_commands_entry={
            "directory": str(tmp_path),
            "file": str(source),
            "arguments": [
                str(compiler),
                "-Iproject/include",
                "-cpp",
                "-c",
                str(source),
                "-o",
                "solver.o",
            ],
        },
        capabilities={"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )


def test_native_fortran_missing_include_does_not_drop_following_source(tmp_path: Path):
    root = tmp_path / "root.F90"

    expanded, included_files, mappings, diagnostics = expand_native_fortran_includes(
        'include "missing.inc"\ninteger :: retained\n',
        root_path=root,
        include_dirs=[],
    )

    assert expanded == "integer :: retained\n"
    assert included_files == []
    assert [(mapping.generated_line, mapping.original_path, mapping.original_line) for mapping in mappings] == [
        (1, str(root), 2)
    ]
    assert [diagnostic.to_dict() for diagnostic in diagnostics] == [
        {
            "category": "INCLUDE_NOT_FOUND",
            "message": 'Fortran INCLUDE file "missing.inc" was not found',
            "severity": "error",
            "path": str(root),
            "line": 1,
            "command": [],
        }
    ]
