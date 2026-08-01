"""Tests split by stable CLI output-contract ownership."""

from tests.fortran.command_line_interface.pipeline._support import (
    Path,
    PreprocessingConfig,
    PreprocessingDiagnostic,
    PreprocessingError,
    TEST_FILE,
    _MainParserError,
    _install_main_parser,
    _main_args,
    _patch_main_report_payloads,
    builtins,
    dataclass,
    fortran_parser_cli,
    json,
    os,
    pytest,
    subprocess,
    sys,
    types,
    prik_cli,
)


def test_cli_readable_output():
    cmd = [sys.executable, "-m", "prik", "parse", str(TEST_FILE)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert f"File: {TEST_FILE}" in res.stdout
    assert "subroutine add1" in res.stdout
    assert "Variables:" not in res.stdout
    assert "Derived types: 0" not in res.stdout
    print(res.stdout)
    assert "Wrappable:" not in res.stdout


def test_cli_parse_show_vars_prints_scope_variables(tmp_path: Path):
    f90 = tmp_path / "module_vars.f90"
    f90.write_text(
        """
module module_vars
  integer :: n
  real(kind=8), dimension(3) :: x
contains
  subroutine work()
  end subroutine work
end module module_vars
""".strip(),
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "parse", str(f90), "--show-vars"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "    - module module_vars (vars=2, uses=0)" in res.stdout
    assert "      Variables: 2" in res.stdout
    assert "        - n:integer[0]" in res.stdout
    assert "        - x:real(8)[1]" in res.stdout


def test_cli_parse_print_limit_limits_scope_variables_when_shown(tmp_path: Path):
    f90 = tmp_path / "module_vars.f90"
    f90.write_text(
        """
module module_vars
  integer :: n
  real(kind=8), dimension(3) :: x
contains
  subroutine work()
  end subroutine work
end module module_vars
""".strip(),
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "parse", str(f90), "--show-vars", "--print-limit", "1"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "      Variables: 2" in res.stdout
    assert "        - n:integer[0]" in res.stdout
    assert "        - x:real(8)[1]" not in res.stdout
    assert "        ... 1 more variables" in res.stdout


def test_cli_parse_print_limit_limits_procedures(tmp_path: Path):
    f90 = tmp_path / "many_procs.f90"
    f90.write_text(
        """
module many_procs
contains
  subroutine first()
  end subroutine first

  subroutine second()
  end subroutine second
end module many_procs
""".strip(),
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "parse", str(f90), "--print-limit", "1"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "      Procedures: 2" in res.stdout
    assert "        - subroutine first()" in res.stdout
    assert "        - subroutine second()" not in res.stdout
    assert "        ... 1 more procedures" in res.stdout
    assert "Variables:" not in res.stdout


def test_cli_json_out(tmp_path: Path):
    out = tmp_path / "report.json"
    cmd = [
        sys.executable,
        "-m",
        "prik",
        "parse",
        str(TEST_FILE),
        "--json",
        "--out",
        str(out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert res.stdout == ""
    assert out.exists()
    file_payload = json.loads(out.read_text())
    assert str(TEST_FILE) in file_payload


def test_cli_out_without_filename_uses_source_basename_json(tmp_path: Path):
    f90 = tmp_path / "mini.f90"
    f90.write_text("subroutine work(n)\n  integer, intent(in) :: n\nend subroutine work\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "prik", "parse", str(f90), "--out"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert res.stdout == ""
    out = tmp_path / "mini.json"
    assert out.exists()
    file_payload = json.loads(out.read_text())
    assert str(f90) in file_payload


def test_cli_json_output_without_out():
    cmd = [sys.executable, "-m", "prik", "parse", str(TEST_FILE), "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(res.stdout)
    assert str(TEST_FILE) in payload


def test_cli_pyi_output_without_out():
    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(TEST_FILE)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert f"File: {TEST_FILE}" in res.stdout
    assert "def add1(" in res.stdout


def test_cli_formats_parse_error_with_ansi_by_default(tmp_path: Path):
    f90 = tmp_path / "bad.f90"
    f90.write_text(
        """subroutine bad(x)
  weirdtype :: x
end subroutine bad
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "parse", str(f90)]
    env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)

    assert res.returncode == 1
    assert "\033[" in res.stderr
    assert "error" in res.stderr


def test_cli_semantics_out_writes_json_without_stdout(tmp_path: Path):
    out = tmp_path / "prik.semantics.json"
    cmd = [sys.executable, "-m", "prik", "semantics", str(TEST_FILE), "--out", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert res.stdout == ""
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert str(TEST_FILE) in payload
    assert "semantic_modules" in payload[str(TEST_FILE)]


def test_cli_semantics_without_json_output():
    cmd = [sys.executable, "-m", "prik", "semantics", str(TEST_FILE)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(res.stdout)
    assert str(TEST_FILE) in payload
    assert "semantic_modules" in payload[str(TEST_FILE)]


def test_cli_pyi_output():
    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(TEST_FILE)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert f"File: {TEST_FILE}" in res.stdout
    assert "def add1(" in res.stdout


def test_cli_pyi_out_writes_adjacent_contract_package(tmp_path: Path):
    f90 = tmp_path / "mini.f90"
    f90.write_text(
        """module m
contains
  subroutine add1(x)
    integer, intent(inout) :: x
    x = x + 1
  end subroutine add1
end module m
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(f90), "--out"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert res.stdout == ""
    package = tmp_path / "mini"
    assert (package / "mini.pyi").read_text(encoding="utf-8") == "from . import m\n"
    assert "def add1" in (package / "m.pyi").read_text(encoding="utf-8")


def test_cli_pyi_out_writes_modules_inside_source_contract_package(tmp_path: Path):
    source = tmp_path / "combined.f90"
    source.write_text(
        """module first_mod
contains
  subroutine first()
  end subroutine first
end module first_mod

module second_mod
contains
  subroutine second()
  end subroutine second
end module second_mod
""",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(source), "--out"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert result.stdout == ""
    package = tmp_path / "combined"
    assert (package / "combined.pyi").read_text(encoding="utf-8") == (
        "from . import first_mod\nfrom . import second_mod\n"
    )
    assert "def first(" in (package / "first_mod.pyi").read_text(encoding="utf-8")
    assert "def second(" in (package / "second_mod.pyi").read_text(encoding="utf-8")


def test_cli_pyi_out_uses_explicit_contract_package_from_inline_code(tmp_path: Path):
    f90 = tmp_path / "explicit.f90"
    f90.write_text(
        """module explicit_mod
contains
  subroutine set_value(x)
    real(8), intent(out) :: x
  end subroutine set_value
end module explicit_mod
""",
        encoding="utf-8",
    )
    out = tmp_path / "contracts"

    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(f90), "--out", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert res.stdout == ""
    text = (out / "__init__.pyi").read_text(encoding="utf-8")
    assert text == "from . import explicit_mod\n"
    leaf_text = (out / "explicit_mod.pyi").read_text(encoding="utf-8")
    assert "@native_call([Return('x', 0)])" in leaf_text
    assert "def set_value(" in leaf_text
    assert "-> Float64: ..." in leaf_text


def test_cli_pyi_out_directory_resolves_renamed_project_kind(tmp_path: Path):
    (tmp_path / "precision.f90").write_text(
        """module precision_mod
  integer, parameter :: word = 4
  integer, parameter :: wp = word * 2
end module precision_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "solver.f90").write_text(
        """subroutine consume(x)
  use precision_mod, only: local_wp => wp
  real(kind=local_wp), intent(inout) :: x(*)
end subroutine consume
""",
        encoding="utf-8",
    )
    out = tmp_path / "contracts"

    cmd = [
        sys.executable,
        "-m",
        "prik",
        "generate",
        "--pyi",
        str(tmp_path),
        "--language",
        "fortran",
        "--out",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert result.stdout == ""
    text = (out / "__init__.pyi").read_text(encoding="utf-8")
    assert "def consume(" in text
    assert "x: Float64[Flat]" in text
    assert "local_wp" not in text


def test_prik_write_pyi_dependencies_handles_nested_modules_and_empty_payloads(tmp_path: Path):
    output_dir = tmp_path / "out"
    text = "class Shared:\n    pass"

    prik_cli._write_pyi_dependencies(
        {
            str(tmp_path / "nodeps.f90"): {},
            str(tmp_path / "first.f90"): {"pyi_dependencies": {"pkg.sub.shared": text}},
            str(tmp_path / "second.f90"): {"pyi_dependencies": {"pkg.sub.shared": text}},
        },
        output_dir=output_dir,
    )

    assert (output_dir / "pkg" / "sub" / "shared.pyi").read_text(encoding="utf-8") == text + "\n"
    assert not (output_dir / "pkg.sub.shared.pyi").exists()


def test_prik_write_pyi_dependencies_uses_explicit_utf8(tmp_path: Path, monkeypatch):
    writes = []

    def write_text(path, data, *args, **kwargs):
        assert not args
        assert kwargs.get("encoding") is not None
        assert kwargs["encoding"].lower() == "utf-8"
        writes.append((path, data))
        return len(data)

    monkeypatch.setattr(Path, "write_text", write_text)

    prik_cli._write_pyi_dependencies(
        {str(tmp_path / "first.f90"): {"pyi_dependencies": {"shared": "class Shared:\n    pass"}}},
        output_dir=tmp_path,
    )

    assert writes == [(tmp_path / "shared.pyi", "class Shared:\n    pass\n")]


def test_prik_main_formats_preprocessing_errors_with_and_without_diagnostics(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["prik", "parse", str(TEST_FILE)])

    def fail_with_diagnostic(_paths, _preprocessing):
        raise PreprocessingError(
            "compiler failed",
            category="PREPROCESSOR_FAILED",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_FAILED",
                    message="bad include",
                    path="source.F90",
                    line=9,
                )
            ],
        )

    monkeypatch.setattr(prik_cli, "_parse_report", fail_with_diagnostic)
    assert prik_cli.main() == 1
    assert "source.F90:9: error[PREPROCESSOR_FAILED]: bad include" in capsys.readouterr().err

    def fail_without_diagnostic(_paths, _preprocessing):
        raise PreprocessingError("plain failure", category="PREPROCESSOR_FAILED")

    monkeypatch.setattr(prik_cli, "_parse_report", fail_without_diagnostic)
    assert prik_cli.main() == 1
    assert "prik: error[PREPROCESSOR_FAILED]: plain failure" in capsys.readouterr().err


def test_prik_main_preserves_zero_print_limit_and_legacy_vars_limit_contract(monkeypatch, capsys):
    args = _main_args(parse=True, print_limit=0, vars_limit=7)
    _install_main_parser(monkeypatch, args)
    preprocessing = object()
    parse_payload = {"parse": "payload"}
    format_calls = []

    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(prik_cli, "_build_preprocessing_config", lambda active_args, parser: preprocessing)
    monkeypatch.setattr(prik_cli, "_parse_report", lambda paths, active_preprocessing: parse_payload)
    monkeypatch.setattr(
        prik_cli,
        "_format_report",
        lambda payload, **kwargs: format_calls.append((payload, kwargs)) or "formatted",
    )

    assert prik_cli.main() == 0
    assert capsys.readouterr().out == "formatted\n"
    assert format_calls == [(parse_payload, {"show_vars": True, "print_limit": 0})]


def test_prik_main_preserves_conflicting_json_and_pyi_out_diagnostic(monkeypatch):
    args = _main_args(pyi=True, json=True, out="/tmp/conflict.pyi")
    _install_main_parser(monkeypatch, args)
    _patch_main_report_payloads(monkeypatch, semantic_payload={"input.f90": {"pyi": "def work() -> None: ..."}})

    with pytest.raises(_MainParserError) as exc_info:
        prik_cli.main()

    assert str(exc_info.value) == "--out cannot be used with both --json and --pyi"


def test_prik_main_preserves_explicit_and_adjacent_json_write_contracts(monkeypatch):
    writes = []
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda path, data, **kwargs: writes.append((path, data, kwargs)) or len(data),
    )

    explicit_payload = {"input.f90": {"node": 1}}
    explicit_args = _main_args(parse=True, out="/tmp/report.json")
    _install_main_parser(monkeypatch, explicit_args)
    _patch_main_report_payloads(monkeypatch, parse_payload=explicit_payload)
    assert prik_cli.main() == 0

    adjacent_payload = {
        "/tmp/first.f90": {"node": 1},
        "/tmp/empty.f90": {},
    }
    adjacent_args = _main_args(parse=True, out="")
    _install_main_parser(monkeypatch, adjacent_args)
    _patch_main_report_payloads(monkeypatch, parse_payload=adjacent_payload)
    assert prik_cli.main() == 0

    assert writes == [
        (Path("/tmp/report.json"), json.dumps(explicit_payload, indent=2), {"encoding": "utf-8"}),
        (
            Path("/tmp/first.json"),
            json.dumps({"/tmp/first.f90": {"node": 1}}, indent=2),
            {"encoding": "utf-8"},
        ),
        (Path("/tmp/empty.json"), json.dumps({"/tmp/empty.f90": {}}, indent=2), {"encoding": "utf-8"}),
    ]


def test_prik_main_preserves_stdout_mode_matrix(monkeypatch, capsys):
    parse_payload = {"parse": {"node": 1}}
    semantic_payload = {"semantic": {"node": 2}}
    scenarios = [
        ({"semantics": True}, json.dumps(semantic_payload, indent=2) + "\n", []),
        ({"parse": True, "json": True}, json.dumps(parse_payload, indent=2) + "\n", []),
        ({"pyi": True}, "", [("pyi-format", semantic_payload), ("pyi-output", "PYI")]),
        (
            {"parse": True},
            "PARSE\n",
            [("parse-format", parse_payload, {"show_vars": False, "print_limit": None})],
        ),
    ]

    for overrides, expected_stdout, expected_formats in scenarios:
        args = _main_args(**overrides)
        _install_main_parser(monkeypatch, args)
        _patch_main_report_payloads(
            monkeypatch,
            parse_payload=parse_payload,
            semantic_payload=semantic_payload,
        )
        formats = []
        monkeypatch.setattr(
            prik_cli,
            "_format_report",
            lambda payload, _formats=formats, **kwargs: _formats.append(("parse-format", payload, kwargs)) or "PARSE",
        )
        monkeypatch.setattr(
            prik_cli,
            "_format_pyi_report",
            lambda payload, _formats=formats: _formats.append(("pyi-format", payload)) or "PYI",
        )
        monkeypatch.setattr(
            prik_cli,
            "print_pyi_output",
            lambda text, _formats=formats: _formats.append(("pyi-output", text)),
        )

        assert prik_cli.main() == 0
        assert capsys.readouterr().out == expected_stdout
        assert formats == expected_formats


def test_prik_cli_helpers_cover_language_and_preprocessing_edges(tmp_path: Path, monkeypatch):
    class ErrorParser:
        def error(self, message):
            raise ValueError(message)

    def args(**overrides):
        values = {
            "defines": [],
            "undefs": [],
            "compiler": None,
            "compile_commands": None,
            "preprocessor_adapter": "auto",
            "preprocess_template": None,
            "include_dirs": [],
            "std": None,
            "compiler_args": [],
            "include_exposure": "reachable-project",
            "public_includes": [],
            "private_includes": [],
            "language": "fortran",
        }
        values.update(overrides)
        return types.SimpleNamespace(**values)

    parser = ErrorParser()
    stub = tmp_path / "api.pyi"
    stub.write_text("def add(x: Int32) -> Int32: ...\n", encoding="utf-8")
    upper_stub = tmp_path / "upper.PYI"
    upper_stub.write_text("def upper() -> None: ...\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    assert prik_cli._expand_pyi_paths([str(tmp_path), str(stub)]) == [stub]
    assert prik_cli._expand_pyi_paths([str(stub)]) == [stub]
    assert prik_cli._expand_pyi_paths([str(upper_stub)]) == [upper_stub]
    assert prik_cli._expand_pyi_paths([str(tmp_path / "notes.txt")]) == []
    with pytest.raises(ValueError, match="Cannot determine"):
        prik_cli._resolve_language([str(tmp_path / "notes.txt")], None, parser)

    with pytest.raises(ValueError, match="--preprocess-template requires"):
        prik_cli._build_preprocessing_config(
            args(
                compiler="cc",
                preprocess_template="{compiler} -E {source}",
            ),
            parser,
        )

    class Recipe:
        def to_dict(self):
            return {"mode": "compiler"}

    def preprocess(path, *, language, config):
        assert path == source
        assert language == "fortran"
        assert config.compiler == "gfortran"
        return "subroutine work()\nend subroutine work\n", Recipe()

    source = tmp_path / "api.f90"
    source.write_text("subroutine ignored()\nend subroutine ignored\n", encoding="utf-8")
    monkeypatch.setattr(prik_cli, "run_compiler_preprocessor_with_recipe", preprocess)
    code, recipe = prik_cli._fortran_source_for_path(
        source,
        PreprocessingConfig(mode="compiler", compiler="gfortran"),
    )
    assert "subroutine work" in code
    assert recipe == {"mode": "compiler"}
    report = prik_cli._parse_report(
        [str(source)],
        PreprocessingConfig(mode="compiler", compiler="gfortran"),
    )
    assert report[str(source)]["preprocessing_recipe"] == {"mode": "compiler"}


def test_cli_help_is_concise_and_points_to_detailed_help():
    cmd = [sys.executable, "-m", "prik", "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    normalized_help = " ".join(res.stdout.split())
    assert "INPUT [INPUT ...] [BUILD OPTIONS]" in res.stdout
    assert "positional arguments:" in res.stdout.lower()
    assert "build options:" in res.stdout
    assert "--native-compile-flags" in res.stdout
    assert "--jobs" in res.stdout
    assert "Input-language compiler used throughout the extension" in res.stdout
    assert "default: gfortran" in normalized_help
    assert "Add an include directory used throughout the extension" in res.stdout
    assert "--native-library openblas passes -lopenblas to the linker" in normalized_help
    assert "------------------------------ EXAMPLES ------------------------------" in res.stdout
    assert "Basic wrapper build:" in res.stdout
    assert "Name the Python extension:" in res.stdout
    assert "Generate an editable semantic contract:" in res.stdout
    assert "python3 -m prik points.f90" in res.stdout
    assert "python3 -m prik points.f90 --out geometry" in res.stdout
    assert "python3 -m prik generate --pyi points.f90 --out contracts" in res.stdout
    assert "See the prik homepage for the points.f90 source and generated Python API:" in res.stdout
    assert "https://pynumlab.github.io/prik/#see-it-in-action" in res.stdout
    assert "python3 -m prik --help-build" in res.stdout
    assert "python3 -m prik parse --help" in res.stdout
    assert "python3 -m prik semantics --help" in res.stdout
    assert "python3 -m prik generate --help" in res.stdout
    assert "python3 -m prik probe --help" in res.stdout


@pytest.mark.parametrize(
    ("command", "expected", "excluded"),
    [
        ("parse", "Compiler used for preprocessing", "datatype measurement"),
        ("semantics", "preprocessing and datatype measurement", "wrapper build files"),
        ("generate", "source analysis and wrapper build files", "used to build the probe"),
        ("probe", "used to build the probe", "source preprocessing"),
    ],
)
def test_subcommand_help_tailors_shared_compiler_options(command, expected, excluded):
    result = subprocess.run(
        [sys.executable, "-m", "prik", command, "--help", "--no-color"],
        capture_output=True,
        text=True,
        check=True,
    )
    normalized_help = " ".join(result.stdout.split())

    assert "options:" in result.stdout
    assert "------------------------------ EXAMPLES ------------------------------" in result.stdout
    if command != "probe":
        assert "positional arguments:" in result.stdout
        assert "default: gfortran; cc with --language c" in normalized_help
    else:
        assert "default: gfortran" not in normalized_help
    assert expected in normalized_help
    assert excluded not in normalized_help


def test_cli_parse_shows_module_derived_types_and_derived_arg_kinds():
    fixture = (
        Path(__file__).parents[2] / "source_parsing" / "parsing" / "fixtures" / "general" / "modern_pyi_example.f90"
    )
    cmd = [sys.executable, "-m", "prik", "parse", str(fixture)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "      Derived types: 3" in res.stdout
    assert "type particle" in res.stdout
    assert "Fields: 3" in res.stdout
    assert "- id:integer[0]" in res.stdout
    assert "- mass:real(8)[0]" in res.stdout
    assert "- position:real(8)[1]" in res.stdout
    assert "init_particle(p:type(particle)[0]" in res.stdout


def test_fortran_parser_cli_helper_branches(tmp_path: Path, monkeypatch):
    @dataclass
    class Node:
        name: str
        parent: object = None

    monkeypatch.setenv("FORTRAN_PARSER_TEST_FLAG", " yes ")
    assert fortran_parser_cli._env_flag("FORTRAN_PARSER_TEST_FLAG") is True
    monkeypatch.delenv("FORTRAN_PARSER_TEST_FLAG")
    assert fortran_parser_cli._env_flag("FORTRAN_PARSER_TEST_FLAG") is False

    assert fortran_parser_cli._diagnostic_color_enabled(disabled=True) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert fortran_parser_cli._diagnostic_color_enabled(disabled=False) is False
    monkeypatch.delenv("NO_COLOR")
    assert fortran_parser_cli._diagnostic_color_enabled(disabled=False) is True

    parent = Node("root")
    assert fortran_parser_cli._to_dict_no_parent(Node("child", parent=parent)) == {"name": "child"}
    assert fortran_parser_cli._to_dict_no_parent(Node("child", parent="root")) == {
        "name": "child",
        "parent": "root",
    }

    source = tmp_path / "nested" / "mini.f90"
    source.parent.mkdir()
    source.write_text("subroutine work(n)\n  integer, intent(in) :: n\nend subroutine work\n", encoding="utf-8")
    (source.parent / "notes.txt").write_text("ignore", encoding="utf-8")

    assert fortran_parser_cli._collect_extensions(tmp_path) == [source]
    report = fortran_parser_cli._parse_paths([str(tmp_path)])
    assert list(report) == [str(source)]
    assert report[str(source)]["signatures"][0]["name"] == "work"


def test_fortran_parser_cli_formatting_branches():
    report = fortran_parser_cli._format_report(
        {
            "types.f90": {
                "signatures": [],
                "types": [{"name": "particle", "fields": [], "methods": []}],
                "modules": [],
                "submodules": [],
                "programs": [],
                "block_data": [],
            }
        }
    )
    assert "Derived types: 1" in report
    assert "- type particle (fields=0, methods=0)" in report
    assert (
        fortran_parser_cli._format_var_type({"base_type": "derived", "kind": "particle", "rank": 0})
        == "type(particle)[0]"
    )
    assert fortran_parser_cli._format_var_type({"base_type": "real", "kind": "4", "rank": 2}) == "real(4)[2]"


def test_fortran_parser_cli_format_report_print_limit_covers_sections():
    var_a = {"name": "a", "base_type": "integer", "kind": "", "rank": 0}
    var_b = {"name": "b", "base_type": "real", "kind": "8", "rank": 1}
    field_a = {"name": "left", "base_type": "integer", "kind": "", "rank": 0}
    field_b = {"name": "right", "base_type": "integer", "kind": "", "rank": 0}
    proc_a = {"kind": "subroutine", "name": "first", "arguments": [var_a], "result": None}
    proc_b = {"kind": "function", "name": "second", "arguments": [], "result": var_b}
    dtype_a = {"name": "pair", "fields": [field_a, field_b], "methods": []}
    dtype_b = {"name": "hidden_pair", "fields": [], "methods": []}

    report = fortran_parser_cli._format_report(
        {
            "mixed.f90": {
                "signatures": [proc_a, proc_b],
                "types": [dtype_a, dtype_b],
                "modules": [
                    {
                        "name": "m1",
                        "variables": [var_a, var_b],
                        "uses": {},
                        "derived_types": [dtype_a, dtype_b],
                        "procedures": [proc_a, proc_b],
                    },
                    {
                        "name": "m2",
                        "variables": [],
                        "uses": {},
                        "derived_types": [],
                        "procedures": [],
                    },
                ],
                "submodules": [
                    {
                        "name": "sm1",
                        "parent": "m1",
                        "ancestor": None,
                        "variables": [var_a, var_b],
                        "uses": {},
                        "procedures": [proc_a, proc_b],
                    },
                    {
                        "name": "sm2",
                        "parent": "m1",
                        "ancestor": "root",
                        "variables": [],
                        "uses": {},
                        "procedures": [],
                    },
                ],
                "programs": [
                    {"name": "driver", "variables": [var_a, var_b], "uses": {}},
                    {"name": "other_driver", "variables": [], "uses": {}},
                ],
                "block_data": [
                    {"name": None, "variables": [var_a, var_b]},
                    {"name": "named_block", "variables": []},
                ],
            }
        },
        show_vars=True,
        print_limit=1,
    )

    assert "  Procedures: 2" in report
    assert "    - subroutine first(a:integer[0])" in report
    assert "    ... 1 more procedures" in report
    assert "  Derived types: 2" in report
    assert "    ... 1 more derived types" in report
    assert "  Modules: 2" in report
    assert "    - module m1 (vars=2, uses=0)" in report
    assert "      Variables: 2" in report
    assert "        - a:integer[0]" in report
    assert "        ... 1 more variables" in report
    assert "            - left:integer[0]" in report
    assert "            ... 1 more fields" in report
    assert "        ... 1 more derived types" in report
    assert "        ... 1 more procedures" in report
    assert "    ... 1 more modules" in report
    assert "  Submodules: 2" in report
    assert "    - submodule sm1 (parent=m1, vars=2, uses=0)" in report
    assert "    ... 1 more submodules" in report
    assert "  Programs: 2" in report
    assert "    - program driver (vars=2, uses=0)" in report
    assert "    ... 1 more programs" in report
    assert "  Block data: 2" in report
    assert "    - block data <unnamed> (vars=2)" in report
    assert "    ... 1 more block data units" in report

    assert fortran_parser_cli._format_variable_lines([], indent="  ", print_limit=1) == []


def test_fortran_parser_cli_json_and_parse_errors(tmp_path: Path):
    good = tmp_path / "good.f90"
    good.write_text("subroutine work(n)\n  integer, intent(in) :: n\nend subroutine work\n", encoding="utf-8")

    json_cmd = [sys.executable, "-m", "prik.parsers.fortran", str(good), "--json"]
    json_res = subprocess.run(json_cmd, capture_output=True, text=True, check=True)
    assert str(good) in json.loads(json_res.stdout)

    bad = tmp_path / "bad.f90"
    bad.write_text("subroutine bad(x)\n  weirdtype :: x\nend subroutine bad\n", encoding="utf-8")
    bad_cmd = [sys.executable, "-m", "prik.parsers.fortran", str(bad), "--no-color"]
    bad_res = subprocess.run(bad_cmd, capture_output=True, text=True)
    assert bad_res.returncode == 1
    assert bad_res.stdout == ""
    assert "Traceback" not in bad_res.stderr
    assert "Unknown or unsupported datatype" in bad_res.stderr


def test_prik_cli_helper_branches(tmp_path: Path, monkeypatch, capsys):
    @dataclass
    class Node:
        name: str
        parent: object = None

    @dataclass
    class ParentFirstNode:
        parent: object
        name: str

    monkeypatch.setenv("PRIK_TEST_FLAG", "ON")
    assert prik_cli._env_flag("PRIK_TEST_FLAG") is True
    monkeypatch.delenv("PRIK_TEST_FLAG")
    assert prik_cli._env_flag("PRIK_TEST_FLAG") is False

    assert prik_cli._diagnostic_color_enabled(disabled=True) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert prik_cli._diagnostic_color_enabled(disabled=False) is False
    monkeypatch.delenv("NO_COLOR")

    assert prik_cli._to_dict_no_parent(Node("child", parent=Node("root"))) == {"name": "child"}
    assert prik_cli._to_dict_no_parent(ParentFirstNode(parent=Node("root"), name="child")) == {"name": "child"}
    assert prik_cli._to_dict_no_parent({"node": Node("child", parent=Node("root"))}) == {"node": {"name": "child"}}

    source = tmp_path / "mini.f90"
    source.write_text("subroutine work(n)\n  integer, intent(in) :: n\nend subroutine work\n", encoding="utf-8")
    assert prik_cli._collect_extensions(tmp_path) == [source]
    assert prik_cli._expand_paths([str(tmp_path)]) == [source]

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    real_import = builtins.__import__

    def fail_rich_import(name, *args, **kwargs):
        if name.startswith("rich"):
            raise ImportError("rich disabled for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_rich_import)
    prik_cli.print_pyi_output("def f() -> None: ...")
    assert "def f() -> None: ..." in capsys.readouterr().out


def test_prik_print_pyi_output_uses_rich_and_falls_back(monkeypatch, capsys):
    calls = []

    class FakeSyntax:
        def __init__(self, code, lexer, **options):
            self.code = code
            self.lexer = lexer
            self.options = options

    class FakeConsole:
        def __init__(self, **options):
            self.options = options

        def print(self, syntax):
            calls.append((syntax.code, syntax.lexer, syntax.options, self.options))

    rich_module = types.ModuleType("rich")
    console_module = types.ModuleType("rich.console")
    syntax_module = types.ModuleType("rich.syntax")
    console_module.Console = FakeConsole
    syntax_module.Syntax = FakeSyntax
    monkeypatch.setitem(sys.modules, "rich", rich_module)
    monkeypatch.setitem(sys.modules, "rich.console", console_module)
    monkeypatch.setitem(sys.modules, "rich.syntax", syntax_module)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    prik_cli.print_pyi_output("def f() -> None: ...")
    assert calls == [
        (
            "def f() -> None: ...",
            "python",
            {
                "theme": "ansi_dark",
                "background_color": "default",
                "line_numbers": False,
                "word_wrap": False,
            },
            {"force_terminal": True, "color_system": "auto"},
        )
    ]
    assert capsys.readouterr().out == ""

    class RaisingConsole(FakeConsole):
        def print(self, syntax):
            raise RuntimeError("terminal failed")

    console_module.Console = RaisingConsole
    prik_cli.print_pyi_output("def g() -> None: ...")
    assert "def g() -> None: ..." in capsys.readouterr().out


def test_prik_main_formats_value_errors_or_reraises_for_debug(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "input.f90"
    source.write_text("module input\nend module input\n", encoding="utf-8")

    def fail_parse(_paths, _preprocessing):
        raise ValueError("invalid generated interface")

    monkeypatch.setattr(prik_cli, "_parse_report", fail_parse)
    monkeypatch.setattr(sys, "argv", ["prik", "parse", str(source)])
    assert prik_cli.main() == 1
    assert "prik: error: invalid generated interface" in capsys.readouterr().err

    monkeypatch.setattr(sys, "argv", ["prik", "parse", str(source), "--debug"])
    with pytest.raises(ValueError, match="invalid generated interface"):
        prik_cli.main()
