"""Measure direct and adapted scalar call overhead after untimed preflight."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np
import pyperf

if __package__:
    from .direct_benchmark import (
        BENCHMARK_ROOT,
        OPTIMIZED_FLAGS,
        Route,
        check_api,
        compact_artifact_membership,
        module_name,
        natural_result_type,
        route_action,
        wrapper_mode,
    )
else:
    from direct_benchmark import (
        BENCHMARK_ROOT,
        OPTIMIZED_FLAGS,
        Route,
        check_api,
        compact_artifact_membership,
        module_name,
        natural_result_type,
        route_action,
        wrapper_mode,
    )


route_value = os.environ.get("PRIK_DIRECT_BENCHMARK_ROUTE")
order_pass = os.environ.get("PRIK_DIRECT_ORDER_PASS")
if route_value not in {"prik-direct", "f2py-direct", "prik-adapted"}:
    raise RuntimeError("Set PRIK_DIRECT_BENCHMARK_ROUTE to prik-direct, f2py-direct, or prik-adapted.")
if order_pass not in {"forward", "reverse"}:
    raise RuntimeError("Set PRIK_DIRECT_ORDER_PASS to forward or reverse.")
route: Route = route_value
api = importlib.import_module(module_name(route))
check_api(api, route)
preflight_path = Path(
    os.environ.get("PRIK_DIRECT_PREFLIGHT_REPORT", BENCHMARK_ROOT / "build/direct-runtime/preflight.json")
)
if not preflight_path.is_file():
    raise RuntimeError(f"Run direct_preflight.py before timing; missing {preflight_path}")
preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
artifact_membership = compact_artifact_membership(preflight[route])

metadata = {
    "binding_tool": route,
    "benchmark_cohort": "direct_entrypoint",
    "artifact_membership": artifact_membership,
    "compile_flags": OPTIMIZED_FLAGS,
    "gil_policy": "held",
    "numpy_version": np.__version__,
    "natural_result_type": natural_result_type(route),
    "platform_details": platform.platform(),
    "python_version": sys.version,
    "route": route_action(route),
    "runtime_order_pass": order_pass,
    "runtime_order_protocol": "balanced_three_route_forward_reverse",
    "wrapper_mode": wrapper_mode(route),
}
if cpu_model := os.environ.get("PRIK_BENCHMARK_CPU_MODEL"):
    metadata["cpu_model_name"] = cpu_model
runner = pyperf.Runner(processes=16, values=4, metadata=metadata)
runner.timeit("direct.call.noop", stmt="fn()", globals={"fn": api.noop}, duplicate=100)
runner.timeit(
    "direct.call.scalar_function",
    stmt="fn(a, b)",
    globals={"fn": api.add_scalars, "a": np.float64(1.25), "b": np.float64(2.75)},
    duplicate=50,
)
runner.timeit(
    "direct.call.scalar_subroutine",
    stmt="fn(a, b)",
    globals={"fn": api.add_scalars_out, "a": np.float64(1.25), "b": np.float64(2.75)},
    duplicate=50,
)
