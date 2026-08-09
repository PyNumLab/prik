from __future__ import annotations

import importlib
import os
import platform
import sys
from collections.abc import Callable
from typing import Any

import numpy as np
import pyperf


def get_function(api: Any, name: str) -> Callable[..., Any]:
    function = getattr(api, name)

    if not callable(function):
        raise TypeError(f"{name!r} is not callable")

    return function


tool = os.environ.get("BINDING_TOOL")
benchmark_group = os.environ.get("PRIK_RUNTIME_BENCHMARK_GROUP", "all")
order_pass = os.environ.get("PRIK_RUNTIME_ORDER_PASS")
group_settings = {
    "all": (8, 3),
    "calls": (16, 4),
    "vector-latency": (16, 4),
    "vector-bulk": (4, 3),
    "matrix-sum-latency": (16, 4),
    "matrix-sum-bulk": (2, 3),
    "matrix-update-latency": (16, 4),
    "matrix-update-bulk": (8, 3),
}

if benchmark_group not in group_settings:
    choices = ", ".join(group_settings)
    raise RuntimeError(f"Unknown PRIK_RUNTIME_BENCHMARK_GROUP {benchmark_group!r}; choose one of: {choices}.")
if order_pass not in {"prik-first", "f2py-first"}:
    raise RuntimeError("Set PRIK_RUNTIME_ORDER_PASS to 'prik-first' or 'f2py-first'.")

if tool == "prik":
    extension = importlib.import_module("bench_prik")
elif tool == "f2py":
    extension = importlib.import_module("bench_f2py")
else:
    raise RuntimeError("Set BINDING_TOOL to 'prik' or 'f2py'.")

api = extension.kernels
noop = get_function(api, "noop")
add_scalars = get_function(api, "add_scalars")
increment_vector = get_function(api, "increment_vector")
sum_matrix = get_function(api, "sum_matrix")
matrix_update = get_function(api, "matrix_update")


processes, values = group_settings[benchmark_group]
metadata = {
    "binding_tool": tool,
    "benchmark_group": benchmark_group,
    "python_version": sys.version,
    "numpy_version": np.__version__,
    "platform_details": platform.platform(),
    "runtime_order_pass": order_pass,
    "runtime_order_protocol": "balanced_ab_ba",
}
if cpu_model := os.environ.get("PRIK_BENCHMARK_CPU_MODEL"):
    metadata["cpu_model_name"] = cpu_model
runner = pyperf.Runner(
    processes=processes,
    values=values,
    metadata=metadata,
)

if benchmark_group in {"all", "calls"}:
    # Duplicate extremely small statements to reduce timing-loop overhead.
    runner.timeit(
        "call.noop",
        stmt="fn()",
        globals={"fn": noop},
        duplicate=100,
    )

    runner.timeit(
        "call.add_scalars",
        stmt="fn(np.float64(1.25), np.float64(2.75))",
        globals={"fn": add_scalars, "np": np},
        duplicate=50,
    )

for size in (1, 16, 1024, 1000000):
    group = "vector-latency" if size <= 16 else "vector-bulk"
    if benchmark_group not in {"all", group}:
        continue
    vector = np.zeros(size, dtype=np.float64)

    runner.timeit(
        f"array.increment_vector.n={size}",
        stmt="fn(a)",
        globals={
            "fn": increment_vector,
            "a": vector,
        },
    )

for shape in ((4, 4), (32, 32), (256, 256), (1024, 1024)):
    rows, columns = shape
    group = "matrix-sum-latency" if rows == 4 else "matrix-sum-bulk"
    if benchmark_group not in {"all", group}:
        continue

    for order in ("F",):
        matrix = np.ones(shape, dtype=np.float64, order=order)

        runner.timeit(
            f"matrix.sum.{rows}x{columns}.order={order}",
            stmt="fn(a)",
            globals={
                "fn": sum_matrix,
                "a": matrix,
            },
        )

# Native in-place Fortran-contiguous path.
for shape in ((4, 4), (256, 256), (1024, 1024)):
    rows, columns = shape
    group = "matrix-update-bulk" if rows == 1024 else "matrix-update-latency"
    if benchmark_group not in {"all", group}:
        continue
    matrix = np.zeros(shape, dtype=np.float64, order="F")

    runner.timeit(
        f"matrix.update.{rows}x{columns}.order=F",
        stmt="fn(a, np.float64(1.0))",
        globals={
            "fn": matrix_update,
            "a": matrix,
            "np": np,
        },
    )
