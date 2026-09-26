"""CLI argument contracts: validation diagnostics, routing to the pipeline owners, and help.

The CLI and the Python build API are two entry points with one owner, so these
tests run real command lines through ``prik.cli.main`` and assert what reaches
the public ``prik.pipeline.build`` functions instead of re-proving the build.
"""

import argparse
import json
from pathlib import Path
import types

import pytest

import prik.cli as prik_cli
from prik.pipeline import build as pipeline_build

MODULE_SOURCE = """module m
contains
  subroutine add1(x)
    integer, intent(inout) :: x
  end subroutine add1
end module m
"""


def _invoke(argv: list[str], capsys) -> tuple[int, str, str]:
    """Run one command line in-process and return its exit code and output."""
    try:
        code = prik_cli.main(argv)
    except SystemExit as exc:
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def cli_inputs(tmp_path: Path, monkeypatch) -> Path:
    """Write one input of each kind the argument rows name, relative to the working directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src.f90").write_text(MODULE_SOURCE, encoding="utf-8")
    (tmp_path / "solver.F90").write_text(MODULE_SOURCE, encoding="utf-8")
    (tmp_path / "solver.source").write_text("subroutine solve()\nend subroutine solve\n", encoding="utf-8")
    (tmp_path / "contract.pyi").write_text("def add1(x: int) -> int: ...\n", encoding="utf-8")
    (tmp_path / "iface.PYI").write_text("def add1(x: int) -> int: ...\n", encoding="utf-8")
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "src.f90").write_text(MODULE_SOURCE, encoding="utf-8")
    for language in ("fortran", "c"):
        (tmp_path / f"{language}-build.json").write_text(
            json.dumps({"schema_version": 5, "build_kind": "pyi-wrapper", "extension": {"native_language": language}}),
            encoding="utf-8",
        )
    return tmp_path


_WRAPPER_NATIVE_INPUTS = (
    "--native-fortran-sources, --native-c-sources, --native-objects, --native-library, or --native-link-item"
)


@pytest.mark.parametrize(
    ("argv", "exit_code", "message"),
    [
        pytest.param(["src.f90", "--out", ""], 2, "--out for wrapper builds requires an output name", id="out-empty"),
        pytest.param(["src.f90", "--out", "module.txt"], 2, "expects NAME or NAME.so", id="out-suffix"),
        pytest.param(["src.f90", "--out", "bad-name"], 2, "expects a valid Python module name", id="out-identifier"),
        pytest.param(["src.f90", "--out"], 2, "argument --out: expected one argument", id="out-without-name"),
        pytest.param(
            ["generate", "--makefile", "src.f90", "--out", "module"],
            2,
            "generate --sources/--makefile/--cmake uses --out-dir, not --out",
            id="generate-makefile-out",
        ),
        pytest.param(
            ["generate", "--pyi", "src.f90", "--json", "--out", "reports"],
            2,
            "--out cannot be used with both --json and --pyi",
            id="generate-json-and-pyi-out",
        ),
        pytest.param(["generate", "src.f90"], 2, "one of the arguments --pyi", id="generate-without-mode"),
        pytest.param(
            ["generate", "--pyi", "--sources", "src.f90"], 2, "not allowed with argument --pyi", id="generate-two-modes"
        ),
        pytest.param(
            ["generate", "--pyi", "contract.pyi"],
            2,
            "generate --pyi expects recognized fortran source suffixes; unsupported input: contract.pyi",
            id="source-stage-given-contract",
        ),
        pytest.param(["parse", "src.f90", "--print-limit", "-1"], 2, "--print-limit must be >= 0", id="print-limit"),
        pytest.param(
            ["parse", "sources"], 2, "Input directory sources requires an explicit frontend", id="directory-language"
        ),
        pytest.param(
            ["parse", "solver.source"],
            2,
            "Cannot determine the input language for solver.source; pass --language fortran or --language c",
            id="unknown-suffix-language",
        ),
        pytest.param(
            ["parse", "src.f90", "--language", "c"],
            2,
            "Fortran input src.f90 is incompatible with --language c; pass --language fortran",
            id="fortran-input-with-c-frontend",
        ),
        pytest.param(
            ["parse", "src.f90", "-D", "=bad"], 2, "--define/-D requires a macro name before '='", id="define-name"
        ),
        pytest.param(
            ["parse", "src.f90", "--compiler", "cc", "--preprocess-template", "{source}"],
            2,
            "--preprocess-template requires --preprocessor-adapter command-template",
            id="template-without-adapter",
        ),
        pytest.param(
            ["contract.pyi"], 2, f"A .pyi wrapper build requires {_WRAPPER_NATIVE_INPUTS}", id="contract-without-native"
        ),
        pytest.param(
            ["solver.source", "--language", "fortran"],
            2,
            "A wrapper build expects recognized Fortran source suffixes or one semantic .pyi contract; "
            "unsupported input: solver.source",
            id="wrapper-unknown-suffix",
        ),
        pytest.param(
            ["src.f90", "--no-compile-input-sources"],
            2,
            f"--no-compile-input-sources requires {_WRAPPER_NATIVE_INPUTS}",
            id="no-compile-without-native",
        ),
        pytest.param(
            ["contract.pyi", "--no-compile-input-sources", "--native-objects", "impl.o"],
            2,
            "--no-compile-input-sources applies only to source-driven wrapper builds",
            id="no-compile-with-contract",
        ),
        pytest.param(
            ["contract.pyi", "--native-fortran-sources", "src.f90", "--assume-intent-in-scalars"],
            2,
            "a semantic .pyi contract already states its own results",
            id="contract-with-assumed-intent",
        ),
        pytest.param(["src.f90", "--jobs", "0"], 2, "jobs must be a positive integer", id="jobs-zero"),
        pytest.param(["src.f90", "--jobs", "many"], 2, "jobs must be a positive integer", id="jobs-non-integer"),
        pytest.param(
            ["src.f90", "--native-compile-flags='-O2"],
            1,
            "prik: error: Invalid --native-compile-flags value",
            id="unbalanced-native-flags",
        ),
        pytest.param(
            ["src.f90", "--wrapper-c-flags='-O0"],
            1,
            "prik: error: Invalid --wrapper-c-flags value",
            id="unbalanced-wrapper-flags",
        ),
        pytest.param(
            ["probe", "--language", "fortran", "--compiler", "gfortran", "-I", "inc", "--std", "f2018"],
            2,
            "add --expr to probe preprocessed expressions",
            id="probe-mapping-with-preprocessing-options",
        ),
        pytest.param(
            ["probe", "--language", "c", "--compiler", "cc", "--expr", "kind(1.0)"],
            2,
            "--expr is supported only for --language fortran",
            id="probe-expressions-for-c",
        ),
        pytest.param(
            ["--build-manifest", "fortran-build.json", "--out-dir", "elsewhere"],
            2,
            "replays its saved output directory",
            id="manifest-out-dir",
        ),
        pytest.param(
            ["--build-manifest", "fortran-build.json", "--language", "fortran"],
            2,
            "replays its saved input language",
            id="manifest-language",
        ),
        pytest.param(
            ["--build-manifest", "fortran-build.json", "-D", "USE_FAST=1"],
            2,
            "replays its saved preprocessing recipe",
            id="manifest-preprocessing",
        ),
        pytest.param(
            ["--build-manifest", "fortran-build.json", "--strict-wrapper-names"],
            2,
            "replays saved wrapper behavior",
            id="manifest-wrapper-behavior",
        ),
        pytest.param(
            ["--build-manifest", "fortran-build.json", "--native-library", "openblas"],
            2,
            "replays saved native inputs",
            id="manifest-native-inputs",
        ),
    ],
)
@pytest.mark.usefixtures("cli_inputs")
def test_cli_rejects_invalid_invocation_with_its_documented_diagnostic(
    capsys, argv: list[str], exit_code: int, message: str
):
    code, out, err = _invoke(argv, capsys)

    assert code == exit_code
    assert out == ""
    assert message in " ".join(err.split())


@pytest.fixture
def pipeline_calls(monkeypatch) -> list[tuple[str, tuple, dict]]:
    """Record the public pipeline owner each wrapper build reaches instead of compiling."""
    calls: list[tuple[str, tuple, dict]] = []
    result = types.SimpleNamespace(
        compiled=False,
        to_dict=lambda: {"module_name": "demo", "compiled": False, "output_dir": "out"},
    )
    for owner in ("build_fortran_extension", "build_pyi_extension", "build_pyi_extension_from_manifest"):
        monkeypatch.setattr(
            pipeline_build,
            owner,
            lambda *args, _owner=owner, **kwargs: calls.append((_owner, args, kwargs)) or result,
        )
    return calls


@pytest.mark.parametrize(
    ("argv", "owner", "positional", "expected"),
    [
        pytest.param(
            ["src.f90"],
            "build_fortran_extension",
            (["src.f90"],),
            {"compile_input_sources": True, "standard_logicals": True, "assume_intent_in_scalars": False},
            id="source-defaults",
        ),
        pytest.param(
            ["solver.F90", "--no-standard-logicals", "--assume-intent-in-scalars"],
            "build_fortran_extension",
            (["solver.F90"],),
            {"standard_logicals": False, "assume_intent_in_scalars": True},
            id="uppercase-source-interpretation-choices",
        ),
        pytest.param(
            ["sources", "--language", "fortran", "--no-compile-input-sources", "--native-objects", "libnative.so"],
            "build_fortran_extension",
            (["sources"],),
            {"compile_input_sources": False, "native_objects": ["libnative.so"]},
            id="source-directory-with-prebuilt-implementation",
        ),
        pytest.param(
            ["contract.pyi", "--native-objects", "native.o", "--compiler", "selected-ifx"],
            "build_pyi_extension",
            ("contract.pyi",),
            {"input_compiler": "selected-ifx", "input_c_compiler": None, "standard_logicals": True},
            id="contract-defers-c-driver-to-compiler-pair",
        ),
        pytest.param(
            ["iface.PYI", "--native-objects", "native.o", "--no-standard-logicals"],
            "build_pyi_extension",
            ("iface.PYI",),
            {"native_language": "fortran", "standard_logicals": False},
            id="uppercase-contract-logical-choice",
        ),
        pytest.param(
            [
                "--build-manifest",
                "fortran-build.json",
                "--out",
                "REPLAYED",
                "--compiler",
                "selected-driver",
                "-I",
                "include",
                "--json",
                "--verbose",
                "--no-color",
                "--debug",
            ],
            "build_pyi_extension_from_manifest",
            ("fortran-build.json",),
            {
                "output_name": "REPLAYED",
                "input_compiler": "selected-driver",
                "input_c_compiler": None,
                "include_dirs": ["include"],
                "verbose": 1,
            },
            id="manifest-accepts-documented-overrides",
        ),
        pytest.param(
            ["--build-manifest", "c-build.json", "--compiler", "selected-driver"],
            "build_pyi_extension_from_manifest",
            ("c-build.json",),
            {"input_compiler": None, "input_c_compiler": "selected-driver"},
            id="manifest-compiler-targets-recorded-c-language",
        ),
    ],
)
@pytest.mark.usefixtures("cli_inputs")
def test_cli_routes_wrapper_builds_to_the_public_pipeline_owner(
    pipeline_calls, capsys, argv, owner, positional, expected
):
    code, _out, _err = _invoke(argv, capsys)

    assert code == 0
    assert [(name, args) for name, args, _kwargs in pipeline_calls] == [(owner, positional)]
    kwargs = pipeline_calls[0][2]
    assert {name: kwargs[name] for name in expected} == expected


@pytest.mark.usefixtures("cli_inputs")
def test_cli_forwards_grouped_and_repeated_build_options_to_the_pipeline(pipeline_calls, capsys):
    """Multi-value options collect every value and grouped shell words split as a shell would."""
    code, out, _err = _invoke(
        [
            "contract.pyi",
            "--compiler",
            "selected-gfortran",
            "-I",
            "include",
            "-I",
            "vendor/include",
            "--native-fortran-sources",
            "source_one.f90",
            "source_two.f90",
            "--native-compile-flags=-O2 -DNAME='value with spaces'",
            "--jobs",
            "3",
            "--native-objects",
            "one.o",
            "two.a",
            "libsolver.so",
            "--native-library",
            "blas",
            "-llapack -lscalapack",
            "--native-link-item",
            "arg:-Wl,--start-group",
            "object:one.o",
            "arg:-Wl,--end-group",
            "--native-library-dir",
            "lib",
            "vendor/lib",
            "-I",
            "mods",
            "--wrapper-compiler-debug",
            "--wrapper-fortran-flags=-fno-range-check -g0",
            "--wrapper-c-flags=-O0 -g0",
            "--json",
        ],
        capsys,
    )

    assert code == 0
    assert json.loads(out)["module_name"] == "demo"
    ((owner, _args, kwargs),) = pipeline_calls
    assert owner == "build_pyi_extension"
    assert kwargs["input_compiler"] == "selected-gfortran"
    assert kwargs["native_include_dirs"] == ("include", "vendor/include", "mods")
    assert kwargs["native_fortran_sources"] == ["source_one.f90", "source_two.f90"]
    assert kwargs["native_fortran_flags"] == ("-O2", "-DNAME=value with spaces")
    assert kwargs["jobs"] == 3
    assert kwargs["native_objects"] == ["one.o", "two.a", "libsolver.so"]
    assert kwargs["native_libraries"] == ("blas", "-llapack", "-lscalapack")
    assert kwargs["native_link_items"] == (
        {"kind": "linker_argument", "argument": "-Wl,--start-group"},
        {"kind": "object", "path": "one.o"},
        {"kind": "linker_argument", "argument": "-Wl,--end-group"},
    )
    assert kwargs["native_library_dirs"] == ["lib", "vendor/lib"]
    assert kwargs["wrapper_compiler_debug"] is True
    assert kwargs["wrapper_fortran_flags"] == ("-fno-range-check", "-g0")
    assert kwargs["wrapper_c_flags"] == ("-O0", "-g0")


def test_top_level_help_is_concise_and_routes_to_detailed_help(capsys):
    code, top_help, _err = _invoke(["--help"], capsys)
    assert code == 0
    normalized = " ".join(top_help.split())
    for command in ("parse", "semantics", "generate", "probe"):
        assert f"python3 -m prik {command} --help" in top_help
    assert "python3 -m prik --help-build" in top_help
    assert prik_cli._HELP_DIVIDER in top_help
    # The first screen carries the options a first build needs, including one
    # that changes the default Python surface, and leaves advanced linking out.
    for option in ("--out", "--out-dir", "--compiler", "--native-library", "--jobs", "--assume-intent-in-scalars"):
        assert option in top_help
    assert "--native-library openblas passes -lopenblas to the linker" in normalized
    for advanced in ("--native-link-item", "--wrapper-c-flags"):
        assert advanced not in top_help

    code, build_help, _err = _invoke(["--help-build", "--no-color"], capsys)
    assert code == 0
    for advanced in ("--native-link-item", "--wrapper-c-flags"):
        assert advanced in build_help
    assert "Link NAME as -lNAME; for example, openblas adds -lopenblas" in " ".join(build_help.split())


@pytest.mark.parametrize(
    "parser_factory",
    [
        prik_cli._build_parser,
        prik_cli._parse_parser,
        prik_cli._semantics_parser,
        prik_cli._generate_parser,
        prik_cli._probe_parser,
    ],
    ids=["build", "parse", "semantics", "generate", "probe"],
)
def test_command_help_lists_every_supported_option(parser_factory):
    parser = parser_factory(["--help"])
    help_text = parser.format_help()
    option_strings = {
        option for action in parser._actions if action.help != argparse.SUPPRESS for option in action.option_strings
    }

    assert option_strings
    assert sorted(option for option in option_strings if option not in help_text) == []


@pytest.mark.parametrize(
    ("command", "expected", "excluded"),
    [
        ("parse", "Compiler used for preprocessing", "datatype measurement"),
        ("semantics", "preprocessing and datatype measurement", "wrapper build files"),
        ("generate", "source analysis and wrapper build files", "used to build the probe"),
        ("probe", "used to build the probe", "source preprocessing"),
    ],
)
def test_command_help_tailors_the_shared_compiler_option(capsys, command, expected, excluded):
    code, help_text, _err = _invoke([command, "--help", "--no-color"], capsys)
    normalized = " ".join(help_text.split())

    assert code == 0
    assert prik_cli._HELP_DIVIDER in help_text
    assert expected in normalized
    assert excluded not in normalized
    assert ("default: gfortran; cc with --language c" in normalized) is (command != "probe")
