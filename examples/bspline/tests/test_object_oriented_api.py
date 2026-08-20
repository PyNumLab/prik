"""Object-oriented B-spline classes over an abstract Fortran base."""

from __future__ import annotations

import numpy as np
import pytest

from examples.bspline.routine_inventory import (
    ABSTRACT_BASE,
    CLASSES,
    DEFERRED_BINDINGS,
    INHERITED_BINDINGS,
)

pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]

CUBIC = np.int32(4)


def _sine_spline(bspline_oo, points=25):
    x = np.linspace(0.0, 2.0 * np.pi, points)
    spline = bspline_oo.bspline_1d(x, np.sin(x), CUBIC)
    assert spline.status_ok()
    return spline


def _affine_grid(dimension):
    """Return Fortran-order samples of the affine function in ``dimension`` axes."""
    axes = [np.linspace(0.0, 1.0, 5) for _ in range(dimension)]
    values = np.zeros((5,) * dimension)
    for axis, points in enumerate(axes):
        shape = [1] * dimension
        shape[axis] = points.size
        values += points.reshape(shape)
    return axes, np.asfortranarray(values)


def test_every_reviewed_class_is_exported(bspline_oo):
    for name in (ABSTRACT_BASE, *CLASSES):
        assert hasattr(bspline_oo, name), name


def test_abstract_base_cannot_be_instantiated(bspline_oo):
    """`bspline_class` is declared abstract, so only its extensions have instances."""
    with pytest.raises(TypeError, match="abstract native type and cannot be instantiated"):
        bspline_oo.bspline_class()


def test_every_class_extends_the_abstract_base(bspline_oo):
    base = bspline_oo.bspline_class
    for name in CLASSES:
        assert issubclass(getattr(bspline_oo, name), base), name


@pytest.mark.parametrize("dimension", range(1, 7))
def test_every_concrete_class_interpolates_an_affine_grid(bspline_oo, dimension):
    """Every dimension-specific constructor and evaluator works end to end."""
    axes, values = _affine_grid(dimension)
    spline = getattr(bspline_oo, f"bspline_{dimension}d")(*axes, values, *(CUBIC,) * dimension)

    value, iflag = spline.evaluate(*(np.float64(0.3),) * dimension, *(np.int32(0),) * dimension)

    assert spline.status_ok()
    assert iflag == np.int32(0)
    assert value == pytest.approx(0.3 * dimension, abs=1.0e-12)


def test_every_class_answers_the_deferred_and_inherited_bindings(bspline_oo):
    for name in CLASSES:
        members = dir(getattr(bspline_oo, name))
        for binding in (*DEFERRED_BINDINGS, *INHERITED_BINDINGS):
            assert binding in members, f"{name}.{binding}"


def test_generic_constructor_accepts_each_declared_signature(bspline_oo):
    """`interface bspline_1d` publishes an empty and a data-driven constructor."""
    empty = bspline_oo.bspline_1d()
    assert empty.status_ok() is False

    spline = _sine_spline(bspline_oo)
    assert spline.status_ok() is True


def test_interpolated_values_match_the_sampled_function(bspline_oo):
    spline = _sine_spline(bspline_oo)

    for point in np.linspace(0.2, 6.0, 9):
        value, iflag = spline.evaluate(np.float64(point), np.int32(0))
        assert iflag == np.int32(0)
        assert value == pytest.approx(np.sin(point), abs=1.0e-4)


def test_first_derivative_matches_the_analytic_derivative(bspline_oo):
    spline = _sine_spline(bspline_oo, points=60)

    for point in np.linspace(0.5, 5.5, 7):
        value, iflag = spline.evaluate(np.float64(point), np.int32(1))
        assert iflag == np.int32(0)
        assert value == pytest.approx(np.cos(point), abs=1.0e-4)


def test_definite_integral_matches_the_analytic_integral(bspline_oo):
    spline = _sine_spline(bspline_oo, points=60)

    value, iflag = spline.integral(np.float64(0.0), np.float64(np.pi))
    assert iflag == np.int32(0)
    assert value == pytest.approx(2.0, abs=1.0e-5)


def test_two_dimensional_interpolation_matches_the_sampled_surface(bspline_oo):
    x = np.linspace(0.0, 1.0, 20)
    y = np.linspace(0.0, 1.0, 20)
    samples = np.asfortranarray(np.exp(-(x[:, None] ** 2 + y[None, :] ** 2)))

    spline = bspline_oo.bspline_2d(x, y, samples, CUBIC, CUBIC)
    assert spline.status_ok()

    value, iflag = spline.evaluate(np.float64(0.33), np.float64(0.47), np.int32(0), np.int32(0))
    assert iflag == np.int32(0)
    assert value == pytest.approx(np.exp(-(0.33**2 + 0.47**2)), abs=1.0e-6)


def test_deferred_bindings_dispatch_through_the_abstract_base(bspline_oo):
    """The base declares `size_of` and `destroy`; the object's own type answers."""
    spline = _sine_spline(bspline_oo)

    assert bspline_oo.bspline_class.size_of(spline) == spline.size_of()
    assert spline.size_of() > np.int32(0)

    spline.destroy()
    assert spline.status_ok() is False
