#!/usr/bin/env python3
"""Measure clean end-to-end wrapper build time for x2py and f2py."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import subprocess  # nosec B404 - fixed module entrypoints benchmark local builds
import sys
from tempfile import TemporaryDirectory
import time
from typing import Literal

import numpy as np
import pyperf


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = BENCHMARK_ROOT / "results"
BLAS_SOURCE_ROOT = (
    REPOSITORY_ROOT
    / "tests"
    / "fortran"
    / "building_shared_library"
    / "end_to_end"
    / "real_libraries"
    / "blas"
    / "native"
)
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
COMPILE_FLAGS = "-O3 -march=native -mtune=native"
TOOLS = ("x2py", "f2py")
Tool = Literal["x2py", "f2py"]


@dataclass(frozen=True)
class BuildWorkload:
    """One source set and its required generated Python exports."""

    benchmark_name: str
    slug: str
    sources: tuple[Path, ...]
    namespace: tuple[str, ...]
    expected_exports: tuple[str, ...]


def build_workloads() -> tuple[BuildWorkload, ...]:
    """Return the maintained small-module and full-BLAS build workloads."""
    small_source = BENCHMARK_ROOT / "sources" / "kernels.f90"
    blas_sources = tuple(
        sorted(
            path for path in BLAS_SOURCE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES
        )
    )
    return (
        BuildWorkload(
            benchmark_name="build.small_module",
            slug="small_module",
            sources=(small_source,),
            namespace=("kernels",),
            expected_exports=("noop", "add_scalars", "increment_vector", "sum_matrix", "matrix_update"),
        ),
        BuildWorkload(
            benchmark_name="build.full_blas",
            slug="full_blas",
            sources=blas_sources,
            namespace=(),
            expected_exports=tuple(source.stem.lower() for source in blas_sources),
        ),
    )


def tool_order(first: Tool, round_index: int) -> tuple[Tool, Tool]:
    """Alternate which binding tool receives the first build in each round."""
    second: Tool = "f2py" if first == "x2py" else "x2py"
    return (first, second) if round_index % 2 == 0 else (second, first)


def module_name(tool: Tool, workload: BuildWorkload) -> str:
    """Return one isolated extension name for a tool and workload."""
    return f"bench_build_{tool}_{workload.slug}"


def build_command(
    tool: Tool,
    workload: BuildWorkload,
    workdir: Path,
    *,
    compiler: str,
) -> tuple[str, ...]:
    """Return the normal end-to-end build command for one timed sample."""
    sources = tuple(str(source.resolve()) for source in workload.sources)
    name = module_name(tool, workload)
    generated = workdir / "generated"
    if tool == "x2py":
        return (
            sys.executable,
            "-m",
            "x2py",
            *sources,
            "--out",
            name,
            "--out-dir",
            str(generated),
            "--compiler",
            compiler,
            f"--native-compile-flags={COMPILE_FLAGS}",
            f"--wrapper-fortran-flags={COMPILE_FLAGS}",
            f"--wrapper-c-flags={COMPILE_FLAGS}",
        )
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        "-m",
        name,
        *sources,
        "--build-dir",
        str(generated),
        f"--f77flags={COMPILE_FLAGS}",
        f"--f90flags={COMPILE_FLAGS}",
        f"--opt={COMPILE_FLAGS}",
    )


def _build_environment(compiler: str) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "CFLAGS": COMPILE_FLAGS,
            "FC": compiler,
            "F77": compiler,
            "F90": compiler,
            "FFLAGS": COMPILE_FLAGS,
            "F90FLAGS": COMPILE_FLAGS,
        }
    )
    return environment


def _failure_message(command: tuple[str, ...], result: subprocess.CompletedProcess[str]) -> str:
    stdout = result.stdout.rstrip() or "<empty>"
    stderr = result.stderr.rstrip() or "<empty>"
    return (
        f"Build command failed with exit code {result.returncode}:\n"
        f"{' '.join(command)}\nstdout:\n{stdout}\nstderr:\n{stderr}"
    )


def _verify_import(tool: Tool, workload: BuildWorkload, workdir: Path) -> None:
    name = module_name(tool, workload)
    namespace = repr(workload.namespace)
    expected = repr(workload.expected_exports)
    verification = (
        "import importlib\n"
        f"api = importlib.import_module({name!r})\n"
        f"for part in {namespace}:\n"
        "    api = getattr(api, part)\n"
        f"missing = [name for name in {expected} if not hasattr(api, name)]\n"
        "if missing:\n"
        "    raise RuntimeError(f'missing expected exports: {missing}')\n"
    )
    result = subprocess.run(  # nosec B603 - fixed interpreter validates generated local extensions
        (sys.executable, "-c", verification),
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(_failure_message((sys.executable, "-c", "<import verification>"), result))


def timed_build(tool: Tool, workload: BuildWorkload, workdir: Path, *, compiler: str) -> float:
    """Run one clean build and validate its import outside the timed interval."""
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True)
    command = build_command(tool, workload, workdir, compiler=compiler)
    started = time.perf_counter()
    result = subprocess.run(  # nosec B603 - command is assembled from fixed benchmark inputs
        command,
        cwd=workdir,
        env=_build_environment(compiler),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode:
        raise RuntimeError(_failure_message(command, result))
    _verify_import(tool, workload, workdir)
    return elapsed


def _write_result_suite(
    tool: Tool,
    workloads: tuple[BuildWorkload, ...],
    timings: dict[tuple[Tool, str], list[float]],
    *,
    runs: int,
    warmups: int,
    first: Tool,
    compiler: str,
    results_root: Path,
) -> Path:
    recorded_at = datetime.now().isoformat(sep=" ")
    benchmarks = []
    for workload in workloads:
        metadata = {
            "binding_tool": tool,
            "build_first_tool": first,
            "build_runs": runs,
            "build_scope": "clean source-to-extension generation, compilation, and linking",
            "build_warmups": warmups,
            "compiler": compiler,
            "date": recorded_at,
            "name": workload.benchmark_name,
            "numpy_version": np.__version__,
            "platform_details": platform.platform(),
            "source_count": len(workload.sources),
        }
        run = pyperf.Run(timings[(tool, workload.benchmark_name)], metadata=metadata, collect_metadata=True)
        benchmarks.append(pyperf.Benchmark([run]))
    suite = pyperf.BenchmarkSuite(benchmarks)
    results_root.mkdir(parents=True, exist_ok=True)
    path = results_root / f"{tool}-build.json"
    suite.dump(str(path), replace=True)
    return path


def run_build_benchmarks(
    *,
    runs: int,
    warmups: int,
    first: Tool,
    compiler: str,
    results_root: Path = RESULTS_ROOT,
) -> tuple[Path, Path]:
    """Measure every clean-build workload and write paired pyperf suites."""
    workloads = build_workloads()
    timings = {(tool, workload.benchmark_name): [] for tool in TOOLS for workload in workloads}
    with TemporaryDirectory(prefix="x2py-build-benchmark-") as temporary:
        temporary_root = Path(temporary)
        for round_index in range(warmups + runs):
            measured = round_index >= warmups
            phase = "run" if measured else "warm-up"
            phase_index = round_index - warmups + 1 if measured else round_index + 1
            phase_total = runs if measured else warmups
            order_index = phase_index - 1
            for workload in workloads:
                for tool in tool_order(first, order_index):
                    elapsed = timed_build(
                        tool,
                        workload,
                        temporary_root / workload.slug / tool,
                        compiler=compiler,
                    )
                    print(
                        f"{phase} {phase_index}/{phase_total}: {workload.benchmark_name} "
                        f"with {tool} took {elapsed:.3f} sec",
                        flush=True,
                    )
                    if measured:
                        timings[(tool, workload.benchmark_name)].append(elapsed)
    paths = tuple(
        _write_result_suite(
            tool,
            workloads,
            timings,
            runs=runs,
            warmups=warmups,
            first=first,
            compiler=compiler,
            results_root=results_root,
        )
        for tool in TOOLS
    )
    return paths[0], paths[1]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=6)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--first", choices=TOOLS, default="x2py")
    parser.add_argument("--compiler", default="gfortran")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_ROOT)
    args = parser.parse_args(argv)
    if args.runs < 2:
        parser.error("--runs must be at least 2")
    if args.warmups < 0:
        parser.error("--warmups must be non-negative")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    compiler = shutil.which(args.compiler)
    if compiler is None:
        print(f"cannot run build benchmark: compiler not found: {args.compiler}", file=sys.stderr)
        return 2
    if importlib.util.find_spec("numpy.f2py") is None:
        print("cannot run build benchmark: NumPy f2py is not installed", file=sys.stderr)
        return 2
    try:
        paths = run_build_benchmarks(
            runs=args.runs,
            warmups=args.warmups,
            first=args.first,
            compiler=compiler,
            results_root=args.results_dir,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"cannot run build benchmark: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote clean-build results to {paths[0]} and {paths[1]}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
