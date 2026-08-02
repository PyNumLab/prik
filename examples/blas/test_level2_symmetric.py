"""Readable independent and differential checks for symmetric BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged, symmetric_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ssymv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    original_a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0], [91.0, 92.0]], dtype=np.float32)
    x = np.array([2.0, -3.0], dtype=np.float32)
    original_y = np.array([4.0, 5.0], dtype=np.float32)
    logical_a = symmetric_from_triangle(original_a, 2, "U")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.ssymv("U", np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.ssymv(b"U", np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3))

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dsymv(prik_blas, f2py_blas):
    alpha, beta = np.float64(-2.0), np.float64(1.0)
    original_a = np.asfortranarray([[2.0, np.nan], [-1.0, 3.0], [91.0, 92.0]], dtype=np.float64)
    x = np.array([2.0, -3.0], dtype=np.float64)
    original_y = np.array([4.0, 5.0], dtype=np.float64)
    logical_a = symmetric_from_triangle(original_a, 2, "L")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dsymv("L", np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.dsymv(b"L", np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3))

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_ssyr(prik_blas, f2py_blas):
    alpha = np.float32(0.75)
    x = np.array([2.0, -1.0], dtype=np.float32)
    original_a = np.asfortranarray([[3.0, 1.0], [np.nan, 4.0], [91.0, 92.0]], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.ssyr("U", np.int32(2), alpha, prik_x, np.int32(1), prik_a, np.int32(3))
    f2py_blas.ssyr(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = original_a[:2, :2] + alpha * x[:, None] * x[None, :]
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(f2py_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(prik_a[:2, :2][upper], f2py_a[:2, :2][upper])
    np.testing.assert_array_equal(prik_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(prik_a[2, :], original_a[2, :])
    np.testing.assert_array_equal(f2py_a[2, :], original_a[2, :])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dsyr(prik_blas, f2py_blas):
    alpha = np.float64(-0.5)
    x = np.array([2.0, -1.0], dtype=np.float64)
    original_a = np.asfortranarray([[3.0, np.nan], [1.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.dsyr("L", np.int32(2), alpha, prik_x, np.int32(1), prik_a, np.int32(3))
    f2py_blas.dsyr(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = original_a[:2, :2] + alpha * x[:, None] * x[None, :]
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(f2py_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(prik_a[:2, :2][lower], f2py_a[:2, :2][lower])
    np.testing.assert_array_equal(prik_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(prik_a[2, :], original_a[2, :])
    np.testing.assert_array_equal(f2py_a[2, :], original_a[2, :])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_ssyr2(prik_blas, f2py_blas):
    alpha = np.float32(0.25)
    x = np.array([2.0, -1.0], dtype=np.float32)
    y = np.array([-3.0, 4.0], dtype=np.float32)
    original_a = np.asfortranarray([[3.0, 1.0], [np.nan, 4.0], [91.0, 92.0]], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.ssyr2("U", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.ssyr2(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = original_a[:2, :2] + alpha * (x[:, None] * y[None, :] + y[:, None] * x[None, :])
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(f2py_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(prik_a[:2, :2][upper], f2py_a[:2, :2][upper])
    np.testing.assert_array_equal(prik_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_dsyr2(prik_blas, f2py_blas):
    alpha = np.float64(-0.75)
    x = np.array([2.0, -1.0], dtype=np.float64)
    y = np.array([-3.0, 4.0], dtype=np.float64)
    original_a = np.asfortranarray([[3.0, np.nan], [1.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.dsyr2("L", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.dsyr2(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = original_a[:2, :2] + alpha * (x[:, None] * y[None, :] + y[:, None] * x[None, :])
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(f2py_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(prik_a[:2, :2][lower], f2py_a[:2, :2][lower])
    np.testing.assert_array_equal(prik_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)
