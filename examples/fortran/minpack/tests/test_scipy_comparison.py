"""MINPACK solvers agree with SciPy's MINPACK-based solvers on nonlinear problems.

SciPy exposes eight of the 22 procedures through public solvers: the hybrid
root finders through ``root(method="hybr")`` and the Levenberg-Marquardt
solvers through ``least_squares(method="lm")``. Each case solves a genuinely
nonlinear problem with both, checks PRIK's answer independently, then checks
that the two interfaces agree. The known answer stays the primary check.
"""

from __future__ import annotations

import numpy as np
import pytest

optimize = pytest.importorskip("scipy.optimize")

pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]

TOLERANCE = np.float64(1.0e-12)
MAX_EVALUATIONS = np.int32(1000)
FACTOR = np.float64(100.0)
ZERO = np.float64(0.0)
N = np.int32(2)

# Root finding: where the circle x^2 + y^2 = 4 meets the curve y = x^3.
ROOT_START = np.array([1.0, 1.0])


def _system(x):
    return np.array([x[0] ** 2 + x[1] ** 2 - 4.0, x[1] - x[0] ** 3])


def _system_jacobian(x):
    return np.array([[2.0 * x[0], 2.0 * x[1]], [-3.0 * x[0] ** 2, 1.0]])


# Least squares: recover a = 2 and b = -0.5 from y = a * exp(b * t).
T = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
Y = 2.0 * np.exp(-0.5 * T)
M = np.int32(T.size)
FIT_START = np.array([1.0, 0.0])
FIT_ANSWER = np.array([2.0, -0.5])


def _fit_residuals(p):
    return p[0] * np.exp(p[1] * T) - Y


def _fit_jacobian(p):
    growth = np.exp(p[1] * T)
    return np.column_stack([growth, p[0] * T * growth])


def _hybrd(minpack):
    x = ROOT_START.copy()
    fvec = np.empty(2)

    def fcn(_n, x, fvec, _iflag):
        fvec[:] = _system(x)

    info, _nfev = minpack.hybrd(
        fcn,
        N,
        x,
        fvec,
        TOLERANCE,
        MAX_EVALUATIONS,
        np.int32(1),
        np.int32(1),
        ZERO,
        np.ones(2),
        np.int32(1),
        FACTOR,
        np.int32(0),
        np.empty((2, 2), order="F"),
        N,
        np.empty(3),
        np.int32(3),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
    )
    return info, x


def _hybrd1(minpack):
    x = ROOT_START.copy()

    def fcn(_n, x, fvec, _iflag):
        fvec[:] = _system(x)

    info = minpack.hybrd1(fcn, N, x, np.empty(2), TOLERANCE, np.empty(19), np.int32(19))
    return info, x


def _root_with_jacobian(_n, x, fvec, fjac, _ldfjac, iflag):
    if iflag == 1:
        fvec[:] = _system(x)
    elif iflag == 2:
        fjac[:, :] = _system_jacobian(x)


def _hybrj(minpack):
    x = ROOT_START.copy()
    info, _nfev, _njev = minpack.hybrj(
        _root_with_jacobian,
        N,
        x,
        np.empty(2),
        np.empty((2, 2), order="F"),
        N,
        TOLERANCE,
        MAX_EVALUATIONS,
        np.ones(2),
        np.int32(1),
        FACTOR,
        np.int32(0),
        np.empty(3),
        np.int32(3),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
    )
    return info, x


def _hybrj1(minpack):
    x = ROOT_START.copy()
    info = minpack.hybrj1(
        _root_with_jacobian,
        N,
        x,
        np.empty(2),
        np.empty((2, 2), order="F"),
        N,
        TOLERANCE,
        np.empty(15),
        np.int32(15),
    )
    return info, x


def _fit(_m, _n, p, fvec, _iflag):
    fvec[:] = _fit_residuals(p)


def _fit_with_jacobian(_m, _n, p, fvec, fjac, _ldfjac, iflag):
    if iflag == 1:
        fvec[:] = _fit_residuals(p)
    elif iflag == 2:
        fjac[:, :] = _fit_jacobian(p)


def _lmdif(minpack):
    p = FIT_START.copy()
    info, _nfev = minpack.lmdif(
        _fit,
        M,
        N,
        p,
        np.empty(M),
        TOLERANCE,
        TOLERANCE,
        ZERO,
        MAX_EVALUATIONS,
        ZERO,
        np.ones(2),
        np.int32(1),
        FACTOR,
        np.int32(0),
        np.empty((M, 2), order="F"),
        M,
        np.empty(2, dtype=np.int32),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(M),
    )
    return info, p


def _lmdif1(minpack):
    p = FIT_START.copy()
    info = minpack.lmdif1(
        _fit, M, N, p, np.empty(M), TOLERANCE, np.empty(2, dtype=np.int32), np.empty(25), np.int32(25)
    )
    return info, p


def _lmder(minpack):
    p = FIT_START.copy()
    info, _nfev, _njev = minpack.lmder(
        _fit_with_jacobian,
        M,
        N,
        p,
        np.empty(M),
        np.empty((M, 2), order="F"),
        M,
        TOLERANCE,
        TOLERANCE,
        ZERO,
        MAX_EVALUATIONS,
        np.ones(2),
        np.int32(1),
        FACTOR,
        np.int32(0),
        np.empty(2, dtype=np.int32),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(2),
        np.empty(M),
    )
    return info, p


def _lmder1(minpack):
    p = FIT_START.copy()
    info = minpack.lmder1(
        _fit_with_jacobian,
        M,
        N,
        p,
        np.empty(M),
        np.empty((M, 2), order="F"),
        M,
        TOLERANCE,
        np.empty(2, dtype=np.int32),
        np.empty(15),
        np.int32(15),
    )
    return info, p


def _scipy_root(jacobian):
    result = optimize.root(_system, ROOT_START, jac=_system_jacobian if jacobian else None, method="hybr")
    assert result.success
    return result.x


def _scipy_fit(jacobian):
    result = optimize.least_squares(
        _fit_residuals, FIT_START, jac=_fit_jacobian if jacobian else "2-point", method="lm"
    )
    assert result.success
    return result.x


@pytest.mark.parametrize(
    ("solve", "scipy_jacobian", "problem"),
    [
        pytest.param(_hybrd, False, "root", id="hybrd-vs-root-hybr"),
        pytest.param(_hybrd1, False, "root", id="hybrd1-vs-root-hybr"),
        pytest.param(_hybrj, True, "root", id="hybrj-vs-root-hybr-jac"),
        pytest.param(_hybrj1, True, "root", id="hybrj1-vs-root-hybr-jac"),
        pytest.param(_lmdif, False, "fit", id="lmdif-vs-least-squares-lm"),
        pytest.param(_lmdif1, False, "fit", id="lmdif1-vs-least-squares-lm"),
        pytest.param(_lmder, True, "fit", id="lmder-vs-least-squares-lm-jac"),
        pytest.param(_lmder1, True, "fit", id="lmder1-vs-least-squares-lm-jac"),
    ],
)
def test_solver_agrees_with_scipy(minpack, solve, scipy_jacobian, problem):
    info, x = solve(minpack)

    if problem == "root":
        assert info == np.int32(1)
        np.testing.assert_allclose(_system(x), 0.0, atol=1.0e-10)
        expected = _scipy_root(scipy_jacobian)
    else:
        assert np.int32(1) <= info <= np.int32(4)
        np.testing.assert_allclose(x, FIT_ANSWER, atol=1.0e-8)
        expected = _scipy_fit(scipy_jacobian)

    np.testing.assert_allclose(x, expected, atol=1.0e-8)
