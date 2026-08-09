"""Callback-driven MINPACK solvers checked against SciPy's solution."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import (
    FLOAT,
    INT,
    assert_solution,
    jacobian_callback,
    least_squares_callback,
    least_squares_jacobian_callback,
    least_squares_row_callback,
    matrix,
    residual_callback,
    scipy_least_squares,
    scipy_root,
    vector,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
ROOT_TOLERANCE = FLOAT(1.0e-12)
MAX_EVALUATIONS = INT(100)
FACTOR = FLOAT(100.0)
ZERO = FLOAT(0.0)
ONE = INT(1)
TWO = INT(2)


def test_hybrd(minpack):
    x, fvec, fjac, r, qtf = vector(), vector((0.0, 0.0)), matrix(), np.empty(3), np.empty(2)
    info, calls = minpack.hybrd(
        residual_callback,
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
        INT(0),
        fjac,
        TWO,
        r,
        INT(3),
        qtf,
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
    )

    assert info == INT(1)
    assert calls > 0
    assert_solution(x, scipy_root())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrd1(minpack):
    x, fvec = vector(), vector((0.0, 0.0))
    info = minpack.hybrd1(residual_callback, TWO, x, fvec, ROOT_TOLERANCE, np.empty(19), INT(19))

    assert info == INT(1)
    assert_solution(x, scipy_root())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrj(minpack):
    x, fvec, fjac, r, qtf = vector(), vector((0.0, 0.0)), matrix(), np.empty(3), np.empty(2)
    info, function_calls, jacobian_calls = minpack.hybrj(
        jacobian_callback,
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
        INT(0),
        r,
        INT(3),
        qtf,
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
    )

    assert (info, function_calls, jacobian_calls) == (INT(1), INT(2), INT(1))
    assert_solution(x, scipy_root())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_hybrj1(minpack):
    x, fvec, fjac = vector(), vector((0.0, 0.0)), matrix()
    info = minpack.hybrj1(jacobian_callback, TWO, x, fvec, fjac, TWO, ROOT_TOLERANCE, np.empty(15), INT(15))

    assert info == INT(1)
    assert_solution(x, scipy_root())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmder(minpack):
    x, fvec, fjac, ipvt, qtf = vector(), vector((0.0, 0.0)), matrix(), np.empty(2, dtype=np.int32), np.empty(2)
    info, function_calls, jacobian_calls = minpack.lmder(
        least_squares_jacobian_callback,
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
        INT(0),
        ipvt,
        qtf,
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
    )

    assert (info, function_calls, jacobian_calls) == (INT(4), INT(2), INT(2))
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmder1(minpack):
    x, fvec, fjac, ipvt = vector(), vector((0.0, 0.0)), matrix(), np.empty(2, dtype=np.int32)
    info = minpack.lmder1(
        least_squares_jacobian_callback,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ipvt,
        np.empty(12),
        INT(12),
    )

    assert info == INT(4)
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmdif(minpack):
    x, fvec, fjac, ipvt, qtf = vector(), vector((0.0, 0.0)), matrix(), np.empty(2, dtype=np.int32), np.empty(2)
    info, function_calls = minpack.lmdif(
        least_squares_callback,
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
        INT(0),
        fjac,
        TWO,
        ipvt,
        qtf,
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
    )

    assert (info, function_calls) == (INT(4), INT(6))
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmdif1(minpack):
    x, fvec, iwa = vector(), vector((0.0, 0.0)), np.empty(2, dtype=np.int32)
    info = minpack.lmdif1(
        least_squares_callback,
        TWO,
        TWO,
        x,
        fvec,
        ROOT_TOLERANCE,
        iwa,
        np.empty(16),
        INT(16),
    )

    assert info == INT(4)
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmstr(minpack):
    x, fvec, fjac, ipvt, qtf = vector(), vector((0.0, 0.0)), matrix(), np.empty(2, dtype=np.int32), np.empty(2)
    info, function_calls, jacobian_calls = minpack.lmstr(
        least_squares_row_callback,
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
        INT(0),
        ipvt,
        qtf,
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
        vector((0.0, 0.0)),
    )

    assert (info, function_calls, jacobian_calls) == (INT(4), INT(2), INT(2))
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)


def test_lmstr1(minpack):
    x, fvec, fjac, ipvt = vector(), vector((0.0, 0.0)), matrix(), np.empty(2, dtype=np.int32)
    info = minpack.lmstr1(
        least_squares_row_callback,
        TWO,
        TWO,
        x,
        fvec,
        fjac,
        TWO,
        ROOT_TOLERANCE,
        ipvt,
        np.empty(12),
        INT(12),
    )

    assert info == INT(4)
    assert_solution(x, scipy_least_squares())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)
