"""Numerical evidence for the ISO C error and gamma routines."""

from __future__ import annotations

import math

import pytest

from .helpers import F, close

pytestmark = pytest.mark.real_library


def test_erf(libm):
    assert close(libm.erf(F(0.5)), math.erf(0.5))


def test_erfc(libm):
    # erf and erfc are complements, which checks both without a shared oracle.
    assert close(libm.erf(F(0.7)) + libm.erfc(F(0.7)), 1.0)
    assert close(libm.erfc(F(0.5)), math.erfc(0.5))


def test_tgamma(libm):
    # tgamma(n + 1) is n! for a whole argument.
    assert libm.tgamma(F(6.0)) == 120.0
    assert close(libm.tgamma(F(0.5)), math.sqrt(math.pi))


def test_lgamma(libm):
    assert close(libm.lgamma(F(5.0)), math.lgamma(5.0))
    assert close(math.exp(libm.lgamma(F(6.0))), 120.0, tolerance=1e-9)
