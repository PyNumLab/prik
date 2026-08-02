"""Readable independent and differential checks for banded BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import (
    assert_allclose_for_dtype,
    assert_storage_unchanged,
    general_from_band,
    hermitian_from_band,
    symmetric_from_band,
    triangular_from_band,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_sgbmv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [4.0, 92.0], [93.0, 94.0]], dtype=np.float32)
    x = np.array([2.0, -3.0], dtype=np.float32)
    original_y = np.array([4.0, 5.0], dtype=np.float32)
    logical_a = general_from_band(original_a, 2, 2, 1, 1)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.sgbmv(
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        prik_a,
        np.int32(4),
        prik_x,
        np.int32(1),
        beta,
        prik_y,
        np.int32(1),
    )
    f2py_blas.sgbmv(
        b"N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        f2py_a,
        f2py_x,
        np.int32(1),
        beta,
        f2py_y,
        np.int32(1),
        lda=np.int32(4),
    )

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dgbmv(prik_blas, f2py_blas):
    alpha, beta = np.float64(-2.0), np.float64(1.0)
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [4.0, 92.0], [93.0, 94.0]], dtype=np.float64)
    x = np.array([2.0, -3.0], dtype=np.float64)
    original_y = np.array([4.0, 5.0], dtype=np.float64)
    logical_a = general_from_band(original_a, 2, 2, 1, 1)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dgbmv(
        "T",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        prik_a,
        np.int32(4),
        prik_x,
        np.int32(1),
        beta,
        prik_y,
        np.int32(1),
    )
    f2py_blas.dgbmv(
        b"T",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        f2py_a,
        f2py_x,
        np.int32(1),
        beta,
        f2py_y,
        np.int32(1),
        lda=np.int32(4),
    )

    expected_y = alpha * logical_a.T @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_cgbmv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    original_a = np.asfortranarray(
        [[91.0j, -1.0 + 2.0j], [2.0 + 1.0j, 3.0 - 1.0j], [4.0 + 0.5j, 92.0j], [93.0j, 94.0j]], dtype=np.complex64
    )
    x = np.array([2.0 + 1.0j, -3.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([4.0 - 1.0j, 5.0 + 2.0j], dtype=np.complex64)
    logical_a = general_from_band(original_a, 2, 2, 1, 1)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.cgbmv(
        "N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        prik_a,
        np.int32(4),
        prik_x,
        np.int32(1),
        beta,
        prik_y,
        np.int32(1),
    )
    f2py_blas.cgbmv(
        b"N",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        f2py_a,
        f2py_x,
        np.int32(1),
        beta,
        f2py_y,
        np.int32(1),
        lda=np.int32(4),
    )

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zgbmv(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    original_a = np.asfortranarray(
        [[91.0j, -1.0 + 2.0j], [2.0 + 1.0j, 3.0 - 1.0j], [4.0 + 0.5j, 92.0j], [93.0j, 94.0j]], dtype=np.complex128
    )
    x = np.array([2.0 + 1.0j, -3.0 + 0.5j], dtype=np.complex128)
    original_y = np.array([4.0 - 1.0j, 5.0 + 2.0j], dtype=np.complex128)
    logical_a = general_from_band(original_a, 2, 2, 1, 1)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zgbmv(
        "C",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        prik_a,
        np.int32(4),
        prik_x,
        np.int32(1),
        beta,
        prik_y,
        np.int32(1),
    )
    f2py_blas.zgbmv(
        b"C",
        np.int32(2),
        np.int32(2),
        np.int32(1),
        np.int32(1),
        alpha,
        f2py_a,
        f2py_x,
        np.int32(1),
        beta,
        f2py_y,
        np.int32(1),
        lda=np.int32(4),
    )

    expected_y = alpha * logical_a.conj().T @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_ssbmv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [93.0, 94.0]], dtype=np.float32)
    x = np.array([2.0, -3.0], dtype=np.float32)
    original_y = np.array([4.0, 5.0], dtype=np.float32)
    logical_a = symmetric_from_band(original_a, 2, 1, "U")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.ssbmv(
        "U", np.int32(2), np.int32(1), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.ssbmv(
        b"U", np.int32(2), np.int32(1), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dsbmv(prik_blas, f2py_blas):
    alpha, beta = np.float64(-2.0), np.float64(1.0)
    original_a = np.asfortranarray([[2.0, 3.0], [-1.0, 92.0], [93.0, 94.0]], dtype=np.float64)
    x = np.array([2.0, -3.0], dtype=np.float64)
    original_y = np.array([4.0, 5.0], dtype=np.float64)
    logical_a = symmetric_from_band(original_a, 2, 1, "L")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dsbmv(
        "L", np.int32(2), np.int32(1), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.dsbmv(
        b"L", np.int32(2), np.int32(1), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_chbmv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    original_a = np.asfortranarray(
        [[91.0j, -1.0 + 2.0j], [2.0 + 77.0j, 3.0 - 88.0j], [93.0j, 94.0j]], dtype=np.complex64
    )
    x = np.array([2.0 + 1.0j, -3.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([4.0 - 1.0j, 5.0 + 2.0j], dtype=np.complex64)
    logical_a = hermitian_from_band(original_a, 2, 1, "U")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.chbmv(
        "U", np.int32(2), np.int32(1), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.chbmv(
        b"U", np.int32(2), np.int32(1), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zhbmv(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    original_a = np.asfortranarray(
        [[2.0 + 77.0j, 3.0 - 88.0j], [-1.0 - 2.0j, 92.0j], [93.0j, 94.0j]], dtype=np.complex128
    )
    x = np.array([2.0 + 1.0j, -3.0 + 0.5j], dtype=np.complex128)
    original_y = np.array([4.0 - 1.0j, 5.0 + 2.0j], dtype=np.complex128)
    logical_a = hermitian_from_band(original_a, 2, 1, "L")
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zhbmv(
        "L", np.int32(2), np.int32(1), alpha, prik_a, np.int32(3), prik_x, np.int32(1), beta, prik_y, np.int32(1)
    )
    f2py_blas.zhbmv(
        b"L", np.int32(2), np.int32(1), alpha, f2py_a, f2py_x, np.int32(1), beta, f2py_y, np.int32(1), lda=np.int32(3)
    )

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_stbmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [93.0, 94.0]], dtype=np.float32)
    original_x = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_band(original_a, 2, 1, "U", unit_diagonal=False)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.stbmv("U", "N", "N", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.stbmv(b"U", b"N", b"N", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_dtbmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[np.nan, np.nan], [-1.0, 92.0], [93.0, 94.0]], dtype=np.float64)
    original_x = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_band(original_a, 2, 1, "L", unit_diagonal=True)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.dtbmv("L", "T", "U", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.dtbmv(b"L", b"T", b"U", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a.T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ctbmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[91.0j, -1.0 + 2.0j], [2.0 + 1.0j, 3.0 - 1.0j], [93.0j, 94.0j]], dtype=np.complex64)
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_band(original_a, 2, 1, "U", unit_diagonal=False)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ctbmv("U", "C", "N", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ctbmv(b"U", b"C", b"N", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a.conj().T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ztbmv(prik_blas, f2py_blas):
    nan = np.nan + 1.0j * np.nan
    original_a = np.asfortranarray([[nan, nan], [-1.0 + 2.0j, 92.0j], [93.0j, 94.0j]], dtype=np.complex128)
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_band(original_a, 2, 1, "L", unit_diagonal=True)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ztbmv("L", "N", "U", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ztbmv(b"L", b"N", b"U", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_stbsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[91.0, -1.0], [2.0, 3.0], [93.0, 94.0]], dtype=np.float32)
    expected_solution = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_band(original_a, 2, 1, "U", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.stbsv("U", "N", "N", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.stbsv(b"U", b"N", b"N", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_dtbsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[np.nan, np.nan], [-1.0, 92.0], [93.0, 94.0]], dtype=np.float64)
    expected_solution = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_band(original_a, 2, 1, "L", unit_diagonal=True)
    original_b = logical_a.T @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.dtbsv("L", "T", "U", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.dtbsv(b"L", b"T", b"U", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a.T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ctbsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[91.0j, -1.0 + 2.0j], [2.0 + 1.0j, 3.0 - 1.0j], [93.0j, 94.0j]], dtype=np.complex64)
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_band(original_a, 2, 1, "U", unit_diagonal=False)
    original_b = logical_a.conj().T @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ctbsv("U", "C", "N", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ctbsv(b"U", b"C", b"N", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a.conj().T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.conj().T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ztbsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray(
        [[2.0 + 1.0j, 3.0 - 1.0j], [-1.0 + 2.0j, 92.0j], [93.0j, 94.0j]], dtype=np.complex128
    )
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_band(original_a, 2, 1, "L", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ztbsv("L", "N", "N", np.int32(2), np.int32(1), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ztbsv(b"L", b"N", b"N", np.int32(2), np.int32(1), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
