"""CLI stage dispatch: report launchers, error presentation, probes, and path commands."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from prik.cmake import cmake_module_dir
from prik.parsers.fortran import FortranParseError
from prik.preprocessing import read_fortran_source
import prik.cli as prik_cli
from prik.parsers.fortran import cli as fortran_parser_cli
from prik.preprocessing import (
    PreprocessingConfig,
    PreprocessingDiagnostic,
    PreprocessingError,
)

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SOLVER_SOURCE = """module solver_mod
contains
  subroutine solve(a, x, b)
    real(8), intent(in) :: a
    real(8), intent(out) :: x
    real(8), intent(in) :: b
  end subroutine solve
end module solver_mod
"""

BAD_SOURCE = """subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""


def _parser_module_main(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["prik.parsers.fortran", *argv])
    return fortran_parser_cli.main()


def test_fortran_parser_module_launcher_reports_every_mode(tmp_path: Path, monkeypatch, capsys):
    """``python -m prik.parsers.fortran`` prints the parse report and each explicit inspection mode."""
    full_tree = NATIVE_FIXTURES / "fortran_parser_cli_full_source_tree.f90"
    launched = subprocess.run(
        [sys.executable, "-m", "prik.parsers.fortran", str(full_tree)],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in (
        f"File: {full_tree}",
        "- module parent_mod (vars=1, uses=0)",
        "- type particle (fields=2, methods=1)",
        "- x:real(8)[1]",
        "- submodule child_mod (parent=parent_mod, vars=0, uses=0)",
        "- program driver (vars=1, uses=1)",
        "- block data init_block (vars=1)",
    ):
        assert line in launched.stdout

    solver = tmp_path / "solver.f90"
    solver.write_text(SOLVER_SOURCE, encoding="utf-8")
    driver = tmp_path / "driver.f90"
    driver.write_text("program driver\n  integer :: n\nend program driver\n", encoding="utf-8")

    parse_json = tmp_path / "parse.json"
    assert _parser_module_main(monkeypatch, str(solver), "--json", "--json-out", str(parse_json)) == 0
    assert str(solver) in json.loads(capsys.readouterr().out)
    assert str(solver) in json.loads(parse_json.read_text(encoding="utf-8"))

    semantics_json = tmp_path / "semantics.json"
    assert _parser_module_main(monkeypatch, str(solver), "--semantics", "--json-out", str(semantics_json)) == 0
    assert "solver_mod" in capsys.readouterr().out
    payload = json.loads(semantics_json.read_text(encoding="utf-8"))
    assert payload[str(solver)]["semantic_modules"][0]["functions"][0]["name"] == "solve"

    assert _parser_module_main(monkeypatch, str(solver), "--pyi") == 0
    contract = capsys.readouterr().out
    assert "@native_call([Addr(Arg(0)), Return('x', 0), Addr(Arg(1))])" in contract
    assert "def solve(" in contract
    assert "x: Addr(Float64)" not in contract

    assert _parser_module_main(monkeypatch, str(driver), "--pyi") == 0
    assert "<no module declarations found>" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("entrypoint", "options", "environment", "concise"),
    [
        pytest.param("prik", [], {}, ("\033[", "error"), id="prik-colored-by-default"),
        pytest.param(
            "prik",
            [],
            {"NO_COLOR": "1"},
            ("bad.f90:", "error[PARSE_UNSUPPORTED_DECLARATION]:"),
            id="prik-no-color-environment",
        ),
        pytest.param("prik", [], {"FORTRAN_PARSER_DEBUG": "1"}, None, id="prik-debug-environment"),
        pytest.param(
            "parser-module",
            ["--no-color"],
            {},
            ("bad.f90:2:1: error[PARSE_UNSUPPORTED_DECLARATION]:", "Unknown or unsupported datatype"),
            id="parser-module-concise",
        ),
        pytest.param("parser-module", ["--debug"], {}, None, id="parser-module-debug-flag"),
        pytest.param("parser-module", [], {"FORTRAN_PARSER_DEBUG": "1"}, None, id="parser-module-debug-environment"),
    ],
)
def test_parse_errors_are_concise_unless_debugging(
    tmp_path: Path, monkeypatch, capsys, entrypoint, options, environment, concise
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad.f90").write_text(BAD_SOURCE, encoding="utf-8")
    for name in ("NO_COLOR", "FORTRAN_PARSER_DEBUG", "PRIK_DEBUG"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    def run() -> int:
        if entrypoint == "prik":
            return prik_cli.main(["parse", "bad.f90", *options])
        return _parser_module_main(monkeypatch, "bad.f90", *options)

    if concise is None:
        with pytest.raises(FortranParseError) as raised:
            run()
        if "FORTRAN_PARSER_DEBUG" in environment:
            assert "note: parser raised at" in str(raised.value)
        return

    assert run() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert [fragment for fragment in concise if fragment not in captured.err] == []
    assert ("\033[" in captured.err) is ("NO_COLOR" not in environment and "--no-color" not in options)


def _located_preprocessing_error():
    return PreprocessingError(
        "compiler failed",
        category="PREPROCESSOR_FAILED",
        diagnostics=[
            PreprocessingDiagnostic(category="PREPROCESSOR_FAILED", message="bad include", path="source.F90", line=9)
        ],
    )


def _pathless_preprocessing_error():
    return PreprocessingError(
        "compiler failed",
        diagnostics=[PreprocessingDiagnostic(category="PREPROCESSOR_FAILED", message="bad include")],
    )


def _plain_preprocessing_error():
    return PreprocessingError("plain failure", category="PREPROCESSOR_FAILED")


def _value_error():
    return ValueError("invalid generated interface")


@pytest.mark.parametrize(
    ("error", "options", "environment", "stderr"),
    [
        pytest.param(
            _located_preprocessing_error,
            [],
            {},
            "source.F90:9: error[PREPROCESSOR_FAILED]: bad include\n",
            id="located-preprocessing-diagnostic",
        ),
        pytest.param(
            _pathless_preprocessing_error,
            [],
            {},
            "<preprocessor>: error[PREPROCESSOR_FAILED]: bad include\n",
            id="pathless-preprocessing-diagnostic",
        ),
        pytest.param(
            _plain_preprocessing_error,
            [],
            {},
            "prik: error[PREPROCESSOR_FAILED]: plain failure\n",
            id="preprocessing-error-without-diagnostics",
        ),
        pytest.param(_value_error, [], {}, "prik: error: invalid generated interface\n", id="value-error"),
        pytest.param(_plain_preprocessing_error, [], {"PRIK_DEBUG": "1"}, None, id="preprocessing-debug-environment"),
        pytest.param(_value_error, ["--debug"], {}, None, id="value-error-debug-flag"),
        pytest.param(_value_error, [], {"PRIK_DEBUG": "1"}, None, id="value-error-debug-environment"),
    ],
)
def test_stage_errors_are_reported_concisely_unless_debugging(
    tmp_path: Path, monkeypatch, capsys, error, options, environment, stderr
):
    source = tmp_path / "input.f90"
    source.write_text("module input\nend module input\n", encoding="utf-8")
    monkeypatch.delenv("PRIK_DEBUG", raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    raised = error()

    def fail(_paths, _preprocessing):
        raise raised

    monkeypatch.setattr(prik_cli, "_parse_report", fail)

    if stderr is None:
        with pytest.raises(type(raised)):
            prik_cli.main(["parse", str(source), *options])
        return

    assert prik_cli.main(["parse", str(source), *options]) == 1
    assert capsys.readouterr().err == stderr


MEASURED_MAPPING = {"report": "type_mapping", "target_profile": "t", "types": []}


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        pytest.param(
            ["--language", "c", "--compiler", "cc", "--json"],
            json.dumps({**MEASURED_MAPPING, "language": "c"}, indent=2),
            id="c-mapping-json",
        ),
        pytest.param(
            ["--language", "fortran", "--compiler", "gfortran", "--json"],
            json.dumps({**MEASURED_MAPPING, "language": "fortran"}, indent=2),
            id="fortran-mapping-json",
        ),
        pytest.param(["--language", "fortran", "--compiler", "gfortran"], "MD:fortran", id="mapping-markdown"),
        pytest.param(
            ["--language", "fortran", "--compiler", "gfortran-13", "--expr", "storage_size(0)"],
            "EXPR:gfortran-13:storage_size(0)",
            id="expressions-markdown",
        ),
    ],
)
def test_probe_selects_its_report_by_expressions_and_its_rendering_by_json(monkeypatch, capsys, argv, expected):
    """--expr selects the measured report; --json only selects how it is rendered."""
    monkeypatch.setattr(prik_cli, "c_type_mapping_report", lambda **options: {**MEASURED_MAPPING, "language": "c"})
    monkeypatch.setattr(
        prik_cli, "fortran_type_mapping_report", lambda **options: {**MEASURED_MAPPING, "language": "fortran"}
    )
    monkeypatch.setattr(prik_cli, "type_mapping_markdown", lambda report: f"MD:{report['language']}")
    monkeypatch.setattr(
        prik_cli,
        "probe_fortran_type_expressions_cached",
        lambda config, expressions, **options: (config.compiler, expressions),
    )
    monkeypatch.setattr(prik_cli, "expression_probe_markdown", lambda report: f"EXPR:{report[0]}:{','.join(report[1])}")

    assert prik_cli.main(["probe", *argv]) == 0
    assert capsys.readouterr().out == expected + "\n"


def test_path_commands_report_the_packaged_cmake_module(monkeypatch, capsys):
    """``cmake-dir``, ``install-dir``, and ``doctor cmake`` print the facts a CMake build would use."""
    assert prik_cli.main(["cmake-dir"]) == 0
    module_dir = Path(capsys.readouterr().out.strip())
    assert module_dir == cmake_module_dir()
    assert (module_dir / "UsePRIK.cmake").is_file()
    assert (module_dir / "PRIKConfig.cmake").is_file()

    try:
        code = prik_cli.main(["install-dir"])
    except SystemExit as exc:
        code = exc.code
    printed = capsys.readouterr()
    if code == 0:
        assert (Path(printed.out.strip()) / "share" / "prik").is_dir()
    else:
        assert "prik" in printed.err.lower()
        assert not printed.out.strip()

    assert prik_cli.main(["doctor", "cmake"]) == 0
    report = dict(line.split(": ", 1) for line in capsys.readouterr().out.splitlines())
    assert report["cmake-dir"] == str(cmake_module_dir())
    assert report["imported package"] == str(cmake_module_dir().parent)
    assert report["python executable"] == sys.executable
    for label in ("prik version", "distribution metadata", "install-dir", "conflicts"):
        assert report[label]
    for group in ("cmake.root", "cmake.module"):
        assert report[f"entry point {group}"]


def test_parse_reports_resolve_kinds_one_input_file_declares_for_another(tmp_path: Path):
    """Both parse commands assemble their inputs as a build does, so a kind from another file resolves."""
    kinds = tmp_path / "kinds.f90"
    kinds.write_text("module kinds\n  integer, parameter :: wp = 8\nend module kinds\n", encoding="utf-8")
    user = tmp_path / "user.f90"
    user.write_text(
        "module user\n  use kinds, only: wp\ncontains\n  subroutine run(x)\n    real(wp) :: x\n"
        "  end subroutine run\nend module user\n",
        encoding="utf-8",
    )

    for report in (
        prik_cli._parse_report([str(kinds), str(user)]),
        fortran_parser_cli._parse_paths([str(kinds), str(user)]),
    ):
        procedure = report[str(user)]["modules"][0]["procedures"][0]
        assert procedure["arguments"][0]["kind"] == "8"


def test_a_fortran_source_read_as_written_carries_its_internal_recipe(tmp_path: Path):
    """Without compiler preprocessing the text is read as UTF-8 and the macros are recorded."""
    path = tmp_path / "raw.f90"
    path.write_text("subroutine raw()\n  ! é\nend subroutine raw\n", encoding="utf-8")

    text = read_fortran_source(path, PreprocessingConfig(defines=["FLAG=1"]))

    assert text.source == path.read_text(encoding="utf-8")
    assert text.recipe is not None and text.recipe["mode"] == "internal"
    assert text.included_files == ()
