"""C input-language CLI report and contract outputs, through real command lines."""

import json
from pathlib import Path

import pytest

import prik.cli as prik_cli
from prik.parsers.c import cli as c_parser_cli


@pytest.fixture
def c_headers(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "api.h").write_text("int add(int a, int b);\n", encoding="utf-8")
    (tmp_path / "many.h").write_text("int first(void);\nint second(void);\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("argv", "destination", "is_json", "fragments"),
    [
        pytest.param(
            ["parse", "api.h", "--language", "c"],
            None,
            False,
            ("File: api.h", "Language: c", "Functions: 1"),
            id="parse-text-stdout",
        ),
        pytest.param(
            ["parse", "many.h", "--language", "c", "--print-limit", "1"],
            None,
            False,
            ("Functions: 2", "    - first", "    ... 1 more functions"),
            id="parse-text-print-limit",
        ),
        pytest.param(
            ["parse", "api.h", "--language", "c", "--json"],
            None,
            True,
            ('"language": "c"', '"name": "add"', '"diagnostics": []'),
            id="parse-json-stdout",
        ),
        pytest.param(
            ["parse", "api.h", "--language", "c", "--json", "--out", "report.json"],
            "report.json",
            True,
            ('"language": "c"', '"name": "add"'),
            id="parse-json-file",
        ),
        pytest.param(
            ["semantics", "api.h", "--language", "c"],
            None,
            False,
            ("File: api.h", "- add(a: Int32 in, b: Int32 in) -> Int32"),
            id="semantics-text-stdout",
        ),
        pytest.param(
            ["semantics", "api.h", "--language", "c", "--json"],
            None,
            True,
            ('"name": "api"', '"dtype": "Int32"', '"c_type_fact_source": "compiler_probe"'),
            id="semantics-json-stdout",
        ),
        pytest.param(
            ["generate", "--pyi", "api.h", "--language", "c"],
            None,
            False,
            ("File: api.h", "def add(", "a: Int"),
            id="generate-pyi-stdout",
        ),
        pytest.param(
            ["generate", "--pyi", "api.h", "--language", "c", "--out"],
            "api.pyi",
            False,
            ("def add(",),
            id="generate-pyi-adjacent",
        ),
    ],
)
def test_c_report_format_and_destination_are_chosen_independently(
    c_headers: Path, capsys, argv, destination, is_json, fragments
):
    assert prik_cli.main(argv) == 0
    out = capsys.readouterr().out

    if destination is None:
        text = out
    else:
        assert out == ""
        text = (c_headers / destination).read_text(encoding="utf-8")
    if is_json:
        json.loads(text)
    assert [fragment for fragment in fragments if fragment not in text] == []


def test_c_parse_preprocesses_with_the_default_c_compiler(tmp_path: Path, monkeypatch, capsys):
    """Without preprocessing options a C parse runs ``cc -E`` and records that recipe."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "api_types.h").write_text("typedef int api_int;\n", encoding="utf-8")
    (tmp_path / "api.h").write_text(
        '#include "api_types.h"\n#define API_DECL(ret) ret\nAPI_DECL(api_int) run(void);\n',
        encoding="utf-8",
    )

    assert prik_cli.main(["parse", "api.h", "--language", "c", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)["api.h"]

    assert payload["preprocessing"] == "compiler"
    assert payload["preprocessing_recipe"]["compiler"] == "cc"
    assert [function["name"] for function in payload["functions"]] == ["run"]


def test_c_generate_pyi_writes_one_contract_per_header_and_imports_shared_types(tmp_path: Path, capsys):
    types = tmp_path / "types.h"
    api = tmp_path / "api.h"
    types.write_text("struct state { int id; };\n", encoding="utf-8")
    api.write_text("struct state;\nvoid step(struct state *state);\n", encoding="utf-8")

    assert prik_cli.main(["generate", "--pyi", str(types), str(api), "--language", "c", "--out"]) == 0

    assert capsys.readouterr().out == ""
    assert "class state(CStruct):" in (tmp_path / "types.pyi").read_text(encoding="utf-8")
    api_stub = (tmp_path / "api.pyi").read_text(encoding="utf-8")
    assert "from .types import state" in api_stub
    assert "class state" not in api_stub
    assert "state: state" in api_stub
    assert "Addr(state)" not in api_stub


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
