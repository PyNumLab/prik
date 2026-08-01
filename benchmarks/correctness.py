from __future__ import annotations

import importlib
from typing import Any

import numpy as np


def load_api(module_name: str, nested_module: str | None = None) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, nested_module) if nested_module else module


x2py = load_api("bench_x2py", "kernels")
f2py = load_api("bench_f2py", "kernels")


def check_implementation(api: Any) -> None:
    assert api.add_scalars(np.float64(2.0), np.float64(3.0)) == np.float64(5.0)

    vector = np.arange(32, dtype=np.float64)
    expected = vector + 1.0
    api.increment_vector(vector)
    np.testing.assert_allclose(vector, expected)

    matrix = np.asfortranarray(np.arange(128, dtype=np.float64).reshape((16, 8), order="F"))
    expected_sum = np.sum(matrix)
    actual_sum = api.sum_matrix(matrix)
    np.testing.assert_allclose(actual_sum, expected_sum)

    api.matrix_update(matrix, np.float64(2.0))
    np.testing.assert_allclose(
        matrix,
        np.arange(128, dtype=np.float64).reshape((16, 8), order="F") + 2.0,
    )


check_implementation(x2py)
check_implementation(f2py)

print("All implementations passed correctness checks.")
