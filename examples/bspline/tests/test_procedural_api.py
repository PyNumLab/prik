"""Procedural B-spline routines checked against SciPy and analytic values."""

from __future__ import annotations

import numpy as np
import pytest

from examples.bspline.routine_inventory import ALL_SUB_ROUTINES, ORDER_CONSTANTS

pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]

CUBIC = np.int32(4)
NOT_A_KNOT = np.int32(0)


def _interpolant(bspline_sub, x, fcn):
    """Build one cubic interpolant through the procedural entry points."""
    nx = np.int32(x.size)
    knots = np.zeros(x.size + int(CUBIC), dtype=np.float64)
    bcoef = np.zeros(x.size, dtype=np.float64)

    iflag = bspline_sub.db1ink(x, nx, fcn, CUBIC, NOT_A_KNOT, knots, bcoef)
    assert iflag == np.int32(0), bspline_sub.get_status_message(iflag)
    return knots, bcoef, nx


def _evaluate(bspline_sub, knots, bcoef, nx, point, derivative=0):
    work = np.zeros(3 * int(CUBIC), dtype=np.float64)
    value, iflag, _inbvx = bspline_sub.db1val(
        np.float64(point),
        np.int32(derivative),
        knots,
        nx,
        CUBIC,
        bcoef,
        np.int32(1),
        work,
    )
    assert iflag == np.int32(0), bspline_sub.get_status_message(iflag)
    return value


def test_every_reviewed_procedure_is_exported(bspline_sub):
    missing = [name for name in ALL_SUB_ROUTINES if not hasattr(bspline_sub, name)]
    assert not missing, f"missing procedures: {missing}"


def test_spline_order_constants_reach_python(bspline_sub):
    for name, expected in ORDER_CONSTANTS.items():
        assert getattr(bspline_sub, name) == np.int32(expected), name


def test_generic_interfaces_publish_every_specific_signature(bspline_sub):
    """`db1ink` and `db1val` are Fortran generics, so each specific is accepted."""
    assert bspline_sub.db1ink.__doc__.count("db1ink(x:") == 3
    assert bspline_sub.db1val.__doc__.count("db1val(xval:") == 2


def test_interpolant_reproduces_the_sampled_function(bspline_sub):
    x = np.linspace(0.0, 2.0 * np.pi, 30)
    knots, bcoef, nx = _interpolant(bspline_sub, x, np.sin(x))

    for point in np.linspace(0.3, 5.9, 7):
        assert _evaluate(bspline_sub, knots, bcoef, nx, point) == pytest.approx(np.sin(point), abs=1.0e-5)


def test_interpolant_is_exact_on_a_low_order_polynomial(bspline_sub):
    """A cubic spline reproduces a cubic exactly, up to rounding."""
    x = np.linspace(0.0, 1.0, 25)
    knots, bcoef, nx = _interpolant(bspline_sub, x, x**3)

    for point in (0.25, 0.5, 0.75):
        assert _evaluate(bspline_sub, knots, bcoef, nx, point) == pytest.approx(point**3, abs=1.0e-9)


def test_first_derivative_matches_the_analytic_derivative(bspline_sub):
    x = np.linspace(0.0, 2.0 * np.pi, 60)
    knots, bcoef, nx = _interpolant(bspline_sub, x, np.sin(x))

    for point in np.linspace(0.5, 5.5, 5):
        value = _evaluate(bspline_sub, knots, bcoef, nx, point, derivative=1)
        assert value == pytest.approx(np.cos(point), abs=1.0e-4)


def test_definite_integral_matches_the_analytic_integral(bspline_sub):
    x = np.linspace(0.0, np.pi, 60)
    knots, bcoef, nx = _interpolant(bspline_sub, x, np.sin(x))
    work = np.zeros(3 * int(CUBIC), dtype=np.float64)

    value, iflag = bspline_sub.db1sqad(knots, bcoef, nx, CUBIC, np.float64(0.0), np.float64(np.pi), work)
    assert iflag == np.int32(0)
    assert value == pytest.approx(2.0, abs=1.0e-6)


def test_scipy_agrees_with_the_wrapped_interpolant(bspline_sub):
    """An independent oracle checks the wrapper rather than the wrapper alone."""
    scipy_interpolate = pytest.importorskip("scipy.interpolate")

    x = np.linspace(0.0, 3.0, 40)
    fcn = np.exp(-x) * np.cos(3.0 * x)
    knots, bcoef, nx = _interpolant(bspline_sub, x, fcn)
    reference = scipy_interpolate.make_interp_spline(x, fcn, k=3)

    for point in np.linspace(0.2, 2.8, 9):
        assert _evaluate(bspline_sub, knots, bcoef, nx, point) == pytest.approx(float(reference(point)), abs=1.0e-6)
