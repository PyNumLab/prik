"""Numerical evidence for the reviewed elementary libm routines."""

from __future__ import annotations

import math

import pytest

from .helpers import F, close

pytestmark = pytest.mark.real_library


def test_sin(libm):
    assert close(libm.sin(F(1.0)), math.sin(1.0))


def test_cos(libm):
    assert close(libm.cos(F(1.0)), math.cos(1.0))


def test_tan(libm):
    assert close(libm.tan(F(0.5)), math.tan(0.5))


def test_asin(libm):
    assert close(libm.asin(F(0.5)), math.asin(0.5))


def test_acos(libm):
    assert close(libm.acos(F(0.5)), math.acos(0.5))


def test_atan(libm):
    assert close(libm.atan(F(0.5)), math.atan(0.5))


def test_atan2(libm):
    assert close(libm.atan2(F(1.0), F(2.0)), math.atan2(1.0, 2.0))


def test_sinh(libm):
    assert close(libm.sinh(F(0.75)), math.sinh(0.75))


def test_cosh(libm):
    assert close(libm.cosh(F(0.75)), math.cosh(0.75))


def test_tanh(libm):
    assert close(libm.tanh(F(0.75)), math.tanh(0.75))


def test_asinh(libm):
    assert close(libm.asinh(F(0.75)), math.asinh(0.75))


def test_acosh(libm):
    assert close(libm.acosh(F(1.75)), math.acosh(1.75))


def test_atanh(libm):
    assert close(libm.atanh(F(0.75)), math.atanh(0.75))


def test_exp(libm):
    assert close(libm.exp(F(1.0)), math.e)


def test_exp2(libm):
    # exp2 is exact on a whole exponent, so no tolerance is needed.
    assert libm.exp2(F(10.0)) == 1024.0


def test_expm1(libm):
    # expm1 keeps the precision that exp(x) - 1 loses for small x.
    assert close(libm.expm1(F(1e-9)), math.expm1(1e-9))
    assert libm.expm1(F(1e-9)) != math.exp(1e-9) - 1.0


def test_log(libm):
    assert close(libm.log(F(math.e)), 1.0)


def test_log2(libm):
    assert libm.log2(F(1024.0)) == 10.0


def test_log10(libm):
    assert close(libm.log10(F(1000.0)), 3.0)


def test_log1p(libm):
    assert close(libm.log1p(F(1e-9)), math.log1p(1e-9))


def test_pow(libm):
    assert libm.pow(F(2.0), F(10.0)) == 1024.0


def test_sqrt(libm):
    assert libm.sqrt(F(144.0)) == 12.0


def test_cbrt(libm):
    assert close(libm.cbrt(F(27.0)), 3.0)


def test_hypot(libm):
    assert libm.hypot(F(3.0), F(4.0)) == 5.0
