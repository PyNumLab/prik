"""Small numerical and storage helpers for the LAPACK correctness example."""

from __future__ import annotations

import numpy as np


def assert_allclose_float64(actual, expected, *, operation_size: int = 1) -> None:
    """Compare float64 LAPACK results with an accumulation-aware tolerance."""
    scale = max(1, operation_size)
    expected_array = np.asarray(expected)
    magnitude = max(1.0, float(np.max(np.abs(expected_array), initial=0.0)))
    np.testing.assert_allclose(
        actual,
        expected,
        rtol=np.finfo(np.float64).eps * 32 * scale,
        atol=np.finfo(np.float64).eps * 32 * scale * magnitude,
    )


def assert_info(result, expected: int = 0) -> None:
    """Check the trailing LAPACK INFO return value."""
    assert int(np.asarray(result[-1])) == expected


def assert_small_residual(
    residual,
    *,
    matrix_norm: float,
    solution_norm: float,
    operation_size: int,
) -> None:
    """Check a backward residual scaled by the represented operation."""
    denominator = max(1.0, matrix_norm * solution_norm)
    scaled = np.linalg.norm(np.asarray(residual, dtype=np.float64), ord=np.inf) / denominator
    tolerance = np.finfo(np.float64).eps * 128 * max(1, operation_size)
    assert scaled <= tolerance, f"scaled residual {scaled} exceeded {tolerance}"


def assert_orthogonal(matrix: np.ndarray, *, columns: int | None = None) -> None:
    """Validate orthonormal columns without hiding a routine invocation."""
    active_columns = matrix.shape[1] if columns is None else columns
    basis = np.asarray(matrix[:, :active_columns], dtype=np.float64)
    assert_allclose_float64(
        basis.T @ basis,
        np.eye(active_columns, dtype=np.float64),
        operation_size=basis.shape[0],
    )


def native_pivots(scipy_pivots: np.ndarray) -> np.ndarray:
    """Convert SciPy's zero-based pivots to LAPACK's native one-based values."""
    return np.asarray(scipy_pivots, dtype=np.int32) + np.int32(1)


def gfortran_logical_mask(values) -> np.ndarray:
    """Represent a default-GFortran LOGICAL vector through PRIK's bool buffer ABI."""
    logical_bytes = np.zeros(len(values) * np.dtype(np.int32).itemsize, dtype=np.bool_)
    logical_bytes[:: np.dtype(np.int32).itemsize] = np.asarray(values, dtype=np.bool_)
    return logical_bytes


def pivot_matrix(pivots: np.ndarray, size: int, *, one_based: bool) -> np.ndarray:
    """Build the row permutation represented by sequential LAPACK pivots."""
    permutation = np.eye(size, dtype=np.float64)
    for row, pivot in enumerate(np.asarray(pivots, dtype=np.int64)):
        target = int(pivot) - int(one_based)
        permutation[[row, target], :] = permutation[[target, row], :]
    return permutation


def unpack_lu(factor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split LAPACK's combined LU storage into logical L and U matrices."""
    rows, columns = factor.shape
    rank = min(rows, columns)
    lower = np.tril(factor[:, :rank], k=-1) + np.eye(rows, rank, dtype=np.float64)
    upper = np.triu(factor[:rank, :])
    return lower, upper


def qr_q_from_reflectors(factor: np.ndarray, tau: np.ndarray) -> np.ndarray:
    """Form reduced Q explicitly from DGEQRF Householder storage."""
    rows, columns = factor.shape
    reflectors = min(rows, columns, len(tau))
    q = np.eye(rows, dtype=np.float64)
    for index in range(reflectors):
        vector = np.zeros(rows, dtype=np.float64)
        vector[index] = 1.0
        vector[index + 1 :] = factor[index + 1 :, index]
        q = q @ (np.eye(rows, dtype=np.float64) - tau[index] * np.outer(vector, vector))
    return q[:, :columns]


def assert_storage_unchanged(actual: np.ndarray, expected: np.ndarray) -> None:
    """Compare storage exactly, including NaN sentinels."""
    np.testing.assert_array_equal(actual, expected)


def general_band_storage(matrix: np.ndarray, lower: int, upper: int, *, factor: bool = False) -> np.ndarray:
    """Pack a square general band matrix in LAPACK column-major storage."""
    logical = np.asarray(matrix, dtype=np.float64)
    rows = 2 * lower + upper + 1 if factor else lower + upper + 1
    diagonal_row = lower + upper if factor else upper
    band = np.zeros((rows, logical.shape[1]), dtype=np.float64, order="F")
    for column in range(logical.shape[1]):
        for row in range(max(0, column - upper), min(logical.shape[0], column + lower + 1)):
            band[diagonal_row + row - column, column] = logical[row, column]
    return band


def symmetric_band_storage(matrix: np.ndarray, bandwidth: int, *, lower: bool) -> np.ndarray:
    """Pack one triangle of a symmetric band matrix."""
    logical = np.asarray(matrix, dtype=np.float64)
    band = np.zeros((bandwidth + 1, logical.shape[1]), dtype=np.float64, order="F")
    for column in range(logical.shape[1]):
        if lower:
            rows = range(column, min(logical.shape[0], column + bandwidth + 1))
            for row in rows:
                band[row - column, column] = logical[row, column]
        else:
            rows = range(max(0, column - bandwidth), column + 1)
            for row in rows:
                band[bandwidth + row - column, column] = logical[row, column]
    return band


def packed_symmetric(matrix: np.ndarray, *, lower: bool) -> np.ndarray:
    """Pack one triangle in LAPACK packed-column order."""
    logical = np.asarray(matrix, dtype=np.float64)
    values: list[float] = []
    for column in range(logical.shape[1]):
        rows = range(column, logical.shape[0]) if lower else range(column + 1)
        values.extend(float(logical[row, column]) for row in rows)
    return np.asarray(values, dtype=np.float64)


def unpack_packed_symmetric(values: np.ndarray, size: int, *, lower: bool) -> np.ndarray:
    """Reconstruct a symmetric matrix from LAPACK packed-column storage."""
    matrix = np.zeros((size, size), dtype=np.float64)
    offset = 0
    for column in range(size):
        rows = range(column, size) if lower else range(column + 1)
        for row in rows:
            matrix[row, column] = values[offset]
            matrix[column, row] = values[offset]
            offset += 1
    return matrix


def tridiagonal_matrix(lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray) -> np.ndarray:
    """Construct the logical matrix represented by three diagonals."""
    return np.diag(diagonal) + np.diag(upper, 1) + np.diag(lower, -1)


def column_major(matrix: np.ndarray, *, rows: int | None = None) -> np.ndarray:
    """Return a Fortran-contiguous float64 matrix with optional leading padding."""
    array = np.asarray(matrix, dtype=np.float64)
    if rows is None or rows == array.shape[0]:
        return np.array(array, dtype=np.float64, order="F", copy=True)
    padded = np.full((rows, array.shape[1]), np.nan, dtype=np.float64, order="F")
    padded[: array.shape[0], :] = array
    return padded


def active(matrix: np.ndarray, rows: int, columns: int) -> np.ndarray:
    """Extract the logical matrix while preserving its column-major convention."""
    return np.asarray(matrix[:rows, :columns], dtype=np.float64)
