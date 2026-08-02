"""Readable independent and differential checks for Hermitian BLAS Level 3."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged, hermitian_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_chemm(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    a = np.asfortranarray([[2.0 + 77.0j, -1.0 + 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 88.0j]], dtype=np.complex64)
    b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    original_c = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j]], dtype=np.complex64)
    logical_a = hermitian_from_triangle(a, 2, "U")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.chemm(
        "L", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.chemm(
        b"L",
        b"U",
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(2),
        ldb=np.int32(2),
        ldc=np.int32(2),
    )

    expected_c = alpha * logical_a @ b + beta * original_c
    assert_allclose_for_dtype(prik_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(f2py_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(prik_c, f2py_c, operation_size=2)
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_zhemm(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    a = np.asfortranarray([[2.0 + 77.0j, np.nan + 1.0j * np.nan], [-1.0 - 2.0j, 3.0 - 88.0j]], dtype=np.complex128)
    b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    original_c = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j]], dtype=np.complex128)
    logical_a = hermitian_from_triangle(a, 2, "L")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zhemm(
        "R", "L", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.zhemm(
        b"R",
        b"L",
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(2),
        ldb=np.int32(2),
        ldc=np.int32(2),
    )

    expected_c = alpha * b @ logical_a + original_c
    assert_allclose_for_dtype(prik_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(f2py_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(prik_c, f2py_c, operation_size=2)
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_cherk(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    original_c = np.asfortranarray(
        [[5.0 + 77.0j, 6.0 - 2.0j], [np.nan + 1.0j * np.nan, 8.0 - 88.0j]], dtype=np.complex64
    )
    logical_c = hermitian_from_triangle(original_c, 2, "U")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.cherk("U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.cherk(b"U", b"N", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a @ a.conj().T) + beta * logical_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=2)
    assert np.all(np.imag(np.diag(prik_c)) == 0.0)
    assert np.all(np.imag(np.diag(f2py_c)) == 0.0)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_zherk(prik_blas, f2py_blas):
    alpha, beta = np.float64(-0.75), np.float64(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    original_c = np.asfortranarray(
        [[5.0 + 77.0j, np.nan + 1.0j * np.nan], [6.0 + 2.0j, 8.0 - 88.0j]], dtype=np.complex128
    )
    logical_c = hermitian_from_triangle(original_c, 2, "L")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zherk("L", "C", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.zherk(b"L", b"C", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a.conj().T @ a) + logical_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=2)
    assert np.all(np.imag(np.diag(prik_c)) == 0.0)
    assert np.all(np.imag(np.diag(f2py_c)) == 0.0)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_cher2k(prik_blas, f2py_blas):
    alpha, beta = np.complex64(0.5 - 0.25j), np.float32(-0.5)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex64)
    original_c = np.asfortranarray(
        [[9.0 + 77.0j, 10.0 - 2.0j], [np.nan + 1.0j * np.nan, 12.0 - 88.0j]], dtype=np.complex64
    )
    logical_c = hermitian_from_triangle(original_c, 2, "U")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.cher2k(
        "U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.cher2k(
        b"U",
        b"N",
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(2),
        ldb=np.int32(2),
        ldc=np.int32(2),
    )

    expected_c = alpha * (a @ b.conj().T) + np.conj(alpha) * (b @ a.conj().T) + beta * logical_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=4)
    assert np.all(np.imag(np.diag(prik_c)) == 0.0)
    assert np.all(np.imag(np.diag(f2py_c)) == 0.0)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_zher2k(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.75 + 0.5j), np.float64(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex128)
    original_c = np.asfortranarray(
        [[9.0 + 77.0j, np.nan + 1.0j * np.nan], [10.0 + 2.0j, 12.0 - 88.0j]], dtype=np.complex128
    )
    logical_c = hermitian_from_triangle(original_c, 2, "L")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zher2k(
        "L", "C", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.zher2k(
        b"L",
        b"C",
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(2),
        ldb=np.int32(2),
        ldc=np.int32(2),
    )

    expected_c = alpha * (a.conj().T @ b) + np.conj(alpha) * (b.conj().T @ a) + logical_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=4)
    assert np.all(np.imag(np.diag(prik_c)) == 0.0)
    assert np.all(np.imag(np.diag(f2py_c)) == 0.0)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)
