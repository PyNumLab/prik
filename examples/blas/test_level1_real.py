"""Readable independent and differential checks for real BLAS Level 1."""

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


def test_saxpy(prik_blas, f2py_blas):
    alpha = np.float32(2.5)
    x = np.array([1.0, -2.0, 3.0], dtype=np.float32)
    original_y = np.array([10.0, 20.0, -5.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.saxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.saxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_daxpy(prik_blas, f2py_blas):
    alpha = np.float64(-1.5)
    x = np.array([2.0, -4.0, 1.0], dtype=np.float64)
    original_y = np.array([3.0, 5.0, -2.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.daxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.daxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_ddot(prik_blas, f2py_blas):
    x = np.array([1.0, -2.0, 4.0], dtype=np.float64)
    y = np.array([3.0, 5.0, -1.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, n, incx, incy = prik_blas.ddot(np.int32(3), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.ddot(np.int32(3), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.float64(1.0 * 3.0 + (-2.0) * 5.0 + 4.0 * (-1.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert (n, incx, incy) == (np.int32(3), np.int32(1), np.int32(1))
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_sasum(prik_blas, f2py_blas):
    x = np.array([-1.0, 99.0, 2.5, 98.0, -3.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.sasum(np.int32(3), prik_x, np.int32(2))
    f2py_value = f2py_blas.sasum(np.int32(3), f2py_x, np.int32(2))

    expected = np.float32(abs(-1.0) + abs(2.5) + abs(-3.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dasum(prik_blas, f2py_blas):
    x = np.array([-1.5, 2.0, -4.25], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.dasum(np.int32(3), prik_x, np.int32(1))
    f2py_value = f2py_blas.dasum(np.int32(3), f2py_x, np.int32(1))

    expected = np.float64(1.5 + 2.0 + 4.25)
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_scopy(prik_blas, f2py_blas):
    x = np.array([1.0, 90.0, 2.0, 91.0, 3.0], dtype=np.float32)
    original_y = np.array([-1.0, 80.0, -2.0, 81.0, -3.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.scopy(np.int32(3), prik_x, np.int32(2), prik_y, np.int32(2))
    f2py_blas.scopy(np.int32(3), f2py_x, np.int32(2), f2py_y, np.int32(2))

    expected_y = with_logical_vector(original_y, logical_vector(x, 3, 2), 3, 2)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dcopy(prik_blas, f2py_blas):
    x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    original_y = np.array([7.0, 8.0, 9.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.dcopy(np.int32(3), prik_x, np.int32(-1), prik_y, np.int32(1))
    f2py_blas.dcopy(np.int32(3), f2py_x, np.int32(-1), f2py_y, np.int32(1))

    expected_y = np.array([3.0, 2.0, 1.0], dtype=np.float64)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_sdot(prik_blas, f2py_blas):
    x = np.array([1.0, 99.0, -2.0, 98.0, 3.0], dtype=np.float32)
    y = np.array([4.0, 5.0, -1.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.sdot(np.int32(3), prik_x, np.int32(2), prik_y, np.int32(1))
    f2py_value = f2py_blas.sdot(np.int32(3), f2py_x, np.int32(2), f2py_y, np.int32(1))

    expected = np.float32(1.0 * 4.0 + (-2.0) * 5.0 + 3.0 * (-1.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_sdsdot(prik_blas, f2py_blas):
    bias = np.float32(1.25)
    x = np.array([1.0, -2.0, 3.0], dtype=np.float32)
    y = np.array([4.0, 0.5, -1.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.sdsdot(np.int32(3), bias, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.sdsdot(np.int32(3), bias, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.float32(np.float64(bias) + 1.0 * 4.0 + (-2.0) * 0.5 + 3.0 * (-1.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_dsdot(prik_blas, f2py_blas):
    x = np.array([1.0e10, 1.0, -1.0e10], dtype=np.float32)
    y = np.ones(3, dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, *_ = prik_blas.dsdot(np.int32(3), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.dsdot(np.int32(3), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.float64(np.float64(x[0]) + np.float64(x[1]) + np.float64(x[2]))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)


def test_snrm2(prik_blas, f2py_blas):
    x = np.array([3.0, 99.0, 4.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.snrm2(np.int32(2), prik_x, np.int32(2))
    f2py_value = f2py_blas.snrm2(np.int32(2), f2py_x, np.int32(2))

    expected = np.float32(np.sqrt(np.float32(3.0**2 + 4.0**2)))
    assert_allclose_for_dtype(prik_value, expected, operation_size=2)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=2)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=2)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_dnrm2(prik_blas, f2py_blas):
    x = np.array([2.0, -3.0, 6.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_value, *_ = prik_blas.dnrm2(np.int32(3), prik_x, np.int32(1))
    f2py_value = f2py_blas.dnrm2(np.int32(3), f2py_x, np.int32(1))

    expected = np.float64(np.sqrt(2.0**2 + (-3.0) ** 2 + 6.0**2))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_srot(prik_blas, f2py_blas):
    c, s = np.float32(0.6), np.float32(0.8)
    x = np.array([1.0, 2.0], dtype=np.float32)
    y = np.array([3.0, 4.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.srot(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1), c, s)
    f2py_blas.srot(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1), c, s)

    expected_x = c * x + s * y
    expected_y = c * y - s * x
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_x, f2py_x)
    assert_allclose_for_dtype(prik_y, f2py_y)


def test_drot(prik_blas, f2py_blas):
    c, s = np.float64(0.8), np.float64(-0.6)
    x = np.array([1.0, 90.0, 2.0], dtype=np.float64)
    y = np.array([3.0, 80.0, 4.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.drot(np.int32(2), prik_x, np.int32(2), prik_y, np.int32(2), c, s)
    f2py_blas.drot(np.int32(2), f2py_x, np.int32(2), f2py_y, np.int32(2), c, s)

    expected_x = with_logical_vector(x, c * x[::2] + s * y[::2], 2, 2)
    expected_y = with_logical_vector(y, c * y[::2] - s * x[::2], 2, 2)
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_x, f2py_x)
    assert_allclose_for_dtype(prik_y, f2py_y)


def test_srotg(prik_blas, f2py_blas):
    a, b = np.float32(3.0), np.float32(4.0)
    f2py_a = np.array(a, dtype=np.float32)
    f2py_b = np.array(b, dtype=np.float32)
    f2py_c = np.array(0.0, dtype=np.float32)
    f2py_s = np.array(0.0, dtype=np.float32)

    prik_a, prik_b, c, s = prik_blas.srotg(a, b, np.float32(0.0), np.float32(0.0))
    f2py_result = f2py_blas.srotg(f2py_a, f2py_b, f2py_c, f2py_s)

    assert_allclose_for_dtype(prik_a, np.float32(5.0))
    assert_allclose_for_dtype(prik_b, np.float32(5.0 / 3.0))
    assert_allclose_for_dtype(c * a + s * b, prik_a, operation_size=2)
    assert_allclose_for_dtype(-s * a + c * b, np.float32(0.0), operation_size=2)
    assert_allclose_for_dtype([f2py_a, f2py_b, f2py_c, f2py_s], [prik_a, prik_b, c, s])
    assert f2py_result is None


def test_drotg(prik_blas, f2py_blas):
    a, b = np.float64(3.0), np.float64(4.0)
    f2py_a = np.array(a, dtype=np.float64)
    f2py_b = np.array(b, dtype=np.float64)
    f2py_c = np.array(0.0, dtype=np.float64)
    f2py_s = np.array(0.0, dtype=np.float64)

    prik_a, prik_b, c, s = prik_blas.drotg(a, b, np.float64(0.0), np.float64(0.0))
    f2py_result = f2py_blas.drotg(f2py_a, f2py_b, f2py_c, f2py_s)

    assert_allclose_for_dtype(prik_a, np.float64(5.0))
    assert_allclose_for_dtype(prik_b, np.float64(5.0 / 3.0))
    assert_allclose_for_dtype(c * a + s * b, prik_a, operation_size=2)
    assert_allclose_for_dtype(-s * a + c * b, np.float64(0.0), operation_size=2)
    assert_allclose_for_dtype([f2py_a, f2py_b, f2py_c, f2py_s], [prik_a, prik_b, c, s])
    assert f2py_result is None


def test_srotm(prik_blas, f2py_blas):
    x = np.array([1.0, 2.0], dtype=np.float32)
    y = np.array([3.0, 4.0], dtype=np.float32)
    param = np.array([-1.0, 2.0, 0.5, -0.25, 3.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_param, f2py_param = param.copy(), param.copy()

    prik_blas.srotm(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1), prik_param)
    f2py_blas.srotm(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_param)

    expected_x = param[1] * x + param[3] * y
    expected_y = param[2] * x + param[4] * y
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_storage_unchanged(prik_param, param)
    assert_storage_unchanged(f2py_param, param)


def test_drotm(prik_blas, f2py_blas):
    x = np.array([1.0, 2.0], dtype=np.float64)
    y = np.array([3.0, 4.0], dtype=np.float64)
    param = np.array([-1.0, 2.0, 0.5, -0.25, 3.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()
    prik_param, f2py_param = param.copy(), param.copy()

    prik_blas.drotm(np.int32(2), prik_x, np.int32(1), prik_y, np.int32(1), prik_param)
    f2py_blas.drotm(np.int32(2), f2py_x, np.int32(1), f2py_y, np.int32(1), f2py_param)

    expected_x = param[1] * x + param[3] * y
    expected_y = param[2] * x + param[4] * y
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_y, expected_y, operation_size=2)
    assert_allclose_for_dtype(f2py_y, expected_y, operation_size=2)
    assert_storage_unchanged(prik_param, param)
    assert_storage_unchanged(f2py_param, param)


def test_srotmg(prik_blas, f2py_blas):
    prik_param = np.zeros(5, dtype=np.float32)
    f2py_param = np.zeros(5, dtype=np.float32)
    f2py_scalars = [np.array(value, dtype=np.float32) for value in (1.0, 2.0, 3.0, 4.0)]

    prik_values = prik_blas.srotmg(np.float32(1.0), np.float32(2.0), np.float32(3.0), np.float32(4.0), prik_param)
    f2py_result = f2py_blas.srotmg(*f2py_scalars, f2py_param)

    expected_values = np.array([1.5609756, 0.7804878, 5.125, 4.0], dtype=np.float32)
    expected_param = np.array([1.0, 0.375, 0.0, 0.0, 0.75], dtype=np.float32)
    assert_allclose_for_dtype(prik_values, expected_values, operation_size=2)
    assert_allclose_for_dtype(f2py_scalars, expected_values, operation_size=2)
    assert_allclose_for_dtype(f2py_scalars, prik_values, operation_size=2)
    assert_allclose_for_dtype(prik_param, expected_param)
    assert_allclose_for_dtype(f2py_param, expected_param)
    assert_allclose_for_dtype(prik_param, f2py_param)
    assert f2py_result is None


def test_drotmg(prik_blas, f2py_blas):
    prik_param = np.zeros(5, dtype=np.float64)
    f2py_param = np.zeros(5, dtype=np.float64)
    f2py_scalars = [np.array(value, dtype=np.float64) for value in (1.0, 2.0, 3.0, 4.0)]

    prik_values = prik_blas.drotmg(np.float64(1.0), np.float64(2.0), np.float64(3.0), np.float64(4.0), prik_param)
    f2py_result = f2py_blas.drotmg(*f2py_scalars, f2py_param)

    expected_values = np.array([1.5609756097560976, 0.7804878048780488, 5.125, 4.0])
    expected_param = np.array([1.0, 0.375, 0.0, 0.0, 0.75])
    assert_allclose_for_dtype(prik_values, expected_values, operation_size=2)
    assert_allclose_for_dtype(f2py_scalars, expected_values, operation_size=2)
    assert_allclose_for_dtype(f2py_scalars, prik_values, operation_size=2)
    assert_allclose_for_dtype(prik_param, expected_param)
    assert_allclose_for_dtype(f2py_param, expected_param)
    assert_allclose_for_dtype(prik_param, f2py_param)
    assert f2py_result is None


def test_sscal(prik_blas, f2py_blas):
    alpha = np.float32(-2.0)
    original = np.array([3.0], dtype=np.float32)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.sscal(np.int32(1), alpha, prik_x, np.int32(1))
    f2py_blas.sscal(np.int32(1), alpha, f2py_x, np.int32(1))

    expected = alpha * original
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_dscal(prik_blas, f2py_blas):
    alpha = np.float64(0.5)
    original = np.array([2.0, 90.0, -4.0], dtype=np.float64)
    prik_x, f2py_x = original.copy(), original.copy()

    prik_blas.dscal(np.int32(2), alpha, prik_x, np.int32(2))
    f2py_blas.dscal(np.int32(2), alpha, f2py_x, np.int32(2))

    expected = with_logical_vector(original, alpha * original[::2], 2, 2)
    assert_allclose_for_dtype(prik_x, expected)
    assert_allclose_for_dtype(f2py_x, expected)
    assert_allclose_for_dtype(prik_x, f2py_x)


def test_sswap(prik_blas, f2py_blas):
    x = np.array([1.0, 90.0, 2.0], dtype=np.float32)
    y = np.array([3.0, 80.0, 4.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.sswap(np.int32(2), prik_x, np.int32(2), prik_y, np.int32(2))
    f2py_blas.sswap(np.int32(2), f2py_x, np.int32(2), f2py_y, np.int32(2))

    expected_x = with_logical_vector(x, y[::2], 2, 2)
    expected_y = with_logical_vector(y, x[::2], 2, 2)
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_dswap(prik_blas, f2py_blas):
    x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    y = np.array([4.0, 5.0, 6.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_blas.dswap(np.int32(3), prik_x, np.int32(-1), prik_y, np.int32(1))
    f2py_blas.dswap(np.int32(3), f2py_x, np.int32(-1), f2py_y, np.int32(1))

    expected_x = np.array([6.0, 5.0, 4.0])
    expected_y = np.array([3.0, 2.0, 1.0])
    assert_allclose_for_dtype(prik_x, expected_x)
    assert_allclose_for_dtype(f2py_x, expected_x)
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)


def test_isamax(prik_blas, f2py_blas):
    x = np.array([1.0, -7.0, 3.0], dtype=np.float32)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_index, *_ = prik_blas.isamax(np.int32(3), prik_x, np.int32(1))
    f2py_index = f2py_blas.isamax(np.int32(3), f2py_x, np.int32(1))

    expected_native_one_based_index = 2
    assert prik_index == expected_native_one_based_index
    assert f2py_index == expected_native_one_based_index
    assert prik_index == f2py_index
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_idamax(prik_blas, f2py_blas):
    x = np.array([1.0, 90.0, -8.0, 91.0, 3.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()

    prik_index, *_ = prik_blas.idamax(np.int32(3), prik_x, np.int32(2))
    f2py_index = f2py_blas.idamax(np.int32(3), f2py_x, np.int32(2))

    expected_native_one_based_index = 2
    assert prik_index == expected_native_one_based_index
    assert f2py_index == expected_native_one_based_index
    assert prik_index == f2py_index
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)


def test_daxpy_alpha_zero_preserves_y(prik_blas, f2py_blas):
    x = np.array([1.0, 2.0], dtype=np.float64)
    original_y = np.array([3.0, 4.0], dtype=np.float64)
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_blas.daxpy(np.int32(2), np.float64(0.0), x.copy(), np.int32(1), prik_y, np.int32(1))
    f2py_blas.daxpy(np.int32(2), np.float64(0.0), x.copy(), np.int32(1), f2py_y, np.int32(1))

    assert_storage_unchanged(prik_y, original_y)
    assert_storage_unchanged(f2py_y, original_y)


def test_sdot_empty_input(prik_blas, f2py_blas):
    x = np.array([91.0], dtype=np.float32)
    y = np.array([92.0], dtype=np.float32)

    prik_value, *_ = prik_blas.sdot(np.int32(0), x.copy(), np.int32(1), y.copy(), np.int32(1))
    f2py_value = f2py_blas.sdot(np.int32(0), x.copy(), np.int32(1), y.copy(), np.int32(1))

    assert_allclose_for_dtype(prik_value, np.float32(0.0))
    assert_allclose_for_dtype(f2py_value, np.float32(0.0))
