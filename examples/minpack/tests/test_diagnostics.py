"""Diagnostic norms, gradients, immutable constants, and finite differences."""

from __future__ import annotations

import numpy as np
import pytest


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
INT = np.int32
FLOAT = np.float64


def test_dpmpar_is_an_immutable_float64_snapshot(minpack):
    values = minpack.dpmpar

    np.testing.assert_array_equal(
        values,
        np.array([np.finfo(np.float64).eps, np.finfo(np.float64).tiny, np.finfo(np.float64).max]),
    )
    assert values.flags.writeable is False
    with pytest.raises(ValueError, match="read-only"):
        values[0] = 1.0


def test_enorm(minpack):
    values = np.array([3.0, 4.0, 12.0], dtype=np.float64)

    assert minpack.enorm(INT(values.size), values) == pytest.approx(np.linalg.norm(values))


def test_chkder(minpack):
    x = np.array([1.5, -2.0], dtype=np.float64)
    fvec = x.copy()
    fjac = np.eye(2, dtype=np.float64, order="F")
    xp = np.empty(2, dtype=np.float64)
    fvecp = np.empty(2, dtype=np.float64)
    err = np.empty(2, dtype=np.float64)

    minpack.chkder(INT(2), INT(2), x, fvec, fjac, INT(2), xp, fvecp, INT(1), err)
    fvecp[:] = xp
    minpack.chkder(INT(2), INT(2), x, fvec, fjac, INT(2), xp, fvecp, INT(2), err)

    np.testing.assert_allclose(err, np.ones(2), rtol=0.0, atol=1.0e-12)


def test_fdjac1(minpack):
    def squared_residual(_count, x, fvec, _iflag):
        fvec[:] = x**2 - 1.0

    x = np.array([1.0, 2.0], dtype=np.float64)
    fvec = x**2 - 1.0
    fjac = np.empty((2, 2), dtype=np.float64, order="F")

    result = minpack.fdjac1(
        squared_residual,
        INT(2),
        x,
        fvec,
        fjac,
        INT(2),
        INT(0),
        INT(1),
        INT(1),
        FLOAT(0.0),
        np.empty(2),
        np.empty(2),
    )

    assert result == INT(0)
    np.testing.assert_allclose(fjac, np.diag([2.0, 4.0]), rtol=1.0e-7, atol=1.0e-7)


def test_fdjac2(minpack):
    def squared_residual(_m, _n, x, fvec, _iflag):
        fvec[:] = x**2 - 1.0

    x = np.array([1.0, 2.0], dtype=np.float64)
    fvec = x**2 - 1.0
    fjac = np.empty((2, 2), dtype=np.float64, order="F")

    result = minpack.fdjac2(
        squared_residual,
        INT(2),
        INT(2),
        x,
        fvec,
        fjac,
        INT(2),
        INT(0),
        FLOAT(0.0),
        np.empty(2),
    )

    assert result == INT(0)
    np.testing.assert_allclose(fjac, np.diag([2.0, 4.0]), rtol=1.0e-7, atol=1.0e-7)
