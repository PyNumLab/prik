from __future__ import annotations

from pathlib import Path
import subprocess

import pyperf

from benchmarks import build_time


def test_build_workloads_cover_small_module_and_complete_reference_blas() -> None:
    small, blas = build_time.build_workloads()

    assert small.slug == "small_module"
    assert len(small.sources) == 1
    assert len(small.expected_exports) == 5
    assert blas.slug == "full_blas"
    assert len(blas.sources) == 155
    assert len(blas.expected_exports) == 155
    assert set(blas.expected_exports) == {source.stem.lower() for source in blas.sources}
    assert [case.benchmark_name for case in build_time.build_cases()] == [
        "build.development.small_module",
        "build.development.full_blas",
        "build.optimized.small_module",
        "build.optimized.full_blas",
    ]


def test_build_commands_use_the_same_sources_and_complete_optimization_flags(tmp_path: Path) -> None:
    workload = build_time.BuildWorkload(
        slug="test",
        sources=(tmp_path / "first.f90", tmp_path / "second.f"),
        namespace=(),
        expected_exports=("first", "second"),
    )

    profile = build_time.BuildProfile("test", "Test", "-O0")
    case = build_time.BuildCase(profile, workload)
    prik = build_time.build_command(
        "prik",
        case,
        tmp_path / "prik",
        compiler="/opt/bin/gfortran",
        jobs=4,
    )
    f2py = build_time.build_command(
        "f2py",
        case,
        tmp_path / "f2py",
        compiler="/opt/bin/gfortran",
        jobs=4,
    )

    for source in workload.sources:
        assert str(source.resolve()) in prik
        assert str(source.resolve()) in f2py
    assert "--compiler" in prik
    assert "/opt/bin/gfortran" in prik
    assert prik[prik.index("--jobs") + 1] == "4"
    assert "--native-compile-flags=-O0" in prik
    assert "--wrapper-fortran-flags=-O0" in prik
    assert "--wrapper-c-flags=-O0" in prik
    assert "--f77flags=-O0" in f2py
    assert "--f90flags=-O0" in f2py
    assert "--opt=-O0" in f2py


def test_tool_order_alternates_between_rounds() -> None:
    assert build_time.tool_order("prik", 0) == ("prik", "f2py")
    assert build_time.tool_order("prik", 1) == ("f2py", "prik")
    assert build_time.tool_order("f2py", 0) == ("f2py", "prik")
    assert build_time.tool_order("f2py", 1) == ("prik", "f2py")


def test_timed_build_excludes_post_build_import_verification(tmp_path: Path, monkeypatch) -> None:
    workload = build_time.BuildWorkload("test", (), (), ())
    case = build_time.BuildCase(build_time.BUILD_PROFILES[0], workload)
    clock = iter((10.0, 12.5))
    verified = []

    monkeypatch.setattr(build_time.time, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(
        build_time.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(("compiler",), 0, "", ""),
    )
    monkeypatch.setattr(build_time, "_verify_import", lambda *args: verified.append(args))

    elapsed = build_time.timed_build(
        "prik",
        case,
        tmp_path / "build",
        compiler="/opt/bin/gfortran",
        jobs=2,
    )

    assert elapsed == 2.5
    assert len(verified) == 1


def test_run_build_benchmarks_excludes_warmups_and_writes_paired_pyperf_suites(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def fake_timed_build(tool, case, _workdir, *, compiler, jobs):
        assert compiler == "/opt/bin/gfortran"
        assert jobs == 4
        calls.append((tool, case.benchmark_name))
        return 1.0 if tool == "prik" else 2.0

    monkeypatch.setattr(build_time, "timed_build", fake_timed_build)
    monkeypatch.setenv("PRIK_BENCHMARK_CPU_MODEL", "Published Benchmark CPU")

    prik_path, f2py_path = build_time.run_build_benchmarks(
        runs=2,
        warmups=1,
        first="prik",
        compiler="/opt/bin/gfortran",
        jobs=4,
        results_root=tmp_path,
    )

    case_names = [case.benchmark_name for case in build_time.build_cases()]
    first_round = [(tool, name) for name in case_names for tool in ("prik", "f2py")]
    second_round = [(tool, name) for name in case_names for tool in ("prik", "f2py")]
    third_round = [(tool, name) for name in case_names for tool in ("f2py", "prik")]
    assert calls == [*first_round, *second_round, *third_round]
    assert prik_path.name == "prik-build.json"
    assert f2py_path.name == "f2py-build.json"
    prik_suite = pyperf.BenchmarkSuite.load(str(prik_path))
    f2py_suite = pyperf.BenchmarkSuite.load(str(f2py_path))
    assert prik_suite.get_benchmark_names() == case_names
    assert f2py_suite.get_benchmark_names() == case_names
    assert prik_suite.get_benchmark(case_names[0]).get_nvalue() == 2
    assert f2py_suite.get_benchmark(case_names[0]).get_nvalue() == 2
    assert prik_suite.get_metadata()["build_runs"] == 2
    assert f2py_suite.get_metadata()["build_warmups"] == 1
    assert prik_suite.get_metadata()["prik_build_jobs"] == 4
    assert prik_suite.get_metadata()["cpu_model_name"] == "Published Benchmark CPU"
    assert f2py_suite.get_metadata()["cpu_model_name"] == "Published Benchmark CPU"
