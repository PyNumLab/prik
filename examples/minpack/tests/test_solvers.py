"""Callback-driven MINPACK solvers checked against known solutions."""

from __future__ import annotations

import numpy as np
import pytest


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
ROOT_TOLERANCE = np.float64(1.0e-12)
MAX_EVALUATIONS = np.int32(100)
FACTOR = np.float64(100.0)
ZERO = np.float64(0.0)
ONE = np.int32(1)
TWO = np.int32(2)
TARGET = np.array([1.0, -2.0], dtype=np.float64)


def test_hybrd(minpack):
    def residual(_count, x, fvec, _iflag):
        fvec[:] = x - TARGET

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    r = np.empty(3, dtype=np.float64)
    qtf = np.empty(2, dtype=np.float64)
    info, calls = minpack.hybrd(
        residual,
        TWO,
        x,
        fvec,
        ROOT_TOLERANCE,
        MAX_EVALUATIONS,
        ONE,
        ONE,
        ZERO,
        np.ones(2),
        TWO,
        FACTOR,
        np.int32(0),
        fjac,
        TWO,
        r,
        np.int32(3),
        qtf,
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
    )

    assert info == np.int32(1)
    assert calls > 0
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrd1(minpack):
    target = np.array([1.0, -2.0], dtype=np.float64)
    callback_calls = 0

    def residual(_count, x, fvec, _iflag):
        nonlocal callback_calls
        callback_calls += 1
        fvec[:] = x - target

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.empty(2, dtype=np.float64)
    info = minpack.hybrd1(
        residual,
        np.int32(2),
        x,
        fvec,
        np.float64(1.0e-12),
        np.empty(19, dtype=np.float64),
        np.int32(19),
    )

    assert info == np.int32(1)
    assert callback_calls > 0
    np.testing.assert_allclose(x, target, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrj(minpack):
    def residual_and_jacobian(_count, x, fvec, fjac, _ldfjac, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        elif iflag == 2:
            fjac[:, :] = np.eye(2, dtype=np.float64)

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    r = np.empty(3, dtype=np.float64)
    qtf = np.empty(2, dtype=np.float64)
    info, function_calls, jacobian_calls = minpack.hybrj(
        residual_and_jacobian,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        MAX_EVALUATIONS,
        np.ones(2),
        TWO,
        FACTOR,
        np.int32(0),
        r,
        np.int32(3),
        qtf,
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
    )

    assert (info, function_calls, jacobian_calls) == (np.int32(1), np.int32(2), np.int32(1))
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrj1(minpack):
    def residual_and_jacobian(_count, x, fvec, fjac, _ldfjac, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        elif iflag == 2:
            fjac[:, :] = np.eye(2, dtype=np.float64)

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    info = minpack.hybrj1(
        residual_and_jacobian,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        np.empty(15, dtype=np.float64),
        np.int32(15),
    )

    assert info == np.int32(1)
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmder(minpack):
    def residual_and_jacobian(_m, _n, x, fvec, fjac, _ldfjac, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        elif iflag == 2:
            fjac[:, :] = np.eye(2, dtype=np.float64)

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    ipvt = np.empty(2, dtype=np.int32)
    qtf = np.empty(2, dtype=np.float64)
    info, function_calls, jacobian_calls = minpack.lmder(
        residual_and_jacobian,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ROOT_TOLERANCE,
        ZERO,
        MAX_EVALUATIONS,
        np.ones(2),
        TWO,
        FACTOR,
        np.int32(0),
        ipvt,
        qtf,
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
    )

    assert (info, function_calls, jacobian_calls) == (np.int32(4), np.int32(2), np.int32(2))
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmder1(minpack):
    def residual_and_jacobian(_m, _n, x, fvec, fjac, _ldfjac, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        elif iflag == 2:
            fjac[:, :] = np.eye(2, dtype=np.float64)

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    ipvt = np.empty(2, dtype=np.int32)
    info = minpack.lmder1(
        residual_and_jacobian,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ipvt,
        np.empty(12, dtype=np.float64),
        np.int32(12),
    )

    assert info == np.int32(4)
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmdif(minpack):
    def residual(_m, _n, x, fvec, _iflag):
        fvec[:] = x - TARGET

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    ipvt = np.empty(2, dtype=np.int32)
    qtf = np.empty(2, dtype=np.float64)
    info, function_calls = minpack.lmdif(
        residual,
        TWO,
        TWO,
        x,
        fvec,
        ROOT_TOLERANCE,
        ROOT_TOLERANCE,
        ZERO,
        MAX_EVALUATIONS,
        ZERO,
        np.ones(2),
        TWO,
        FACTOR,
        np.int32(0),
        fjac,
        TWO,
        ipvt,
        qtf,
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
    )

    assert (info, function_calls) == (np.int32(4), np.int32(6))
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmdif1(minpack):
    def residual(_m, _n, x, fvec, _iflag):
        fvec[:] = x - TARGET

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    iwa = np.empty(2, dtype=np.int32)
    info = minpack.lmdif1(
        residual,
        TWO,
        TWO,
        x,
        fvec,
        ROOT_TOLERANCE,
        iwa,
        np.empty(16, dtype=np.float64),
        np.int32(16),
    )

    assert info == np.int32(4)
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmstr(minpack):
    def residual_and_row(_m, _n, x, fvec, fjrow, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        else:
            fjrow[:] = 0.0
            fjrow[int(iflag) - 2] = 1.0

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    ipvt = np.empty(2, dtype=np.int32)
    qtf = np.empty(2, dtype=np.float64)
    info, function_calls, jacobian_calls = minpack.lmstr(
        residual_and_row,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ROOT_TOLERANCE,
        ZERO,
        MAX_EVALUATIONS,
        np.ones(2),
        TWO,
        FACTOR,
        np.int32(0),
        ipvt,
        qtf,
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
        np.zeros(2, dtype=np.float64),
    )

    assert (info, function_calls, jacobian_calls) == (np.int32(4), np.int32(2), np.int32(2))
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmstr1(minpack):
    def residual_and_row(_m, _n, x, fvec, fjrow, iflag):
        if iflag == 1:
            fvec[:] = x - TARGET
        else:
            fjrow[:] = 0.0
            fjrow[int(iflag) - 2] = 1.0

    x = np.array([4.0, 4.0], dtype=np.float64)
    fvec = np.zeros(2, dtype=np.float64)
    fjac = np.empty((2, 2), dtype=np.float64, order="F")
    ipvt = np.empty(2, dtype=np.int32)
    info = minpack.lmstr1(
        residual_and_row,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ipvt,
        np.empty(12, dtype=np.float64),
        np.int32(12),
    )

    assert info == np.int32(4)
    np.testing.assert_allclose(x, TARGET, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)
