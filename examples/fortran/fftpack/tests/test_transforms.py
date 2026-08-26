"""Every public FFTPACK procedure checked against NumPy or SciPy."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import fft as scipy_fft

from .helpers import numpy_rfft_packing, take_owned_array


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_zffti(fftpack):
    values = np.array([1.0 + 2.0j, -2.0 + 1.0j, 4.0 - 3.0j, 3.0 + 0.5j, -1.0j], dtype=np.complex128)
    expected = np.fft.fft(values)
    n = np.int32(values.size)
    wsave = np.full(4 * n + 15, np.nan, dtype=np.float64)

    fftpack.zffti(n, wsave)
    fftpack.zfftf(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_zfftf(fftpack):
    values = np.array([1.0 + 2.0j, -2.0 + 1.0j, 4.0 - 3.0j, 3.0 + 0.5j, -1.0j], dtype=np.complex128)
    expected = np.fft.fft(values)
    wsave = np.empty(4 * values.size + 15, dtype=np.float64)
    fftpack.zffti(np.int32(values.size), wsave)

    fftpack.zfftf(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_zfftb(fftpack):
    values = np.array([1.0 + 2.0j, -2.0 + 1.0j, 4.0 - 3.0j, 3.0 + 0.5j, -1.0j], dtype=np.complex128)
    expected = values * values.size
    wsave = np.empty(4 * values.size + 15, dtype=np.float64)
    fftpack.zffti(np.int32(values.size), wsave)
    fftpack.zfftf(np.int32(values.size), values, wsave)

    fftpack.zfftb(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dffti(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = numpy_rfft_packing(values)
    n = np.int32(values.size)
    wsave = np.full(2 * n + 15, np.nan, dtype=np.float64)

    fftpack.dffti(n, wsave)
    fftpack.dfftf(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dfftf(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = numpy_rfft_packing(values)
    wsave = np.empty(2 * values.size + 15, dtype=np.float64)
    fftpack.dffti(np.int32(values.size), wsave)

    fftpack.dfftf(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dfftb(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = values * values.size
    wsave = np.empty(2 * values.size + 15, dtype=np.float64)
    fftpack.dffti(np.int32(values.size), wsave)
    fftpack.dfftf(np.int32(values.size), values, wsave)

    fftpack.dfftb(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dzffti(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    spectrum = np.fft.rfft(values)
    coefficients_a = np.empty((values.size + 1) // 2, dtype=np.float64)
    coefficients_b = np.empty_like(coefficients_a)
    n = np.int32(values.size)
    wsave = np.full(3 * n + 15, np.nan, dtype=np.float64)

    fftpack.dzffti(n, wsave)
    azero = fftpack.dzfftf(n, values, coefficients_a, coefficients_b, wsave)

    np.testing.assert_allclose(azero, spectrum[0].real / values.size, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(coefficients_a[:-1], 2.0 * spectrum[1:].real / values.size, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(coefficients_b[:-1], -2.0 * spectrum[1:].imag / values.size, rtol=0.0, atol=1.0e-12)


def test_dzfftf(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    spectrum = np.fft.rfft(values)
    coefficients_a = np.empty((values.size + 1) // 2, dtype=np.float64)
    coefficients_b = np.empty_like(coefficients_a)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dzffti(np.int32(values.size), wsave)

    azero = fftpack.dzfftf(np.int32(values.size), values, coefficients_a, coefficients_b, wsave)

    np.testing.assert_allclose(azero, spectrum[0].real / values.size, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(coefficients_a[:-1], 2.0 * spectrum[1:].real / values.size, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(coefficients_b[:-1], -2.0 * spectrum[1:].imag / values.size, rtol=0.0, atol=1.0e-12)


def test_dzfftb(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    coefficients_a = np.empty((values.size + 1) // 2, dtype=np.float64)
    coefficients_b = np.empty_like(coefficients_a)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dzffti(np.int32(values.size), wsave)
    azero = fftpack.dzfftf(np.int32(values.size), values, coefficients_a, coefficients_b, wsave)
    result = np.empty_like(values)

    fftpack.dzfftb(np.int32(values.size), result, np.float64(azero), coefficients_a, coefficients_b, wsave)

    np.testing.assert_allclose(result, values, rtol=0.0, atol=1.0e-12)


def test_dcosqi(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=3, norm=None)
    n = np.int32(values.size)
    wsave = np.full(3 * n + 15, np.nan, dtype=np.float64)

    fftpack.dcosqi(n, wsave)
    fftpack.dcosqf(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dcosqf(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=3, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dcosqi(np.int32(values.size), wsave)

    fftpack.dcosqf(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dcosqb(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = 2.0 * scipy_fft.dct(values, type=2, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dcosqi(np.int32(values.size), wsave)

    fftpack.dcosqb(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dcosti(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=1, norm=None)
    n = np.int32(values.size)
    wsave = np.full(3 * n + 15, np.nan, dtype=np.float64)

    fftpack.dcosti(n, wsave)
    fftpack.dcost(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dcost(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=1, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dcosti(np.int32(values.size), wsave)

    fftpack.dcost(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dsinti(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dst(values, type=1, norm=None)
    n = np.int32(values.size)
    wsave = np.full(2 * n + 15, np.nan, dtype=np.float64)

    fftpack.dsinti(n, wsave)
    fftpack.dsint(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dsint(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dst(values, type=1, norm=None)
    wsave = np.empty(2 * values.size + 15, dtype=np.float64)
    fftpack.dsinti(np.int32(values.size), wsave)

    fftpack.dsint(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_fft(fftpack):
    values = np.array([1.0 + 2.0j, 2.0 - 1.0j, -1.0 + 1.0j, 3.0], dtype=np.complex128)
    original = values.copy()

    result = take_owned_array(fftpack.fft(values))

    np.testing.assert_allclose(result, np.fft.fft(values), rtol=0.0, atol=1.0e-12)
    np.testing.assert_array_equal(values, original)


def test_ifft(fftpack):
    spectrum = np.array([5.0 + 2.0j, 4.0 - 1.0j, -5.0 + 2.0j, -3.0j], dtype=np.complex128)
    original = spectrum.copy()

    result = take_owned_array(fftpack.ifft(spectrum))

    np.testing.assert_allclose(result, np.fft.ifft(spectrum) * spectrum.size, rtol=0.0, atol=1.0e-12)
    np.testing.assert_array_equal(spectrum, original)


def test_rfft(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    original = values.copy()

    result = take_owned_array(fftpack.rfft(values))

    np.testing.assert_allclose(result, numpy_rfft_packing(values), rtol=0.0, atol=1.0e-12)
    np.testing.assert_array_equal(values, original)


def test_irfft(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    packed = take_owned_array(fftpack.rfft(values))

    result = take_owned_array(fftpack.irfft(packed))

    np.testing.assert_allclose(result, values * values.size, rtol=0.0, atol=1.0e-12)


def test_dct(fftpack):
    values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

    for transform_type, scale in ((1, 1.0), (2, 2.0), (3, 1.0)):
        result = take_owned_array(fftpack.dct(values, type=np.int32(transform_type)))
        reference = scipy_fft.dct(values, type=transform_type, norm=None) * scale
        np.testing.assert_allclose(result, reference, rtol=0.0, atol=1.0e-12)


def test_idct(fftpack):
    values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

    for transform_type, scale in ((1, 2 * (values.size - 1)), (2, 4 * values.size), (3, 4 * values.size)):
        transformed = take_owned_array(fftpack.dct(values, type=np.int32(transform_type)))
        result = take_owned_array(fftpack.idct(transformed, type=np.int32(transform_type)))
        np.testing.assert_allclose(result, values * scale, rtol=0.0, atol=1.0e-12)


def test_dct_t1i(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=1, norm=None)
    n = np.int32(values.size)
    wsave = np.full(3 * n + 15, np.nan, dtype=np.float64)

    fftpack.dct_t1i(n, wsave)
    fftpack.dct_t1(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dct_t1(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=1, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dct_t1i(np.int32(values.size), wsave)

    fftpack.dct_t1(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dct_t23i(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = 2.0 * scipy_fft.dct(values, type=2, norm=None)
    n = np.int32(values.size)
    wsave = np.full(3 * n + 15, np.nan, dtype=np.float64)

    fftpack.dct_t23i(n, wsave)
    fftpack.dct_t2(n, values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dct_t2(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = 2.0 * scipy_fft.dct(values, type=2, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dct_t23i(np.int32(values.size), wsave)

    fftpack.dct_t2(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_dct_t3(fftpack):
    values = np.array([1.0, -2.0, 4.0, 3.0, -1.0], dtype=np.float64)
    expected = scipy_fft.dct(values, type=3, norm=None)
    wsave = np.empty(3 * values.size + 15, dtype=np.float64)
    fftpack.dct_t23i(np.int32(values.size), wsave)

    fftpack.dct_t3(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)


def test_fftfreq(fftpack):
    for size, expected in ((4, [0, 1, -2, -1]), (5, [0, 1, 2, -2, -1])):
        np.testing.assert_array_equal(fftpack.fftfreq(np.int32(size)), expected)


def test_rfftfreq(fftpack):
    for size, expected in ((4, [0, 1, 1, -2]), (5, [0, 1, 1, 2, 2])):
        np.testing.assert_array_equal(fftpack.rfftfreq(np.int32(size)), expected)


def test_fftshift(fftpack):
    for values in (np.arange(5, dtype=np.float64), np.arange(6, dtype=np.float64) + 1.0j):
        np.testing.assert_array_equal(fftpack.fftshift(values), np.fft.fftshift(values))


def test_ifftshift(fftpack):
    for values in (np.arange(5, dtype=np.float64), np.arange(6, dtype=np.float64) + 1.0j):
        np.testing.assert_array_equal(fftpack.ifftshift(values), np.fft.ifftshift(values))
