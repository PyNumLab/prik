"""Readable independent and differential checks for general BLAS Level 3."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgemm(prik_blas, f2py_blas):
    alpha, beta = np.float64(2.0), np.float64(-0.5)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0], [93.0, 94.0]], dtype=np.float64)
    original_c = np.asfortranarray([[9.0, 10.0], [11.0, 12.0], [95.0, 96.0]], dtype=np.float64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_scalars = prik_blas.dgemm(
        "N",
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        beta,
        prik_c,
        np.int32(3),
    )
    # f2py moves its inferred optional leading dimensions to keyword arguments.
    f2py_result = f2py_blas.dgemm(
        b"N",
        b"N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        f2py_a,
        f2py_b,
        beta,
        f2py_c,
        lda=np.int32(3),
        ldb=np.int32(3),
        ldc=np.int32(3),
    )

    product = np.array(
        [[1.0 * 5.0 + 2.0 * 7.0, 1.0 * 6.0 + 2.0 * 8.0], [3.0 * 5.0 + 4.0 * 7.0, 3.0 * 6.0 + 4.0 * 8.0]],
        dtype=np.float64,
    )
    expected_active = alpha * product + beta * original_c[:2, :]
    assert_allclose_for_dtype(prik_c[:2, :], expected_active, operation_size=2)
    assert_allclose_for_dtype(f2py_c[:2, :], expected_active, operation_size=2)
    assert_allclose_for_dtype(prik_c[:2, :], f2py_c[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_c[2, :], original_c[2, :], strict=True)
    np.testing.assert_array_equal(f2py_c[2, :], original_c[2, :], strict=True)
    assert prik_scalars == (2, 2, 2, alpha, 3, 3, beta, 3)
    assert f2py_result is None
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_sgemm(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(0.0)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    original_c = np.asfortranarray([[9.0, 10.0], [11.0, 12.0]], dtype=np.float32)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.sgemm(
        "N",
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.sgemm(
        b"N",
        b"N",
        np.int32(2),
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

    expected_c = alpha * (a @ b)
    assert_allclose_for_dtype(prik_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(f2py_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(prik_c, f2py_c, operation_size=2)
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_cgemm(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex64)
    original_c = np.asfortranarray([[9.0j, 10.0], [11.0, 12.0j]], dtype=np.complex64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.cgemm(
        "N",
        "C",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.cgemm(
        b"N",
        b"C",
        np.int32(2),
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

    expected_c = alpha * (a @ b.conj().T) + original_c
    assert_allclose_for_dtype(prik_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(f2py_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(prik_c, f2py_c, operation_size=2)
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_zgemm(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(-1.0j)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex128)
    original_c = np.asfortranarray([[9.0j, 10.0], [11.0, 12.0j]], dtype=np.complex128)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zgemm(
        "T",
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.zgemm(
        b"T",
        b"N",
        np.int32(2),
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

    expected_c = alpha * (a.T @ b) + beta * original_c
    assert_allclose_for_dtype(prik_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(f2py_c, expected_c, operation_size=2)
    assert_allclose_for_dtype(prik_c, f2py_c, operation_size=2)
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_sgemmtr(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    original_c = np.asfortranarray([[9.0, 10.0], [np.nan, 12.0]], dtype=np.float32)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.sgemmtr(
        "U",
        "N",
        "N",
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.sgemmtr(
        b"U",
        b"N",
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

    expected_c = alpha * (a @ b) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_dgemmtr(prik_blas, f2py_blas):
    alpha, beta = np.float64(-0.75), np.float64(1.0)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float64)
    original_c = np.asfortranarray([[9.0, np.nan], [11.0, 12.0]], dtype=np.float64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.dgemmtr(
        "L",
        "T",
        "N",
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.dgemmtr(
        b"L",
        b"T",
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

    expected_c = alpha * (a.T @ b) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_cgemmtr(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex64)
    original_c = np.asfortranarray([[9.0j, 10.0], [np.nan + 1.0j * np.nan, 12.0j]], dtype=np.complex64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.cgemmtr(
        "U",
        "N",
        "C",
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.cgemmtr(
        b"U",
        b"N",
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

    expected_c = alpha * (a @ b.conj().T) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_zgemmtr(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex128)
    original_c = np.asfortranarray([[9.0j, np.nan + 1.0j * np.nan], [11.0, 12.0j]], dtype=np.complex128)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zgemmtr(
        "L",
        "C",
        "N",
        np.int32(2),
        np.int32(2),
        alpha,
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        beta,
        prik_c,
        np.int32(2),
    )
    f2py_blas.zgemmtr(
        b"L",
        b"C",
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

    expected_c = alpha * (a.conj().T @ b) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)
