"""C input-language stage dispatch: parse-error presentation and the C parser module launcher."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

import prik.cli as prik_cli
from prik.parsers.c import CParseError
from prik.parsers.c import cli as c_parser_cli

INVALID_SPECIFIERS = "unsigned float value;\n"
KNR_DEFINITION = "int add(a, b)\nint a;\nint b;\n{\n    return a + b;\n}\n"
FOREIGN_SYNTAX = "int add(int a, int b);\nvalue_type :: state;\n"


@pytest.mark.parametrize(
    ("entrypoint", "argv", "source", "environment", "concise"),
    [
        pytest.param(
            "prik",
            ["parse", "bad.h", "--language", "c"],
            INVALID_SPECIFIERS,
            {},
            ("\033[", "CPARSE_INVALID_SPECIFIER_SEQUENCE"),
            id="prik-colored-by-default",
        ),
        pytest.param(
            "prik",
            ["parse", "bad.h", "--language", "c", "--no-color"],
            INVALID_SPECIFIERS,
            {},
            ("error[CPARSE_INVALID_SPECIFIER_SEQUENCE]: Invalid type specifier sequence 'unsigned float'.",),
            id="prik-no-color-flag",
        ),
        pytest.param(
            "prik",
            ["parse", "bad.h", "--language", "c"],
            KNR_DEFINITION,
            {"NO_COLOR": "1"},
            ("K&R style function definitions are not supported",),
            id="prik-no-color-environment",
        ),
        pytest.param(
            "prik",
            ["generate", "--pyi", "bad.h", "--language", "c", "--no-color"],
            FOREIGN_SYNTAX,
            {},
            ("error[CPARSE_INVALID_SYNTAX]", "Invalid C syntax"),
            id="prik-generate-pyi-invalid-syntax",
        ),
        pytest.param(
            "prik", ["parse", "bad.h", "--language", "c", "--debug"], INVALID_SPECIFIERS, {}, None, id="prik-debug-flag"
        ),
        pytest.param(
            "prik",
            ["parse", "bad.h", "--language", "c"],
            INVALID_SPECIFIERS,
            {"C_PARSER_DEBUG": "1"},
            None,
            id="prik-debug-environment",
        ),
        pytest.param(
            "parser-module",
            ["bad.h", "--no-color"],
            "@@@;\n",
            {},
            ("bad.h:1:1: error[CPARSE_INVALID_SYNTAX]",),
            id="parser-module-concise",
        ),
        pytest.param("parser-module", ["bad.h", "--debug"], "@@@;\n", {}, None, id="parser-module-debug-flag"),
    ],
)
def test_c_parse_errors_are_concise_unless_debugging(
    tmp_path: Path, monkeypatch, capsys, entrypoint, argv, source, environment, concise
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad.h").write_text(source, encoding="utf-8")
    for name in ("NO_COLOR", "C_PARSER_DEBUG", "PRIK_DEBUG"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    main = prik_cli.main if entrypoint == "prik" else c_parser_cli.main

    if concise is None:
        with pytest.raises(CParseError):
            main(argv)
        return

    assert main(argv) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert [fragment for fragment in concise if fragment not in captured.err] == []
    assert ("\033[" in captured.err) is ("NO_COLOR" not in environment and "--no-color" not in argv)


def test_c_parser_module_launcher_reports_every_mode(tmp_path: Path, capsys):
    """``python -m prik.parsers.c`` prints the parse report, JSON, or a JSON file for C inputs only."""
    header = tmp_path / "api.h"
    output = tmp_path / "c-report.json"
    header.write_text("int add(int a, int b);\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    launched = subprocess.run(
        [sys.executable, "-m", "prik.parsers.c", str(header), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(launched.stdout)[str(header)]["functions"][0]["name"] == "add"

    # A directory expands to its C inputs; other files in it are ignored.
    assert c_parser_cli.main([str(tmp_path)]) == 0
    report = capsys.readouterr().out
    assert f"File: {header}" in report
    assert "Functions: 1" in report
    assert "ignored.txt" not in report

    assert c_parser_cli.main([str(header), "--out", str(output)]) == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output.read_text(encoding="utf-8"))[str(header)]["language"] == "c"
