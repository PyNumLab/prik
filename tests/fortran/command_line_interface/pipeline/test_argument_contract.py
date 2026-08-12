"""Tests split by stable CLI argument-contract ownership."""

import json
from pathlib import Path
import subprocess
import sys
import types

import pytest

import prik.cli as prik_cli
from prik.preprocessing import PreprocessingError
from tests.fortran.command_line_interface.pipeline._support import (
    TEST_FILE,
    _MainParserError,
    _install_main_parser,
    _main_args,
)


def test_cli_pyi_out_rejects_ambiguous_single_file_contract_package(tmp_path: Path):
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
    output = tmp_path / "combined.pyi"

    cmd = [sys.executable, "-m", "prik", "generate", "--pyi", str(source), "--out", str(output)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode != 0
    assert "generated contracts use one file per module" in result.stderr
    assert not output.exists()


def test_cli_rejects_conflicting_json_and_pyi_out_from_inline_code(tmp_path: Path):
    f90 = tmp_path / "conflict.f90"
    f90.write_text(
        """module conflict_mod
contains
  subroutine ping()
  end subroutine ping
end module conflict_mod
""",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "prik",
        "generate",
        "--pyi",
        str(f90),
        "--json",
        "--out",
        str(tmp_path / "out"),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 2
    assert "--out cannot be used with both --json and --pyi" in res.stderr


def test_prik_pyi_report_formats_and_rejects_conflicting_dependency_stubs():
    report = {
        "first.f90": {
            "pyi": "def first() -> None: ...",
            "pyi_dependencies": {"shared": "class shared(Opaque):\n    pass"},
        },
        "second.f90": {
            "pyi": "def second() -> None: ...",
            "pyi_dependencies": {
                "shared": "class shared(Opaque):\n    pass",
                "extra": "class extra(Opaque):\n    pass",
            },
        },
        "empty.f90": {},
    }

    text = prik_cli._format_pyi_report(report)

    assert (
        text
        == """File: first.f90
def first() -> None: ...

Dependency stub: shared.pyi
class shared(Opaque):
    pass

File: second.f90
def second() -> None: ...

Dependency stub: extra.pyi
class extra(Opaque):
    pass

File: empty.f90
<no module declarations found>"""
    )
    with pytest.raises(ValueError, match="Conflicting generated dependency stub"):
        prik_cli._write_pyi_dependencies(
            {
                "first.f90": {"pyi_dependencies": {"shared": "class shared:\n    pass"}},
                "second.f90": {"pyi_dependencies": {"shared": "class shared:\n    value: int"}},
            }
        )


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {"out": ""},
            "--out for wrapper builds requires an output name",
        ),
        (
            {"out": "module.txt"},
            "--out for wrapper builds expects NAME or NAME.so",
        ),
        (
            {"out": "bad-name"},
            "--out for wrapper builds expects a valid Python module name",
        ),
        (
            {"out": "module", "makefile": True},
            "generate --sources/--makefile uses --out-dir, not --out",
        ),
        ({"parse": True, "print_limit": -1}, "--print-limit must be >= 0"),
        (
            {"paths": ["input.pyi"]},
            "A .pyi wrapper build requires --native-fortran-sources, --native-objects, "
            "--native-library, or --native-link-item",
        ),
        (
            {"paths": ["input.unknown"]},
            "A wrapper build expects recognized Fortran source suffixes or one semantic .pyi contract; "
            "unsupported input: input.unknown",
        ),
        (
            {"no_compile_input_sources": True},
            "--no-compile-input-sources requires --native-fortran-sources, --native-objects, "
            "--native-library, or --native-link-item",
        ),
        (
            {
                "paths": ["input.pyi"],
                "no_compile_input_sources": True,
                "native_objects": ["implementation.o"],
            },
            "--no-compile-input-sources applies only to source-driven wrapper builds",
        ),
    ],
)
def test_prik_main_preserves_validation_diagnostics(monkeypatch, overrides, expected):
    args = _main_args(**overrides)
    _install_main_parser(monkeypatch, args)
    monkeypatch.setattr(prik_cli, "_resolve_language", lambda paths, language, parser: language)
    monkeypatch.setattr(prik_cli, "_build_preprocessing_config", lambda active_args, parser: object())

    with pytest.raises(_MainParserError) as exc_info:
        prik_cli.main()

    assert str(exc_info.value) == expected


def test_prik_main_collects_many_native_inputs_from_one_option_group(
    monkeypatch,
    tmp_path: Path,
    capsys,
):
    contract = tmp_path / "module.pyi"
    contract.write_text("def scale(x: float) -> float: ...\n", encoding="utf-8")
    build_dir = tmp_path / "build"
    calls = []
    result = types.SimpleNamespace(
        to_dict=lambda: {
            "module_name": "module",
            "shared_library": str(build_dir / "module.so"),
        }
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prik",
            str(contract),
            "--compiler",
            "selected-gfortran",
            "-I",
            "include",
            "-I",
            "vendor/include",
            "--native-fortran-sources",
            "source_one.f90",
            "source_two.f90",
            "--native-compile-flags=-O2 -g0",
            "--jobs",
            "3",
            "--native-objects",
            "one.o",
            "two.a",
            "libsolver.so",
            "--native-library",
            "blas",
            "lapack",
            "--native-link-item",
            "arg:-Wl,--start-group",
            "object:one.o",
            "arg:-Wl,--end-group",
            "--native-library-dir",
            "lib",
            "vendor/lib",
            "-I",
            "mods",
            "-I",
            "vendor/mods",
            "--wrapper-compiler-debug",
            "--wrapper-fortran-flags=-fno-range-check -g0",
            "--wrapper-c-flags=-O0 -g0",
            "--out-dir",
            str(build_dir),
            "--json",
        ],
    )
    monkeypatch.setattr(
        prik_cli,
        "_run_wrap_build_with_diagnostics",
        lambda active_args, active_preprocessing: calls.append((active_args, active_preprocessing)) or result,
    )

    assert prik_cli.main() == 0

    assert len(calls) == 1
    active_args, _preprocessing = calls[0]
    assert active_args.paths == [str(contract)]
    assert active_args.compiler == "selected-gfortran"
    assert active_args.include_dirs == ["include", "vendor/include", "mods", "vendor/mods"]
    assert active_args.native_fortran_sources == ["source_one.f90", "source_two.f90"]
    assert active_args.native_compile_flags == ["-O2 -g0"]
    assert active_args.jobs == 3
    assert active_args.native_objects == ["one.o", "two.a", "libsolver.so"]
    assert active_args.native_libraries == ["blas", "lapack"]
    assert active_args.native_link_items == [
        "arg:-Wl,--start-group",
        "object:one.o",
        "arg:-Wl,--end-group",
    ]
    assert active_args.native_library_dirs == ["lib", "vendor/lib"]
    assert prik_cli._cli_build_include_dirs(active_args) == (
        "include",
        "vendor/include",
        "mods",
        "vendor/mods",
    )
    assert active_args.wrapper_compiler_debug is True
    assert active_args.wrapper_fortran_flags == ["-fno-range-check -g0"]
    assert active_args.wrapper_c_flags == ["-O0 -g0"]
    payload = json.loads(capsys.readouterr().out)
    assert payload["module_name"] == "module"


@pytest.mark.parametrize(
    "overrides",
    [
        {"paths": ["input.f90"]},
        {"paths": ["contract.pyi"], "native_objects": ["native.o"]},
        {"paths": ["input.f90"], "makefile": True},
        {"paths": [], "build_manifest": "build/prik-build.json"},
    ],
)
def test_wrapper_inputs_select_the_default_build_stage(overrides):
    assert prik_cli._is_wrapper_build(_main_args(**overrides))


def test_explicit_inspection_stage_prevents_default_wrapper_selection():
    assert not prik_cli._is_wrapper_build(_main_args(parse=True))


def test_cli_native_compile_flags_split_grouped_shell_words():
    assert prik_cli._cli_native_compile_flags(["-O2 -g0", "-DNAME='value with spaces'"]) == (
        "-O2",
        "-g0",
        "-DNAME=value with spaces",
    )


def test_source_build_routes_disabled_input_compilation_to_the_pipeline(monkeypatch):
    from prik.pipeline import build as pipeline_build

    calls = []
    result = types.SimpleNamespace(compiled=False)
    monkeypatch.setattr(
        pipeline_build,
        "build_fortran_extension",
        lambda *args, **kwargs: calls.append((args, kwargs)) or result,
    )
    args = _main_args(
        paths=["native"],
        no_compile_input_sources=True,
        native_objects=["libnative.so"],
    )

    assert prik_cli._run_wrap_build(args, types.SimpleNamespace(compiler="gfortran")) is result
    assert calls[0][0] == (["native"],)
    assert calls[0][1]["compile_input_sources"] is False
    assert calls[0][1]["native_objects"] == ["libnative.so"]


@pytest.mark.parametrize("jobs", ("0", "many"))
def test_cli_compile_jobs_rejects_non_positive_or_non_integer_values(jobs: str, capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        prik_cli.main([str(TEST_FILE), "--jobs", jobs])

    assert exc_info.value.code == 2
    assert "jobs must be a positive integer" in capsys.readouterr().err


def test_cli_wrapper_flags_split_grouped_shell_words():
    assert prik_cli._cli_wrapper_fortran_flags(["-O0 -g", "-DNAME='value with spaces'"]) == (
        "-O0",
        "-g",
        "-DNAME=value with spaces",
    )
    assert prik_cli._cli_wrapper_c_flags(["-O1 -g0"]) == ("-O1", "-g0")


def test_cli_native_compile_flags_reject_malformed_grouped_value():
    with pytest.raises(ValueError, match="Invalid --native-compile-flags value"):
        prik_cli._cli_native_compile_flags(["'-O2"])


def test_cli_wrapper_flags_reject_malformed_grouped_value():
    with pytest.raises(ValueError, match="Invalid --wrapper-c-flags value"):
        prik_cli._cli_wrapper_c_flags(["'-O0"])


def test_prik_build_preprocessing_config_preserves_macro_validation_errors(monkeypatch):
    class Parser:
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

    def reject(value, option):
        raise PreprocessingError(f"{option}: invalid {value}", category="INVALID_MACRO_NAME")

    monkeypatch.setattr(prik_cli, "validate_macro_name", reject)

    with pytest.raises(ValueError) as define_error:
        prik_cli._build_preprocessing_config(args(defines=["=bad"]), Parser())
    assert str(define_error.value) == "--define/-D: invalid =bad"

    with pytest.raises(ValueError) as undef_error:
        prik_cli._build_preprocessing_config(args(undefs=["=bad"]), Parser())
    assert str(undef_error.value) == "--undef/-U: invalid =bad"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"compiler": "cc", "preprocess_template": "{source}"},
            "--preprocess-template requires --preprocessor-adapter command-template",
        ),
    ],
)
def test_prik_build_preprocessing_config_preserves_validation_diagnostics(overrides, message):
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

    class Parser:
        def error(self, received):
            raise ValueError(received)

    with pytest.raises(ValueError) as error:
        prik_cli._build_preprocessing_config(types.SimpleNamespace(**values), Parser())
    assert str(error.value) == message


def test_prik_resolve_language_handles_fortran_and_ambiguous_input_edges(tmp_path: Path):
    class ErrorParser:
        def error(self, message):
            raise ValueError(message)

    parser = ErrorParser()
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    f_source = tmp_path / "solver.F90"
    f_source.write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")
    stub = tmp_path / "iface.PYI"
    stub.write_text("def solve() -> None: ...\n", encoding="utf-8")
    unknown = tmp_path / "notes.txt"
    unknown.write_text("notes\n", encoding="utf-8")

    with pytest.raises(ValueError) as directory_error:
        prik_cli._resolve_language([str(input_dir)], None, parser)
    assert str(directory_error.value) == (
        f"Input directory {input_dir} requires an explicit frontend; "
        "pass --language fortran or --language c. Use --help for examples."
    )

    assert prik_cli._resolve_language([str(f_source)], None, parser) == "fortran"
    assert prik_cli._resolve_language([str(stub)], None, parser) == "fortran"

    with pytest.raises(ValueError) as unknown_error:
        prik_cli._resolve_language([str(unknown)], None, parser)
    assert str(unknown_error.value) == (
        f"Cannot determine the input language for {unknown}; "
        "pass --language fortran or --language c. Use --help for examples."
    )


def test_cli_without_language_keeps_fortran_default_behavior():
    cmd = [sys.executable, "-m", "prik", "parse", str(TEST_FILE)]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "subroutine add1" in result.stdout
    assert "Language: c" not in result.stdout


def test_cli_wrapper_out_requires_name_for_default_wrap():
    cmd = [sys.executable, "-m", "prik", str(TEST_FILE), "--out"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "argument --out: expected one argument" in res.stderr


def test_prik_command_parsers_group_options_by_user_intent():
    top_help = prik_cli._top_level_parser(["--help"]).format_help()
    build_help = prik_cli._build_parser(["input.f90", "--help"]).format_help()
    parse_help = prik_cli._parse_parser(["--help"]).format_help()
    semantics_help = prik_cli._semantics_parser(["--help"]).format_help()
    generate_help = prik_cli._generate_parser(["--help"]).format_help()
    probe_help = prik_cli._probe_parser(["--help"]).format_help()
    normalized_top_help = " ".join(top_help.split())
    normalized_build_help = " ".join(build_help.split())
    normalized_parse_help = " ".join(parse_help.split())
    normalized_semantics_help = " ".join(semantics_help.split())
    normalized_generate_help = " ".join(generate_help.split())
    normalized_probe_help = " ".join(probe_help.split())

    def assert_group_order(help_text, *headings):
        positions = [help_text.index(heading) for heading in headings]
        assert positions == sorted(positions)

    assert "commands:" in top_help
    assert all(command in top_help for command in ("parse", "semantics", "generate", "probe"))
    assert top_help.startswith("usage: python3 -m prik INPUT [INPUT ...] [BUILD OPTIONS]")
    assert "python3 -m prik {parse,semantics,generate,probe} [OPTIONS] ..." in top_help
    assert "python3 -m prik --version" in top_help
    assert "Build Python extensions from Fortran and inspect native interface artifacts." in top_help
    assert prik_cli._HELP_DIVIDER in top_help
    assert "Basic wrapper build:" in top_help
    assert "Name the Python extension:" in top_help
    assert "Generate an editable semantic contract:" in top_help
    assert "python3 -m prik points.f90" in top_help
    assert "python3 -m prik points.f90 --out geometry" in top_help
    assert "python3 -m prik generate --pyi points.f90 --out contracts" in top_help
    assert "See the PRIK homepage for the points.f90 source and generated Python API:" in top_help
    assert "https://pynumlab.github.io/prik/#see-it-in-action" in top_help
    assert "points.f90" in build_help
    assert "points.f90" in parse_help
    assert "points.f90" in semantics_help
    assert "points.f90" in generate_help
    for help_text in (top_help, build_help, parse_help, semantics_help, generate_help, probe_help):
        assert "scale.f90" not in help_text
    assert "Run `python3 -m prik --help-build` for the full list of build options." in top_help
    for command in ("parse", "semantics", "generate", "probe"):
        assert f"python3 -m prik {command} --help" in top_help
    for heading in ("positional arguments:", "build options:"):
        assert heading in top_help
    for common_option in (
        "--out",
        "--out-dir",
        "--compiler",
        "--include-dir",
        "--native-compile-flags",
        "--jobs",
        "--native-library",
        "--verbose",
        "--help-build",
        "--version",
    ):
        assert common_option in top_help
    assert "Input-language compiler used throughout the extension" in top_help
    assert "default: gfortran" in normalized_top_help
    assert "Add an include directory used throughout the extension" in top_help
    assert "Compiler used for preprocessing and internal datatype measurement" not in top_help
    assert "--native-library openblas passes -lopenblas to the linker" in normalized_top_help
    assert "--native-link-item" not in top_help
    assert "--wrapper-c-flags" not in top_help
    assert build_help.startswith("usage: python3 -m prik INPUT [INPUT ...]\n")
    assert "[OUTPUT OPTIONS] [COMPILER OPTIONS] [WRAPPER OPTIONS]" in build_help
    assert "[NATIVE OPTIONS] [DIAGNOSTIC OPTIONS]" in build_help
    assert "python3 -m prik --build-manifest PATH [MANIFEST OVERRIDES]" in build_help
    assert "positional arguments:" in build_help
    for heading in (
        "input selection:",
        "output options:",
        "compiler options:",
        "wrapper options:",
        "native options:",
        "diagnostic options:",
    ):
        assert heading in build_help
    assert "--native-link-item" in build_help
    assert "--jobs" in build_help
    assert "--wrapper-c-flags" in build_help
    assert "Compiler used throughout the extension build" in build_help
    assert "Add a compiler include search directory" in build_help
    assert "default: gfortran" in normalized_build_help
    assert "default: ./__prik__" in normalized_build_help
    assert (
        "Fortran source file(s), one source directory, or exactly one semantic .pyi contract" in normalized_build_help
    )
    assert "--no-compile-input-sources" in build_help
    assert "Input language (default: fortran)" in normalized_build_help
    assert "Rebuild the extension from an existing prik-build.json" in normalized_build_help
    assert "Name the Python extension and stable NAME.so library" in normalized_build_help
    assert "Print build paths and metadata as JSON" in normalized_build_help
    assert 'Native compiler flags (for example, "-O3 -fopenmp")' in normalized_build_help
    assert "docs/user/reference/cli-commands.md" in build_help
    assert "See docs/user/reference/cli-commands.md for all build options." in build_help
    assert "Build from a semantic contract:" in build_help
    assert "Replay a build manifest:" in build_help
    assert "Manifest overrides: --out, --compiler, -I/--include-dir, --jobs" in normalized_build_help
    assert "--language {fortran}" in build_help
    assert "--language {fortran,c}" not in build_help
    assert parse_help.startswith("usage: python3 -m prik parse INPUT [INPUT ...] [OPTIONS]")
    for heading in (
        "positional arguments:",
        "input options:",
        "preprocessing options:",
        "C include options:",
        "report options:",
        "output options:",
        "diagnostic options:",
    ):
        assert heading in parse_help
    assert_group_order(
        parse_help,
        "options:",
        "positional arguments:",
        "input options:",
        "preprocessing options:",
        "C include options:",
        "report options:",
        "output options:",
        "diagnostic options:",
    )
    assert "--language {fortran,c}" in parse_help
    assert "--compile-commands" in parse_help
    assert "Compiler used for preprocessing" in normalized_parse_help
    assert "Add a preprocessing include search directory" in normalized_parse_help
    assert "datatype measurement" not in normalized_parse_help
    assert "native and bridge compilation" not in normalized_parse_help
    assert "default: gfortran; cc with --language c" in normalized_parse_help
    assert semantics_help.startswith("usage: python3 -m prik semantics INPUT [INPUT ...] [OPTIONS]")
    assert "--json" not in semantics_help
    assert "Write combined JSON to PATH" in semantics_help
    assert "Define a preprocessing macro" in semantics_help
    for heading in (
        "positional arguments:",
        "input options:",
        "preprocessing options:",
        "C include options:",
        "output options:",
        "diagnostic options:",
    ):
        assert heading in semantics_help
    assert_group_order(
        semantics_help,
        "options:",
        "positional arguments:",
        "input options:",
        "preprocessing options:",
        "C include options:",
        "output options:",
        "diagnostic options:",
    )
    assert "preprocessing and datatype measurement" in normalized_semantics_help
    assert "native and bridge compilation" not in normalized_semantics_help
    assert "default: gfortran; cc with --language c" in normalized_semantics_help
    assert "(--pyi | --sources | --makefile)" in generate_help
    assert "INPUT [INPUT ...] [OPTIONS]" in generate_help
    assert "--build-manifest PATH [OVERRIDES]" in generate_help
    for heading in (
        "generation modes:",
        "positional arguments:",
        "input options:",
        "compiler and preprocessing options:",
        "C include options:",
        "wrapper options:",
        "native options:",
        "output options:",
        "diagnostic options:",
    ):
        assert heading in generate_help
    assert_group_order(
        generate_help,
        "options:",
        "generation modes:",
        "positional arguments:",
        "input options:",
        "compiler and preprocessing options:",
        "C include options:",
        "wrapper options:",
        "native options:",
        "output options:",
        "diagnostic options:",
    )
    assert "--pyi" in generate_help
    assert "--sources" in generate_help
    assert "--makefile" in generate_help
    assert "Read an existing prik-build.json and regenerate wrapper artifacts" in normalized_generate_help
    assert "Compiler used for source analysis and wrapper build files" in normalized_generate_help
    assert "default: gfortran; cc with --language c" in normalized_generate_help
    assert "native compiler options:" not in generate_help
    assert "link options:" not in generate_help
    assert probe_help.startswith("usage: python3 -m prik probe --language {fortran,c} --compiler COMPILER [OPTIONS]\n")
    for heading in ("probe options:", "execution options:", "output options:", "diagnostic options:"):
        assert heading in probe_help
    assert_group_order(
        probe_help,
        "options:",
        "probe options:",
        "execution options:",
        "output options:",
        "diagnostic options:",
    )
    assert "--format {json,markdown}" in probe_help
    assert "Probe compiler-target datatype sizes, alignment, and ABI facts." in probe_help
    assert "Probe flags that change default kinds:" in probe_help
    assert "--compiler-arg=-fdefault-real-8 --compiler-arg=-fdefault-integer-8" in probe_help
    assert "Cross-target probe:" in probe_help
    assert "--runner qemu-aarch64" in probe_help
    assert "Native or cross compiler used to build the probe" in normalized_probe_help
    assert "Add a probe include search directory" in normalized_probe_help
    assert "default: gfortran" not in normalized_probe_help
    assert "--sources" not in parse_help
    assert "--show-vars" not in semantics_help
    assert "--native-library-dir" not in probe_help


@pytest.mark.parametrize(
    ("parser_factory", "purpose"),
    [
        (
            prik_cli._top_level_parser,
            "Build Python extensions from Fortran and inspect native interface artifacts.",
        ),
        (
            prik_cli._build_parser,
            "Build a Python extension from Fortran source or a semantic .pyi contract.",
        ),
        (
            prik_cli._parse_parser,
            "Inspect Fortran or C source declarations before semantic conversion.",
        ),
        (
            prik_cli._semantics_parser,
            "Convert Fortran or C source code into language-neutral semantic IR models.",
        ),
        (
            prik_cli._generate_parser,
            "Generate semantic .pyi contracts or wrapper build artifacts without compiling.",
        ),
        (
            prik_cli._probe_parser,
            "Probe compiler-target datatype sizes, alignment, and ABI facts.",
        ),
    ],
)
def test_cli_help_places_a_clear_purpose_below_usage(parser_factory, purpose):
    help_text = parser_factory(["--help", "--no-color"]).format_help()

    assert f"\n\n{purpose}\n\n" in help_text


@pytest.mark.parametrize(
    ("parser_factory", "example_headings"),
    [
        (
            prik_cli._top_level_parser,
            ("Basic wrapper build:", "Name the Python extension:", "More help:"),
        ),
        (
            prik_cli._build_parser,
            ("Basic wrapper build:", "Build from a semantic contract:", "Replay a build manifest:"),
        ),
        (
            prik_cli._parse_parser,
            ("Basic Fortran inspection:", "Detailed Fortran report:", "C header as JSON:"),
        ),
        (
            prik_cli._semantics_parser,
            ("Basic Fortran conversion:", "C header:", "Save semantic IR:"),
        ),
        (
            prik_cli._generate_parser,
            ("Editable semantic contract:", "Wrapper sources only:", "Reproducible Makefile build:"),
        ),
        (
            prik_cli._probe_parser,
            (
                "Basic target probes:",
                "Human-readable mapping table:",
                "Probe flags that change default kinds:",
                "Cross-target probe:",
            ),
        ),
    ],
)
def test_cli_help_groups_examples_by_task(parser_factory, example_headings):
    help_text = parser_factory(["--help", "--no-color"]).format_help()

    assert prik_cli._HELP_DIVIDER in help_text
    assert all(heading in help_text for heading in example_headings)


def test_help_build_routes_to_the_full_default_build_help():
    result = subprocess.run(
        [sys.executable, "-m", "prik", "--help-build", "--no-color"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "[OUTPUT OPTIONS] [COMPILER OPTIONS] [WRAPPER OPTIONS]" in result.stdout
    assert "[NATIVE OPTIONS] [DIAGNOSTIC OPTIONS]" in result.stdout
    assert "compiler options:" in result.stdout
    assert "native options:" in result.stdout
    assert "diagnostic options:" in result.stdout
    assert "--native-link-item" in result.stdout
    assert "--wrapper-c-flags" in result.stdout
    normalized_help = " ".join(result.stdout.split())
    assert "Link NAME as -lNAME; for example, openblas adds -lopenblas" in normalized_help


def test_help_build_exposes_every_supported_build_option():
    parser = prik_cli._build_parser(["--help"])
    help_text = parser.format_help()
    option_strings = {option for action in parser._actions for option in action.option_strings}

    assert option_strings
    assert all(option in help_text for option in option_strings)


@pytest.mark.parametrize(
    "parser_factory",
    (
        prik_cli._parse_parser,
        prik_cli._semantics_parser,
        prik_cli._generate_parser,
        prik_cli._probe_parser,
    ),
)
def test_subcommand_help_exposes_every_supported_option(parser_factory):
    parser = parser_factory(["--help"])
    help_text = parser.format_help()
    option_strings = {option for action in parser._actions for option in action.option_strings}

    assert option_strings
    assert all(option in help_text for option in option_strings)


@pytest.mark.parametrize(
    ("extra_args", "message"),
    [
        (["--out-dir", "elsewhere"], "replays its saved output directory"),
        (["--language", "fortran"], "replays its saved input language"),
        (["--preprocessor-adapter", "auto"], "replays its saved preprocessing recipe"),
        (["-D", "USE_FAST=1"], "replays its saved preprocessing recipe"),
        (["--strict-wrapper-names"], "replays saved wrapper behavior"),
        (["--native-library", "openblas"], "replays saved native inputs"),
    ],
)
def test_manifest_replay_rejects_saved_settings_instead_of_ignoring_them(extra_args, message, capsys):
    with pytest.raises(SystemExit) as exc_info:
        prik_cli.main(["--build-manifest", "build/prik-build.json", *extra_args])

    assert exc_info.value.code == 2
    assert message in capsys.readouterr().err


def test_manifest_replay_accepts_documented_overrides(monkeypatch):
    captured = {}

    def run_build(args, preprocessing):
        captured["args"] = args
        captured["preprocessing"] = preprocessing
        return object()

    monkeypatch.setattr(prik_cli, "_run_wrap_build_with_diagnostics", run_build)
    monkeypatch.setattr(prik_cli, "_print_wrap_build_output", lambda _args, _result: None)

    result = prik_cli.main(
        [
            "--build-manifest",
            "build/prik-build.json",
            "--out",
            "REPLAYED",
            "--compiler",
            "selected-gfortran",
            "-I",
            "include",
            "--json",
            "--verbose",
            "--no-color",
            "--debug",
        ]
    )

    assert result == 0
    assert captured["args"].out == "REPLAYED"
    assert captured["args"].json is True
    assert captured["args"].verbose is True
    assert captured["args"].no_color is True
    assert captured["args"].debug is True
    assert captured["preprocessing"].compiler == "selected-gfortran"
    assert captured["preprocessing"].include_dirs == ["include"]


@pytest.mark.parametrize(
    "argv",
    [
        ["generate", "input.f90"],
        ["generate", "--pyi", "--sources", "input.f90"],
    ],
)
def test_generate_requires_exactly_one_output_mode(argv):
    with pytest.raises(SystemExit) as exc_info:
        prik_cli.main(argv)

    assert exc_info.value.code == 2


def test_cli_requires_explicit_language_for_directory_and_unknown_suffix(tmp_path: Path):
    source = tmp_path / "solver.source"
    source.write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")

    unknown = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(source)],
        capture_output=True,
        text=True,
    )
    assert unknown.returncode == 2
    assert "Cannot determine the input language" in unknown.stderr
    assert "--language fortran or --language c" in unknown.stderr

    directory = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert directory.returncode == 2
    assert "requires an explicit frontend" in directory.stderr

    explicit = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(source), "--language", "fortran"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "subroutine solve" in explicit.stdout


def test_cli_rejects_fortran_file_with_explicit_c_frontend(tmp_path: Path):
    source = tmp_path / "solver.f90"
    source.write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "prik", "parse", str(source), "--language", "c"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "incompatible with --language c" in result.stderr
    assert "pass --language fortran" in result.stderr


def test_cli_fortran_rejects_embedded_c_declaration_outside_execution_body(tmp_path: Path):
    source = tmp_path / "solver.f90"
    source.write_text(
        "subroutine solve()\n  int add(int a, int b);\nend subroutine solve\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--pyi", str(source)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "PARSE_UNSUPPORTED_DECLARATION" in result.stderr
    assert "Unknown or unsupported datatype declaration" in result.stderr


def test_prik_cli_defaults_pyi_to_wrapper_and_requires_native_implementation(tmp_path: Path):
    pyi = tmp_path / "module.pyi"
    pyi.write_text("def f() -> None: ...\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "prik", str(pyi)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "A .pyi wrapper build requires --native-fortran-sources" in res.stderr


@pytest.mark.parametrize("macro_flag", ["-D", "-U"])
def test_prik_main_rejects_invalid_macro_names(macro_flag: str, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prik", "parse", str(TEST_FILE), macro_flag, "=invalid"])
    with pytest.raises(SystemExit):
        prik_cli.main()
