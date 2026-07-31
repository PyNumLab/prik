"""Compiler-derived Fortran scalar type and kind contracts."""

import json
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

import x2py.probes.fortran_types as fortran_type_probe
from x2py.semantics.fortran2ir import (
    collect_semantic_compile_time_requirements,
    fortran_module_to_semantic_module,
)
from x2py import parse_fortran_file as parse_fortran_source
from x2py.probes.fortran_types import (
    FortranTypeProbeRecipe,
    FortranTypeProbeReport,
    FortranTypeProbeError,
    _value_for_expression,
    build_fortran_type_probe_source,
    evaluate_fortran_type_facts,
    evaluate_fortran_type_requirements,
    fortran_type_probe_cache_key,
    fortran_type_probe_expressions,
    load_fortran_type_probe_report,
    probe_fortran_type_expressions,
    probe_fortran_type_expressions_cached,
)
from x2py.pipeline.preprocessing import PreprocessingConfig


_FC = shutil.which("gfortran") or shutil.which("f95")


def _required_fortran_compiler() -> str:
    assert _FC is not None, "the full Fortran pipeline test suite requires an available native Fortran compiler"
    return _FC


def test_fortran_type_probe_source_evaluates_integer_initialization_expressions():
    source = build_fortran_type_probe_source(["selected_real_kind(12)", "real64", "c_double"])

    assert "use, intrinsic :: iso_fortran_env, only: real64" in source
    assert "use, intrinsic :: iso_c_binding, only: c_double" in source
    assert "integer, parameter :: x2py_value_0 = selected_real_kind(12)" in source
    assert "integer, parameter :: x2py_value_1 = real64" in source
    assert "integer, parameter :: x2py_value_2 = c_double" in source
    assert '{"values":[' in source

    normalized = build_fortran_type_probe_source(["", "real64", "REAL64"])
    assert "integer, parameter :: x2py_value_0 = real64" in normalized
    assert "x2py_value_1" not in normalized


def test_fortran_type_probe_wraps_long_intrinsic_import_lists():
    source = build_fortran_type_probe_source(
        [
            "c_bool",
            "c_char",
            "c_double",
            "c_double_complex",
            "c_float",
            "c_float_complex",
            "c_int",
            "c_int16_t",
            "c_int32_t",
            "c_int64_t",
            "c_int8_t",
            "c_long",
            "c_long_double",
            "c_long_double_complex",
            "c_long_long",
            "c_short",
            "c_signed_char",
            "c_size_t",
        ]
    )

    assert "use, intrinsic :: iso_c_binding, only: &" in source
    assert "    c_bool, &" in source
    assert "    c_size_t\n" in source
    assert all(len(line) <= 120 for line in source.splitlines())


def test_x2py_public_api_lazily_exposes_type_probe_symbols_and_rejects_unknown_names():
    import x2py

    assert x2py.FortranTypeProbeError is FortranTypeProbeError
    assert x2py.FortranTypeProbeReport is FortranTypeProbeReport
    with pytest.raises(AttributeError, match="not_exported"):
        _ = x2py.not_exported


def test_fortran_type_probe_rejects_statement_injection():
    with pytest.raises(FortranTypeProbeError, match="single initialization expression"):
        build_fortran_type_probe_source(["selected_real_kind(12); stop"])


def test_fortran_type_probe_requires_an_explicit_compiler():
    with pytest.raises(FortranTypeProbeError, match="exact compiler"):
        probe_fortran_type_expressions(
            PreprocessingConfig(mode="compiler"),
            ["selected_real_kind(12)"],
        )


def test_fortran_type_probe_rejects_compile_database_and_validates_expression_forms():
    with pytest.raises(FortranTypeProbeError, match="does not consume compile_commands"):
        probe_fortran_type_expressions(
            PreprocessingConfig(mode="compiler", compiler="gfortran", compile_commands="compile_commands.json"),
            ["selected_real_kind(12)"],
        )
    with pytest.raises(FortranTypeProbeError, match="unsupported characters"):
        build_fortran_type_probe_source(["selected_real_kind(12)!"])
    with pytest.raises(FortranTypeProbeError, match="custom preprocessing templates"):
        probe_fortran_type_expressions(
            PreprocessingConfig(mode="compiler", compiler="gfortran", command_template="{compiler} {source}"),
            ["selected_real_kind(12)"],
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "must contain a JSON object"),
        ({}, "missing valid 'values'"),
        ({"values": {}, "recipe": {}, "source_text": "probe"}, "missing a valid 'recipe'"),
        ({"values": {}, "recipe": {"compiler": "gfortran"}}, "missing valid 'source_text'"),
    ],
)
def test_fortran_type_probe_report_loader_validates_reusable_reports(tmp_path, payload, message):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(FortranTypeProbeError, match=message):
        load_fortran_type_probe_report(report_path)


def test_fortran_type_probe_report_loader_reports_read_json_and_missing_expression_errors(tmp_path):
    with pytest.raises(FortranTypeProbeError, match="failed to read"):
        load_fortran_type_probe_report(tmp_path / "missing.json")

    report_path = tmp_path / "invalid.json"
    report_path.write_text("not json", encoding="utf-8")
    with pytest.raises(FortranTypeProbeError, match="contains invalid JSON"):
        load_fortran_type_probe_report(report_path)

    report = FortranTypeProbeReport(
        values={"selected_real_kind(12)": 8},
        recipe=FortranTypeProbeRecipe(
            compiler="gfortran",
            compile_argv=[],
            run_argv=[],
            expressions=["selected_real_kind(12)"],
        ),
        source_text="probe",
    )
    with pytest.raises(FortranTypeProbeError, match="missing required expressions"):
        evaluate_fortran_type_facts(
            PreprocessingConfig(),
            [{"base_type": "real", "kind": None, "expression": "storage_size(real(0.0))"}],
            report=report,
        )


def test_fortran_type_probe_cache_directory_precedence(monkeypatch, tmp_path):
    explicit = tmp_path / "explicit"
    assert fortran_type_probe._probe_cache_dir(explicit) == explicit

    monkeypatch.setenv("X2PY_CACHE_DIR", str(tmp_path / "x2py"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert fortran_type_probe._probe_cache_dir(None) == tmp_path / "x2py" / "fortran_type_probe"

    monkeypatch.delenv("X2PY_CACHE_DIR")
    assert fortran_type_probe._probe_cache_dir(None) == tmp_path / "xdg" / "x2py" / "fortran_type_probe"


def test_fortran_type_probe_cache_reuses_report_and_invalidates_for_flags(monkeypatch, tmp_path):
    fortran_type_probe._MEMORY_CACHE.clear()
    calls = []
    compiler = tmp_path / "fake-gfortran"
    compiler.write_text("first compiler identity", encoding="utf-8")
    expression = "storage_size(real(0.0))"
    report = FortranTypeProbeReport(
        values={expression: 32},
        recipe=FortranTypeProbeRecipe(
            compiler=str(compiler),
            compile_argv=[str(compiler)],
            run_argv=["probe"],
            expressions=[expression],
        ),
        source_text=build_fortran_type_probe_source([expression]),
    )

    def probe(config, expressions, *, runner=None):
        calls.append((config, expressions, runner))
        return report

    monkeypatch.setattr(fortran_type_probe, "probe_fortran_type_expressions", probe)
    config = PreprocessingConfig(mode="compiler", compiler=str(compiler), compiler_args=["-fdefault-real-8"])

    first = probe_fortran_type_expressions_cached(config, [expression], cache_dir=tmp_path)
    second = probe_fortran_type_expressions_cached(config, [expression], cache_dir=tmp_path)
    assert first is second
    assert len(calls) == 1

    fortran_type_probe._MEMORY_CACHE.clear()
    loaded = probe_fortran_type_expressions_cached(config, [expression], cache_dir=tmp_path)
    assert loaded.values == report.values
    assert len(calls) == 1

    changed = PreprocessingConfig(mode="compiler", compiler=str(compiler), compiler_args=["-fdefault-real-16"])
    assert fortran_type_probe_cache_key(changed, [expression]) != fortran_type_probe_cache_key(config, [expression])
    assert fortran_type_probe_cache_key(config, ["storage_size(int(0))"]) != fortran_type_probe_cache_key(
        config, [expression]
    )
    probe_fortran_type_expressions_cached(changed, [expression], cache_dir=tmp_path)
    assert len(calls) == 2

    probe_fortran_type_expressions_cached(config, [expression], cache_dir=tmp_path, refresh=True)
    assert len(calls) == 3


def test_fortran_type_probe_expressions_extracts_semantic_requirement_inputs():
    requirements = [
        {"code": "parameter_value", "symbol": "blank", "expression": " "},
        {"code": "parameter_value", "symbol": "rk", "expression": "selected_real_kind(12)"},
        {"code": "unsupported_kind", "symbol": "x", "expression": "selected_real_kind(12)"},
        {"code": "parameter_value", "symbol": "ik", "expression": "selected_int_kind(9)"},
    ]

    assert fortran_type_probe_expressions(requirements) == [
        "selected_real_kind(12)",
        "selected_int_kind(9)",
    ]


def test_fortran_type_probe_report_resolves_only_matching_parameter_requirements():
    report = FortranTypeProbeReport(
        values={"Selected_Real_Kind(12)": 8},
        recipe=FortranTypeProbeRecipe(
            compiler="gfortran",
            compile_argv=[],
            run_argv=[],
            expressions=["Selected_Real_Kind(12)"],
        ),
        source_text="",
    )
    requirements = [
        {"code": "parameter_value", "symbol": "rk", "expression": "selected_real_kind(12)"},
        {"code": "unsupported_kind", "symbol": "not_added", "expression": "selected_real_kind(12)"},
        {"code": "parameter_value", "symbol": "", "expression": "selected_real_kind(12)"},
        {"code": "parameter_value", "symbol": "missing", "expression": "missing_expr"},
    ]

    assert report.to_compile_time_values() == {"Selected_Real_Kind(12)": 8}
    assert report.to_compile_time_values(requirements)["rk"] == 8
    assert "not_added" not in report.to_compile_time_values(requirements)
    assert _value_for_expression({}, "not_present") is None
    assert evaluate_fortran_type_requirements(PreprocessingConfig(mode="compiler"), []) == {}


@pytest.mark.parametrize(
    ("results", "message"),
    [
        ([OSError("missing")], "failed to run Fortran type probe compiler"),
        ([SimpleNamespace(returncode=1, stderr="compile failed")], "compilation failed"),
        ([SimpleNamespace(returncode=0, stderr=""), OSError("cannot execute")], "failed to execute"),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=2, stderr="run failed")],
            "execution failed",
        ),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=0, stdout="not json", stderr="")],
            "invalid JSON",
        ),
        (
            [SimpleNamespace(returncode=0, stderr=""), SimpleNamespace(returncode=0, stdout="{}", stderr="")],
            "missing 'values'",
        ),
        (
            [
                SimpleNamespace(returncode=0, stderr=""),
                SimpleNamespace(returncode=0, stdout='{"values":[]}', stderr=""),
            ],
            "count does not match",
        ),
        (
            [
                SimpleNamespace(returncode=0, stderr=""),
                SimpleNamespace(returncode=0, stdout='{"values":["bad"]}', stderr=""),
            ],
            "is not an integer",
        ),
    ],
)
def test_fortran_type_probe_reports_compiler_and_runner_failures(monkeypatch, results, message):
    responses = iter(results)

    def run(*_args, **_kwargs):
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(fortran_type_probe.subprocess, "run", run)
    with pytest.raises(FortranTypeProbeError, match=message):
        probe_fortran_type_expressions(
            PreprocessingConfig(mode="compiler", compiler="gfortran"),
            ["selected_real_kind(12)"],
            runner=["runner"],
        )


def test_fortran_type_probe_accepts_runner_and_cli_validates_macro_names(monkeypatch):
    responses = iter(
        [
            SimpleNamespace(returncode=0, stderr=""),
            SimpleNamespace(returncode=0, stdout='{"values":[8]}', stderr=""),
        ]
    )
    monkeypatch.setattr(fortran_type_probe.subprocess, "run", lambda *_args, **_kwargs: next(responses))
    report = probe_fortran_type_expressions(
        PreprocessingConfig(mode="compiler", compiler="gfortran"),
        ["selected_real_kind(12)"],
        runner=["emulator"],
    )
    assert report.recipe.run_argv[0] == "emulator"

    with pytest.raises(SystemExit):
        fortran_type_probe.main(["--compiler", "gfortran", "-D", "=bad"])
    with pytest.raises(SystemExit):
        fortran_type_probe.main(["--compiler", "gfortran", "-U", "=bad"])


def test_fortran_type_probe_reports_values_from_native_compiler():
    compiler = _required_fortran_compiler()
    report = probe_fortran_type_expressions(
        PreprocessingConfig(mode="compiler", compiler=compiler),
        ["selected_int_kind(9)", "selected_real_kind(12)", "kind(1.0d0)"],
    )

    assert report.values["selected_int_kind(9)"] > 0
    assert report.values["selected_real_kind(12)"] > 0
    assert report.values["kind(1.0d0)"] > 0
    assert report.recipe.compiler == compiler
    assert "-cpp" in report.recipe.compile_argv
    assert "selected_real_kind(12)" in report.source_text


def test_fortran_type_probe_carries_target_relevant_user_flags(tmp_path):
    compiler = _required_fortran_compiler()
    include_dir = tmp_path / "include"
    include_dir.mkdir()

    report = probe_fortran_type_expressions(
        PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            include_dirs=[str(include_dir)],
            defines=["X2PY_FEATURE=1"],
            undefs=["X2PY_OLD_FEATURE"],
            std="f2008",
            compiler_args=["-fno-range-check"],
        ),
        ["selected_real_kind(12)"],
    )

    argv = report.recipe.compile_argv
    assert "-cpp" in argv
    assert f"-I{include_dir}" in argv
    assert "-DX2PY_FEATURE=1" in argv
    assert "-UX2PY_OLD_FEATURE" in argv
    assert "-std=f2008" in argv
    assert "-fno-range-check" in argv
    assert report.recipe.requested_standard == "f2008"
    assert report.recipe.include_dirs == [str(include_dir)]
    assert report.recipe.defines == ["X2PY_FEATURE=1"]
    assert report.recipe.undefs == ["X2PY_OLD_FEATURE"]
    assert report.recipe.compiler_args == ["-fno-range-check"]


def test_fortran_type_probe_maps_compiler_storage_facts():
    compiler = _required_fortran_compiler()
    requirements = [
        {
            "base_type": "integer",
            "kind": None,
            "expression": "storage_size(int(0))",
        },
        {
            "base_type": "real",
            "kind": None,
            "expression": "storage_size(real(0.0))",
        },
    ]

    facts = evaluate_fortran_type_facts(
        PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            compiler_args=["-fdefault-integer-8", "-fdefault-real-8"],
        ),
        requirements,
    )

    assert facts[("integer", None)]["bits"] == 64
    assert facts[("real", None)]["bits"] == 64


def test_fortran_type_probe_evaluates_collected_semantic_requirements():
    compiler = _required_fortran_compiler()
    parsed = parse_fortran_source(
        """
module solver_mod
  integer, parameter :: rk = selected_real_kind(12)
contains
subroutine scale(x)
  real(kind=rk), intent(inout) :: x
end subroutine scale
end module solver_mod
"""
    )
    requirements = collect_semantic_compile_time_requirements(parsed)

    values = evaluate_fortran_type_requirements(
        PreprocessingConfig(mode="compiler", compiler=compiler),
        requirements,
    )
    module = fortran_module_to_semantic_module(parsed, compile_time_values=values)

    assert values["rk"] == values["selected_real_kind(12)"]
    assert module.functions[0].arguments[0].semantic_type.name == "Float64"


def test_fortran_type_probe_module_cli_emits_json_for_semantic_input(tmp_path):
    compiler = _required_fortran_compiler()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py.probes.fortran_types",
            "--compiler",
            compiler,
            "--expr",
            "selected_int_kind(9)",
            "--expr",
            "selected_real_kind(12)",
            "--cache-dir",
            str(tmp_path / "cache"),
            "--refresh",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["values"]["selected_int_kind(9)"] > 0
    assert payload["values"]["selected_real_kind(12)"] > 0
    assert payload["recipe"]["compiler"] == compiler
    assert payload["source_text"].startswith("program x2py_fortran_type_probe")


def test_x2py_semantics_cli_evaluates_collected_fortran_type_requirements(tmp_path):
    compiler = _required_fortran_compiler()
    source = tmp_path / "solver.f90"
    source.write_text(
        """
module solver_mod
  integer, parameter :: rk = selected_real_kind(12)
contains
subroutine scale(x)
  real(kind=rk), intent(inout) :: x
end subroutine scale
end module solver_mod
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "semantics",
            str(source),
            "--compiler",
            compiler,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    semantic_type = payload[str(source)]["semantic_modules"][0]["functions"][0]["arguments"][0]["semantic_type"]
    assert semantic_type["name"] == "Float64"


def test_x2py_semantics_cli_uses_compiler_dependent_default_fortran_kinds(tmp_path):
    compiler = _required_fortran_compiler()
    source = tmp_path / "defaults.f90"
    source.write_text(
        """
module defaults
  integer :: count
  real :: scale
  complex :: value
  double precision :: double_scale
  double complex :: double_value
  complex*16 :: legacy_value
end module defaults
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "semantics",
            str(source),
            "--compiler",
            compiler,
            "--compiler-arg=-fdefault-integer-8",
            "--compiler-arg=-fdefault-real-8",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    variables = payload[str(source)]["semantic_modules"][0]["variables"]
    semantic_types = {variable["name"]: variable["semantic_type"] for variable in variables}
    assert semantic_types["count"]["name"] == "Int64"
    assert semantic_types["scale"]["name"] == "Float64"
    assert semantic_types["value"]["name"] == "Complex128"
    assert semantic_types["double_scale"]["name"] == "Float128"
    assert semantic_types["double_value"]["name"] == "Complex256"
    assert semantic_types["legacy_value"]["name"] == "Complex128"
    assert semantic_types["scale"]["metadata"]["fortran_type_fact_source"] == "compiler_probe"
    assert semantic_types["legacy_value"]["metadata"]["fortran_type_fact_source"] == "legacy_star_storage"
