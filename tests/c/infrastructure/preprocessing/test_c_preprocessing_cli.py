"""C preprocessing options reach the compiler exactly, and its output reaches the parse report."""

import json
from pathlib import Path

import pytest

import prik.cli as prik_cli
from prik.preprocessing import PreprocessingError
from tests.c._support.preprocessing import (
    _failing_compiler,
    _fake_compiler,
)


def _use_fake_compiler(monkeypatch, tmp_path: Path, output: str) -> tuple[Path, Path]:
    compiler, args_file, env = _fake_compiler(tmp_path, output)
    for name in ("PRIK_FAKE_COMPILER_ARGS", "PRIK_FAKE_COMPILER_OUTPUT"):
        monkeypatch.setenv(name, env[name])
    return compiler, args_file


def test_cli_c_compiler_mode_runs_exact_compiler_and_parses_preprocessed_stdout(tmp_path: Path, monkeypatch, capsys):
    header = tmp_path / "api.h"
    header.write_text("#define API(ret) ret\nAPI(int) hidden(void);\n", encoding="utf-8")
    compiler, args_file = _use_fake_compiler(
        monkeypatch,
        tmp_path,
        '# 44 "include/api.h"\n#define API_VERSION 3\nint expanded(void);\n',
    )

    assert (
        prik_cli.main(
            [
                "parse",
                str(header),
                "--language",
                "c",
                "--json",
                "--compiler",
                str(compiler),
                "-I",
                "include",
                "-D",
                "API_EXPORT=",
                "-U",
                "DEBUG",
                "--std",
                "c11",
                "--compiler-arg=--sysroot=/opt/sdk",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)[str(header)]
    compiler_args = args_file.read_text(encoding="utf-8").splitlines()

    assert payload["preprocessing"] == "compiler"
    assert [fn["name"] for fn in payload["functions"]] == ["expanded"]
    assert "origin" not in payload["functions"][0]
    assert payload["functions"][0]["source_location"]["filename"] == "include/api.h"
    assert payload["functions"][0]["source_location"]["line"] == 45
    assert {macro["name"]: macro["value"] for macro in payload["macros"]} == {"API_VERSION": "3"}
    assert compiler_args == [
        "-E",
        "-x",
        "c",
        "-Iinclude",
        "-DAPI_EXPORT=",
        "-UDEBUG",
        "-std=c11",
        "--sysroot=/opt/sdk",
        str(header),
    ]
    recipe = payload["preprocessing_recipe"]
    assert recipe["mode"] == "compiler"
    assert recipe["language"] == "c"
    assert recipe["source_path"] == str(header)
    assert recipe["compiler"] == str(compiler)
    assert recipe["argv"] == [str(compiler), *compiler_args]
    assert recipe["include_dirs"] == ["include"]
    assert recipe["defines"] == ["API_EXPORT="]
    assert recipe["undefs"] == ["DEBUG"]
    assert recipe["standard"] == "c11"
    assert recipe["compiler_args"] == ["--sysroot=/opt/sdk"]
    assert recipe["compile_commands"] is None
    assert recipe["compile_commands_entry"] is None
    assert payload["original_source_paths"] == ["include/api.h"]


def test_cli_preprocessing_failure_has_category_without_traceback_unless_debug(tmp_path: Path, monkeypatch, capsys):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")
    compiler = _failing_compiler(tmp_path, "bad option\n")
    monkeypatch.delenv("PRIK_DEBUG", raising=False)
    argv = ["parse", str(header), "--language", "c", "--compiler", str(compiler)]

    assert prik_cli.main(argv) == 1
    err = capsys.readouterr().err
    assert "error[PREPROCESSOR_FAILED]" in err
    assert "bad option" in err

    with pytest.raises(PreprocessingError, match="bad option"):
        prik_cli.main([*argv, "--debug"])


def test_cli_c_compile_commands_mode_uses_exact_database_compiler(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "api.c"
    source.write_text("API(int) hidden(void);\n", encoding="utf-8")
    compiler, args_file = _use_fake_compiler(
        monkeypatch, tmp_path, '#line 12 "generated/api.h"\nint from_database(void);\n'
    )
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
                        "-DPROJECT_API=",
                        "-c",
                        str(source),
                        "-o",
                        "api.o",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    assert prik_cli.main(["parse", str(source), "--language", "c", "--json", "--compile-commands", str(database)]) == 0
    payload = json.loads(capsys.readouterr().out)[str(source)]
    compiler_args = args_file.read_text(encoding="utf-8").splitlines()

    assert [fn["name"] for fn in payload["functions"]] == ["from_database"]
    assert payload["functions"][0]["source_location"]["filename"] == "generated/api.h"
    assert payload["functions"][0]["source_location"]["line"] == 12
    assert compiler_args == ["-E", "-Iproject/include", "-DPROJECT_API=", str(source)]
    recipe = payload["preprocessing_recipe"]
    assert recipe["compiler"] == str(compiler)
    assert recipe["argv"] == [str(compiler), *compiler_args]
    assert recipe["cwd"] == str(tmp_path)
    assert recipe["compile_commands"] == str(database)
    assert recipe["compile_commands_entry"]["file"] == str(source)
    assert recipe["compile_commands_entry"]["arguments"][0] == str(compiler)
