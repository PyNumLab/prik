"""Least-squares and equality-constrained least-squares correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_small_residual


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _exact_tall_problem():
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    rhs = np.array([[1.0], [2.0], [3.0]], dtype=np.float64, order="F")
    return matrix, rhs, expected


def _assert_least_squares(matrix, rhs, solution):
    residual = matrix @ solution - rhs
    assert_small_residual(
        residual,
        matrix_norm=np.linalg.norm(matrix, ord=np.inf),
        solution_norm=np.linalg.norm(solution, ord=np.inf),
        operation_size=matrix.shape[0],
    )
    assert_allclose_float64(matrix.T @ residual, np.zeros((matrix.shape[1], 1)), operation_size=3)


def test_dgels_solves_full_rank_least_squares(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, rhs, expected = _exact_tall_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dgels(
        "N",
        np.int32(3),
        np.int32(2),
        np.int32(1),
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        np.empty(64),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgels(b"N", 3, 2, 1, f2py_a, f2py_b, np.empty(64), 64, 0)
    _factor, scipy_b, scipy_info = scipy_lapack.dgels(matrix.copy(order="F"), rhs.copy(order="F"), trans=b"N", lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for solution in (prik_b[:2], f2py_b[:2], scipy_b[:2]):
        assert_allclose_float64(solution, expected, operation_size=3)
        _assert_least_squares(matrix, rhs, solution)


def test_dgelsd_solves_rank_revealing_least_squares(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, rhs, expected = _exact_tall_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")
    prik_s, f2py_s = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgelsd(
        np.int32(3),
        np.int32(2),
        np.int32(1),
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        prik_s,
        np.float64(-1.0),
        np.int32(0),
        np.empty(802),
        np.int32(802),
        np.empty(128, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgelsd(
        3, 2, 1, f2py_a, f2py_b, f2py_s, -1.0, 0, np.empty(802), 802, np.empty(128, dtype=np.int32), 0
    )
    scipy_x, scipy_s, scipy_rank, scipy_info = scipy_lapack.dgelsd(
        matrix.copy(order="F"), rhs.copy(order="F"), 802, 128, cond=-1.0
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[-3] == scipy_rank == 2
    for solution in (prik_b[:2], f2py_b[:2], scipy_x[:2]):
        assert_allclose_float64(solution, expected, operation_size=3)
        _assert_least_squares(matrix, rhs, solution)
    assert_allclose_float64(prik_s, scipy_s, operation_size=3)
    assert_allclose_float64(f2py_s, scipy_s, operation_size=3)


def test_dgelss_solves_svd_least_squares(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, rhs, expected = _exact_tall_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")
    prik_s, f2py_s = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgelss(
        np.int32(3),
        np.int32(2),
        np.int32(1),
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        prik_s,
        np.float64(-1.0),
        np.int32(0),
        np.empty(128),
        np.int32(128),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgelss(3, 2, 1, f2py_a, f2py_b, f2py_s, -1.0, 0, np.empty(128), 128, 0)
    _v, scipy_x, scipy_s, scipy_rank, _work, scipy_info = scipy_lapack.dgelss(
        matrix.copy(order="F"), rhs.copy(order="F"), cond=-1.0, lwork=128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[-3] == scipy_rank == 2
    for solution in (prik_b[:2], f2py_b[:2], scipy_x[:2]):
        assert_allclose_float64(solution, expected, operation_size=3)
        _assert_least_squares(matrix, rhs, solution)
    assert_allclose_float64(prik_s, scipy_s, operation_size=3)
    assert_allclose_float64(f2py_s, scipy_s, operation_size=3)


def test_dgelsy_solves_pivoted_rank_revealing_least_squares(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, rhs, expected = _exact_tall_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")
    prik_jpvt, f2py_jpvt = np.zeros(2, dtype=np.int32), np.zeros(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgelsy(
        np.int32(3),
        np.int32(2),
        np.int32(1),
        prik_a,
        np.int32(3),
        prik_b,
        np.int32(3),
        prik_jpvt,
        np.float64(-1.0),
        np.int32(0),
        np.empty(128),
        np.int32(128),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgelsy(3, 2, 1, f2py_a, f2py_b, f2py_jpvt, -1.0, 0, np.empty(128), 128, 0)
    _v, scipy_x, scipy_jpvt, scipy_rank, scipy_info = scipy_lapack.dgelsy(
        matrix.copy(order="F"), rhs.copy(order="F"), np.zeros(2, dtype=np.int32), -1.0, 128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[-3] == scipy_rank == 2
    for solution in (prik_b[:2], f2py_b[:2], scipy_x[:2]):
        assert_allclose_float64(solution, expected, operation_size=3)
        _assert_least_squares(matrix, rhs, solution)
    # SciPy preserves LAPACK's one-based JPVT convention for DGELSY.
    np.testing.assert_array_equal(prik_jpvt, scipy_jpvt)
    np.testing.assert_array_equal(f2py_jpvt, scipy_jpvt)


def test_dgglse_solves_equality_constrained_least_squares(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.eye(2, dtype=np.float64, order="F")
    constraint = np.array([[1.0, 0.0]], dtype=np.float64, order="F")
    target = np.array([1.0, 2.0], dtype=np.float64)
    constrained_value = np.array([1.0], dtype=np.float64)
    expected = np.array([1.0, 2.0], dtype=np.float64)
    prik_x, f2py_x = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgglse(
        np.int32(2),
        np.int32(2),
        np.int32(1),
        matrix.copy(order="F"),
        np.int32(2),
        constraint.copy(order="F"),
        np.int32(1),
        target.copy(),
        constrained_value.copy(),
        prik_x,
        np.empty(128),
        np.int32(128),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgglse(
        2,
        2,
        1,
        matrix.copy(order="F"),
        constraint.copy(order="F"),
        target.copy(),
        constrained_value.copy(),
        f2py_x,
        np.empty(128),
        128,
        0,
    )
    _t, _r, _res, scipy_x, scipy_info = scipy_lapack.dgglse(
        matrix.copy(order="F"), constraint.copy(order="F"), target.copy(), constrained_value.copy(), lwork=128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_x, expected, operation_size=2)
    assert_allclose_float64(f2py_x, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(constraint @ prik_x, constrained_value)
    assert_allclose_float64(matrix.T @ (matrix @ prik_x - target), np.zeros(2))
