"""Readable independent and differential checks for Hermitian BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged, hermitian_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_chemv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    original_a = np.asfortranarray(
        [[2.0 + 77.0j, 1.0 - 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 88.0j], [91.0j, 92.0j]], dtype=np.complex64
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([4.0 - 2.0j, 5.0 + 3.0j], dtype=np.complex64)
    logical_a = hermitian_from_triangle(original_a, 2, "U")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.chemv("U", np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.chemv(b"U", np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3))

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zhemv(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    original_a = np.asfortranarray(
        [[2.0 + 77.0j, np.nan + 1.0j * np.nan], [1.0 + 2.0j, 3.0 - 88.0j], [91.0j, 92.0j]], dtype=np.complex128
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    original_y = np.array([4.0 - 2.0j, 5.0 + 3.0j], dtype=np.complex128)
    logical_a = hermitian_from_triangle(original_a, 2, "L")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zhemv("L", np.int32(2), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.zhemv(b"L", np.int32(2), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3))

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_cher(prik_blas, f2py_blas):
    alpha = np.float32(0.75)
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    original_a = np.asfortranarray(
        [[3.0 + 9.0j, 1.0 - 2.0j], [np.nan + 1.0j * np.nan, 4.0 - 8.0j], [91.0j, 92.0j]], dtype=np.complex64
    )
    prik_x, f2py_x = x.copy(), x.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.cher("U", np.int32(2), alpha, prik_x, np.int32(1), prik_a, np.int32(3))
    f2py_blas.cher(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = hermitian_from_triangle(original_a, 2, "U") + alpha * x[:, None] * np.conj(x[None, :])
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(f2py_a[:2, :2][upper], expected_a[upper])
    assert_allclose_for_dtype(prik_a[:2, :2][upper], f2py_a[:2, :2][upper])
    assert np.all(np.imag(np.diag(prik_a[:2, :2])) == 0.0)
    assert np.all(np.imag(np.diag(f2py_a[:2, :2])) == 0.0)
    np.testing.assert_array_equal(prik_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zher(prik_blas, f2py_blas):
    alpha = np.float64(-0.25)
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    original_a = np.asfortranarray(
        [[3.0 + 9.0j, np.nan + 1.0j * np.nan], [1.0 + 2.0j, 4.0 - 8.0j], [91.0j, 92.0j]], dtype=np.complex128
    )
    prik_x, f2py_x = x.copy(), x.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.zher("L", np.int32(2), alpha, prik_x, np.int32(1), prik_a, np.int32(3))
    f2py_blas.zher(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_a, lda=np.int32(3))

    expected_a = hermitian_from_triangle(original_a, 2, "L") + alpha * x[:, None] * np.conj(x[None, :])
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(f2py_a[:2, :2][lower], expected_a[lower])
    assert_allclose_for_dtype(prik_a[:2, :2][lower], f2py_a[:2, :2][lower])
    assert np.all(np.imag(np.diag(prik_a[:2, :2])) == 0.0)
    assert np.all(np.imag(np.diag(f2py_a[:2, :2])) == 0.0)
    np.testing.assert_array_equal(prik_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_cher2(prik_blas, f2py_blas):
    alpha = np.complex64(0.5 - 0.25j)
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    y = np.array([-3.0 + 0.5j, 4.0 - 2.0j], dtype=np.complex64)
    original_a = np.asfortranarray(
        [[3.0 + 9.0j, 1.0 - 2.0j], [np.nan + 1.0j * np.nan, 4.0 - 8.0j], [91.0j, 92.0j]], dtype=np.complex64
    )
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.cher2("U", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.cher2(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    logical_a = hermitian_from_triangle(original_a, 2, "U")
    expected_a = (
        logical_a + alpha * x[:, None] * np.conj(y[None, :]) + np.conj(alpha) * y[:, None] * np.conj(x[None, :])
    )
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][upper], expected_a[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_a[:2, :2][upper], expected_a[upper], operation_size=2)
    assert_allclose_for_dtype(prik_a[:2, :2][upper], f2py_a[:2, :2][upper], operation_size=2)
    assert np.all(np.imag(np.diag(prik_a[:2, :2])) == 0.0)
    assert np.all(np.imag(np.diag(f2py_a[:2, :2])) == 0.0)
    np.testing.assert_array_equal(prik_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_a[np.tril_indices(2, -1)], original_a[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zher2(prik_blas, f2py_blas):
    alpha = np.complex128(-0.75 + 0.5j)
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    y = np.array([-3.0 + 0.5j, 4.0 - 2.0j], dtype=np.complex128)
    original_a = np.asfortranarray(
        [[3.0 + 9.0j, np.nan + 1.0j * np.nan], [1.0 + 2.0j, 4.0 - 8.0j], [91.0j, 92.0j]], dtype=np.complex128
    )
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")

    prik_blas.zher2("L", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_a, np.int32(3))
    f2py_blas.zher2(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_a, lda=np.int32(3))

    logical_a = hermitian_from_triangle(original_a, 2, "L")
    expected_a = (
        logical_a + alpha * x[:, None] * np.conj(y[None, :]) + np.conj(alpha) * y[:, None] * np.conj(x[None, :])
    )
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_a[:2, :2][lower], expected_a[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_a[:2, :2][lower], expected_a[lower], operation_size=2)
    assert_allclose_for_dtype(prik_a[:2, :2][lower], f2py_a[:2, :2][lower], operation_size=2)
    assert np.all(np.imag(np.diag(prik_a[:2, :2])) == 0.0)
    assert np.all(np.imag(np.diag(f2py_a[:2, :2])) == 0.0)
    np.testing.assert_array_equal(prik_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_a[np.triu_indices(2, 1)], original_a[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)
