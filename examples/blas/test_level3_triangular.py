"""Readable independent and differential checks for triangular BLAS Level 3."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_for_dtype, assert_storage_unchanged, triangular_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_strmm(prik_blas, f2py_blas):
    alpha = np.float32(1.5)
    a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0]], dtype=np.float32)
    original_b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float32)
    logical_a = triangular_from_triangle(a, 2, "U", unit_diagonal=False)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.strmm("L", "U", "N", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.strmm(
        b"L", b"U", b"N", b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = alpha * logical_a @ original_b[:2, :]
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_dtrmm(prik_blas, f2py_blas):
    alpha = np.float64(-0.5)
    a = np.asfortranarray([[np.nan, np.nan], [-1.0, np.nan]], dtype=np.float64)
    original_b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    logical_a = triangular_from_triangle(a, 2, "L", unit_diagonal=True)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.dtrmm("R", "L", "T", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.dtrmm(
        b"R", b"L", b"T", b"U", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = alpha * original_b[:2, :] @ logical_a.T
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_ctrmm(prik_blas, f2py_blas):
    alpha = np.complex64(1.0 - 0.5j)
    a = np.asfortranarray([[2.0 + 1.0j, -1.0 + 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 1.0j]], dtype=np.complex64)
    original_b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j], [91.0j, 92.0j]], dtype=np.complex64)
    logical_a = triangular_from_triangle(a, 2, "U", unit_diagonal=False)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.ctrmm("L", "U", "C", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.ctrmm(
        b"L", b"U", b"C", b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = alpha * logical_a.conj().T @ original_b[:2, :]
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_ztrmm(prik_blas, f2py_blas):
    alpha = np.complex128(-0.5 + 0.25j)
    nan = np.nan + 1.0j * np.nan
    a = np.asfortranarray([[nan, nan], [-1.0 + 2.0j, nan]], dtype=np.complex128)
    original_b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j], [91.0j, 92.0j]], dtype=np.complex128)
    logical_a = triangular_from_triangle(a, 2, "L", unit_diagonal=True)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.ztrmm("R", "L", "N", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.ztrmm(
        b"R", b"L", b"N", b"U", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = alpha * original_b[:2, :] @ logical_a
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_strsm(prik_blas, f2py_blas):
    alpha = np.float32(1.5)
    a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0]], dtype=np.float32)
    original_b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float32)
    logical_a = triangular_from_triangle(a, 2, "U", unit_diagonal=False)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.strsm("L", "U", "N", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.strsm(
        b"L", b"U", b"N", b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = np.linalg.solve(logical_a, alpha * original_b[:2, :])
    assert_allclose_for_dtype(logical_a @ prik_b[:2, :], alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_b[:2, :], alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_dtrsm(prik_blas, f2py_blas):
    alpha = np.float64(-0.5)
    a = np.asfortranarray([[np.nan, np.nan], [-1.0, np.nan]], dtype=np.float64)
    original_b = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [91.0, 92.0]], dtype=np.float64)
    logical_a = triangular_from_triangle(a, 2, "L", unit_diagonal=True)
    op_a = logical_a.T
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.dtrsm("R", "L", "T", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.dtrsm(
        b"R", b"L", b"T", b"U", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = np.linalg.solve(op_a.T, (alpha * original_b[:2, :]).T).T
    assert_allclose_for_dtype(prik_b[:2, :] @ op_a, alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :] @ op_a, alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_ctrsm(prik_blas, f2py_blas):
    alpha = np.complex64(1.0 - 0.5j)
    a = np.asfortranarray([[2.0 + 1.0j, -1.0 + 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 1.0j]], dtype=np.complex64)
    original_b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j], [91.0j, 92.0j]], dtype=np.complex64)
    logical_a = triangular_from_triangle(a, 2, "U", unit_diagonal=False)
    op_a = logical_a.conj().T
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.ctrsm("L", "U", "C", "N", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.ctrsm(
        b"L", b"U", b"C", b"N", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = np.linalg.solve(op_a, alpha * original_b[:2, :])
    assert_allclose_for_dtype(op_a @ prik_b[:2, :], alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(op_a @ f2py_b[:2, :], alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)


def test_ztrsm(prik_blas, f2py_blas):
    alpha = np.complex128(-0.5 + 0.25j)
    nan = np.nan + 1.0j * np.nan
    a = np.asfortranarray([[nan, nan], [-1.0 + 2.0j, nan]], dtype=np.complex128)
    original_b = np.asfortranarray([[1.0 + 1.0j, 2.0], [3.0 - 1.0j, 4.0 + 0.5j], [91.0j, 92.0j]], dtype=np.complex128)
    logical_a = triangular_from_triangle(a, 2, "L", unit_diagonal=True)
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")

    prik_blas.ztrsm("R", "L", "N", "U", np.int32(2), np.int32(2), alpha, prik_a, np.int32(2), prik_b, np.int32(3))
    f2py_blas.ztrsm(
        b"R", b"L", b"N", b"U", np.int32(2), np.int32(2), alpha, f2py_a, f2py_b, lda=np.int32(2), ldb=np.int32(3)
    )

    expected_b = np.linalg.solve(logical_a.T, (alpha * original_b[:2, :]).T).T
    assert_allclose_for_dtype(prik_b[:2, :] @ logical_a, alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :] @ logical_a, alpha * original_b[:2, :], operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(f2py_b[:2, :], expected_b, operation_size=2)
    assert_allclose_for_dtype(prik_b[:2, :], f2py_b[:2, :], operation_size=2)
    np.testing.assert_array_equal(prik_b[2, :], original_b[2, :])
    np.testing.assert_array_equal(f2py_b[2, :], original_b[2, :])
    assert_storage_unchanged(prik_a, a)
    assert_storage_unchanged(f2py_a, a)
