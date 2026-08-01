from __future__ import annotations

from pathlib import Path
import subprocess

import pyperf

from benchmarks import build_time


def test_build_workloads_cover_small_module_and_complete_reference_blas() -> None:
    small, blas = build_time.build_workloads()

    assert small.benchmark_name == "build.small_module"
    assert len(small.sources) == 1
    assert len(small.expected_exports) == 5
    assert blas.benchmark_name == "build.full_blas"
    assert len(blas.sources) == 155
    assert len(blas.expected_exports) == 155
    assert set(blas.expected_exports) == {source.stem.lower() for source in blas.sources}


def test_build_commands_use_the_same_sources_and_complete_optimization_flags(tmp_path: Path) -> None:
    workload = build_time.BuildWorkload(
        benchmark_name="build.test",
        slug="test",
        sources=(tmp_path / "first.f90", tmp_path / "second.f"),
        namespace=(),
        expected_exports=("first", "second"),
    )

    x2py = build_time.build_command("x2py", workload, tmp_path / "x2py", compiler="/opt/bin/gfortran")
    f2py = build_time.build_command("f2py", workload, tmp_path / "f2py", compiler="/opt/bin/gfortran")

    for source in workload.sources:
        assert str(source.resolve()) in x2py
        assert str(source.resolve()) in f2py
    assert "--compiler" in x2py
    assert "/opt/bin/gfortran" in x2py
    assert f"--native-compile-flags={build_time.COMPILE_FLAGS}" in x2py
    assert f"--wrapper-fortran-flags={build_time.COMPILE_FLAGS}" in x2py
    assert f"--wrapper-c-flags={build_time.COMPILE_FLAGS}" in x2py
    assert f"--f77flags={build_time.COMPILE_FLAGS}" in f2py
    assert f"--f90flags={build_time.COMPILE_FLAGS}" in f2py
    assert f"--opt={build_time.COMPILE_FLAGS}" in f2py


def test_tool_order_alternates_between_rounds() -> None:
    assert build_time.tool_order("x2py", 0) == ("x2py", "f2py")
    assert build_time.tool_order("x2py", 1) == ("f2py", "x2py")
    assert build_time.tool_order("f2py", 0) == ("f2py", "x2py")
    assert build_time.tool_order("f2py", 1) == ("x2py", "f2py")


def test_timed_build_excludes_post_build_import_verification(tmp_path: Path, monkeypatch) -> None:
    workload = build_time.BuildWorkload("build.test", "test", (), (), ())
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
        "x2py",
        workload,
        tmp_path / "build",
        compiler="/opt/bin/gfortran",
    )

    assert elapsed == 2.5
    assert len(verified) == 1


def test_run_build_benchmarks_excludes_warmups_and_writes_paired_pyperf_suites(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def fake_timed_build(tool, workload, _workdir, *, compiler):
        assert compiler == "/opt/bin/gfortran"
        calls.append((tool, workload.benchmark_name))
        return 1.0 if tool == "x2py" else 2.0

    monkeypatch.setattr(build_time, "timed_build", fake_timed_build)

    x2py_path, f2py_path = build_time.run_build_benchmarks(
        runs=2,
        warmups=1,
        first="x2py",
        compiler="/opt/bin/gfortran",
        results_root=tmp_path,
    )

    assert calls[:4] == [
        ("x2py", "build.small_module"),
        ("f2py", "build.small_module"),
        ("x2py", "build.full_blas"),
        ("f2py", "build.full_blas"),
    ]
    assert calls[4:8] == [
        ("x2py", "build.small_module"),
        ("f2py", "build.small_module"),
        ("x2py", "build.full_blas"),
        ("f2py", "build.full_blas"),
    ]
    assert calls[8:12] == [
        ("f2py", "build.small_module"),
        ("x2py", "build.small_module"),
        ("f2py", "build.full_blas"),
        ("x2py", "build.full_blas"),
    ]
    assert x2py_path.name == "x2py-build.json"
    assert f2py_path.name == "f2py-build.json"
    x2py_suite = pyperf.BenchmarkSuite.load(str(x2py_path))
    f2py_suite = pyperf.BenchmarkSuite.load(str(f2py_path))
    assert x2py_suite.get_benchmark_names() == ["build.small_module", "build.full_blas"]
    assert f2py_suite.get_benchmark_names() == ["build.small_module", "build.full_blas"]
    assert x2py_suite.get_benchmark("build.small_module").get_nvalue() == 2
    assert f2py_suite.get_benchmark("build.small_module").get_nvalue() == 2
    assert x2py_suite.get_metadata()["build_runs"] == 2
    assert f2py_suite.get_metadata()["build_warmups"] == 1
