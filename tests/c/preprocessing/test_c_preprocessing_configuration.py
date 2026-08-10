"""Tests split by stable ownership concept from `test_cli.py`."""

import json
from pathlib import Path

import pytest

import prik.pipeline.preprocessing as preprocessing
from prik.pipeline.preprocessing import (
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


def test_preprocessing_metadata_models_and_adapter_helpers(tmp_path: Path):
    source = tmp_path / "api.c"
    source.write_text("int api(void);\n", encoding="utf-8")
    diagnostic = preprocessing.PreprocessingDiagnostic(
        category="PREPROCESSOR_FAILED",
        message="bad flag",
        path=str(source),
        line=3,
        command=["cc", "-E"],
    )
    included = preprocessing.IncludedFile(
        path=str(tmp_path / "public.h"),
        included_by=str(source),
        include_line=1,
    )
    mapping = preprocessing.SourceMapping(
        generated_line=2,
        original_path=str(source),
        original_line=7,
        include_stack=[str(source)],
    )
    macro = preprocessing.MacroDefinition(
        name="SQR",
        value="((x) * (x))",
        function_like=True,
        parameters=["x"],
        path=str(source),
        line=4,
    )
    plan = preprocessing.PreprocessingPlan(
        language="c",
        source_path=str(source),
        adapter="direct",
        compiler="cc",
        include_dirs=["include"],
        defines=["API=1"],
        undefs=["DEBUG"],
        standard="c11",
        compiler_args=["-Wall"],
    )
    result = preprocessing.PreprocessResult(
        source="#define SQR(x) ((x) * (x))\n",
        recipe={"mode": "compiler"},
        included_files=[included],
        source_mappings=[mapping],
        macros=[macro],
        diagnostics=[diagnostic],
    )
    recipe = preprocessing.PreprocessingRecipe(language="c", compiler="cc", standard="c11")

    assert diagnostic.to_dict() == {
        "category": "PREPROCESSOR_FAILED",
        "message": "bad flag",
        "severity": "error",
        "path": str(source),
        "line": 3,
        "command": ["cc", "-E"],
    }
    assert plan.to_dict() == {
        "language": "c",
        "source_path": str(source),
        "adapter": "direct",
        "compiler": "cc",
        "cwd": None,
        "include_dirs": ["include"],
        "defines": ["API=1"],
        "undefs": ["DEBUG"],
        "standard": "c11",
        "compiler_args": ["-Wall"],
        "compile_commands": None,
        "command_template": None,
    }
    assert included.to_dict() == {
        "path": str(tmp_path / "public.h"),
        "included_by": str(source),
        "include_line": 1,
        "mechanism": "cpp_include",
        "dependency_kind": "project",
        "exposure": "public",
    }
    assert mapping.to_dict() == {
        "generated_line": 2,
        "original_path": str(source),
        "original_line": 7,
        "include_stack": [str(source)],
    }
    assert macro.to_dict() == {
        "name": "SQR",
        "value": "((x) * (x))",
        "function_like": True,
        "parameters": ["x"],
        "path": str(source),
        "line": 4,
        "builtin": False,
    }
    assert result.to_dict() == {
        "source": "#define SQR(x) ((x) * (x))\n",
        "recipe": {"mode": "compiler"},
        "included_files": [included.to_dict()],
        "source_mappings": [mapping.to_dict()],
        "macros": [macro.to_dict()],
        "diagnostics": [diagnostic.to_dict()],
    }
    assert recipe.std == "c11"
    assert recipe.to_dict() == {
        "language": "c",
        "compiler": "cc",
        "mode": "compiler",
        "adapter": "direct",
        "argv": [],
        "cwd": None,
        "include_dirs": [],
        "defines": [],
        "undefs": [],
        "standard": "c11",
        "std": "c11",
        "compiler_args": [],
        "source_path": None,
        "source_file": None,
        "compile_commands": None,
        "compile_commands_entry": None,
        "command_template": None,
        "included_files": [],
        "source_mappings": [],
        "macros": [],
        "diagnostics": [],
        "capabilities": {},
    }

    adapter = preprocessing.GCCCompatibleCAdapter()
    config = PreprocessingConfig(mode="compiler", compiler="cc")
    assert adapter.build_preprocess_invocation(source, language="c", config=config) == preprocessing.Invocation(
        argv=["cc", "-E", "-x", "c", str(source)],
        cwd=None,
        adapter="gcc-compatible-c",
        language="c",
        compiler="cc",
        capabilities={"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )
    assert adapter.collect_dependencies(result) == [included]
    assert adapter.collect_macros(result) == [macro]
    assert adapter.parse_linemarkers('#line 7 "dir\\\\api\\".h"\nint x;\n')[0].original_line == 7
    assert adapter.parse_linemarkers("int x;\n", filename="api.h")[0].original_path == "api.h"

    invocation = preprocessing.CommandTemplateAdapter().build_preprocess_invocation(
        source,
        language="c",
        config=PreprocessingConfig(
            mode="compiler",
            compiler="vendor-cc",
            adapter="command-template",
            command_template="{compiler} --lang {language} {source}",
        ),
    )
    assert invocation.argv == ["vendor-cc", "--lang", "c", str(source)]


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
                    "file": str(source),
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
            "file": str(source),
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


def test_compile_commands_internal_helpers_cover_paths_commands_and_selection(monkeypatch, tmp_path: Path):
    source = tmp_path / "src" / "api.c"
    source.parent.mkdir()
    source.write_text("int api(void);\n", encoding="utf-8")
    relative_entry = {"directory": str(tmp_path), "file": "src/api.c"}
    absolute_entry = {"directory": "/ignored", "file": str(source)}

    assert preprocessing._entry_file_path(relative_entry) == source
    assert preprocessing._entry_file_path(absolute_entry) == source
    assert preprocessing._entry_file_path({"file": "api.c"}) == Path("api.c")
    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing._entry_file_path({})
    _assert_preprocessing_error(exc_info, message="compile_commands entry is missing 'file'")

    assert preprocessing._compile_command_argv({"arguments": ["cc", 7]}) == ["cc", "7"]
    assert preprocessing._compile_command_argv({"command": "cc -DNAME='two words' api.c"}) == [
        "cc",
        "-DNAME=two words",
        "api.c",
    ]
    for entry, message in [
        ({"arguments": "cc api.c"}, "compile_commands entry 'arguments' must contain a list"),
        ({"command": ["cc", "api.c"]}, "compile_commands entry 'command' must contain a string"),
        ({}, "compile_commands entry must contain 'arguments' or 'command'"),
        ({"arguments": []}, "compile_commands entry has an empty command"),
    ]:
        with pytest.raises(PreprocessingError) as exc_info:
            preprocessing._compile_command_argv(entry)
        _assert_preprocessing_error(exc_info, message=message)

    args = [
        "-c",
        "/c",
        "-o",
        "api.o",
        "-oother.o",
        "/Fowindows.obj",
        "-MF",
        "deps.d",
        "-MT",
        "api.o",
        "-MQ",
        "api.o",
        "-MFdeps2.d",
        "-MTapi",
        "-MQapi",
        "src/api.c",
        "-Wall",
    ]
    assert preprocessing._filter_compile_only_args(args, source, tmp_path) == ["-Wall"]
    assert preprocessing._compile_commands_entry(source, [relative_entry]) == relative_entry
    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing._compile_commands_entry(source, [1])
    _assert_preprocessing_error(exc_info, message="compile_commands entries must be objects")

    original_resolve = Path.resolve

    def fail_resolve(path: Path):
        raise OSError(f"cannot resolve {path}")

    monkeypatch.setattr(Path, "resolve", fail_resolve)
    try:
        assert preprocessing._same_source(source, source)
    finally:
        monkeypatch.setattr(Path, "resolve", original_resolve)


def test_load_compile_commands_uses_explicit_utf8_and_exact_errors(monkeypatch, tmp_path: Path):
    database = tmp_path / "compile_commands.json"
    seen_encodings = []

    def read_empty_database(_path: Path, *, encoding: str):
        seen_encodings.append(encoding)
        return "[]"

    monkeypatch.setattr(Path, "read_text", read_empty_database)
    assert preprocessing._load_compile_commands(database) == []
    assert seen_encodings == ["utf-8"]

    def fail_read(_path: Path, *, encoding: str):
        raise OSError(f"denied with {encoding}")

    monkeypatch.setattr(Path, "read_text", fail_read)
    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing._load_compile_commands(database)
    _assert_preprocessing_error(
        exc_info,
        message=f"cannot read compile commands file {database}: denied with utf-8",
    )

    monkeypatch.setattr(Path, "read_text", lambda _path, *, encoding: "not json")
    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing._load_compile_commands(database)
    _assert_preprocessing_error(
        exc_info,
        message="invalid compile commands JSON: Expecting value: line 1 column 1 (char 0)",
    )

    monkeypatch.setattr(Path, "read_text", lambda _path, *, encoding: "{}")
    with pytest.raises(PreprocessingError) as exc_info:
        preprocessing._load_compile_commands(database)
    _assert_preprocessing_error(exc_info, message="compile_commands.json must contain a list")


@pytest.mark.parametrize(
    "compile_only_args",
    [
        ["-c"],
        ["/c"],
        ["-o", "api.o"],
        ["-oapi.o"],
        ["/Foapi.o"],
        ["-MF", "deps.d"],
        ["-MT", "api.o"],
        ["-MQ", "api.o"],
        ["-MFdeps.d"],
        ["-MTapi.o"],
        ["-MQapi.o"],
    ],
)
def test_compile_only_arg_filter_removes_each_flag_without_skipping_following_args(
    compile_only_args: list[str], tmp_path: Path
):
    source = tmp_path / "api.c"

    assert preprocessing._filter_compile_only_args([*compile_only_args, "-Wall"], source, tmp_path) == ["-Wall"]


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
        command_template="vendor-cc --preprocess {include_dirs} {defines} {undefs} {standard} {compiler_args} {source}",
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
            str(source),
        ],
        adapter="command-template",
        language="c",
        compiler="vendor-cc",
        capabilities={"dependency_output": False, "macro_dump": False, "linemarkers": False},
    )


def test_command_template_tokens_expand_exactly(tmp_path: Path):
    source = tmp_path / "api.h"
    config = PreprocessingConfig(
        mode="compiler",
        compiler="vendor-cc",
        include_dirs=["include"],
        defines=["API=1"],
        undefs=["DEBUG"],
        std="c11",
        compiler_args=["--target=x86_64-linux"],
    )

    assert preprocessing._template_token_value("{source}", source, "c", config) == [str(source)]
    assert preprocessing._template_token_value("{compiler}", source, "c", config) == ["vendor-cc"]
    assert preprocessing._template_token_value("{language}", source, "c", config) == ["c"]
    assert preprocessing._template_token_value("{include_dirs}", source, "c", config) == ["-Iinclude"]
    assert preprocessing._template_token_value("{defines}", source, "c", config) == ["-DAPI=1"]
    assert preprocessing._template_token_value("{undefs}", source, "c", config) == ["-UDEBUG"]
    assert preprocessing._template_token_value("{standard}", source, "c", config) == ["-std=c11"]
    assert preprocessing._template_token_value("{compiler_args}", source, "c", config) == ["--target=x86_64-linux"]
    assert preprocessing._template_token_value("--std={standard}", source, "c", config) == ["--std=c11"]
    assert preprocessing._template_token_value(
        "--meta={source}:{compiler}:{language}:{standard}",
        source,
        "c",
        config,
    ) == [f"--meta={source}:vendor-cc:c:c11"]
    assert preprocessing._template_token_value("{standard}", source, "c", PreprocessingConfig()) == []
    assert preprocessing._template_token_value("{compiler}", source, "c", PreprocessingConfig()) == [""]
    assert preprocessing._template_token_value("{include_dirs}", source, "c", PreprocessingConfig()) == []
    assert preprocessing._template_token_value("{defines}", source, "c", PreprocessingConfig()) == []
    assert preprocessing._template_token_value("{undefs}", source, "c", PreprocessingConfig()) == []
    assert preprocessing._template_token_value("{compiler_args}", source, "c", PreprocessingConfig()) == []
    assert preprocessing._template_token_value(
        "--meta={compiler}:{standard}",
        source,
        "c",
        PreprocessingConfig(),
    ) == ["--meta=:"]
    with pytest.raises(KeyError, match="unknown"):
        preprocessing._template_token_value("{unknown}", source, "c", PreprocessingConfig())


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
