"""C parser CLI coverage for the current partial subset."""

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from x2py.parsers.c import CParseError
from x2py.parsers.c import cli as c_parser_cli
from x2py import cli as x2py_cli
from x2py.pipeline.preprocessing import PreprocessingConfig

CONTRACT_IMPORT = "from x2py.contracts import Int32\n\n"


def test_cli_parse_help_shows_explicit_c_language_mode():
    cmd = [sys.executable, "-m", "x2py", "parse", "--help"]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "--language {fortran,c}" in res.stdout
    assert "Input language (default: fortran; use c for C inputs)" in " ".join(res.stdout.split())


def test_cli_c_parse_human_tree_output_for_header(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "parse", str(header), "--language", "c"]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert f"File: {header}" in res.stdout
    assert "Language: c" in res.stdout
    assert "Functions: 1" in res.stdout
    assert "Parser status" not in res.stdout


def test_format_c_report_print_limit_expands_repeated_sections():
    report = {
        "api.h": {
            "language": "c",
            "functions": [{"name": "add"}, {"name": "scale"}],
            "structs": [{"reference": "struct context"}],
            "unions": [],
            "enums": [{"anonymous_id": "enum@api.h:1:1"}],
            "typedefs": [],
            "variables": [],
            "macros": [],
            "includes": [{"path": "api_types.h"}, {}],
            "diagnostics": [
                {
                    "severity": "warning",
                    "code": "C_UNMODELED_COMPILER_EXTENSION",
                    "message": "attribute ignored",
                }
            ],
        }
    }

    output = c_parser_cli.format_c_report(report, print_limit=1)

    assert "  Functions: 2" in output
    assert "    - add" in output
    assert "    - scale" not in output
    assert "    ... 1 more functions" in output
    assert "  Structs: 1" in output
    assert "    - struct context" in output
    assert "  Enums: 1" in output
    assert "    - enum@api.h:1:1" in output
    assert "  Includes: 2" in output
    assert "    - api_types.h" in output
    assert "    ... 1 more includes" in output
    assert "warning: C_UNMODELED_COMPILER_EXTENSION: attribute ignored" in output


def test_cli_c_parse_json_stdout_for_header(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "x2py",
        "parse",
        str(header),
        "--language",
        "c",
        "--json",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(res.stdout)
    file_payload = payload[str(header)]

    assert file_payload["language"] == "c"
    assert "parser_status" not in file_payload
    assert [fn["name"] for fn in file_payload["functions"]] == ["add"]
    assert file_payload["structs"] == []
    assert file_payload["unions"] == []
    assert file_payload["enums"] == []
    assert file_payload["typedefs"] == []
    assert file_payload["variables"] == []
    assert file_payload["macros"] == []
    assert file_payload["includes"] == []
    assert file_payload["diagnostics"] == []


def test_cli_c_parse_preprocesses_macros_by_default(tmp_path: Path):
    header = tmp_path / "api.h"
    types = tmp_path / "api_types.h"
    types.write_text("typedef int api_int;\n", encoding="utf-8")
    header.write_text(
        '#include "api_types.h"\n#define API_DECL(ret) ret\nAPI_DECL(api_int) run(void);\n',
        encoding="utf-8",
    )
    cmd = [sys.executable, "-m", "x2py", "parse", str(header), "--language", "c", "--json"]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(res.stdout)[str(header)]

    assert payload["preprocessing"] == "compiler"
    assert [function["name"] for function in payload["functions"]] == ["run"]


def test_attach_preprocessing_recipe_filters_invalid_and_duplicate_macros():
    empty = c_parser_cli.CFile()
    c_parser_cli.attach_preprocessing_recipe(empty, None)
    assert empty.preprocessing_recipe is None

    parsed = c_parser_cli.CFile(
        macros=[
            c_parser_cli.CMacro(
                name="EXISTING",
                source_location=c_parser_cli.CSourceLocation(filename="api.h", line=2),
            )
        ]
    )
    recipe = {
        "macros": [
            None,
            {"name": ""},
            {"name": "EXISTING", "path": "api.h", "line": 2},
            {"name": "NEW", "value": 123, "function_like": 1, "path": 42, "line": "bad"},
            {"name": "WITH_LOC", "value": "1", "path": "api.h", "line": 4},
        ]
    }

    c_parser_cli.attach_preprocessing_recipe(parsed, recipe)

    assert parsed.preprocessing_recipe == recipe
    assert [macro.name for macro in parsed.macros] == ["EXISTING", "NEW", "WITH_LOC"]
    assert parsed.macros[1].value is None
    assert parsed.macros[1].function_like is True
    assert parsed.macros[1].source_location.filename is None
    assert parsed.macros[2].source_location.line == 4


def test_c_parser_cli_helpers_errors_and_module_entrypoint(monkeypatch, capsys):
    monkeypatch.setenv("C_PARSER_TEST_FLAG", " on ")
    assert c_parser_cli._env_flag("C_PARSER_TEST_FLAG") is True
    monkeypatch.delenv("C_PARSER_TEST_FLAG")
    assert c_parser_cli._env_flag("C_PARSER_TEST_FLAG") is False

    assert c_parser_cli._diagnostic_color_enabled(disabled=True) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert c_parser_cli._diagnostic_color_enabled(disabled=False) is False
    monkeypatch.delenv("NO_COLOR")
    assert c_parser_cli._diagnostic_color_enabled(disabled=False) is True

    def fail_parse(_paths):
        raise CParseError("invalid", filename="bad.h", line_number=1, column=1, source_line="@@@")

    monkeypatch.setattr(c_parser_cli, "parse_c_report", fail_parse)
    assert c_parser_cli.main(["bad.h", "--no-color"]) == 1
    assert "bad.h:1:1: error[CPARSE_ERROR]: invalid" in capsys.readouterr().err

    monkeypatch.setattr(c_parser_cli, "main", lambda _argv=None: 0)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("x2py.parsers.c.__main__", run_name="__main__")
    assert exc_info.value.code == 0


def test_cli_c_parse_json_out_writes_file_and_suppresses_stdout(tmp_path: Path):
    header = tmp_path / "api.h"
    output = tmp_path / "report.json"
    header.write_text("double scale(double x);\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "x2py",
        "parse",
        str(header),
        "--language",
        "c",
        "--json",
        "--out",
        str(output),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert res.stdout == ""
    assert payload[str(header)]["language"] == "c"
    assert "parser_status" not in payload[str(header)]


def test_cli_c_parse_out_without_json_writes_json_and_suppresses_stdout(tmp_path: Path):
    header = tmp_path / "api.h"
    output = tmp_path / "report.json"
    header.write_text("int run(void);\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "x2py",
        "parse",
        str(header),
        "--language",
        "c",
        "--out",
        str(output),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert res.stdout == ""
    assert "parser_status" not in payload[str(header)]


def test_cli_c_semantics_stdout_for_header(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "semantics", str(header), "--language", "c"]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(res.stdout)
    semantic_modules = payload[str(header)]["semantic_modules"]

    assert semantic_modules[0]["name"] == "api"
    assert semantic_modules[0]["functions"][0]["name"] == "add"
    argument_type = semantic_modules[0]["functions"][0]["arguments"][0]["semantic_type"]
    assert argument_type["name"] == "Int"
    assert argument_type["dtype"] == "Int32"
    assert argument_type["metadata"]["c_type_fact_source"] == "compiler_probe"


def test_cli_c_pyi_human_output_for_header(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "generate", "--pyi", str(header), "--language", "c"]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert f"File: {header}" in res.stdout
    assert "def add(" in res.stdout
    assert "a: Int" in res.stdout


def test_cli_c_pyi_out_requires_explicit_language_and_writes_when_selected(tmp_path: Path):
    header = tmp_path / "api.h"
    output = tmp_path / "api.pyi"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")

    omitted = subprocess.run(
        [sys.executable, "-m", "x2py", "generate", "--pyi", str(header), "--out"],
        capture_output=True,
        text=True,
    )
    assert omitted.returncode == 2
    assert "usage:" in omitted.stderr
    assert "requires explicit --language c" in omitted.stderr
    assert not output.exists()

    selected = subprocess.run(
        [sys.executable, "-m", "x2py", "generate", "--pyi", str(header), "--out", "--language", "c"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert selected.stdout == ""
    assert "def add(" in output.read_text(encoding="utf-8")


def test_cli_c_pyi_out_writes_explicit_multi_header_owner_stubs(tmp_path: Path):
    types = tmp_path / "types.h"
    api = tmp_path / "api.h"
    types.write_text("struct state { int id; };\n", encoding="utf-8")
    api.write_text("struct state;\nvoid step(struct state *state);\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            str(types),
            str(api),
            "--language",
            "c",
            "--out",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == ""
    assert "class state(CStruct):" in (tmp_path / "types.pyi").read_text(encoding="utf-8")
    api_stub = (tmp_path / "api.pyi").read_text(encoding="utf-8")
    assert "from types import state" in api_stub
    assert "class state" not in api_stub
    assert "state: state" in api_stub
    assert "Addr(state)" not in api_stub


def test_cli_c_input_rejects_explicit_fortran_frontend(tmp_path: Path):
    header = tmp_path / "api.h"
    output = tmp_path / "api.pyi"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "x2py", "generate", "--pyi", str(header), "--language", "fortran", "--out"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "incompatible with --language fortran" in result.stderr
    assert "pass --language c" in result.stderr
    assert not output.exists()


def test_cli_c_pyi_rejects_invalid_c_syntax(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text(
        "int add(int a, int b);\nvalue_type :: state;\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "x2py", "generate", "--pyi", str(header), "--language", "c"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "CPARSE_INVALID_SYNTAX" in result.stderr
    assert "Invalid C syntax" in result.stderr


def test_cli_c_rejects_fortran_only_parse_flags(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "parse", str(header), "--language", "c", "--show-vars"]

    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode != 0
    assert "show-vars" in res.stderr
    assert "Fortran-only" in res.stderr


def test_cli_c_no_color_and_debug_flags_are_accepted(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "x2py",
        "parse",
        str(header),
        "--language",
        "c",
        "--no-color",
        "--debug",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Parser status" not in res.stdout


def test_cli_c_no_color_and_no_color_env_format_parse_errors_without_ansi(tmp_path: Path):
    source = tmp_path / "old_style.c"
    source.write_text(
        """
int add(a, b)
int a;
int b;
{
    return a + b;
}
""",
        encoding="utf-8",
    )

    base_cmd = [sys.executable, "-m", "x2py", "parse", str(source), "--language", "c"]
    no_color_res = subprocess.run(
        [*base_cmd, "--no-color"],
        capture_output=True,
        text=True,
    )
    env = {**os.environ, "NO_COLOR": "1"}
    env_res = subprocess.run(base_cmd, capture_output=True, text=True, env=env)

    assert no_color_res.returncode == 1
    assert "K&R style function definitions are not supported" in no_color_res.stderr
    assert "\x1b[" not in no_color_res.stderr
    assert env_res.returncode == 1
    assert "K&R style function definitions are not supported" in env_res.stderr
    assert "\x1b[" not in env_res.stderr


def test_cli_c_invalid_primitive_specifier_sequence_is_fatal(tmp_path: Path):
    header = tmp_path / "invalid_specifiers.h"
    header.write_text("unsigned float value;\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "parse", str(header), "--language", "c", "--no-color"]

    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 1
    assert "error[CPARSE_INVALID_SPECIFIER_SEQUENCE]: Invalid type specifier sequence 'unsigned float'." in res.stderr
    assert "\x1b[" not in res.stderr


def test_cli_c_debug_reraises_parse_errors(tmp_path: Path):
    header = tmp_path / "invalid_specifiers.h"
    header.write_text("unsigned float value;\n", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "x2py",
        "parse",
        str(header),
        "--language",
        "c",
        "--debug",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 1
    assert "Traceback" in res.stderr
    assert "CParseError" in res.stderr


def test_cli_c_debug_env_reraises_parse_errors(tmp_path: Path):
    header = tmp_path / "invalid_specifiers.h"
    header.write_text("unsigned float value;\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "x2py", "parse", str(header), "--language", "c"]

    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "C_PARSER_DEBUG": "1"},
    )

    assert res.returncode == 1
    assert "Traceback" in res.stderr
    assert "CParseError" in res.stderr


def test_cli_without_language_keeps_fortran_default_behavior():
    fixture = Path(__file__).resolve().parents[2] / "data" / "fortran" / "general" / "basic_subroutine.f90"
    cmd = [sys.executable, "-m", "x2py", "parse", str(fixture)]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "subroutine add1" in res.stdout
    assert "Language: c" not in res.stdout


def test_c_parser_cli_module_handles_directory_loader_and_output_modes(tmp_path: Path, capsys):
    header = tmp_path / "api.h"
    output = tmp_path / "c-report.json"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    assert c_parser_cli.expand_c_paths([str(tmp_path), str(header)]) == [header]
    loaded = c_parser_cli.parse_c_report(
        [str(header)],
        source_loader=lambda _path: ("int generated(void);\n", {"mode": "test"}),
    )
    assert loaded[str(header)]["functions"][0]["name"] == "generated"
    assert loaded[str(header)]["preprocessing_recipe"] == {"mode": "test"}

    assert c_parser_cli.main([str(header)]) == 0
    assert "Functions: 1" in capsys.readouterr().out

    assert c_parser_cli.main([str(header), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[str(header)]["functions"][0]["name"] == "add"

    assert c_parser_cli.main([str(header), "--out", str(output)]) == 0
    assert capsys.readouterr().out == ""
    assert "parser_status" not in json.loads(output.read_text(encoding="utf-8"))[str(header)]


def test_c_parser_module_entrypoint_and_exports(tmp_path: Path):
    import x2py.parsers.c.__main__ as c_module_entrypoint
    from x2py.parsers.c.parser import parse_c_project

    header = tmp_path / "api.h"
    header.write_text("int run(void);\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "x2py.parsers.c", str(header), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert json.loads(result.stdout)[str(header)]["functions"][0]["name"] == "run"
    assert c_module_entrypoint.main is c_parser_cli.main
    assert parse_c_project({"api.h": "int run(void);\n"}).functions["run"].name == "run"


def test_c_parser_module_formats_parse_errors_without_traceback(tmp_path: Path):
    header = tmp_path / "invalid.h"
    header.write_text("@@@;\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "x2py.parsers.c", str(header), "--no-color"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "error[CPARSE_INVALID_SYNTAX]" in result.stderr
    assert "Traceback" not in result.stderr


def test_c_parser_module_debug_reraises_parse_errors(tmp_path: Path):
    header = tmp_path / "invalid.h"
    header.write_text("@@@;\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "x2py.parsers.c", str(header), "--debug"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Traceback" in result.stderr
    assert "CParseError" in result.stderr


def test_x2py_c_compiler_source_loader_drives_semantics_and_pyi(tmp_path: Path, monkeypatch):
    header = tmp_path / "api.h"
    header.write_text("API(int) add(int a, int b);\n", encoding="utf-8")
    calls: list[Path] = []

    def preprocess(path, *, language, config):
        calls.append(path)
        assert language == "c"
        assert config.compiler == "cc"
        return (
            "int add(int a, int b);\n",
            SimpleNamespace(to_dict=lambda: {"mode": "compiler", "compiler": config.compiler}),
        )

    monkeypatch.setattr(x2py_cli, "run_compiler_preprocessor_with_recipe", preprocess)
    config = PreprocessingConfig(mode="compiler", compiler="cc")

    semantics = x2py_cli._semantic_report([str(header)], config, language="c")
    assert semantics[str(header)]["semantic_modules"][0]["functions"][0]["name"] == "add"
    assert calls == [header]


def test_cli_c_default_build_rejects_the_unsupported_build_language(tmp_path: Path):
    header = tmp_path / "api.h"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")

    no_stage = subprocess.run(
        [sys.executable, "-m", "x2py", str(header), "--language", "c"],
        capture_output=True,
        text=True,
    )
    assert no_stage.returncode == 2
    assert "argument --language: invalid choice: 'c'" in no_stage.stderr
    assert "choose from" in no_stage.stderr
    assert "fortran" in no_stage.stderr
