"""Orthogonal-factorization and transformation correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_orthogonal, column_major, qr_q_from_reflectors


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgemqrt_applies_compact_wy_reflector(prik_lapack, scipy_lapack, f2py_lapack):
    original = np.array([[3.0], [4.0]], dtype=np.float64, order="F")
    factor, compact_t, factor_info = scipy_lapack.dgeqrt(1, original.copy(order="F"))
    assert factor_info == 0
    vector = np.array([1.0, factor[1, 0]], dtype=np.float64)
    q = np.eye(2) - compact_t[0, 0] * np.outer(vector, vector)
    target = np.array([[2.0], [1.0]], dtype=np.float64, order="F")
    expected = q @ target
    prik_c, f2py_c = target.copy(order="F"), target.copy(order="F")

    prik_scalars = prik_lapack.dgemqrt("L", "N", 2, 1, 1, 1, factor, 2, compact_t, 1, prik_c, 2, np.empty(1), 0)
    f2py_result = f2py_lapack.dgemqrt(b"L", b"N", 2, 1, 1, 1, factor, 2, compact_t, 1, f2py_c, 2, np.empty(1), 0)
    scipy_c, scipy_info = scipy_lapack.dgemqrt(factor, compact_t, target.copy(order="F"), side=b"L", trans=b"N")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_c, expected, operation_size=2)
    assert_allclose_float64(f2py_c, expected, operation_size=2)
    assert_allclose_float64(scipy_c, expected, operation_size=2)


def test_dgeqp3_reconstructs_column_pivoted_qr(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 5.0], [2.0, 6.0], [3.0, 8.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_jpvt, f2py_jpvt = np.zeros(2, dtype=np.int32), np.zeros(2, dtype=np.int32)
    prik_tau, f2py_tau = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgeqp3(3, 2, prik_a, 3, prik_jpvt, prik_tau, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dgeqp3(3, 2, f2py_a, 3, f2py_jpvt, f2py_tau, np.empty(64), 64, 0)
    scipy_qr, scipy_jpvt, _scipy_tau, _work, scipy_info = scipy_lapack.dgeqp3(matrix.copy(order="F"), lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor, tau, pivots in ((prik_a, prik_tau, prik_jpvt), (f2py_a, f2py_tau, f2py_jpvt)):
        q = qr_q_from_reflectors(factor, tau)
        r = np.triu(factor[:2, :])
        assert_allclose_float64(q @ r, matrix[:, pivots - 1], operation_size=3)
    assert_allclose_float64(prik_a, scipy_qr, operation_size=3)
    assert_allclose_float64(f2py_a, scipy_qr, operation_size=3)
    np.testing.assert_array_equal(prik_jpvt, scipy_jpvt + 1)
    np.testing.assert_array_equal(f2py_jpvt, scipy_jpvt + 1)


def test_dgeqrf_reconstructs_qr_factorization(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(matrix), column_major(matrix)
    prik_tau = np.empty(2, dtype=np.float64)
    f2py_tau = np.empty(2, dtype=np.float64)

    prik_scalars = prik_lapack.dgeqrf(3, 2, prik_a, 3, prik_tau, np.empty(16), 16, 0)
    f2py_result = f2py_lapack.dgeqrf(3, 2, f2py_a, 3, f2py_tau, np.empty(16), 16, 0)
    scipy_qr, scipy_tau, _scipy_work, scipy_info = scipy_lapack.dgeqrf(matrix.copy(order="F"), lwork=16)

    assert prik_scalars == (3, 2, 3, 16, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for factor, tau in ((prik_a, prik_tau), (f2py_a, f2py_tau), (scipy_qr, scipy_tau)):
        q = qr_q_from_reflectors(factor, tau)
        r = np.triu(factor[:2, :])
        assert_orthogonal(q)
        assert_allclose_float64(q @ r, matrix, operation_size=3)
    assert_allclose_float64(prik_a, scipy_qr, operation_size=3)
    assert_allclose_float64(f2py_a, scipy_qr, operation_size=3)
    assert_allclose_float64(prik_tau, scipy_tau, operation_size=3)
    assert_allclose_float64(f2py_tau, scipy_tau, operation_size=3)


def test_dgeqrfp_reconstructs_qr_with_nonnegative_diagonal(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, -4.0], [5.0, 7.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_tau, f2py_tau = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgeqrfp(3, 2, prik_a, 3, prik_tau, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dgeqrfp(3, 2, f2py_a, 3, f2py_tau, np.empty(64), 64, 0)
    scipy_qr, scipy_tau, scipy_info = scipy_lapack.dgeqrfp(matrix.copy(order="F"), lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor, tau in ((prik_a, prik_tau), (f2py_a, f2py_tau), (scipy_qr, scipy_tau)):
        q = qr_q_from_reflectors(factor, tau)
        r = np.triu(factor[:2, :])
        assert_allclose_float64(q @ r, matrix, operation_size=3)
        assert np.all(np.diag(r) >= 0.0)


def test_dgeqrt_reconstructs_compact_wy_qr(prik_lapack, scipy_lapack, f2py_lapack):
    original = np.array([[3.0], [4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = original.copy(order="F"), original.copy(order="F")
    prik_t, f2py_t = np.empty((1, 1), order="F"), np.empty((1, 1), order="F")

    prik_scalars = prik_lapack.dgeqrt(2, 1, 1, prik_a, 2, prik_t, 1, np.empty(1), 0)
    f2py_result = f2py_lapack.dgeqrt(2, 1, 1, f2py_a, 2, f2py_t, 1, np.empty(1), 0)
    scipy_a, scipy_t, scipy_info = scipy_lapack.dgeqrt(1, original.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor, compact_t in ((prik_a, prik_t), (f2py_a, f2py_t), (scipy_a, scipy_t)):
        vector = np.array([1.0, factor[1, 0]])
        q = np.eye(2) - compact_t[0, 0] * np.outer(vector, vector)
        assert_orthogonal(q)
        assert_allclose_float64(q @ np.array([[factor[0, 0]], [0.0]]), original, operation_size=2)


def test_dgerqf_reconstructs_rq_factorization(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[3.0, 4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_tau, f2py_tau = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgerqf(1, 2, prik_a, 1, prik_tau, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dgerqf(1, 2, f2py_a, 1, f2py_tau, np.empty(64), 64, 0)
    scipy_rq, scipy_tau, _work, scipy_info = scipy_lapack.dgerqf(matrix.copy(order="F"), lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor, tau in ((prik_a, prik_tau), (f2py_a, f2py_tau), (scipy_rq, scipy_tau)):
        vector = np.array([factor[0, 0], 1.0])
        q = np.eye(2) - tau[0] * np.outer(vector, vector)
        assert_allclose_float64(np.array([[0.0, factor[0, 1]]]) @ q, matrix, operation_size=2)


def test_dorgqr_forms_explicit_orthogonal_q(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    factor, tau, _work, factor_info = scipy_lapack.dgeqrf(matrix.copy(order="F"), lwork=16)
    assert factor_info == 0
    r = np.triu(factor[:2, :])
    prik_q, f2py_q = column_major(factor), column_major(factor)

    prik_scalars = prik_lapack.dorgqr(3, 2, 2, prik_q, 3, tau.copy(), np.empty(16), 16, 0)
    f2py_result = f2py_lapack.dorgqr(3, 2, 2, f2py_q, 3, tau.copy(), np.empty(16), 16, 0)
    scipy_q, _scipy_work, scipy_info = scipy_lapack.dorgqr(factor.copy(order="F"), tau.copy(), lwork=16)

    assert prik_scalars == (3, 2, 2, 3, 16, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for q in (prik_q, f2py_q, scipy_q):
        assert_orthogonal(q)
        assert_allclose_float64(q @ r, matrix, operation_size=3)
    assert_allclose_float64(prik_q, scipy_q, operation_size=3)
    assert_allclose_float64(f2py_q, scipy_q, operation_size=3)


def test_dorgrq_forms_explicit_row_orthogonal_q(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[3.0, 4.0]], dtype=np.float64, order="F")
    factor, tau, _work, factor_info = scipy_lapack.dgerqf(matrix.copy(order="F"), lwork=64)
    assert factor_info == 0
    r = factor[0, 1]
    prik_q, f2py_q = factor.copy(order="F"), factor.copy(order="F")

    prik_scalars = prik_lapack.dorgrq(1, 2, 1, prik_q, 1, tau.copy(), np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dorgrq(1, 2, 1, f2py_q, 1, tau.copy(), np.empty(64), 64, 0)
    scipy_q, _work, scipy_info = scipy_lapack.dorgrq(factor.copy(order="F"), tau.copy(), lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for q in (prik_q, f2py_q, scipy_q):
        assert_allclose_float64(q @ q.T, np.eye(1), operation_size=2)
        assert_allclose_float64(r * q, matrix, operation_size=2)


def test_dormqr_applies_qr_reflectors(prik_lapack, scipy_lapack, f2py_lapack):
    source = np.array([[3.0], [4.0]], dtype=np.float64, order="F")
    factor, tau, _work, factor_info = scipy_lapack.dgeqrf(source.copy(order="F"), lwork=64)
    assert factor_info == 0
    q = qr_q_from_reflectors(factor, tau)
    target = np.array([[2.0], [1.0]], dtype=np.float64, order="F")
    expected = q @ target
    prik_c, f2py_c = target.copy(order="F"), target.copy(order="F")

    prik_scalars = prik_lapack.dormqr("L", "N", 2, 1, 1, factor, 2, tau, prik_c, 2, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dormqr(b"L", b"N", 2, 1, 1, factor, 2, tau, f2py_c, 2, np.empty(64), 64, 0)
    scipy_c, _work, scipy_info = scipy_lapack.dormqr(b"L", b"N", factor, tau, target.copy(order="F"), 64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_c, expected, operation_size=2)
    assert_allclose_float64(f2py_c, expected, operation_size=2)
    assert_allclose_float64(scipy_c, expected, operation_size=2)


def test_dormrz_applies_rz_reflector(prik_lapack, scipy_lapack, f2py_lapack):
    source = np.array([[3.0, 4.0]], dtype=np.float64, order="F")
    factor, tau, factor_info = scipy_lapack.dtzrzf(source.copy(order="F"), lwork=64)
    assert factor_info == 0
    vector = np.array([1.0, factor[0, 1]])
    z = np.eye(2) - tau[0] * np.outer(vector, vector)
    target = np.array([[2.0, 1.0]], dtype=np.float64, order="F")
    expected = target @ z
    prik_c, f2py_c = target.copy(order="F"), target.copy(order="F")

    prik_scalars = prik_lapack.dormrz("R", "N", 1, 2, 1, 1, factor, 1, tau, prik_c, 1, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dormrz(b"R", b"N", 1, 2, 1, 1, factor, 1, tau, f2py_c, 1, np.empty(64), 64, 0)
    scipy_c, scipy_info = scipy_lapack.dormrz(factor, tau, target.copy(order="F"), side=b"R", trans=b"N", lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_c, expected, operation_size=2)
    assert_allclose_float64(f2py_c, expected, operation_size=2)
    assert_allclose_float64(scipy_c, expected, operation_size=2)


def test_dtpmqrt_applies_triangular_pentagonal_reflector(prik_lapack, scipy_lapack, f2py_lapack):
    top = np.array([[2.0]], dtype=np.float64, order="F")
    bottom = np.array([[3.0]], dtype=np.float64, order="F")
    _factor_a, factor_b, compact_t, factor_info = scipy_lapack.dtpqrt(0, 1, top.copy(order="F"), bottom.copy(order="F"))
    assert factor_info == 0
    vector = np.array([1.0, factor_b[0, 0]])
    q = np.eye(2) - compact_t[0, 0] * np.outer(vector, vector)
    target_a = np.array([[4.0]], dtype=np.float64, order="F")
    target_b = np.array([[5.0]], dtype=np.float64, order="F")
    expected = q @ np.vstack((target_a, target_b))
    prik_a, prik_b = target_a.copy(order="F"), target_b.copy(order="F")
    f2py_a, f2py_b = target_a.copy(order="F"), target_b.copy(order="F")

    prik_scalars = prik_lapack.dtpmqrt(
        "L", "N", 1, 1, 1, 0, 1, factor_b, 1, compact_t, 1, prik_a, 1, prik_b, 1, np.empty(1), 0
    )
    f2py_result = f2py_lapack.dtpmqrt(
        b"L", b"N", 1, 1, 1, 0, 1, factor_b, 1, compact_t, 1, f2py_a, 1, f2py_b, 1, np.empty(1), 0
    )
    scipy_a, scipy_b, scipy_info = scipy_lapack.dtpmqrt(
        0, factor_b, compact_t, target_a.copy(order="F"), target_b.copy(order="F"), side=b"L", trans=b"N"
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(np.vstack((prik_a, prik_b)), expected, operation_size=2)
    assert_allclose_float64(np.vstack((f2py_a, f2py_b)), expected, operation_size=2)
    assert_allclose_float64(np.vstack((scipy_a, scipy_b)), expected, operation_size=2)


def test_dtpqrt_reconstructs_triangular_pentagonal_qr(prik_lapack, scipy_lapack, f2py_lapack):
    top = np.array([[2.0]], dtype=np.float64, order="F")
    bottom = np.array([[3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = top.copy(order="F"), top.copy(order="F")
    prik_b, f2py_b = bottom.copy(order="F"), bottom.copy(order="F")
    prik_t, f2py_t = np.empty((1, 1), order="F"), np.empty((1, 1), order="F")

    prik_scalars = prik_lapack.dtpqrt(1, 1, 0, 1, prik_a, 1, prik_b, 1, prik_t, 1, np.empty(1), 0)
    f2py_result = f2py_lapack.dtpqrt(1, 1, 0, 1, f2py_a, 1, f2py_b, 1, f2py_t, 1, np.empty(1), 0)
    scipy_a, scipy_b, scipy_t, scipy_info = scipy_lapack.dtpqrt(0, 1, top.copy(order="F"), bottom.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor_a, factor_b, compact_t in (
        (prik_a, prik_b, prik_t),
        (f2py_a, f2py_b, f2py_t),
        (scipy_a, scipy_b, scipy_t),
    ):
        vector = np.array([1.0, factor_b[0, 0]])
        q = np.eye(2) - compact_t[0, 0] * np.outer(vector, vector)
        assert_allclose_float64(q @ np.array([[factor_a[0, 0]], [0.0]]), np.vstack((top, bottom)), operation_size=2)


def test_dtzrzf_reconstructs_rz_factorization(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[3.0, 4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_tau, f2py_tau = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dtzrzf(1, 2, prik_a, 1, prik_tau, np.empty(64), 64, 0)
    f2py_result = f2py_lapack.dtzrzf(1, 2, f2py_a, 1, f2py_tau, np.empty(64), 64, 0)
    scipy_a, scipy_tau, scipy_info = scipy_lapack.dtzrzf(matrix.copy(order="F"), lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for factor, tau in ((prik_a, prik_tau), (f2py_a, f2py_tau), (scipy_a, scipy_tau)):
        vector = np.array([1.0, factor[0, 1]])
        z = np.eye(2) - tau[0] * np.outer(vector, vector)
        assert_allclose_float64(np.array([[factor[0, 0], 0.0]]) @ z, matrix, operation_size=2)
