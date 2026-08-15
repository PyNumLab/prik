#!/usr/bin/env python3
"""Build and verify every direct-entrypoint benchmark route before timing."""

from __future__ import annotations

import os
import shutil
import sys

if __package__:
    from .direct_benchmark import (
        BENCHMARK_ROOT,
        ROUTES,
        Route,
        extension_path,
        run_build,
        verify_build,
        write_preflight_report,
    )
else:
    from direct_benchmark import (
        BENCHMARK_ROOT,
        ROUTES,
        Route,
        extension_path,
        run_build,
        verify_build,
        write_preflight_report,
    )


def _available_jobs() -> int:
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return 1


def main() -> int:
    compiler = shutil.which("gfortran")
    if compiler is None:
        print("cannot run direct benchmark preflight: gfortran not found", file=sys.stderr)
        return 2
    root = BENCHMARK_ROOT / "build" / "direct-runtime"
    reports: dict[str, dict[str, object]] = {}
    try:
        for route_value in ROUTES:
            route: Route = route_value
            workdir = root / route
            run_build(route, workdir, compiler=compiler, jobs=_available_jobs())
            reports[route] = verify_build(route, workdir)
            extension = extension_path(route, workdir)
            for old_extension in BENCHMARK_ROOT.glob(f"{extension.name.split('.')[0]}*.so"):
                old_extension.unlink()
            shutil.copy2(extension, BENCHMARK_ROOT / extension.name)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"direct benchmark preflight failed: {exc}", file=sys.stderr)
        return 2
    report_path = root / "preflight.json"
    write_preflight_report(reports, report_path)
    print(f"Direct benchmark correctness and artifact preflight passed; wrote {report_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
