"""Readable independent and differential checks for symmetric BLAS Level 3."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged, symmetric_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ssymm(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0]], dtype=np.float32)
    b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    original_c = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    logical_a = symmetric_from_triangle(a, 2, "U")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.ssymm(
        "L", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.ssymm(
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


def test_dsymm(prik_blas, f2py_blas):
    alpha, beta = np.float64(-2.0), np.float64(1.0)
    a = np.asfortranarray([[2.0, np.nan], [-1.0, 3.0]], dtype=np.float64)
    b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    original_c = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float64)
    logical_a = symmetric_from_triangle(a, 2, "L")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.dsymm(
        "R", "L", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.dsymm(
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


def test_csymm(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    a = np.asfortranarray([[2.0 + 1.0j, -1.0 + 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 1.0j]], dtype=np.complex64)
    b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    original_c = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j]], dtype=np.complex64)
    logical_a = symmetric_from_triangle(a, 2, "U")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.csymm(
        "L", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.csymm(
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


def test_zsymm(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    a = np.asfortranarray([[2.0 + 1.0j, np.nan + 1.0j * np.nan], [-1.0 + 2.0j, 3.0 - 1.0j]], dtype=np.complex128)
    b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    original_c = np.asfortranarray([[5.0j, 6.0], [7.0, 8.0j]], dtype=np.complex128)
    logical_a = symmetric_from_triangle(a, 2, "L")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zsymm(
        "R", "L", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.zsymm(
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


def test_ssyrk(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    original_c = np.asfortranarray([[5.0, 6.0], [np.nan, 8.0]], dtype=np.float32)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.ssyrk("U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.ssyrk(b"U", b"N", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a @ a.T) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_dsyrk(prik_blas, f2py_blas):
    alpha, beta = np.float64(-0.75), np.float64(1.0)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    original_c = np.asfortranarray([[5.0, np.nan], [7.0, 8.0]], dtype=np.float64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.dsyrk("L", "T", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.dsyrk(b"L", b"T", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a.T @ a) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_csyrk(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    original_c = np.asfortranarray([[5.0j, 6.0], [np.nan + 1.0j * np.nan, 8.0j]], dtype=np.complex64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.csyrk("U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.csyrk(b"U", b"N", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a @ a.T) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=2)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_zsyrk(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    original_c = np.asfortranarray([[5.0j, np.nan + 1.0j * np.nan], [7.0, 8.0j]], dtype=np.complex128)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zsyrk("L", "T", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), beta, prik_c, np.int32(2))
    f2py_blas.zsyrk(b"L", b"T", np.int32(2), np.int32(2), alpha, f2py_a, beta, f2py_c, lda=np.int32(2), ldc=np.int32(2))

    expected_c = alpha * (a.T @ a) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=2)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=2)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_ssyr2k(prik_blas, f2py_blas):
    alpha, beta = np.float32(0.75), np.float32(-0.5)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    original_c = np.asfortranarray([[9.0, 10.0], [np.nan, 12.0]], dtype=np.float32)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.ssyr2k(
        "U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.ssyr2k(
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

    expected_c = alpha * (a @ b.T + b @ a.T) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=4)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_dsyr2k(prik_blas, f2py_blas):
    alpha, beta = np.float64(-0.25), np.float64(1.0)
    a = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    b = np.asfortranarray([[5.0, 6.0], [7.0, 8.0]], dtype=np.float64)
    original_c = np.asfortranarray([[9.0, np.nan], [11.0, 12.0]], dtype=np.float64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.dsyr2k(
        "L", "T", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.dsyr2k(
        b"L",
        b"T",
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

    expected_c = alpha * (a.T @ b + b.T @ a) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=4)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_csyr2k(prik_blas, f2py_blas):
    alpha, beta = np.complex64(0.5 - 0.25j), np.complex64(0.25j)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex64)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex64)
    original_c = np.asfortranarray([[9.0j, 10.0], [np.nan + 1.0j * np.nan, 12.0j]], dtype=np.complex64)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.csyr2k(
        "U", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.csyr2k(
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

    expected_c = alpha * (a @ b.T + b @ a.T) + beta * original_c
    upper = np.triu_indices(2)
    assert_allclose_for_dtype(prik_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(f2py_c[upper], expected_c[upper], operation_size=4)
    assert_allclose_for_dtype(prik_c[upper], f2py_c[upper], operation_size=4)
    np.testing.assert_array_equal(prik_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    np.testing.assert_array_equal(f2py_c[np.tril_indices(2, -1)], original_c[np.tril_indices(2, -1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)


def test_zsyr2k(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.75 + 0.5j), np.complex128(1.0)
    a = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j]], dtype=np.complex128)
    b = np.asfortranarray([[5.0 + 2.0j, 6.0], [7.0 - 1.0j, 8.0 + 1.0j]], dtype=np.complex128)
    original_c = np.asfortranarray([[9.0j, np.nan + 1.0j * np.nan], [11.0, 12.0j]], dtype=np.complex128)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_c, f2py_c = original_c.copy(order="F"), original_c.copy(order="F")

    prik_blas.zsyr2k(
        "L", "T", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(2), beta, prik_c, np.int32(2)
    )
    f2py_blas.zsyr2k(
        b"L",
        b"T",
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

    expected_c = alpha * (a.T @ b + b.T @ a) + original_c
    lower = np.tril_indices(2)
    assert_allclose_for_dtype(prik_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(f2py_c[lower], expected_c[lower], operation_size=4)
    assert_allclose_for_dtype(prik_c[lower], f2py_c[lower], operation_size=4)
    np.testing.assert_array_equal(prik_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    np.testing.assert_array_equal(f2py_c[np.triu_indices(2, 1)], original_c[np.triu_indices(2, 1)])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
    assert_storage_unchanged(prik_b, b)
    assert_storage_unchanged(f2py_b, b)
