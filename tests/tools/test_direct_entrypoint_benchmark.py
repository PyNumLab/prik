"""Evidence for the separate direct-entrypoint benchmark cohort."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace

import numpy as np
import pyperf
import pytest

from benchmarks import direct_benchmark, direct_build_time


def _report(route: direct_benchmark.Route) -> dict[str, object]:
    adapters = ("generated/bind_c_wrapper.f90",) if route == "prik-adapted" else ()
    report = {
        "route": direct_benchmark.route_action(route),
        "wrapper_mode": direct_benchmark.wrapper_mode(route),
        "native_source": direct_benchmark.native_source(route).name,
        "generated_fortran_adapter_sources": adapters,
        "f2py_fortran_wrapper_sources": (),
        "generated_c_sources": ("generated/wrapper.c",),
        "compiled_objects": ("generated/native.o", "generated/wrapper.o"),
        "linked_extension": f"generated/{direct_benchmark.module_name(route)}.so",
    }
    if route != "prik-adapted":
        report.update(
            {
                "binding_direct_symbol_references": direct_benchmark.DIRECT_SYMBOLS,
                "native_direct_symbol_definitions": direct_benchmark.DIRECT_SYMBOLS,
                "linked_direct_symbol_definitions": direct_benchmark.DIRECT_SYMBOLS,
            }
        )
    return report


def test_direct_pair_uses_one_native_source_equal_labels_and_matching_flags(tmp_path: Path) -> None:
    prik = direct_benchmark.build_command("prik-direct", tmp_path / "prik", compiler="/opt/gfortran", jobs=4)
    f2py = direct_benchmark.build_command("f2py-direct", tmp_path / "f2py", compiler="/opt/gfortran", jobs=4)
    source = str(direct_benchmark.DIRECT_SOURCE.resolve())

    assert source in prik
    assert source in f2py
    assert "--no-wrap-functions" in f2py
    assert "--skip-empty-wrappers" in f2py
    assert str(direct_benchmark.DIRECT_SIGNATURE.resolve()) in f2py
    assert all(direct_benchmark.OPTIMIZED_FLAGS in argument for argument in prik[-3:])
    assert all(direct_benchmark.OPTIMIZED_FLAGS in argument for argument in f2py[-3:])

    native = direct_benchmark.DIRECT_SOURCE.read_text(encoding="utf-8").casefold()
    for name in ("noop", "add_scalars", "add_scalars_out"):
        assert f"{name}(" in native
        assert "bind(c)" in native[native.index(f"{name}(") : native.index(f"{name}(") + 100]
    assert 'name="' not in native


@pytest.mark.parametrize("route", direct_benchmark.ROUTES)
def test_direct_correctness_preserves_each_tools_natural_result_type(route) -> None:
    expected_type = float if route == "f2py-direct" else np.float64
    api = SimpleNamespace(
        noop=lambda: None,
        add_scalars=lambda _a, _b: expected_type(4.0),
        add_scalars_out=lambda _a, _b: expected_type(4.0),
    )

    direct_benchmark.check_api(api, route)
    assert direct_benchmark.natural_result_type(route) == (
        "builtins.float" if route == "f2py-direct" else "numpy.float64"
    )


def test_artifact_preflight_rejects_wrappers_and_proves_direct_linkage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def symbols(path: Path) -> dict[str, str]:
        kind = "U" if path.name.endswith(("_wrapper.o", "module.o")) else "T"
        return dict.fromkeys(direct_benchmark.DIRECT_SYMBOLS, kind)

    monkeypatch.setattr(direct_benchmark, "_global_symbols", symbols)
    direct = tmp_path / "prik-direct"
    direct.mkdir()
    (direct / "bench_prik_direct.so").touch()
    (direct / "bench_prik_direct_wrapper.c").touch()
    (direct / "bench_prik_direct_wrapper.o").touch()
    (direct / "direct_kernels.o").touch()
    report = direct_benchmark.artifact_report("prik-direct", direct)
    assert report["generated_fortran_adapter_sources"] == ()
    assert report["binding_direct_symbol_references"] == direct_benchmark.DIRECT_SYMBOLS
    assert report["linked_direct_symbol_definitions"] == direct_benchmark.DIRECT_SYMBOLS

    (direct / "bind_c_bench_prik_direct_wrapper.f90").touch()
    with pytest.raises(RuntimeError, match="generated user adapters"):
        direct_benchmark.artifact_report("prik-direct", direct)

    f2py = tmp_path / "f2py-direct"
    f2py.mkdir()
    (f2py / "bench_f2py_direct.so").touch()
    (f2py / "bench_f2py_directmodule.c").touch()
    (f2py / "bench_f2py_directmodule.o").touch()
    (f2py / "direct_kernels.o").touch()
    (f2py / "bench_f2py_direct-f2pywrappers.f90").touch()
    with pytest.raises(RuntimeError, match="generated Fortran wrapper sources"):
        direct_benchmark.artifact_report("f2py-direct", f2py)

    (f2py / "bench_f2py_direct-f2pywrappers.f90").unlink()
    report = direct_benchmark.artifact_report("f2py-direct", f2py)
    assert report["f2py_fortran_wrapper_sources"] == ()
    assert report["native_direct_symbol_definitions"] == direct_benchmark.DIRECT_SYMBOLS


def test_timed_direct_build_keeps_import_and_artifact_checks_outside_timer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = iter((10.0, 12.5))
    verified = []
    monkeypatch.setattr(direct_build_time.time, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(
        direct_build_time.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(("compiler",), 0, "", ""),
    )
    monkeypatch.setattr(
        direct_build_time,
        "verify_build",
        lambda route, workdir: verified.append((route, workdir)) or _report(route),
    )

    elapsed, report = direct_build_time.timed_build("prik-direct", tmp_path / "build", compiler="/opt/gfortran", jobs=2)

    assert elapsed == 2.5
    assert verified == [("prik-direct", tmp_path / "build")]
    assert report["route"] == "direct_c_abi"


def test_direct_build_results_are_separate_and_record_route_membership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[direct_benchmark.Route] = []
    reports = {route: _report(route) for route in direct_benchmark.ROUTES}
    monkeypatch.setattr(
        direct_build_time,
        "preflight",
        lambda **_kwargs: reports,
    )

    def fake_timed(route, _workdir, *, compiler, jobs):
        assert compiler == "/opt/gfortran"
        assert jobs == 4
        calls.append(route)
        return (1.0 if route == "prik-direct" else 2.0), reports[route]

    monkeypatch.setattr(direct_build_time, "timed_build", fake_timed)
    paths = direct_build_time.run_benchmarks(
        runs=2,
        warmups=1,
        first="prik",
        compiler="/opt/gfortran",
        jobs=4,
        results_root=tmp_path,
    )

    assert [path.name for path in paths] == [
        "prik-direct-build.json",
        "f2py-direct-build.json",
        "prik-adapted-build.json",
    ]
    assert calls == [
        "prik-direct",
        "f2py-direct",
        "prik-adapted",
        "prik-direct",
        "f2py-direct",
        "prik-adapted",
        "prik-adapted",
        "f2py-direct",
        "prik-direct",
    ]
    for route, path in zip(direct_benchmark.ROUTES, paths, strict=True):
        suite = pyperf.BenchmarkSuite.load(str(path))
        assert suite.get_benchmark_names() == ["direct.build.optimized.small"]
        assert suite.get_metadata()["binding_tool"] == route
        assert suite.get_metadata()["route"] == direct_benchmark.route_action(route)
        assert suite.get_metadata()["benchmark_cohort"] == "direct_entrypoint"
        assert suite.get_metadata()["artifact_membership"]


def test_direct_runtime_uses_identical_cases_and_preflight_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {"names": []}

    class FakeRunner:
        def __init__(self, **kwargs):
            observed.update(kwargs)

        def timeit(self, name: str, **_kwargs) -> None:
            observed["names"].append(name)

    api = SimpleNamespace(
        noop=lambda: None,
        add_scalars=lambda a, b: np.float64(a + b),
        add_scalars_out=lambda a, b: np.float64(a + b),
    )
    report_path = tmp_path / "preflight.json"
    report_path.write_text(json.dumps({"prik-direct": _report("prik-direct")}), encoding="utf-8")
    monkeypatch.syspath_prepend(str(Path("benchmarks").resolve()))
    monkeypatch.setenv("PRIK_DIRECT_BENCHMARK_ROUTE", "prik-direct")
    monkeypatch.setenv("PRIK_DIRECT_ORDER_PASS", "forward")
    monkeypatch.setenv("PRIK_DIRECT_PREFLIGHT_REPORT", str(report_path))
    monkeypatch.setattr(importlib, "import_module", lambda _name: api)
    monkeypatch.setattr(pyperf, "Runner", FakeRunner)

    runpy.run_path(Path("benchmarks/direct_runtime.py"), run_name="__main__")

    assert observed["processes"] == 16
    assert observed["values"] == 4
    assert observed["metadata"]["route"] == "direct_c_abi"
    assert observed["metadata"]["wrapper_mode"] == "python_c_binding;no_user_fortran_adapter"
    assert observed["metadata"]["artifact_membership"]
    assert observed["metadata"]["natural_result_type"] == "numpy.float64"
    assert observed["names"] == [
        "direct.call.noop",
        "direct.call.scalar_function",
        "direct.call.scalar_subroutine",
    ]


def test_run_and_workflows_keep_direct_results_out_of_default_population() -> None:
    run_script = Path("benchmarks/run.sh").read_text(encoding="utf-8")
    generator = Path("tools/generate_performance_docs.py").read_text(encoding="utf-8")
    workflows = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (".github/workflows/docs.yml", ".github/workflows/merge-validation.yml")
    )

    assert "python3 direct_preflight.py" in run_script
    assert "python3 direct_build_time.py" in run_script
    assert "direct_runtime.py" in run_script
    assert '--output "results/$binding_tool.json"' in run_script
    assert '--output "results/$direct_route.json"' in run_script
    assert "prik-adapted.json" in run_script
    assert "direct_runtime_passes=(forward reverse)" in run_script
    assert "direct_routes=(prik-adapted f2py-direct prik-direct)" in run_script
    assert "direct" not in generator.partition("DEFAULT_F2PY_RESULTS")[0]
    assert workflows.count("name: direct-entrypoint-preflight") == 2
    assert workflows.count("path: benchmarks/build/direct-runtime") == 2
    for name in (
        "f2py-direct.json",
        "prik-direct.json",
        "prik-adapted.json",
        "f2py-direct-build.json",
        "prik-direct-build.json",
        "prik-adapted-build.json",
    ):
        assert workflows.count(name) == 4
