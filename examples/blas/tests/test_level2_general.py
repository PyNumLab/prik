"""Readable independent and differential checks for general BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_for_dtype, assert_storage_unchanged


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgemv_no_transpose(prik_blas, f2py_blas):
    alpha, beta = np.float64(2.0), np.float64(-1.0)
    matrix = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    x = np.array([5.0, -2.0], dtype=np.float64)
    original_y = np.array([7.0, 11.0], dtype=np.float64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.dgemv(
        "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    # f2py places its inferred optional leading dimension after the native arrays.
    f2py_result = f2py_blas.dgemv(
        b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    product = np.array([1.0 * 5.0 + 2.0 * (-2.0), 3.0 * 5.0 + 4.0 * (-2.0)])
    expected_y = alpha * product + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert prik_scalars == (2, 2, alpha, 3, 1, beta, 1)
    assert f2py_result is None
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dgemv_transpose(prik_blas, f2py_blas):
    alpha, beta = np.float64(1.0), np.float64(0.0)
    matrix = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [93.0, 94.0]], dtype=np.float64)
    x = np.array([5.0, -2.0], dtype=np.float64)
    original_y = np.array([17.0, 19.0], dtype=np.float64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dgemv(
        "T", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.dgemv(
        b"T", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected_y = np.array([1.0 * 5.0 + 3.0 * (-2.0), 2.0 * 5.0 + 4.0 * (-2.0)])
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_sgemv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(0.5)
    matrix = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float32)
    x = np.array([2.0, -1.0], dtype=np.float32)
    original_y = np.array([5.0, 6.0], dtype=np.float32)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.sgemv(
        "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.sgemv(
        b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected = alpha * np.array([1.0 * 2.0 + 2.0 * -1.0, 3.0 * 2.0 + 4.0 * -1.0]) + beta * original_y
    assert_allclose_for_dtype(prik_y, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_cgemv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(-1.0j)
    matrix = np.asfortranarray(
        [[1.0 + 1.0j, 2.0 - 1.0j], [3.0 + 0.5j, 4.0 + 2.0j], [91.0j, 92.0j]],
        dtype=np.complex64,
    )
    x = np.array([2.0 - 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([5.0 + 1.0j, 6.0 - 2.0j], dtype=np.complex64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.cgemv(
        "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.cgemv(
        b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected = (
        alpha * np.array([matrix[0, 0] * x[0] + matrix[0, 1] * x[1], matrix[1, 0] * x[0] + matrix[1, 1] * x[1]])
        + beta * original_y
    )
    assert_allclose_for_dtype(prik_y, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zgemv(prik_blas, f2py_blas):
    alpha, beta = np.complex128(1.0 + 0.25j), np.complex128(0.0j)
    matrix = np.asfortranarray(
        [[1.0 + 1.0j, 2.0 - 1.0j], [3.0 + 0.5j, 4.0 + 2.0j], [91.0j, 92.0j]],
        dtype=np.complex128,
    )
    x = np.array([2.0 - 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    original_y = np.array([5.0 + 1.0j, 6.0 - 2.0j], dtype=np.complex128)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zgemv(
        "C", np.int32(2), np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.zgemv(
        b"C", np.int32(2), np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected = alpha * np.array(
        [
            np.conj(matrix[0, 0]) * x[0] + np.conj(matrix[1, 0]) * x[1],
            np.conj(matrix[0, 1]) * x[0] + np.conj(matrix[1, 1]) * x[1],
        ]
    )
    assert_allclose_for_dtype(prik_y, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, matrix)
    assert_storage_unchanged(f2py_a, matrix)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_sger(prik_blas, f2py_blas):
    alpha = np.float32(2.0)
    x = np.array([1.0, -2.0], dtype=np.float32)
    y = np.array([3.0, 4.0], dtype=np.float32)
    original = np.asfortranarray([[5.0, 6.0], [7.0, 8.0], [91.0, 92.0]], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.sger(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.sger(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * y[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_dger(prik_blas, f2py_blas):
    alpha = np.float64(-0.5)
    x = np.array([1.0, -2.0], dtype=np.float64)
    y = np.array([3.0, 4.0], dtype=np.float64)
    original = np.asfortranarray([[5.0, 6.0], [7.0, 8.0], [91.0, 92.0]], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.dger(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.dger(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * y[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_cgeru(prik_blas, f2py_blas):
    alpha = np.complex64(1.0 - 0.5j)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex64)
    original = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j], [91.0j, 92.0j]], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.cgeru(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.cgeru(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * y[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zgeru(prik_blas, f2py_blas):
    alpha = np.complex128(-0.25 + 0.75j)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex128)
    original = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j], [91.0j, 92.0j]], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.zgeru(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.zgeru(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * y[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_cgerc(prik_blas, f2py_blas):
    alpha = np.complex64(1.0 - 0.5j)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex64)
    original = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j], [91.0j, 92.0j]], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.cgerc(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.cgerc(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * np.conj(y)[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zgerc(prik_blas, f2py_blas):
    alpha = np.complex128(-0.25 + 0.75j)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex128)
    original = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j], [91.0j, 92.0j]], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")

    prik_blas.zgerc(np.int32(2), np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.zgerc(np.int32(2), np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected = original[:2, :] + alpha * x[:, None] * np.conj(y)[None, :]
    assert_allclose_for_dtype(prik_a[:2, :], expected)
    assert_allclose_for_dtype(f2py_a[:2, :], expected)
    assert_allclose_for_dtype(prik_a[:2, :], f2py_a[:2, :])
    np.testing.assert_array_equal(prik_a[2, :], original[2, :], strict=True)
    np.testing.assert_array_equal(f2py_a[2, :], original[2, :], strict=True)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)
