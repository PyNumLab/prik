"""Shared conversions for the reviewed libm surface."""

from __future__ import annotations

import ctypes

import numpy as np

# libm takes exact target dtypes at the boundary, so tests state them once.
F = np.float64
I = np.dtype(f"int{ctypes.sizeof(ctypes.c_int) * 8}").type  # noqa: E741 - C `int`
L = np.dtype(f"int{ctypes.sizeof(ctypes.c_long) * 8}").type
LONG_DOUBLE = np.longdouble if np.finfo(np.longdouble).nmant > np.finfo(np.float64).nmant else np.float64


def close(actual, expected, *, tolerance: float = 1e-12) -> bool:
    """Return whether two finite doubles agree to a relative tolerance."""
    return abs(float(actual) - float(expected)) <= tolerance * max(1.0, abs(float(expected)))
