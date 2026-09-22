"""The selected PRIMA solver surface runs through one statically linked extension."""

from __future__ import annotations

import numpy as np
import pytest


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _objective(x, f):
    f[...] = (x[0] - 1.0) ** 2 + (x[1] + 2.0) ** 2


@pytest.mark.parametrize(
    ("module_name", "procedure_name"),
    [
        ("bobyqa_mod", "bobyqa"),
        ("newuoa_mod", "newuoa"),
        ("uobyqa_mod", "uobyqa"),
    ],
)
def test_unconstrained_solvers_minimize_a_quadratic(prima, module_name, procedure_name):
    solver = getattr(getattr(prima, module_name), procedure_name)
    x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))

    solver(_objective, x, maxfun=np.int32(100))

    np.testing.assert_allclose(x, np.array([1.0, -2.0]), atol=2.0e-3, rtol=0.0)


def test_lincoa_minimizes_a_quadratic(prima):
    x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))

    prima.lincoa_mod.lincoa(_objective, x, maxfun=np.int32(100))

    np.testing.assert_allclose(x, np.array([1.0, -2.0]), atol=2.0e-3, rtol=0.0)


def test_cobyla_runs_with_every_optional_callback_dummy_present(prima):
    x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
    observed = []

    def objective_and_constraints(values, f, constraints):
        _objective(values, f)

    def progress(values, f, nf, tr, cstrv, nlconstr, terminate):
        observed.append((f, nf, tr, cstrv, nlconstr.shape, terminate.shape))

    prima.cobyla_mod.cobyla(
        objective_and_constraints,
        np.int32(0),
        x,
        maxfun=np.int32(100),
        callback_fcn=progress,
    )

    np.testing.assert_allclose(x, np.array([1.0, -2.0]), atol=2.0e-3, rtol=0.0)
    assert observed
    assert observed[-1][4:] == ((0,), ())


def test_uobyqa_callback_receives_omitted_optional_dummies_as_none(prima):
    x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
    observed = []

    def progress(values, f, nf, tr, cstrv, nlconstr, terminate):
        observed.append((cstrv, nlconstr, terminate.shape))

    prima.uobyqa_mod.uobyqa(_objective, x, maxfun=np.int32(100), callback_fcn=progress)

    assert observed
    assert observed[-1] == (None, None, ())
