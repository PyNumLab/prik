"""Tests split by stable CLI stage-dispatch ownership."""

from tests.fortran.command_line_interface.pipeline._support import (
    FortranParseError,
    Path,
    PreprocessingDiagnostic,
    PreprocessingError,
    TEST_FILE,
    _install_main_parser,
    _main_args,
    _patch_main_report_payloads,
    fortran_parser_cli,
    json,
    os,
    pytest,
    runpy,
    subprocess,
    sys,
    types,
    x2py_cli,
)


def test_cli_keeps_free_procedure_when_module_has_same_name(tmp_path: Path):
    f90 = tmp_path / "same_name_scopes.f90"
    f90.write_text(
        """
subroutine work(n)
  integer, intent(in) :: n
end subroutine work

module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
end module m
""".strip()
    )

    cmd = [sys.executable, "-m", "x2py", "parse", str(f90)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "  Procedures: 1" in res.stdout
    assert "    - subroutine work(n:integer[0])" in res.stdout
    assert "  Modules: 1" in res.stdout
    assert "      Procedures: 1" in res.stdout


def test_cli_debug_traceback_env_reraises_parse_errors(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "x2py", "parse", str(f90)]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "FORTRAN_PARSER_DEBUG": "1"},
    )

    assert res.returncode == 1
    assert "Traceback" in res.stderr
    assert "note: parser raised at" in res.stderr


def test_cli_no_color_env_disables_default_ansi(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "x2py", "parse", str(f90)]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "NO_COLOR": "1"},
    )

    assert res.returncode == 1
    assert "\033[" not in res.stderr
    assert f"{f90}:" in res.stderr
    assert "error[PARSE_UNSUPPORTED_DECLARATION]:" in res.stderr


def test_fortran_parser_cli_reports_full_source_tree_from_inline_code(tmp_path: Path):
    f90 = tmp_path / "full_tree.f90"
    f90.write_text(
        """
module parent_mod
  integer :: counter
  type :: particle
    integer :: id
    real(8) :: x(3)
  contains
    procedure :: reset
  end type particle
contains
  subroutine reset(self)
    type(particle), intent(inout) :: self
  end subroutine reset
end module parent_mod

submodule (parent_mod) child_mod
contains
  module subroutine child_step(n)
    integer, intent(in) :: n
  end subroutine child_step
end submodule child_mod

program driver
  use parent_mod
  integer :: n
end program driver

block data init_block
  integer :: flag
end block data init_block
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "x2py.parsers.fortran", str(f90)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert f"File: {f90}" in res.stdout
    assert "Modules: 1" in res.stdout
    assert "- module parent_mod (vars=1, uses=0)" in res.stdout
    assert "Derived types: 1" in res.stdout
    assert "- type particle (fields=2, methods=1)" in res.stdout
    assert "Fields: 2" in res.stdout
    assert "- x:real(8)[1]" in res.stdout
    assert "Submodules: 1" in res.stdout
    assert "- submodule child_mod (parent=parent_mod, vars=0, uses=0)" in res.stdout
    assert "Programs: 1" in res.stdout
    assert "- program driver (vars=1, uses=1)" in res.stdout
    assert "Block data: 1" in res.stdout
    assert "- block data init_block (vars=1)" in res.stdout


def test_fortran_parser_cli_semantics_pyi_and_empty_module_report_from_inline_code(tmp_path: Path):
    module_source = tmp_path / "x2py.semantics.f90"
    module_source.write_text(
        """
module solver_mod
contains
  subroutine solve(a, x, b)
    real(8), intent(in) :: a
    real(8), intent(out) :: x
    real(8), intent(in) :: b
  end subroutine solve
end module solver_mod
""",
        encoding="utf-8",
    )
    program_source = tmp_path / "driver.f90"
    program_source.write_text(
        """
program driver
  integer :: n
end program driver
""",
        encoding="utf-8",
    )
    json_out = tmp_path / "x2py.semantics.json"

    semantics_cmd = [
        sys.executable,
        "-m",
        "x2py.parsers.fortran",
        str(module_source),
        "--semantics",
        "--json-out",
        str(json_out),
    ]
    semantics_res = subprocess.run(semantics_cmd, capture_output=True, text=True, check=True)
    payload = json.loads(json_out.read_text(encoding="utf-8"))

    assert "solver_mod" in semantics_res.stdout
    assert str(module_source) in payload
    assert payload[str(module_source)]["semantic_modules"][0]["functions"][0]["name"] == "solve"

    pyi_cmd = [sys.executable, "-m", "x2py.parsers.fortran", str(module_source), "--pyi"]
    pyi_res = subprocess.run(pyi_cmd, capture_output=True, text=True, check=True)
    assert "@native_call([Addr(Arg(0)), Return('x', 0), Addr(Arg(1))])" in pyi_res.stdout
    assert "x: Addr(Float64)" not in pyi_res.stdout
    assert "def solve(" in pyi_res.stdout

    empty_pyi_cmd = [sys.executable, "-m", "x2py.parsers.fortran", str(program_source), "--pyi"]
    empty_pyi_res = subprocess.run(empty_pyi_cmd, capture_output=True, text=True, check=True)
    assert "<no module declarations found>" in empty_pyi_res.stdout


def test_x2py_semantics_marks_explicit_cross_file_derived_type_as_wrapped(tmp_path: Path):
    types_mod = tmp_path / "types_mod.f90"
    physics = tmp_path / "physics.f90"
    types_mod.write_text(
        """
module types_mod
  type :: particle
    real :: mass
  end type particle
end module types_mod
""",
        encoding="utf-8",
    )
    physics.write_text(
        """
module physics
  use types_mod, only: particle
contains
  subroutine move(p)
    type(particle), intent(inout) :: p
  end subroutine move
end module physics
""",
        encoding="utf-8",
    )

    payload = x2py_cli._semantic_report([str(types_mod), str(physics)])
    semantic_type = payload[str(physics)]["semantic_modules"][0]["functions"][0]["arguments"][0]["semantic_type"]

    assert semantic_type["metadata"]["external_type_ref"]["wrapped"] is True
    assert "class particle" not in payload[str(physics)]["pyi"]


def test_x2py_pyi_report_writes_opaque_dependency_stub_for_external_type(tmp_path: Path, monkeypatch):
    physics = tmp_path / "physics.f90"
    physics.write_text(
        """
module physics
  use types_mod, only: particle
contains
  function create_particle() result(p)
    type(particle) :: p
  end function create_particle
end module physics
""",
        encoding="utf-8",
    )

    payload = x2py_cli._semantic_report([str(physics)])

    assert payload[str(physics)]["pyi_dependencies"] == {
        "types_mod": "from x2py.contracts import Opaque\n\nclass particle(Opaque):\n    pass"
    }
    monkeypatch.setattr(sys, "argv", ["x2py", "generate", "--pyi", str(physics), "--out"])
    assert x2py_cli.main() == 0

    package = tmp_path / "physics"
    assert (package / "__init__.pyi").read_text(encoding="utf-8") == "from . import physics\n"
    assert (package / "types_mod.pyi").read_text(
        encoding="utf-8"
    ) == "from x2py.contracts import Opaque\n\nclass particle(Opaque):\n    pass\n"


@pytest.mark.parametrize(
    ("overrides", "expected_stage_calls"),
    [
        ({"parse": True}, [("parse",)]),
        ({"semantics": True}, [("semantic",)]),
        ({"pyi": True}, [("semantic",)]),
    ],
)
def test_x2py_main_preserves_fortran_stage_dispatch_contract(monkeypatch, overrides, expected_stage_calls):
    class StopAfterDispatch(Exception):
        pass

    args = _main_args(**overrides)
    parser = _install_main_parser(monkeypatch, args)
    preprocessing = object()
    parse_payload = {"parse": "payload"}
    semantic_payload = {"semantic": "payload"}
    calls = []

    def resolve_language(paths, language, active_parser):
        calls.append(("resolve", paths, language, active_parser))
        return "fortran"

    def build_preprocessing_config(active_args, active_parser):
        calls.append(("config", active_args, active_parser))
        return preprocessing

    def parse_report(paths, active_preprocessing):
        calls.append(("parse", paths, active_preprocessing))
        return parse_payload

    def semantic_report(paths, active_preprocessing, *, language):
        calls.append(("semantic", paths, active_preprocessing, language))
        return semantic_payload

    def select_main_payload(*_args):
        raise StopAfterDispatch

    monkeypatch.setattr(x2py_cli, "_resolve_language", resolve_language)
    monkeypatch.setattr(x2py_cli, "_build_preprocessing_config", build_preprocessing_config)
    monkeypatch.setattr(x2py_cli, "_parse_report", parse_report)
    monkeypatch.setattr(x2py_cli, "_semantic_report", semantic_report)
    monkeypatch.setattr(x2py_cli, "_select_main_payload", select_main_payload)

    with pytest.raises(StopAfterDispatch):
        x2py_cli.main()

    expected_calls = [
        ("resolve", args.paths, "fortran", parser),
        ("config", args, parser),
    ]
    for (stage_name,) in expected_stage_calls:
        if stage_name == "parse":
            expected_calls.append(("parse", args.paths, preprocessing))
        elif stage_name == "semantic":
            expected_calls.append(("semantic", args.paths, preprocessing, "fortran"))
    assert calls == expected_calls


def test_x2py_main_runs_default_wrapper_build(monkeypatch, tmp_path: Path, capsys):
    source = tmp_path / "fmath.f"
    source.write_text("      real function square(x)\n      real x\n      square = x*x\n      end\n", encoding="utf-8")
    args = _main_args(paths=[str(source)], out_dir=str(tmp_path), json=True)
    _install_main_parser(monkeypatch, args)
    preprocessing = object()
    calls = []
    result = types.SimpleNamespace(
        to_dict=lambda: {
            "source": str(source),
            "module_name": "fmath",
            "shared_library": str(tmp_path / "fmath.so"),
            "generated_sources": [str(tmp_path / "fmath_wrapper.c")],
        }
    )

    monkeypatch.setattr(x2py_cli, "_resolve_language", lambda paths, language, parser: "fortran")
    monkeypatch.setattr(x2py_cli, "_build_preprocessing_config", lambda active_args, parser: preprocessing)
    monkeypatch.setattr(
        x2py_cli,
        "_run_wrap_build_with_diagnostics",
        lambda active_args, active_preprocessing: calls.append((active_args, active_preprocessing)) or result,
    )

    assert x2py_cli.main() == 0

    assert calls == [(args, preprocessing)]
    payload = json.loads(capsys.readouterr().out)
    assert payload["module_name"] == "fmath"


def test_cli_native_libraries_split_grouped_prefixed_names():
    assert x2py_cli._cli_native_libraries(["blas", "-llapack -lscalapack"]) == (
        "blas",
        "-llapack",
        "-lscalapack",
    )


def test_x2py_main_preserves_pathless_preprocessing_diagnostic_contract(monkeypatch, capsys):
    args = _main_args(parse=True)
    _install_main_parser(monkeypatch, args)
    calls = []

    monkeypatch.setattr(x2py_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(x2py_cli, "_build_preprocessing_config", lambda active_args, parser: object())
    monkeypatch.setattr(x2py_cli, "_env_flag", lambda name: calls.append(name) or False)
    monkeypatch.setattr(
        x2py_cli,
        "_parse_report",
        lambda paths, preprocessing: (_ for _ in ()).throw(
            PreprocessingError(
                "compiler failed",
                diagnostics=[PreprocessingDiagnostic(category="PREPROCESSOR_FAILED", message="bad include")],
            )
        ),
    )

    assert x2py_cli.main() == 1
    assert capsys.readouterr().err == "<preprocessor>: error[PREPROCESSOR_FAILED]: bad include\n"
    assert calls == ["X2PY_DEBUG"]


def test_x2py_main_reraises_value_errors_for_debug_environment(monkeypatch):
    args = _main_args(parse=True)
    _install_main_parser(monkeypatch, args)
    calls = []

    monkeypatch.setattr(x2py_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(x2py_cli, "_build_preprocessing_config", lambda active_args, parser: object())
    monkeypatch.setattr(x2py_cli, "_env_flag", lambda name: calls.append(name) or name == "X2PY_DEBUG")
    monkeypatch.setattr(
        x2py_cli,
        "_parse_report",
        lambda paths, preprocessing: (_ for _ in ()).throw(ValueError("invalid generated interface")),
    )

    with pytest.raises(ValueError, match="invalid generated interface"):
        x2py_cli.main()

    assert calls == ["X2PY_DEBUG"]


def test_x2py_main_preserves_explicit_pyi_write_contract(monkeypatch):
    semantic_payload = {
        "first.f90": {"pyi": "def first() -> None: ..."},
        "empty.f90": {},
        "second.f90": {"pyi": "def second() -> None: ..."},
    }
    args = _main_args(pyi=True, out="/tmp/api.pyi")
    _install_main_parser(monkeypatch, args)
    _patch_main_report_payloads(monkeypatch, semantic_payload=semantic_payload)
    writes = []
    dependencies = []

    monkeypatch.setattr(
        Path,
        "write_text",
        lambda path, data, **kwargs: writes.append((path, data, kwargs)) or len(data),
    )
    monkeypatch.setattr(
        x2py_cli,
        "_write_pyi_dependencies",
        lambda payload, **kwargs: dependencies.append((payload, kwargs)),
    )

    assert x2py_cli.main() == 0
    assert writes == [
        (Path("/tmp/api.pyi"), "def first() -> None: ...\n\n\n\ndef second() -> None: ...\n", {"encoding": "utf-8"})
    ]
    assert dependencies == [(semantic_payload, {"output_dir": Path("/tmp")})]


def test_x2py_main_preserves_adjacent_pyi_write_contract(monkeypatch):
    semantic_payload = {
        "/tmp/first.f90": {
            "pyi": "def first() -> None: ...",
            "pyi_modules": {"first_mod": "def first() -> None: ..."},
        },
        "/tmp/empty.f90": {"pyi_modules": {}},
    }
    args = _main_args(pyi=True, out="")
    _install_main_parser(monkeypatch, args)
    _patch_main_report_payloads(monkeypatch, semantic_payload=semantic_payload)
    writes = []
    dependencies = []

    monkeypatch.setattr(
        Path,
        "write_text",
        lambda path, data, **kwargs: writes.append((path, data, kwargs)) or len(data),
    )
    monkeypatch.setattr(
        x2py_cli,
        "_write_pyi_dependencies",
        lambda payload, **kwargs: dependencies.append((payload, kwargs)),
    )

    assert x2py_cli.main() == 0
    assert writes == [
        (Path("/tmp/first_mod.pyi"), "def first() -> None: ...\n", {"encoding": "utf-8"}),
    ]
    assert dependencies == [(semantic_payload, {})]


def test_x2py_and_fortran_module_entrypoints_and_debug_errors(monkeypatch, capsys):
    original_fortran_main = fortran_parser_cli.main
    monkeypatch.setattr(x2py_cli, "main", lambda: 0)
    with pytest.raises(SystemExit) as x2py_exit:
        runpy.run_module("x2py.__main__", run_name="__main__")
    assert x2py_exit.value.code == 0

    monkeypatch.setattr(fortran_parser_cli, "main", lambda: 0)
    with pytest.raises(SystemExit) as fortran_exit:
        runpy.run_module("x2py.parsers.fortran.__main__", run_name="__main__")
    assert fortran_exit.value.code == 0
    monkeypatch.setattr(fortran_parser_cli, "main", original_fortran_main)

    def fail_parse(_paths):
        raise FortranParseError("bad", filename="bad.f90", line_number=1, source_line="bad")

    monkeypatch.setattr(fortran_parser_cli, "_parse_paths", fail_parse)
    monkeypatch.setattr(sys, "argv", ["x2py.parsers.fortran", "bad.f90", "--no-color"])
    assert fortran_parser_cli.main() == 1
    assert "bad.f90:1:1: error[PARSE_ERROR]: bad" in capsys.readouterr().err
    monkeypatch.setenv("FORTRAN_PARSER_DEBUG", "1")
    with pytest.raises(FortranParseError):
        fortran_parser_cli.main()


def test_x2py_main_debug_reraises_preprocessing_errors(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x2py", "parse", str(TEST_FILE)])
    monkeypatch.setenv("X2PY_DEBUG", "1")

    def fail_parse(_paths, _preprocessing):
        raise PreprocessingError("plain failure", category="PREPROCESSOR_FAILED")

    monkeypatch.setattr(x2py_cli, "_parse_report", fail_parse)
    with pytest.raises(PreprocessingError):
        x2py_cli.main()


def test_cli_parse_modern_fixture_prints_derived_block_verbatim():
    fixture = (
        Path(__file__).parents[2] / "source_parsing" / "parsing" / "fixtures" / "general" / "modern_pyi_example.f90"
    )
    cmd = [sys.executable, "-m", "x2py", "parse", str(fixture)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    expected_block = """      Derived types: 3
        - type particle (fields=3, methods=0)
          Fields: 3
            - id:integer[0]
            - mass:real(8)[0]
            - position:real(8)[1]
        - type vector3 (fields=1, methods=0)
          Fields: 1
            - values:real(8)[1]
        - type hidden_state (fields=1, methods=0)
          Fields: 1
            - code:integer[0]
"""
    assert expected_block in res.stdout


def test_fortran_parser_cli_debug_flag_reraises_parse_errors(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "x2py.parsers.fortran", str(f90), "--debug"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 1
    assert "Traceback" in res.stderr
    assert "FortranParseError" in res.stderr


def test_fortran_parser_cli_debug_traceback_env_reraises_parse_errors(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "x2py.parsers.fortran", str(f90)]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "FORTRAN_PARSER_DEBUG": "1"},
    )

    assert res.returncode == 1
    assert "Traceback" in res.stderr
    assert "note: parser raised at" in res.stderr


def test_fortran_parser_main_public_api_modes_from_inline_source(tmp_path: Path, monkeypatch, capsys):
    f90 = tmp_path / "mini.f90"
    f90.write_text(
        """module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
end module m
""",
        encoding="utf-8",
    )
    json_out = tmp_path / "report.json"

    monkeypatch.setattr(sys, "argv", ["x2py.parsers.fortran", str(f90), "--json-out", str(json_out), "--json"])
    assert fortran_parser_cli.main() == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    assert str(f90) in stdout_payload
    assert json_out.exists()

    monkeypatch.setattr(sys, "argv", ["x2py.parsers.fortran", str(f90), "--pyi"])
    assert fortran_parser_cli.main() == 0
    pyi_out = capsys.readouterr().out
    assert "File:" in pyi_out
    assert "def work(" in pyi_out

    monkeypatch.setattr(sys, "argv", ["x2py.parsers.fortran", str(f90)])
    assert fortran_parser_cli.main() == 0
    readable = capsys.readouterr().out
    assert "module m" in readable


def test_x2py_main_public_api_modes_from_inline_source(tmp_path: Path, monkeypatch, capsys):
    f90 = tmp_path / "mini.f90"
    f90.write_text(
        """module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
end module m
""",
        encoding="utf-8",
    )
    json_out = tmp_path / "parse.json"

    monkeypatch.setattr(sys, "argv", ["x2py", "parse", str(f90), "--json", "--out", str(json_out)])
    assert x2py_cli.main() == 0
    assert capsys.readouterr().out == ""
    assert json.loads(json_out.read_text(encoding="utf-8")).get(str(f90)) is not None

    monkeypatch.setattr(sys, "argv", ["x2py", "generate", "--pyi", str(f90)])
    assert x2py_cli.main() == 0
    assert "def work(" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["x2py", "parse", str(f90)])
    assert x2py_cli.main() == 0
    assert "module m" in capsys.readouterr().out


def test_x2py_fortran_source_for_path_raw_uses_utf8_and_internal_recipe():
    class RawPath:
        def read_text(self, *, encoding):
            assert encoding is not None
            assert encoding.lower() == "utf-8"
            return "subroutine raw()\nend subroutine raw\n"

    class RawPreprocessing:
        uses_compiler = False

        def fortran_internal_recipe(self, received):
            assert received is path
            return {"mode": "internal"}

    path = RawPath()

    assert x2py_cli._fortran_source_for_path(path, RawPreprocessing()) == (
        "subroutine raw()\nend subroutine raw\n",
        {"mode": "internal"},
    )


def test_x2py_probe_subcommand_dispatches_one_flag_driven_probe(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        x2py_cli,
        "_probe_output",
        lambda args: calls.append(args) or '{"target": "fortran"}',
    )

    assert (
        x2py_cli.main(
            [
                "probe",
                "--language",
                "fortran",
                "--compiler",
                "gfortran-13",
                "--expr",
                "storage_size(0)",
            ]
        )
        == 0
    )

    assert capsys.readouterr().out == '{"target": "fortran"}\n'
    assert len(calls) == 1
    assert calls[0].language == "fortran"
    assert calls[0].compiler == "gfortran-13"
    assert calls[0].expressions == ["storage_size(0)"]
