"""Readable independent and differential checks for complex BLAS Level 1."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import (
    assert_allclose_for_dtype,
    assert_storage_unchanged,
    logical_vector,
    with_logical_vector,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_caxpy(prik_blas, f2py_blas):
    alpha = np.complex64(1.5 - 0.5j)
    x = np.array([1.0 + 2.0j, -2.0 + 1.0j, 0.5 - 3.0j], dtype=np.complex64)
    original_y = np.array([3.0 - 1.0j, 2.0 + 4.0j, -5.0 + 0.5j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.caxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.caxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zaxpy(prik_blas, f2py_blas):
    alpha = np.complex128(-0.25 + 2.0j)
    x = np.array([2.0 - 1.0j, 3.0 + 0.5j, -1.0 + 4.0j], dtype=np.complex128)
    original_y = np.array([1.0 + 3.0j, -2.0 + 1.0j, 5.0 - 0.5j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.zaxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.zaxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_scasum(prik_blas, f2py_blas):
    x = np.array([1.0 - 2.0j, 90.0j, -3.0 + 4.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.scasum(np.int32(2), prik_x, np.int32(2))
    f2py_value = f2py_blas.scasum(np.int32(2), f2py_x, np.int32(2))

    expected = np.float32(1.0 + 2.0 + 3.0 + 4.0)
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dzasum(prik_blas, f2py_blas):
    x = np.array([1.5 - 2.5j, -3.0 + 4.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.dzasum(np.int32(2), prik_x, np.int32(1))
    f2py_value = f2py_blas.dzasum(np.int32(2), f2py_x, np.int32(1))

    expected = np.float64(1.5 + 2.5 + 3.0 + 4.0)
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_ccopy(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, 90.0j, -3.0 + 4.0j], dtype=np.complex64)
    original_y = np.array([5.0 - 1.0j, 80.0j, 6.0 + 2.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.ccopy(np.int32(2), prik_x, np.int32(2), prik_y, np.int32(2))
    f2py_blas.ccopy(np.int32(2), f2py_x, np.int32(2), f2py_y, np.int32(2))

    expected_y = with_logical_vector(original_y, logical_vector(x, 2, 2), 2, 2)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_zcopy(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -3.0 + 4.0j], dtype=np.complex128)
    original_y = np.array([5.0 - 1.0j, 6.0 + 2.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.zcopy(np.int32(2), prik_x, np.int32(-1), prik_y, np.int32(1))
    f2py_blas.zcopy(np.int32(2), f2py_x, np.int32(-1), f2py_y, np.int32(1))

    expected_y = x[::-1]
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_cdotc(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -3.0 + 1.0j], dtype=np.complex64)
    y = np.array([2.0 - 1.0j, 4.0 + 3.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.cdotc(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.cdotc(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.conj(x[0]) * y[0] + np.conj(x[1]) * y[1]
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zdotc(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, 90.0j, -3.0 + 1.0j], dtype=np.complex128)
    y = np.array([2.0 - 1.0j, 4.0 + 3.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.zdotc(np.int32(2), prik_x, np.int32(2), prik_y, np.int32(1))
    f2py_value = f2py_blas.zdotc(np.int32(2), f2py_x, np.int32(2), f2py_y, np.int32(1))

    expected = np.conj(x[0]) * y[0] + np.conj(x[2]) * y[1]
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_cdotu(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -3.0 + 1.0j], dtype=np.complex64)
    y = np.array([2.0 - 1.0j, 4.0 + 3.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.cdotu(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.cdotu(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = x[0] * y[0] + x[1] * y[1]
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_zdotu(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -3.0 + 1.0j], dtype=np.complex128)
    y = np.array([2.0 - 1.0j, 4.0 + 3.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.zdotu(np.int32(2), prik_x, np.int32(-1), prik_y, np.int32(1))
    f2py_value = f2py_blas.zdotu(np.int32(2), f2py_x, np.int32(-1), f2py_y, np.int32(1))

    expected = x[1] * y[0] + x[0] * y[1]
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_scnrm2(prik_blas, f2py_blas):
    x = np.array([3.0 + 0.0j, 90.0j, 0.0 + 4.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.scnrm2(np.int32(2), prik_x, np.int32(2))
    f2py_value = f2py_blas.scnrm2(np.int32(2), f2py_x, np.int32(2))

    expected = np.float32(np.sqrt(3.0**2 + 4.0**2))
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dznrm2(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -3.0 + 4.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.dznrm2(np.int32(2), prik_x, np.int32(1))
    f2py_value = f2py_blas.dznrm2(np.int32(2), f2py_x, np.int32(1))

    expected = np.float64(np.sqrt(1.0**2 + 2.0**2 + 3.0**2 + 4.0**2))
    assert_allclose_for_dtype(prik_value, expected, operation_size=4)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=4)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=4)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_crotg(prik_blas, f2py_blas):
    a, b = np.complex64(3.0 + 1.0j), np.complex64(4.0 - 2.0j)
    f2py_a = np.array(a, dtype=np.complex64)
    f2py_b = np.array(b, dtype=np.complex64)
    f2py_c = np.array(0.0, dtype=np.float32)
    f2py_s = np.array(0.0j, dtype=np.complex64)

    result, prik_b, c, s = prik_blas.crotg(a, b, np.float32(0.0), np.complex64(0.0j))
    f2py_result = f2py_blas.crotg(f2py_a, f2py_b, f2py_c, f2py_s)

    assert_allclose_for_dtype(c * a + s * b, result, operation_size=2)
    assert_allclose_for_dtype(-np.conj(s) * a + c * b, np.complex64(0.0j), operation_size=2)
    assert_allclose_for_dtype(c * c + abs(s) ** 2, np.float32(1.0), operation_size=2)
    assert_allclose_for_dtype([f2py_a, f2py_b, f2py_c, f2py_s], [result, prik_b, c, s])
    assert f2py_result is None


def test_zrotg(prik_blas, f2py_blas):
    a, b = np.complex128(3.0 + 1.0j), np.complex128(4.0 - 2.0j)
    f2py_a = np.array(a, dtype=np.complex128)
    f2py_b = np.array(b, dtype=np.complex128)
    f2py_c = np.array(0.0, dtype=np.float64)
    f2py_s = np.array(0.0j, dtype=np.complex128)

    result, prik_b, c, s = prik_blas.zrotg(a, b, np.float64(0.0), np.complex128(0.0j))
    f2py_result = f2py_blas.zrotg(f2py_a, f2py_b, f2py_c, f2py_s)

    assert_allclose_for_dtype(c * a + s * b, result, operation_size=2)
    assert_allclose_for_dtype(-np.conj(s) * a + c * b, np.complex128(0.0j), operation_size=2)
    assert_allclose_for_dtype(c * c + abs(s) ** 2, np.float64(1.0), operation_size=2)
    assert_allclose_for_dtype([f2py_a, f2py_b, f2py_c, f2py_s], [result, prik_b, c, s])
    assert f2py_result is None


def test_cscal(prik_blas, f2py_blas):
    alpha = np.complex64(1.0 - 2.0j)
    original = np.array([2.0 + 1.0j, -3.0 + 4.0j], dtype=np.complex64)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.cscal(np.int32(2), alpha, prik_x, np.int32(1))
    f2py_blas.cscal(np.int32(2), alpha, f2py_x, np.int32(1))

    expected = alpha * original
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_zscal(prik_blas, f2py_blas):
    alpha = np.complex128(-0.5 + 1.5j)
    original = np.array([2.0 + 1.0j, 90.0j, -3.0 + 4.0j], dtype=np.complex128)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.zscal(np.int32(2), alpha, prik_x, np.int32(2))
    f2py_blas.zscal(np.int32(2), alpha, f2py_x, np.int32(2))

    expected = with_logical_vector(original, alpha * original[::2], 2, 2)
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_csscal(prik_blas, f2py_blas):
    alpha = np.float32(-2.0)
    original = np.array([2.0 + 1.0j, -3.0 + 4.0j], dtype=np.complex64)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.csscal(np.int32(2), alpha, prik_x, np.int32(1))
    f2py_blas.csscal(np.int32(2), alpha, f2py_x, np.int32(1))

    expected = alpha * original
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_zdscal(prik_blas, f2py_blas):
    alpha = np.float64(0.25)
    original = np.array([2.0 + 1.0j, -3.0 + 4.0j], dtype=np.complex128)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.zdscal(np.int32(2), alpha, prik_x, np.int32(1))
    f2py_blas.zdscal(np.int32(2), alpha, f2py_x, np.int32(1))

    expected = alpha * original
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_csrot(prik_blas, f2py_blas):
    c, s = np.float32(0.6), np.float32(0.8)
    x = np.array([1.0 + 2.0j, -2.0 + 1.0j], dtype=np.complex64)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.csrot(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1), c, s)
    f2py_blas.csrot(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1), c, s)

    expected_x = c * x + s * y
    expected_y = c * y - s * x
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_zdrot(prik_blas, f2py_blas):
    c, s = np.float64(0.8), np.float64(-0.6)
    x = np.array([1.0 + 2.0j, -2.0 + 1.0j], dtype=np.complex128)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.zdrot(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1), c, s)
    f2py_blas.zdrot(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1), c, s)

    expected_x = c * x + s * y
    expected_y = c * y - s * x
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_cswap(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, 90.0j, -2.0 + 1.0j], dtype=np.complex64)
    y = np.array([3.0 - 1.0j, 80.0j, 4.0 + 2.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.cswap(np.int32(2), prik_x, np.int32(2), prik_y, np.int32(2))
    f2py_blas.cswap(np.int32(2), f2py_x, np.int32(2), f2py_y, np.int32(2))

    expected_x = with_logical_vector(x, y[::2], 2, 2)
    expected_y = with_logical_vector(y, x[::2], 2, 2)
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_zswap(prik_blas, f2py_blas):
    x = np.array([1.0 + 2.0j, -2.0 + 1.0j], dtype=np.complex128)
    y = np.array([3.0 - 1.0j, 4.0 + 2.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.zswap(np.int32(2), prik_x, np.int32(-1), prik_y, np.int32(1))
    f2py_blas.zswap(np.int32(2), f2py_x, np.int32(-1), f2py_y, np.int32(1))

    expected_x = y[::-1]
    expected_y = x[::-1]
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_icamax(prik_blas, f2py_blas):
    x = np.array([1.0 + 1.0j, -4.0 + 5.0j, 3.0 - 2.0j], dtype=np.complex64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_index, *_ = prik_blas.icamax(np.int32(3), prik_x, np.int32(1))
    f2py_index = f2py_blas.icamax(np.int32(3), f2py_x, np.int32(1))

    expected_native_one_based_index = 2
    assert prik_index == expected_native_one_based_index
    assert f2py_index == expected_native_one_based_index
    assert prik_index == f2py_index
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_izamax(prik_blas, f2py_blas):
    x = np.array([1.0 + 1.0j, 90.0j, -4.0 + 5.0j, 80.0j, 3.0 - 2.0j], dtype=np.complex128)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_index, *_ = prik_blas.izamax(np.int32(3), prik_x, np.int32(2))
    f2py_index = f2py_blas.izamax(np.int32(3), f2py_x, np.int32(2))

    expected_native_one_based_index = 2
    assert prik_index == expected_native_one_based_index
    assert f2py_index == expected_native_one_based_index
    assert prik_index == f2py_index
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
