"""Small numerical and storage helpers used by the readable BLAS tests."""

from __future__ import annotations

import numpy as np


def assert_allclose_for_dtype(actual, expected, *, operation_size: int = 1) -> None:
    """Compare floating values with dtype- and accumulation-aware tolerances."""
    actual_array = np.asarray(actual)
    expected_array = np.asarray(expected)
    dtype = np.result_type(actual_array.dtype, expected_array.dtype)
    real_dtype = np.empty((), dtype=dtype).real.dtype
    epsilon = np.finfo(real_dtype).eps
    scale = max(1, operation_size)
    magnitude = max(1.0, float(np.max(np.abs(expected_array), initial=0.0)))
    np.testing.assert_allclose(
        actual_array,
        expected_array,
        rtol=epsilon * 8 * scale,
        atol=epsilon * 8 * scale * magnitude,
    )


def logical_indices(n: int, increment: int) -> np.ndarray:
    """Return zero-based storage positions visited by a native BLAS vector."""
    if n <= 0:
        return np.array([], dtype=np.intp)
    start = 0 if increment > 0 else (n - 1) * (-increment)
    return start + np.arange(n, dtype=np.intp) * increment


def logical_vector(storage: np.ndarray, n: int, increment: int) -> np.ndarray:
    """Copy the logical BLAS vector represented by storage and an increment."""
    return storage[logical_indices(n, increment)].copy()


def assert_storage_unchanged(actual: np.ndarray, original: np.ndarray) -> None:
    """Require exact preservation, including NaNs and sentinel padding."""
    np.testing.assert_array_equal(actual, original, strict=True)


def with_logical_vector(
    original: np.ndarray,
    values: np.ndarray,
    n: int,
    increment: int,
) -> np.ndarray:
    """Return storage with only the logical BLAS vector positions replaced."""
    expected = original.copy()
    expected[logical_indices(n, increment)] = values
    return expected


def symmetric_from_triangle(storage: np.ndarray, n: int, uplo: str) -> np.ndarray:
    """Reconstruct a logical symmetric matrix without reading the unused triangle."""
    active = storage[:n, :n]
    triangle = np.triu(active) if uplo.upper() == "U" else np.tril(active)
    return triangle + triangle.T - np.diag(np.diag(triangle))


def hermitian_from_triangle(storage: np.ndarray, n: int, uplo: str) -> np.ndarray:
    """Reconstruct a Hermitian matrix and discard stored diagonal imaginary parts."""
    active = storage[:n, :n]
    triangle = np.triu(active) if uplo.upper() == "U" else np.tril(active)
    diagonal = np.diag(np.real(np.diag(triangle))).astype(storage.dtype)
    return triangle + triangle.conj().T - np.diag(np.diag(triangle)) - np.diag(np.diag(triangle).conj()) + diagonal


def triangular_from_triangle(
    storage: np.ndarray,
    n: int,
    uplo: str,
    *,
    unit_diagonal: bool,
) -> np.ndarray:
    """Reconstruct a triangular matrix without inspecting unused or unit diagonal data."""
    active = storage[:n, :n]
    if uplo.upper() == "U":
        triangle = np.triu(active, k=1 if unit_diagonal else 0)
    else:
        triangle = np.tril(active, k=-1 if unit_diagonal else 0)
    if unit_diagonal:
        triangle = triangle + np.eye(n, dtype=storage.dtype)
    return triangle


def packed_from_triangle(matrix: np.ndarray, uplo: str) -> np.ndarray:
    """Pack one matrix triangle in the column-major BLAS packed format."""
    n = matrix.shape[0]
    if uplo.upper() == "U":
        values = [matrix[row, column] for column in range(n) for row in range(column + 1)]
    else:
        values = [matrix[row, column] for column in range(n) for row in range(column, n)]
    return np.asarray(values, dtype=matrix.dtype)


def symmetric_from_packed(packed: np.ndarray, n: int, uplo: str) -> np.ndarray:
    """Reconstruct a symmetric matrix from packed BLAS storage."""
    triangle = np.zeros((n, n), dtype=packed.dtype)
    index = 0
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(column + 1):
                triangle[row, column] = packed[index]
                index += 1
    else:
        for column in range(n):
            for row in range(column, n):
                triangle[row, column] = packed[index]
                index += 1
    return triangle + triangle.T - np.diag(np.diag(triangle))


def hermitian_from_packed(packed: np.ndarray, n: int, uplo: str) -> np.ndarray:
    """Reconstruct a Hermitian matrix from packed BLAS storage."""
    triangle = np.zeros((n, n), dtype=packed.dtype)
    index = 0
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(column + 1):
                triangle[row, column] = packed[index]
                index += 1
    else:
        for column in range(n):
            for row in range(column, n):
                triangle[row, column] = packed[index]
                index += 1
    diagonal = np.diag(np.real(np.diag(triangle))).astype(packed.dtype)
    return triangle + triangle.conj().T - np.diag(np.diag(triangle)) - np.diag(np.diag(triangle).conj()) + diagonal


def triangular_from_packed(
    packed: np.ndarray,
    n: int,
    uplo: str,
    *,
    unit_diagonal: bool,
) -> np.ndarray:
    """Reconstruct a triangular matrix from packed BLAS storage."""
    triangle = np.zeros((n, n), dtype=packed.dtype)
    index = 0
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(column + 1):
                if not unit_diagonal or row != column:
                    triangle[row, column] = packed[index]
                index += 1
    else:
        for column in range(n):
            for row in range(column, n):
                if not unit_diagonal or row != column:
                    triangle[row, column] = packed[index]
                index += 1
    if unit_diagonal:
        triangle += np.eye(n, dtype=packed.dtype)
    return triangle


def general_from_band(storage: np.ndarray, m: int, n: int, kl: int, ku: int) -> np.ndarray:
    """Reconstruct an m-by-n matrix from general band storage."""
    matrix = np.zeros((m, n), dtype=storage.dtype)
    for column in range(n):
        for row in range(max(0, column - ku), min(m, column + kl + 1)):
            matrix[row, column] = storage[ku + row - column, column]
    return matrix


def symmetric_from_band(storage: np.ndarray, n: int, k: int, uplo: str) -> np.ndarray:
    """Reconstruct a symmetric matrix from symmetric band storage."""
    triangle = np.zeros((n, n), dtype=storage.dtype)
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(max(0, column - k), column + 1):
                triangle[row, column] = storage[k + row - column, column]
    else:
        for column in range(n):
            for row in range(column, min(n, column + k + 1)):
                triangle[row, column] = storage[row - column, column]
    return triangle + triangle.T - np.diag(np.diag(triangle))


def hermitian_from_band(storage: np.ndarray, n: int, k: int, uplo: str) -> np.ndarray:
    """Reconstruct a Hermitian matrix from Hermitian band storage."""
    triangle = np.zeros((n, n), dtype=storage.dtype)
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(max(0, column - k), column + 1):
                triangle[row, column] = storage[k + row - column, column]
    else:
        for column in range(n):
            for row in range(column, min(n, column + k + 1)):
                triangle[row, column] = storage[row - column, column]
    diagonal = np.diag(np.real(np.diag(triangle))).astype(storage.dtype)
    return triangle + triangle.conj().T - np.diag(np.diag(triangle)) - np.diag(np.diag(triangle).conj()) + diagonal


def triangular_from_band(
    storage: np.ndarray,
    n: int,
    k: int,
    uplo: str,
    *,
    unit_diagonal: bool,
) -> np.ndarray:
    """Reconstruct a triangular matrix from triangular band storage."""
    triangle = np.zeros((n, n), dtype=storage.dtype)
    if uplo.upper() == "U":
        for column in range(n):
            for row in range(max(0, column - k), column + 1):
                if not unit_diagonal or row != column:
                    triangle[row, column] = storage[k + row - column, column]
    else:
        for column in range(n):
            for row in range(column, min(n, column + k + 1)):
                if not unit_diagonal or row != column:
                    triangle[row, column] = storage[row - column, column]
    if unit_diagonal:
        triangle += np.eye(n, dtype=storage.dtype)
    return triangle


def assert_runtime_smoke(module) -> None:
    """Exercise representative complete-library BLAS exports."""
    x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    y = np.array([10.0, 20.0, 30.0], dtype=np.float64)
    daxpy_scalars = module.daxpy(np.int32(3), np.float64(2.0), x, np.int32(1), y, np.int32(1))
    assert daxpy_scalars == (np.int32(3), np.float64(2.0), np.int32(1), np.int32(1))
    np.testing.assert_allclose(y, [12.0, 24.0, 36.0])
    assert module.ddot(np.int32(3), x, np.int32(1), y, np.int32(1)) == (
        np.float64(168.0),
        np.int32(3),
        np.int32(1),
        np.int32(1),
    )
    assert module.dasum(np.int32(3), y, np.int32(1)) == (
        np.float64(72.0),
        np.int32(3),
        np.int32(1),
    )
    dscal_scalars = module.dscal(np.int32(3), np.float64(0.5), y, np.int32(1))
    assert dscal_scalars == (np.int32(3), np.float64(0.5), np.int32(1))
    np.testing.assert_allclose(y, [6.0, 12.0, 18.0])
