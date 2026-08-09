"""Nonsymmetric eigenvalue, Schur, Hessenberg, and Sylvester correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_orthogonal


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgebal_preserves_eigenvalues_while_balancing(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.diag(np.array([2.0, 5.0], dtype=np.float64)).copy(order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_scale, f2py_scale = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dgebal(
        "B", np.int32(2), prik_a, np.int32(2), np.int32(0), np.int32(0), prik_scale, np.int32(0)
    )
    f2py_result = f2py_lapack.dgebal(b"B", 2, f2py_a, 0, 0, f2py_scale, 0)
    scipy_a, scipy_lo, scipy_hi, scipy_scale, scipy_info = scipy_lapack.dgebal(
        matrix.copy(order="F"), scale=1, permute=1
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[2:4] == (scipy_lo + 1, scipy_hi + 1)
    assert_allclose_float64(np.sort(np.diag(prik_a)), [2.0, 5.0])
    assert_allclose_float64(np.sort(np.diag(f2py_a)), [2.0, 5.0])
    assert_allclose_float64(prik_a, scipy_a)
    assert_allclose_float64(f2py_a, scipy_a)
    assert_allclose_float64(prik_scale, scipy_scale)
    assert_allclose_float64(f2py_scale, scipy_scale)


def test_dgees_computes_real_schur_decomposition(prik_lapack, scipy_lapack):
    matrix = np.array([[1.0, 2.0], [0.0, 3.0]], dtype=np.float64, order="F")
    prik_t = matrix.copy(order="F")
    prik_wr, prik_wi = np.empty(2), np.empty(2)
    prik_vs = np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dgees(
        "V",
        "N",
        np.bool_(False),
        np.int32(2),
        prik_t,
        np.int32(2),
        np.int32(0),
        prik_wr,
        prik_wi,
        prik_vs,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.zeros(2, dtype=np.bool_),
        np.int32(0),
    )
    scipy_t, scipy_sdim, scipy_wr, scipy_wi, scipy_vs, _work, scipy_info = scipy_lapack.dgees(
        lambda _wr, _wi: 0, matrix.copy(order="F"), compute_v=1, sort_t=0, lwork=64
    )

    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[3] == scipy_sdim == 0
    for t, vs, wr, wi in (
        (prik_t, prik_vs, prik_wr, prik_wi),
        (scipy_t, scipy_vs, scipy_wr, scipy_wi),
    ):
        assert_orthogonal(vs)
        assert_allclose_float64(vs @ t @ vs.T, matrix, operation_size=2)
        assert_allclose_float64(np.sort(wr), [1.0, 3.0])
        assert_allclose_float64(wi, [0.0, 0.0])


def test_dgeev_returns_right_eigenvectors(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [0.0, 3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_wr, prik_wi = np.empty(2), np.empty(2)
    f2py_wr, f2py_wi = np.empty(2), np.empty(2)
    prik_vl, prik_vr = np.empty((1, 2), order="F"), np.empty((2, 2), order="F")
    f2py_vl, f2py_vr = np.empty((1, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dgeev(
        "N",
        "V",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_wr,
        prik_wi,
        prik_vl,
        np.int32(1),
        prik_vr,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgeev(b"N", b"V", 2, f2py_a, f2py_wr, f2py_wi, f2py_vl, f2py_vr, np.empty(64), 64, 0)
    scipy_wr, scipy_wi, _vl, scipy_vr, scipy_info = scipy_lapack.dgeev(
        matrix.copy(order="F"), compute_vl=0, compute_vr=1, lwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for wr, wi, vr in ((prik_wr, prik_wi, prik_vr), (f2py_wr, f2py_wi, f2py_vr), (scipy_wr, scipy_wi, scipy_vr)):
        assert_allclose_float64(wi, [0.0, 0.0])
        for index in range(2):
            assert_allclose_float64(matrix @ vr[:, index], wr[index] * vr[:, index], operation_size=2)


def test_dgehrd_reduces_matrix_to_upper_hessenberg(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_tau, f2py_tau = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgehrd(
        np.int32(2), np.int32(1), np.int32(2), prik_a, np.int32(2), prik_tau, np.empty(64), np.int32(64), np.int32(0)
    )
    f2py_result = f2py_lapack.dgehrd(2, 1, 2, f2py_a, f2py_tau, np.empty(64), 64, 0)
    scipy_a, scipy_tau, scipy_info = scipy_lapack.dgehrd(matrix.copy(order="F"), lo=0, hi=1, lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(np.triu(prik_a, -1), matrix)
    assert_allclose_float64(np.triu(f2py_a, -1), matrix)
    assert_allclose_float64(prik_a, scipy_a)
    assert_allclose_float64(f2py_a, scipy_a)
    assert_allclose_float64(prik_tau, scipy_tau)
    assert_allclose_float64(f2py_tau, scipy_tau)


def test_dorghr_forms_hessenberg_similarity_transform(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64, order="F")
    factor, tau, factor_info = scipy_lapack.dgehrd(matrix.copy(order="F"), lo=0, hi=1, lwork=64)
    assert factor_info == 0
    prik_q, f2py_q = factor.copy(order="F"), factor.copy(order="F")

    prik_scalars = prik_lapack.dorghr(
        np.int32(2), np.int32(1), np.int32(2), prik_q, np.int32(2), tau, np.empty(64), np.int32(64), np.int32(0)
    )
    f2py_result = f2py_lapack.dorghr(2, 1, 2, f2py_q, tau, np.empty(64), 64, 0)
    scipy_q, scipy_info = scipy_lapack.dorghr(factor.copy(order="F"), tau, lo=0, hi=1, lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for q in (prik_q, f2py_q, scipy_q):
        assert_orthogonal(q)
        assert_allclose_float64(q.T @ matrix @ q, matrix, operation_size=2)


def test_dtrexc_reorders_real_schur_blocks(prik_lapack, scipy_lapack, f2py_lapack):
    schur = np.diag([1.0, 2.0]).astype(np.float64, order="F")
    identity = np.eye(2, dtype=np.float64, order="F")
    prik_t, f2py_t = schur.copy(order="F"), schur.copy(order="F")
    prik_q, f2py_q = identity.copy(order="F"), identity.copy(order="F")

    prik_scalars = prik_lapack.dtrexc(
        "V", np.int32(2), prik_t, np.int32(2), prik_q, np.int32(2), np.int32(1), np.int32(2), np.empty(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dtrexc(b"V", 2, f2py_t, f2py_q, 1, 2, np.empty(2), 0)
    scipy_t, scipy_q, scipy_info = scipy_lapack.dtrexc(schur.copy(order="F"), identity.copy(order="F"), 1, 2, wantq=1)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for t, q in ((prik_t, prik_q), (f2py_t, f2py_q), (scipy_t, scipy_q)):
        assert_allclose_float64(np.diag(t), [2.0, 1.0])
        assert_orthogonal(q)
        assert_allclose_float64(q @ t @ q.T, schur, operation_size=2)


def test_dtrsen_reorders_selected_schur_eigenvalue(prik_lapack, scipy_lapack, f2py_lapack):
    schur = np.diag([1.0, 2.0]).astype(np.float64, order="F")
    identity = np.eye(2, dtype=np.float64, order="F")
    prik_t, f2py_t = schur.copy(order="F"), schur.copy(order="F")
    prik_q, f2py_q = identity.copy(order="F"), identity.copy(order="F")
    prik_wr, prik_wi = np.empty(2), np.empty(2)
    f2py_wr, f2py_wi = np.empty(2), np.empty(2)
    selection = np.array([False, True], dtype=np.bool_)
    prik_selection = selection.copy()

    prik_scalars = prik_lapack.dtrsen(
        "N",
        "V",
        prik_selection,
        np.int32(2),
        prik_t,
        np.int32(2),
        prik_q,
        np.int32(2),
        prik_wr,
        prik_wi,
        np.int32(0),
        np.float64(0.0),
        np.float64(0.0),
        np.empty(8),
        np.int32(8),
        np.empty(2, dtype=np.int32),
        np.int32(2),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtrsen(
        b"N",
        b"V",
        selection.astype(np.int32),
        2,
        f2py_t,
        f2py_q,
        f2py_wr,
        f2py_wi,
        0,
        0.0,
        0.0,
        np.empty(8),
        8,
        np.empty(2, dtype=np.int32),
        2,
        0,
    )
    scipy_t, scipy_q, scipy_wr, scipy_wi, scipy_m, _s, _sep, scipy_info = scipy_lapack.dtrsen(
        selection.astype(np.int32),
        schur.copy(order="F"),
        identity.copy(order="F"),
        job=b"N",
        wantq=1,
        lwork=8,
        liwork=2,
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[3] == scipy_m == 1
    for t, q, wr, wi in (
        (prik_t, prik_q, prik_wr, prik_wi),
        (f2py_t, f2py_q, f2py_wr, f2py_wi),
        (scipy_t, scipy_q, scipy_wr, scipy_wi),
    ):
        assert_allclose_float64(wr, [2.0, 1.0])
        assert_allclose_float64(wi, [0.0, 0.0])
        assert_allclose_float64(q @ t @ q.T, schur, operation_size=2)


def test_dtrsyl_solves_sylvester_equation(prik_lapack, scipy_lapack, f2py_lapack):
    a = np.array([[2.0]], dtype=np.float64, order="F")
    b = np.array([[3.0]], dtype=np.float64, order="F")
    c = np.array([[10.0]], dtype=np.float64, order="F")
    prik_c, f2py_c = c.copy(order="F"), c.copy(order="F")

    prik_scalars = prik_lapack.dtrsyl(
        "N",
        "N",
        np.int32(1),
        np.int32(1),
        np.int32(1),
        a,
        np.int32(1),
        b,
        np.int32(1),
        prik_c,
        np.int32(1),
        np.float64(0.0),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtrsyl(b"N", b"N", 1, 1, 1, a, b, f2py_c, 0.0, 0)
    scipy_x, scipy_scale, scipy_info = scipy_lapack.dtrsyl(a, b, c.copy(order="F"), trana=b"N", tranb=b"N", isgn=1)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_c, [[2.0]])
    assert_allclose_float64(f2py_c, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])
    assert_allclose_float64(prik_scalars[-2], scipy_scale)
    assert_allclose_float64(a @ prik_c + prik_c @ b, prik_scalars[-2] * c)
