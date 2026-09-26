"""Tests split by stable ownership concept from `test_cli.py`."""

import json
from pathlib import Path

import pytest

import prik.preprocessing.source as preprocessing
from prik.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    build_compile_commands_invocation,
    build_direct_preprocess_invocation,
    build_preprocess_invocation,
    build_template_preprocess_invocation,
)
from tests.c._support.preprocessing import _assert_preprocessing_error


def test_direct_c_preprocess_invocation_uses_exact_compiler_and_flags(tmp_path: Path):
    source = tmp_path / "api.h"
    config = PreprocessingConfig(
        mode="compiler",
        compiler="/usr/bin/clang-18",
        include_dirs=["include", "/opt/sdk/include"],
        defines=["API_EXPORT=", "USE_FAST"],
        undefs=["DEBUG"],
        std="c11",
        compiler_args=["--sysroot=/opt/sdk", "-target", "x86_64-linux-gnu"],
    )

    invocation = build_direct_preprocess_invocation(source, language="c", config=config)

    assert invocation == preprocessing.Invocation(
        argv=[
            "/usr/bin/clang-18",
            "-E",
            "-x",
            "c",
            "-Iinclude",
            "-I/opt/sdk/include",
            "-DAPI_EXPORT=",
            "-DUSE_FAST",
            "-UDEBUG",
            "-std=c11",
            "--sysroot=/opt/sdk",
            "-target",
            "x86_64-linux-gnu",
            str(source),
        ],
        cwd=None,
        adapter="gcc-compatible-c",
        language="c",
        compiler="/usr/bin/clang-18",
        capabilities={"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )


def test_direct_preprocess_invocation_rejects_missing_compiler_and_unknown_language(tmp_path: Path):
    source = tmp_path / "input.txt"
    with pytest.raises(PreprocessingError) as exc_info:
        build_direct_preprocess_invocation(source, language="c", config=PreprocessingConfig(mode="compiler"))
    _assert_preprocessing_error(
        exc_info,
        message="c compiler preprocessing requires --compiler with an exact executable",
    )
    with pytest.raises(PreprocessingError) as exc_info:
        build_direct_preprocess_invocation(
            source,
            language="rust",
            config=PreprocessingConfig(mode="compiler", compiler="cc"),
        )
    _assert_preprocessing_error(
        exc_info,
        message="compiler preprocessing is not supported for language 'rust'",
    )


def test_compile_commands_invocation_uses_database_compiler_and_filters_compile_only_args(tmp_path: Path):
    source = tmp_path / "src" / "api.c"
    source.parent.mkdir()
    source.write_text("int api(void);\n", encoding="utf-8")
    fake_compiler = tmp_path / "toolchains" / "gcc-13"
    fake_compiler.parent.mkdir()
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [
                {
                    "directory": str(tmp_path),
                    "file": "src/api.c",
                    "arguments": [
                        str(fake_compiler),
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
    config = PreprocessingConfig(mode="compiler", compile_commands=str(database), defines=["CLI_DEFINE=1"])

    invocation = build_compile_commands_invocation(source, config=config)

    assert invocation == preprocessing.Invocation(
        argv=[
            str(fake_compiler),
            "-E",
            "-DCLI_DEFINE=1",
            "-Iproject/include",
            "-DPROJECT_API=",
            str(source),
        ],
        cwd=str(tmp_path),
        adapter="gcc-compatible-c",
        language="c",
        compiler=str(fake_compiler),
        compile_commands=str(database),
        compile_commands_entry={
            "directory": str(tmp_path),
            "file": "src/api.c",
            "arguments": [
                str(fake_compiler),
                "-Iproject/include",
                "-DPROJECT_API=",
                "-c",
                str(source),
                "-o",
                "api.o",
            ],
        },
        capabilities={"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not json", "invalid compile commands JSON"),
        ("{}", "must contain a list"),
        ("[]", "no compile_commands entry found"),
        (
            '[{"directory": ".", "file": "api.c", "arguments": ["cc"]}, {"directory": ".", "file": "api.c", "arguments": ["cc"]}]',
            "multiple compile_commands entries",
        ),
        ('[{"directory": ".", "arguments": ["cc"]}]', "missing 'file'"),
        ('[{"directory": ".", "file": "api.c", "arguments": "cc -c api.c"}]', "'arguments' must contain a list"),
        ('[{"directory": ".", "file": "api.c", "command": ["cc"]}]', "'command' must contain a string"),
        ('[{"directory": ".", "file": "api.c"}]', "must contain 'arguments' or 'command'"),
        ('[{"directory": ".", "file": "api.c", "arguments": []}]', "empty command"),
        ("[1]", "entries must be objects"),
    ],
)
def test_compile_commands_invocation_reports_invalid_database_entries(tmp_path: Path, payload: str, message: str):
    source = tmp_path / "api.c"
    database = tmp_path / "compile_commands.json"
    source.write_text("int api(void);\n", encoding="utf-8")
    database.write_text(payload.replace('"directory": "."', f'"directory": "{tmp_path}"'), encoding="utf-8")

    with pytest.raises(PreprocessingError, match=message) as exc_info:
        build_compile_commands_invocation(
            source,
            config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
        )
    assert exc_info.value.category == "INVALID_COMPILER_ARGUMENTS"
    assert exc_info.value.diagnostics == []


def test_compile_commands_invocation_reports_missing_file_and_supports_command_strings(tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    with pytest.raises(PreprocessingError) as exc_info:
        build_compile_commands_invocation(source, config=PreprocessingConfig(mode="compiler"))
    _assert_preprocessing_error(exc_info, message="compile_commands database path is missing")

    missing = tmp_path / "absent.json"
    with pytest.raises(PreprocessingError, match="cannot read compile commands file"):
        build_compile_commands_invocation(
            source,
            config=PreprocessingConfig(mode="compiler", compile_commands=str(missing)),
        )

    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [{"directory": str(tmp_path), "file": str(source), "command": f"cc -c {source} -oapi.o /Fowindows.obj"}]
        ),
        encoding="utf-8",
    )
    invocation = build_compile_commands_invocation(
        source,
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database), compiler="clang"),
    )
    assert invocation.argv == ["clang", "-E", str(source)]


@pytest.mark.parametrize(
    "compile_only_args",
    [
        pytest.param(["-c"], id="compile-only"),
        pytest.param(["/c"], id="msvc-compile-only"),
        pytest.param(["-o", "api.o"], id="separate-output"),
        pytest.param(["-oapi.o"], id="joined-output"),
        pytest.param(["/Foapi.obj"], id="msvc-output"),
        pytest.param(["-MF", "deps.d", "-MT", "api.o", "-MQ", "api.o"], id="separate-dependency-outputs"),
        pytest.param(["-MFdeps.d", "-MTapi.o", "-MQapi.o"], id="joined-dependency-outputs"),
    ],
)
def test_compile_commands_invocation_drops_compile_only_args_without_skipping_following_args(
    tmp_path: Path, compile_only_args: list[str]
):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [{"directory": str(tmp_path), "file": "api.c", "arguments": ["cc", *compile_only_args, "-Wall", "api.c"]}]
        ),
        encoding="utf-8",
    )

    invocation = build_compile_commands_invocation(
        source,
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
    )

    assert invocation.argv == ["cc", "-E", "-Wall", str(source)]


def test_compile_commands_invocation_defaults_missing_directory_to_current_directory(tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps([{"file": str(source), "arguments": ["cc", str(source)]}]),
        encoding="utf-8",
    )

    invocation = build_compile_commands_invocation(
        source,
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
    )

    assert invocation.cwd == "."
    assert invocation.argv == ["cc", "-E", str(source)]


def test_command_template_preprocess_invocation_expands_placeholders(tmp_path: Path):
    source = tmp_path / "api.h"
    config = PreprocessingConfig(
        mode="compiler",
        adapter="command-template",
        command_template=(
            "vendor-cc --preprocess {include_dirs} {defines} {undefs} {standard} {compiler_args} "
            "--meta={language}:{standard} {source}"
        ),
        include_dirs=["include"],
        defines=["API_EXPORT="],
        undefs=["DEBUG"],
        std="c11",
        compiler_args=["--target=x86_64-linux"],
    )

    invocation = build_template_preprocess_invocation(source, language="c", config=config)

    assert invocation == preprocessing.Invocation(
        argv=[
            "vendor-cc",
            "--preprocess",
            "-Iinclude",
            "-DAPI_EXPORT=",
            "-UDEBUG",
            "-std=c11",
            "--target=x86_64-linux",
            "--meta=c:c11",
            str(source),
        ],
        adapter="command-template",
        language="c",
        compiler="vendor-cc",
        capabilities={"dependency_output": False, "macro_dump": False, "linemarkers": False},
    )


def test_command_template_validation_and_dispatch_edges(tmp_path: Path):
    source = tmp_path / "api.h"
    source.write_text("int api(void);\n", encoding="utf-8")

    with pytest.raises(PreprocessingError, match="requires --preprocess-template"):
        build_template_preprocess_invocation(
            source,
            language="c",
            config=PreprocessingConfig(mode="compiler", adapter="command-template"),
        )
    with pytest.raises(PreprocessingError) as exc_info:
        build_template_preprocess_invocation(
            source,
            language="c",
            config=PreprocessingConfig(
                mode="compiler",
                adapter="command-template",
                command_template="''",
            ),
        )
    _assert_preprocessing_error(exc_info, message="custom command-template adapter expanded to an empty command")

    invocation = build_preprocess_invocation(
        source,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            compiler="vendor-cc",
            adapter="command-template",
            command_template="{compiler} {language} --std={standard} {source}",
            std="c99",
        ),
    )

    assert invocation.argv == ["vendor-cc", "c", "--std=c99", str(source)]

    with pytest.raises(PreprocessingError) as exc_info:
        build_preprocess_invocation(
            source,
            language="c",
            config=PreprocessingConfig(mode="compiler", adapter="command-template"),
        )
    _assert_preprocessing_error(
        exc_info,
        message="custom command-template adapter requires --preprocess-template",
    )
    assert build_preprocess_invocation(
        source,
        language="c",
        config=PreprocessingConfig(mode="compiler", command_template="vendor-cc {source}"),
    ).argv == ["vendor-cc", str(source)]
