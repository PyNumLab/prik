"""Small deterministic problems shared by the MINPACK routine tests."""

from __future__ import annotations

import numpy as np
from scipy import optimize


INT = np.int32
FLOAT = np.float64
TARGET = np.array([1.0, -2.0], dtype=np.float64)


def vector(values=(4.0, 4.0)) -> np.ndarray:
    """Return one writable float64 vector for a two-variable test problem."""
    return np.array(values, dtype=np.float64)


def matrix() -> np.ndarray:
    """Return one writable Fortran-order 2-by-2 float64 matrix."""
    return np.empty((2, 2), dtype=np.float64, order="F")


def residual_callback(_count, x, fvec, _iflag) -> None:
    """Write the residual of the linear root problem ``x - TARGET``."""
    fvec[:] = x - TARGET


def squared_residual_callback(_count, x, fvec, _iflag) -> None:
    """Write the elementwise nonlinear residual ``x**2 - 1``."""
    fvec[:] = x**2 - 1.0


def squared_least_squares_callback(_m, _n, x, fvec, _iflag) -> None:
    """Write the elementwise nonlinear residual for ``fdjac2``."""
    fvec[:] = x**2 - 1.0


def jacobian_callback(_count, x, fvec, fjac, _ldfjac, iflag) -> None:
    """Write residuals or the exact identity Jacobian as MINPACK requests."""
    if iflag == 1:
        fvec[:] = x - TARGET
    elif iflag == 2:
        fjac[:, :] = np.eye(2, dtype=np.float64)


def least_squares_callback(_m, _n, x, fvec, _iflag) -> None:
    """Write residuals for the two-equation least-squares problem."""
    fvec[:] = x - TARGET


def least_squares_jacobian_callback(_m, _n, x, fvec, fjac, _ldfjac, iflag) -> None:
    """Write residuals or an exact Jacobian for LMDER-style callbacks."""
    if iflag == 1:
        fvec[:] = x - TARGET
    elif iflag == 2:
        fjac[:, :] = np.eye(2, dtype=np.float64)


def least_squares_row_callback(_m, _n, x, fvec, fjrow, iflag) -> None:
    """Write residuals or the one requested identity-Jacobian row."""
    if iflag == 1:
        fvec[:] = x - TARGET
    else:
        fjrow[:] = 0.0
        fjrow[int(iflag) - 2] = 1.0


def scipy_root() -> np.ndarray:
    """Solve the same root problem independently through SciPy."""
    result = optimize.root(lambda x: x - TARGET, vector())
    assert result.success
    return result.x


def scipy_least_squares() -> np.ndarray:
    """Solve the same least-squares problem independently through SciPy."""
    result = optimize.least_squares(lambda x: x - TARGET, vector())
    assert result.success
    return result.x


def assert_solution(x: np.ndarray, reference: np.ndarray) -> None:
    """Check a MINPACK iterate against the independently solved target."""
    np.testing.assert_allclose(x, reference, rtol=0.0, atol=1.0e-10)
