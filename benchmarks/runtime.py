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

if tool == "x2py":
    extension = importlib.import_module("bench_x2py")
elif tool == "f2py":
    extension = importlib.import_module("bench_f2py")
else:
    raise RuntimeError("Set BINDING_TOOL to 'x2py' or 'f2py'.")

api = extension.kernels
noop = get_function(api, "noop")
add_scalars = get_function(api, "add_scalars")
increment_vector = get_function(api, "increment_vector")
sum_matrix = get_function(api, "sum_matrix")
matrix_update = get_function(api, "matrix_update")


runner = pyperf.Runner(
    metadata={
        "binding_tool": tool,
        "python_version": sys.version,
        "numpy_version": np.__version__,
        "platform_details": platform.platform(),
    }
)

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
    matrix = np.zeros(shape, dtype=np.float64, order="F")
    rows, columns = shape

    runner.timeit(
        f"matrix.update.{rows}x{columns}.order=F",
        stmt="fn(a, np.float64(1.0))",
        globals={
            "fn": matrix_update,
            "a": matrix,
            "np": np,
        },
    )
