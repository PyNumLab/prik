"""Readable independent and differential checks for packed BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import (
    assert_allclose_for_dtype,
    assert_storage_unchanged,
    hermitian_from_packed,
    packed_from_triangle,
    symmetric_from_packed,
    triangular_from_packed,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_sspmv(prik_blas, f2py_blas):
    alpha, beta = np.float32(1.5), np.float32(-0.5)
    ap = packed_from_triangle(np.array([[2.0, -1.0], [91.0, 3.0]], dtype=np.float32), "U")
    x = np.array([2.0, -3.0], dtype=np.float32)
    original_y = np.array([4.0, 5.0], dtype=np.float32)
    logical_a = symmetric_from_packed(ap, 2, "U")
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.sspmv("U", np.int32(2), alpha, prik_ap, prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.sspmv(b"U", np.int32(2), alpha, f2py_ap, f2py_x, np.int32(1), beta, f2py_y, np.int32(1))

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dspmv(prik_blas, f2py_blas):
    alpha, beta = np.float64(-2.0), np.float64(1.0)
    ap = packed_from_triangle(np.array([[2.0, 91.0], [-1.0, 3.0]], dtype=np.float64), "L")
    x = np.array([2.0, -3.0], dtype=np.float64)
    original_y = np.array([4.0, 5.0], dtype=np.float64)
    logical_a = symmetric_from_packed(ap, 2, "L")
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dspmv("L", np.int32(2), alpha, prik_ap, prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.dspmv(b"L", np.int32(2), alpha, f2py_ap, f2py_x, np.int32(1), beta, f2py_y, np.int32(1))

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_sspr(prik_blas, f2py_blas):
    alpha = np.float32(0.75)
    original_ap = packed_from_triangle(np.array([[3.0, 1.0], [91.0, 4.0]], dtype=np.float32), "U")
    x = np.array([2.0, -1.0], dtype=np.float32)
    logical_a = symmetric_from_packed(original_ap, 2, "U")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()

    prik_blas.sspr("U", np.int32(2), alpha, prik_x, np.int32(1), prik_ap)
    f2py_blas.sspr(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_ap)

    expected_ap = packed_from_triangle(logical_a + alpha * x[:, None] * x[None, :], "U")
    assert_allclose_for_dtype(prik_ap, expected_ap)
    assert_allclose_for_dtype(f2py_ap, expected_ap)
    assert_allclose_for_dtype(prik_ap, f2py_ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dspr(prik_blas, f2py_blas):
    alpha = np.float64(-0.5)
    original_ap = packed_from_triangle(np.array([[3.0, 91.0], [1.0, 4.0]], dtype=np.float64), "L")
    x = np.array([2.0, -1.0], dtype=np.float64)
    logical_a = symmetric_from_packed(original_ap, 2, "L")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()

    prik_blas.dspr("L", np.int32(2), alpha, prik_x, np.int32(1), prik_ap)
    f2py_blas.dspr(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_ap)

    expected_ap = packed_from_triangle(logical_a + alpha * x[:, None] * x[None, :], "L")
    assert_allclose_for_dtype(prik_ap, expected_ap)
    assert_allclose_for_dtype(f2py_ap, expected_ap)
    assert_allclose_for_dtype(prik_ap, f2py_ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_sspr2(prik_blas, f2py_blas):
    alpha = np.float32(0.25)
    original_ap = packed_from_triangle(np.array([[3.0, 1.0], [91.0, 4.0]], dtype=np.float32), "U")
    x = np.array([2.0, -1.0], dtype=np.float32)
    y = np.array([-3.0, 4.0], dtype=np.float32)
    logical_a = symmetric_from_packed(original_ap, 2, "U")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.sspr2("U", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_ap)
    f2py_blas.sspr2(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_ap)

    expected = logical_a + alpha * (x[:, None] * y[None, :] + y[:, None] * x[None, :])
    expected_ap = packed_from_triangle(expected, "U")
    assert_allclose_for_dtype(prik_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(f2py_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(prik_ap, f2py_ap, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_dspr2(prik_blas, f2py_blas):
    alpha = np.float64(-0.75)
    original_ap = packed_from_triangle(np.array([[3.0, 91.0], [1.0, 4.0]], dtype=np.float64), "L")
    x = np.array([2.0, -1.0], dtype=np.float64)
    y = np.array([-3.0, 4.0], dtype=np.float64)
    logical_a = symmetric_from_packed(original_ap, 2, "L")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.dspr2("L", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_ap)
    f2py_blas.dspr2(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_ap)

    expected = logical_a + alpha * (x[:, None] * y[None, :] + y[:, None] * x[None, :])
    expected_ap = packed_from_triangle(expected, "L")
    assert_allclose_for_dtype(prik_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(f2py_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(prik_ap, f2py_ap, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_chpmv(prik_blas, f2py_blas):
    alpha, beta = np.complex64(1.0 - 0.5j), np.complex64(0.25j)
    ap = packed_from_triangle(np.array([[2.0 + 77.0j, 1.0 - 2.0j], [91.0j, 3.0 - 88.0j]], dtype=np.complex64), "U")
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    original_y = np.array([4.0 - 2.0j, 5.0 + 3.0j], dtype=np.complex64)
    logical_a = hermitian_from_packed(ap, 2, "U")
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.chpmv("U", np.int32(2), alpha, prik_ap, prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.chpmv(b"U", np.int32(2), alpha, f2py_ap, f2py_x, np.int32(1), beta, f2py_y, np.int32(1))

    expected_y = alpha * logical_a @ x + beta * original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zhpmv(prik_blas, f2py_blas):
    alpha, beta = np.complex128(-0.5 + 0.25j), np.complex128(1.0)
    ap = packed_from_triangle(np.array([[2.0 + 77.0j, 91.0j], [1.0 + 2.0j, 3.0 - 88.0j]], dtype=np.complex128), "L")
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    original_y = np.array([4.0 - 2.0j, 5.0 + 3.0j], dtype=np.complex128)
    logical_a = hermitian_from_packed(ap, 2, "L")
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zhpmv("L", np.int32(2), alpha, prik_ap, prik_x, np.int32(1), beta, prik_y, np.int32(1))
    f2py_blas.zhpmv(b"L", np.int32(2), alpha, f2py_ap, f2py_x, np.int32(1), beta, f2py_y, np.int32(1))

    expected_y = alpha * logical_a @ x + original_y
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(prik_y, f2py_y, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_chpr(prik_blas, f2py_blas):
    alpha = np.float32(0.75)
    original_ap = packed_from_triangle(
        np.array([[3.0 + 9.0j, 1.0 - 2.0j], [91.0j, 4.0 - 8.0j]], dtype=np.complex64), "U"
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    logical_a = hermitian_from_packed(original_ap, 2, "U")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()

    prik_blas.chpr("U", np.int32(2), alpha, prik_x, np.int32(1), prik_ap)
    f2py_blas.chpr(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_ap)

    expected_ap = packed_from_triangle(logical_a + alpha * x[:, None] * np.conj(x[None, :]), "U")
    assert_allclose_for_dtype(prik_ap, expected_ap)
    assert_allclose_for_dtype(f2py_ap, expected_ap)
    assert_allclose_for_dtype(prik_ap, f2py_ap)
    assert np.all(np.imag(prik_ap[[0, 2]]) == 0.0)
    assert np.all(np.imag(f2py_ap[[0, 2]]) == 0.0)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zhpr(prik_blas, f2py_blas):
    alpha = np.float64(-0.25)
    original_ap = packed_from_triangle(
        np.array([[3.0 + 9.0j, 91.0j], [1.0 + 2.0j, 4.0 - 8.0j]], dtype=np.complex128), "L"
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    logical_a = hermitian_from_packed(original_ap, 2, "L")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()

    prik_blas.zhpr("L", np.int32(2), alpha, prik_x, np.int32(1), prik_ap)
    f2py_blas.zhpr(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_ap)

    expected_ap = packed_from_triangle(logical_a + alpha * x[:, None] * np.conj(x[None, :]), "L")
    assert_allclose_for_dtype(prik_ap, expected_ap)
    assert_allclose_for_dtype(f2py_ap, expected_ap)
    assert_allclose_for_dtype(prik_ap, f2py_ap)
    assert np.all(np.imag(prik_ap[[0, 2]]) == 0.0)
    assert np.all(np.imag(f2py_ap[[0, 2]]) == 0.0)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_chpr2(prik_blas, f2py_blas):
    alpha = np.complex64(0.5 - 0.25j)
    original_ap = packed_from_triangle(
        np.array([[3.0 + 9.0j, 1.0 - 2.0j], [91.0j, 4.0 - 8.0j]], dtype=np.complex64), "U"
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex64)
    y = np.array([-3.0 + 0.5j, 4.0 - 2.0j], dtype=np.complex64)
    logical_a = hermitian_from_packed(original_ap, 2, "U")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.chpr2("U", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_ap)
    f2py_blas.chpr2(b"U", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_ap)

    expected = logical_a + alpha * x[:, None] * np.conj(y[None, :]) + np.conj(alpha) * y[:, None] * np.conj(x[None, :])
    expected_ap = packed_from_triangle(expected, "U")
    assert_allclose_for_dtype(prik_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(f2py_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(prik_ap, f2py_ap, operation_size=2)
    assert np.all(np.imag(prik_ap[[0, 2]]) == 0.0)
    assert np.all(np.imag(f2py_ap[[0, 2]]) == 0.0)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zhpr2(prik_blas, f2py_blas):
    alpha = np.complex128(-0.75 + 0.5j)
    original_ap = packed_from_triangle(
        np.array([[3.0 + 9.0j, 91.0j], [1.0 + 2.0j, 4.0 - 8.0j]], dtype=np.complex128), "L"
    )
    x = np.array([2.0 + 1.0j, -1.0 + 0.5j], dtype=np.complex128)
    y = np.array([-3.0 + 0.5j, 4.0 - 2.0j], dtype=np.complex128)
    logical_a = hermitian_from_packed(original_ap, 2, "L")
    prik_ap, f2py_ap = original_ap.copy(), original_ap.copy()
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.zhpr2("L", np.int32(2), alpha, prik_x, np.int32(1), prik_y, np.int32(1), prik_ap)
    f2py_blas.zhpr2(b"L", np.int32(2), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_ap)

    expected = logical_a + alpha * x[:, None] * np.conj(y[None, :]) + np.conj(alpha) * y[:, None] * np.conj(x[None, :])
    expected_ap = packed_from_triangle(expected, "L")
    assert_allclose_for_dtype(prik_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(f2py_ap, expected_ap, operation_size=2)
    assert_allclose_for_dtype(prik_ap, f2py_ap, operation_size=2)
    assert np.all(np.imag(prik_ap[[0, 2]]) == 0.0)
    assert np.all(np.imag(f2py_ap[[0, 2]]) == 0.0)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_stpmv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[2.0, -1.0], [91.0, 3.0]], dtype=np.float32), "U")
    original_x = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_packed(ap, 2, "U", unit_diagonal=False)
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.stpmv("U", "N", "N", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.stpmv(b"U", b"N", b"N", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_dtpmv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[np.nan, 91.0], [-1.0, np.nan]], dtype=np.float64), "L")
    original_x = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_packed(ap, 2, "L", unit_diagonal=True)
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.dtpmv("L", "T", "U", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.dtpmv(b"L", b"T", b"U", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    expected_x = logical_a.T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_ctpmv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[2.0 + 1.0j, -1.0 + 2.0j], [91.0j, 3.0 - 1.0j]], dtype=np.complex64), "U")
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_packed(ap, 2, "U", unit_diagonal=False)
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ctpmv("U", "C", "N", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.ctpmv(b"U", b"C", b"N", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    expected_x = logical_a.conj().T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_ztpmv(prik_blas, f2py_blas):
    nan = np.nan + 1.0j * np.nan
    ap = packed_from_triangle(np.array([[nan, 91.0j], [-1.0 + 2.0j, nan]], dtype=np.complex128), "L")
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_packed(ap, 2, "L", unit_diagonal=True)
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ztpmv("L", "N", "U", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.ztpmv(b"L", b"N", b"U", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_stpsv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[2.0, -1.0], [91.0, 3.0]], dtype=np.float32), "U")
    expected_solution = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_packed(ap, 2, "U", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.stpsv("U", "N", "N", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.stpsv(b"U", b"N", b"N", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_dtpsv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[np.nan, 91.0], [-1.0, np.nan]], dtype=np.float64), "L")
    expected_solution = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_packed(ap, 2, "L", unit_diagonal=True)
    original_b = logical_a.T @ expected_solution
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.dtpsv("L", "T", "U", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.dtpsv(b"L", b"T", b"U", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    assert_allclose_for_dtype(logical_a.T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_ctpsv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[2.0 + 1.0j, -1.0 + 2.0j], [91.0j, 3.0 - 1.0j]], dtype=np.complex64), "U")
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_packed(ap, 2, "U", unit_diagonal=False)
    original_b = logical_a.conj().T @ expected_solution
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ctpsv("U", "C", "N", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.ctpsv(b"U", b"C", b"N", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    assert_allclose_for_dtype(logical_a.conj().T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.conj().T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)


def test_ztpsv(prik_blas, f2py_blas):
    ap = packed_from_triangle(np.array([[2.0 + 1.0j, 91.0j], [-1.0 + 2.0j, 3.0 - 1.0j]], dtype=np.complex128), "L")
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_packed(ap, 2, "L", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_ap, f2py_ap = ap.copy(), ap.copy()
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ztpsv("L", "N", "N", np.int32(2), prik_ap, prik_x, np.int32(1))
    f2py_blas.ztpsv(b"L", b"N", b"N", np.int32(2), f2py_ap, f2py_x, np.int32(1))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_ap, ap)
    assert_storage_unchanged(f2py_ap, ap)
