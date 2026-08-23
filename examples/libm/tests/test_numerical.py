"""Grouped numerical evidence for the reviewed ISO C99 libm surface."""

from __future__ import annotations

import math

import numpy as np
import pytest

pytestmark = pytest.mark.real_library
DOUBLE_TOLERANCE = 1e-12
FLOAT32_TOLERANCE = 4 * np.finfo(np.float32).eps


def test_elementary(libm):
    assert np.isclose(libm.sin(np.float64(1.0)), math.sin(1.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.cos(np.float64(1.0)), math.cos(1.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.tan(np.float64(0.5)), math.tan(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.asin(np.float64(0.5)), math.asin(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.acos(np.float64(0.5)), math.acos(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.atan(np.float64(0.5)), math.atan(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(
        libm.atan2(np.float64(1.0), np.float64(2.0)),
        math.atan2(1.0, 2.0),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert np.isclose(libm.sinh(np.float64(0.75)), math.sinh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.cosh(np.float64(0.75)), math.cosh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.tanh(np.float64(0.75)), math.tanh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.asinh(np.float64(0.75)), math.asinh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.acosh(np.float64(1.75)), math.acosh(1.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.atanh(np.float64(0.75)), math.atanh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.exp(np.float64(1.0)), math.e, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)

    # exp2 is exact on a whole exponent, so no tolerance is needed.
    assert libm.exp2(np.float64(10.0)) == 1024.0

    # expm1 keeps the precision that exp(x) - 1 loses for small x.
    assert np.isclose(
        libm.expm1(np.float64(1e-9)),
        math.expm1(1e-9),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert libm.expm1(np.float64(1e-9)) != math.exp(1e-9) - 1.0

    assert np.isclose(libm.log(np.float64(math.e)), 1.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.log2(np.float64(1024.0)) == 10.0
    assert np.isclose(libm.log10(np.float64(1000.0)), 3.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.log1p(np.float64(1e-9)), math.log1p(1e-9), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.pow(np.float64(2.0), np.float64(10.0)) == 1024.0
    assert libm.sqrt(np.float64(144.0)) == 12.0
    assert np.isclose(libm.cbrt(np.float64(27.0)), 3.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.hypot(np.float64(3.0), np.float64(4.0)) == 5.0


def test_precision(libm, public_long_double_dtype):
    result = libm.sinf(np.float32(1.0))
    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.sin(1.0)), rtol=FLOAT32_TOLERANCE, atol=0.0)

    result = libm.cosf(np.float32(1.0))
    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.cos(1.0)), rtol=FLOAT32_TOLERANCE, atol=0.0)

    result = libm.expf(np.float32(1.0))
    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.exp(1.0)), rtol=FLOAT32_TOLERANCE, atol=0.0)

    result = libm.logf(np.float32(math.e))
    assert result.dtype == np.float32
    assert np.isclose(result, 1.0, rtol=1e-6, atol=1e-6)

    result = libm.sqrtf(np.float32(144.0))
    assert result.dtype == np.float32
    assert result == np.float32(12.0)

    result = libm.sinl(public_long_double_dtype.type(1.0))
    assert result.dtype == public_long_double_dtype
    assert np.isclose(result, math.sin(1.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)

    result = libm.sqrtl(public_long_double_dtype.type(2))
    assert result.dtype == public_long_double_dtype
    assert np.isclose(result, math.sqrt(2.0), rtol=1e-15, atol=1e-15)


def test_rounding(libm, public_long_double_dtype):
    assert libm.ceil(np.float64(2.1)) == 3.0
    assert libm.floor(np.float64(2.9)) == 2.0
    assert libm.trunc(np.float64(-2.9)) == -2.0

    # C `round` breaks ties away from zero, unlike Python's banker's rounding.
    assert libm.round(np.float64(2.5)) == 3.0
    assert libm.round(np.float64(-2.5)) == -3.0

    # nearbyint and rint follow the active floating-point rounding mode.
    assert libm.nearbyint(np.float64(2.5)) == libm.rint(np.float64(2.5))
    assert libm.nearbyint(np.float64(-2.5)) == libm.rint(np.float64(-2.5))
    result = libm.rint(np.float64(2.5))
    assert result in {2.0, 3.0}
    assert result == libm.nearbyint(np.float64(2.5))

    result = libm.lrint(np.float64(2.7))
    assert result == np.long(libm.rint(np.float64(2.7)))
    assert result.dtype == np.dtype(np.long)
    assert libm.llrint(np.float64(2.7)) == np.int64(libm.rint(np.float64(2.7)))
    assert libm.llrint(np.float64(-2.7)) == np.int64(libm.rint(np.float64(-2.7)))

    result = libm.lround(np.float64(2.5))
    assert result == np.long(3)
    assert result.dtype == np.dtype(np.long)
    assert libm.llround(np.float64(2.5)) == np.int64(3)
    assert libm.llround(np.float64(-2.5)) == np.int64(-3)

    assert np.isclose(
        libm.fmod(np.float64(10.0), np.float64(3.0)),
        math.fmod(10.0, 3.0),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )

    # IEEE remainder rounds the quotient to nearest, so it differs from fmod.
    assert np.isclose(
        libm.remainder(np.float64(10.0), np.float64(3.0)),
        math.remainder(10.0, 3.0),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert libm.remainder(np.float64(10.0), np.float64(6.0)) == -2.0

    assert libm.copysign(np.float64(2.0), np.float64(-0.0)) == -2.0
    assert libm.fabs(np.float64(-2.5)) == 2.5
    assert libm.fdim(np.float64(5.0), np.float64(3.0)) == 2.0
    assert libm.fdim(np.float64(3.0), np.float64(5.0)) == 0.0
    assert libm.fmax(np.float64(2.0), np.float64(3.0)) == 3.0
    assert libm.fmin(np.float64(2.0), np.float64(3.0)) == 2.0
    assert libm.fma(np.float64(2.0), np.float64(3.0), np.float64(4.0)) == 10.0

    # A single rounding keeps the product bits an unfused expression discards.
    left, right = 1.0 + 2.0**-52, 1.0 - 2.0**-52
    assert libm.fma(np.float64(left), np.float64(right), np.float64(-1.0)) == -(2.0**-104)
    assert left * right - 1.0 == 0.0

    assert libm.ldexp(np.float64(1.5), np.intc(3)) == 12.0
    assert libm.scalbn(np.float64(1.5), np.intc(3)) == 12.0
    assert libm.scalbln(np.float64(1.5), np.long(3)) == 12.0
    assert libm.nextafter(np.float64(1.0), np.float64(2.0)) == math.nextafter(1.0, 2.0)
    assert libm.nexttoward(np.float64(1.0), public_long_double_dtype.type(2.0)) == math.nextafter(1.0, 2.0)
    assert libm.logb(np.float64(8.0)) == 3.0
    result = libm.ilogb(np.float64(8.0))
    assert result == np.intc(3)
    assert result.dtype == np.dtype(np.intc)


def test_special(libm):
    assert np.isclose(libm.erf(np.float64(0.5)), math.erf(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)

    # erf and erfc are complements, which checks both without a shared oracle.
    assert np.isclose(
        libm.erf(np.float64(0.7)) + libm.erfc(np.float64(0.7)),
        1.0,
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert np.isclose(libm.erfc(np.float64(0.5)), math.erfc(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)

    # tgamma(n + 1) is n! for a whole argument.
    assert libm.tgamma(np.float64(6.0)) == 120.0
    assert np.isclose(libm.tgamma(np.float64(0.5)), math.sqrt(math.pi), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.lgamma(np.float64(5.0)), math.lgamma(5.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(math.exp(libm.lgamma(np.float64(6.0))), 120.0, rtol=1e-9, atol=1e-9)
