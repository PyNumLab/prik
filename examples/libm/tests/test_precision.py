"""Each precision variant keeps its own target dtype at the Python boundary."""

from __future__ import annotations

import math

import numpy as np
import pytest

from .helpers import LONG_DOUBLE, close

pytestmark = pytest.mark.real_library


def test_sinf(libm):
    result = libm.sinf(np.float32(1.0))

    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.sin(1.0)), rtol=4 * np.finfo(np.float32).eps, atol=0.0)


def test_cosf(libm):
    result = libm.cosf(np.float32(1.0))

    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.cos(1.0)), rtol=4 * np.finfo(np.float32).eps, atol=0.0)


def test_expf(libm):
    result = libm.expf(np.float32(1.0))

    assert result.dtype == np.float32
    assert np.isclose(result, np.float32(math.exp(1.0)), rtol=4 * np.finfo(np.float32).eps, atol=0.0)


def test_logf(libm):
    result = libm.logf(np.float32(math.e))

    assert result.dtype == np.float32
    assert close(result, 1.0, tolerance=1e-6)


def test_sqrtf(libm):
    result = libm.sqrtf(np.float32(144.0))

    assert result.dtype == np.float32
    assert result == np.float32(12.0)


def test_sinl(libm):
    result = libm.sinl(LONG_DOUBLE(1.0))

    assert result.dtype == np.dtype(LONG_DOUBLE)
    assert close(result, math.sin(1.0))


def test_sqrtl(libm):
    result = libm.sqrtl(LONG_DOUBLE(2))

    assert result.dtype == np.dtype(LONG_DOUBLE)
    assert close(result, math.sqrt(2.0), tolerance=1e-15)
