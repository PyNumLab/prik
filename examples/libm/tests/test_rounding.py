"""Numerical evidence for rounding, remainder, and floating-point manipulation."""

from __future__ import annotations

import math

import numpy as np
import pytest

from .helpers import F, I, L, LONG_DOUBLE, close

pytestmark = pytest.mark.real_library


def test_ceil(libm):
    assert libm.ceil(F(2.1)) == 3.0


def test_floor(libm):
    assert libm.floor(F(2.9)) == 2.0


def test_trunc(libm):
    assert libm.trunc(F(-2.9)) == -2.0


def test_round(libm):
    # C `round` breaks ties away from zero, unlike Python's banker's rounding.
    assert libm.round(F(2.5)) == 3.0
    assert libm.round(F(-2.5)) == -3.0


def test_nearbyint(libm):
    # Both functions follow the active floating-point rounding mode.
    assert libm.nearbyint(F(2.5)) == libm.rint(F(2.5))
    assert libm.nearbyint(F(-2.5)) == libm.rint(F(-2.5))


def test_rint(libm):
    result = libm.rint(F(2.5))
    assert result in {2.0, 3.0}
    assert result == libm.nearbyint(F(2.5))


def test_lrint(libm):
    result = libm.lrint(F(2.7))
    assert result == L(libm.rint(F(2.7)))
    assert result.dtype == np.dtype(L)


def test_llrint(libm):
    result = libm.llrint(F(2.7))
    assert result == np.int64(libm.rint(F(2.7)))
    assert libm.llrint(F(-2.7)) == np.int64(libm.rint(F(-2.7)))


def test_lround(libm):
    result = libm.lround(F(2.5))
    assert result == L(3)
    assert result.dtype == np.dtype(L)


def test_llround(libm):
    assert libm.llround(F(2.5)) == np.int64(3)
    assert libm.llround(F(-2.5)) == np.int64(-3)


def test_fmod(libm):
    assert close(libm.fmod(F(10.0), F(3.0)), math.fmod(10.0, 3.0))


def test_remainder(libm):
    # IEEE remainder rounds the quotient to nearest, so it differs from fmod.
    assert close(libm.remainder(F(10.0), F(3.0)), math.remainder(10.0, 3.0))
    assert libm.remainder(F(10.0), F(6.0)) == -2.0


def test_copysign(libm):
    assert libm.copysign(F(2.0), F(-0.0)) == -2.0


def test_fabs(libm):
    assert libm.fabs(F(-2.5)) == 2.5


def test_fdim(libm):
    assert libm.fdim(F(5.0), F(3.0)) == 2.0
    assert libm.fdim(F(3.0), F(5.0)) == 0.0


def test_fmax(libm):
    assert libm.fmax(F(2.0), F(3.0)) == 3.0


def test_fmin(libm):
    assert libm.fmin(F(2.0), F(3.0)) == 2.0


def test_fma(libm):
    assert libm.fma(F(2.0), F(3.0), F(4.0)) == 10.0

    # A single rounding keeps the product bits an unfused expression discards.
    left, right = 1.0 + 2.0**-52, 1.0 - 2.0**-52
    assert libm.fma(F(left), F(right), F(-1.0)) == -(2.0**-104)
    assert left * right - 1.0 == 0.0


def test_ldexp(libm):
    assert libm.ldexp(F(1.5), I(3)) == 12.0


def test_scalbn(libm):
    assert libm.scalbn(F(1.5), I(3)) == 12.0


def test_scalbln(libm):
    assert libm.scalbln(F(1.5), L(3)) == 12.0


def test_nextafter(libm):
    assert libm.nextafter(F(1.0), F(2.0)) == math.nextafter(1.0, 2.0)


def test_nexttoward(libm):
    assert libm.nexttoward(F(1.0), LONG_DOUBLE(2.0)) == math.nextafter(1.0, 2.0)


def test_logb(libm):
    assert libm.logb(F(8.0)) == 3.0


def test_ilogb(libm):
    result = libm.ilogb(F(8.0))
    assert result == I(3)
    assert result.dtype == np.dtype(I)
