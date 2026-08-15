#!/usr/bin/env python3
"""Measure clean small builds for direct PRIK/f2py and adapted PRIK routes."""

from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import platform
import shutil
import subprocess  # nosec B404 - fixed local benchmark build commands
import sys
from tempfile import TemporaryDirectory
import time

import numpy as np
import pyperf

if __package__:
    from .direct_benchmark import (
        BENCHMARK_ROOT,
        OPTIMIZED_FLAGS,
        ROUTES,
        Route,
        build_command,
        build_environment,
        compact_artifact_membership,
        failure_message,
        route_action,
        run_build,
        verify_build,
        wrapper_mode,
    )
else:
    from direct_benchmark import (
        BENCHMARK_ROOT,
        OPTIMIZED_FLAGS,
        ROUTES,
        Route,
        build_command,
        build_environment,
        compact_artifact_membership,
        failure_message,
        route_action,
        run_build,
        verify_build,
        wrapper_mode,
    )


RESULTS_ROOT = BENCHMARK_ROOT / "results"


def available_jobs() -> int:
    """Return the compiler-process budget available to the current job."""
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def route_order(first: str, round_index: int) -> tuple[Route, Route, Route]:
    """Reverse all three routes so every pair receives both relative orders."""
    direct: tuple[Route, Route] = ("prik-direct", "f2py-direct") if first == "prik" else ("f2py-direct", "prik-direct")
    if round_index % 2:
        return "prik-adapted", direct[1], direct[0]
    return direct[0], direct[1], "prik-adapted"


def timed_build(route: Route, workdir: Path, *, compiler: str, jobs: int) -> tuple[float, dict[str, object]]:
    """Time generation/compilation/linking, then verify artifacts and behavior."""
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True)
    command = build_command(route, workdir, compiler=compiler, jobs=jobs)
    started = time.perf_counter()
    result = subprocess.run(  # nosec B603 - command uses fixed benchmark inputs
        command,
        cwd=workdir,
        env=build_environment(compiler),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode:
        raise RuntimeError(failure_message(command, result))
    report = verify_build(route, workdir)
    return elapsed, report


def preflight(*, compiler: str, jobs: int, root: Path) -> dict[Route, dict[str, object]]:
    """Prove correctness and physical membership before any measured round."""
    reports: dict[Route, dict[str, object]] = {}
    for route_value in ROUTES:
        route: Route = route_value
        workdir = root / route
        run_build(route, workdir, compiler=compiler, jobs=jobs)
        reports[route] = verify_build(route, workdir)
    return reports


def _write_suite(
    route: Route,
    values: list[float],
    report: dict[str, object],
    *,
    runs: int,
    warmups: int,
    first: str,
    compiler: str,
    jobs: int,
    results_root: Path,
) -> Path:
    """Write one route-specific pyperf build suite with preflight membership."""
    metadata = {
        "artifact_membership": compact_artifact_membership(report),
        "benchmark_cohort": "direct_entrypoint",
        "binding_tool": route,
        "build_first_tool": first,
        "build_order_protocol": "balanced_three_route_forward_reverse",
        "build_runs": runs,
        "build_scope": "clean small source-to-extension generation, compilation, and linking",
        "build_warmups": warmups,
        "compile_flags": OPTIMIZED_FLAGS,
        "compiler": compiler,
        "date": datetime.now().isoformat(sep=" "),
        "name": "direct.build.optimized.small",
        "native_source": report["native_source"],
        "numpy_version": np.__version__,
        "platform_details": platform.platform(),
        "prik_build_jobs": jobs,
        "route": route_action(route),
        "wrapper_mode": wrapper_mode(route),
    }
    if cpu_model := os.environ.get("PRIK_BENCHMARK_CPU_MODEL"):
        metadata["cpu_model_name"] = cpu_model
    run = pyperf.Run(values, metadata=metadata, collect_metadata=True)
    suite = pyperf.BenchmarkSuite([pyperf.Benchmark([run])])
    results_root.mkdir(parents=True, exist_ok=True)
    path = results_root / f"{route}-build.json"
    suite.dump(str(path), replace=True)
    return path


def run_benchmarks(
    *,
    runs: int,
    warmups: int,
    first: str,
    compiler: str,
    jobs: int,
    results_root: Path = RESULTS_ROOT,
) -> tuple[Path, Path, Path]:
    """Run preflight and measured clean builds without touching default results."""
    values: dict[Route, list[float]] = {route: [] for route in ROUTES}
    reports: dict[Route, dict[str, object]]
    with TemporaryDirectory(prefix="prik-direct-build-benchmark-") as temporary:
        root = Path(temporary)
        reports = preflight(compiler=compiler, jobs=jobs, root=root / "preflight")
        for round_index in range(warmups + runs):
            measured = round_index >= warmups
            phase = "run" if measured else "warm-up"
            phase_index = round_index - warmups + 1 if measured else round_index + 1
            phase_total = runs if measured else warmups
            order_index = phase_index - 1
            for route in route_order(first, order_index):
                elapsed, report = timed_build(
                    route,
                    root / "timed" / route,
                    compiler=compiler,
                    jobs=jobs,
                )
                if compact_artifact_membership(report) != compact_artifact_membership(reports[route]):
                    raise RuntimeError(f"Artifact membership changed after {route!r} preflight")
                print(f"{phase} {phase_index}/{phase_total}: {route} took {elapsed:.3f} sec", flush=True)
                if measured:
                    values[route].append(elapsed)
    return tuple(
        _write_suite(
            route,
            values[route],
            reports[route],
            runs=runs,
            warmups=warmups,
            first=first,
            compiler=compiler,
            jobs=jobs,
            results_root=results_root,
        )
        for route in ROUTES
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=4)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--first", choices=("prik", "f2py"), default="prik")
    parser.add_argument("--compiler", default="gfortran")
    parser.add_argument("--jobs", type=int, default=None)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_ROOT)
    args = parser.parse_args(argv)
    if args.runs < 2:
        parser.error("--runs must be at least 2")
    if args.warmups < 0:
        parser.error("--warmups must be non-negative")
    if args.jobs is not None and args.jobs < 1:
        parser.error("--jobs must be a positive integer")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    compiler = shutil.which(args.compiler)
    if compiler is None:
        print(f"cannot run direct build benchmark: compiler not found: {args.compiler}", file=sys.stderr)
        return 2
    try:
        paths = run_benchmarks(
            runs=args.runs,
            warmups=args.warmups,
            first=args.first,
            compiler=compiler,
            jobs=args.jobs or available_jobs(),
            results_root=args.results_dir,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"cannot run direct build benchmark: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote direct/adapted clean-build results to {', '.join(str(path) for path in paths)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
