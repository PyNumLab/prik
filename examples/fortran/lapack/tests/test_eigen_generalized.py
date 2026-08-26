"""Generalized nonsymmetric and symmetric eigenvalue correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_orthogonal


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _generalized_problem():
    a = np.diag([2.0, 6.0]).astype(np.float64, order="F")
    b = np.diag([1.0, 2.0]).astype(np.float64, order="F")
    return a, b


def _assert_generalized_eigenpairs(a, b, values, vectors):
    assert_allclose_float64(values, [2.0, 3.0])
    for index in range(2):
        assert_allclose_float64(a @ vectors[:, index], values[index] * (b @ vectors[:, index]), operation_size=2)
    assert_allclose_float64(vectors.T @ b @ vectors, np.eye(2), operation_size=2)


def test_dgges_computes_generalized_real_schur_form(prik_lapack, scipy_lapack):
    original_a, original_b = _generalized_problem()
    prik_a = original_a.copy(order="F")
    prik_b = original_b.copy(order="F")
    prik_ar, prik_ai, prik_beta = np.empty(2), np.empty(2), np.empty(2)
    prik_vsl, prik_vsr = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dgges(
        "V",
        "V",
        "N",
        np.bool_(False),
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        np.int32(0),
        prik_ar,
        prik_ai,
        prik_beta,
        prik_vsl,
        np.int32(2),
        prik_vsr,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.zeros(2, dtype=np.bool_),
        np.int32(0),
    )
    scipy_a, scipy_b, scipy_sdim, scipy_ar, scipy_ai, scipy_beta, scipy_vsl, scipy_vsr, _work, scipy_info = (
        scipy_lapack.dgges(
            lambda _ar, _ai, _beta: 0,
            original_a.copy(order="F"),
            original_b.copy(order="F"),
            jobvsl=1,
            jobvsr=1,
            sort_t=0,
            lwork=64,
        )
    )

    assert prik_scalars[-1] == scipy_info == 0
    # Character selectors are returned too, so the projected scalars sit at
    # their native-argument positions in the returned tuple.
    assert prik_scalars[7] == scipy_sdim == 0
    for s, t, ar, ai, beta, q, z in (
        (prik_a, prik_b, prik_ar, prik_ai, prik_beta, prik_vsl, prik_vsr),
        (scipy_a, scipy_b, scipy_ar, scipy_ai, scipy_beta, scipy_vsl, scipy_vsr),
    ):
        assert_orthogonal(q)
        assert_orthogonal(z)
        assert_allclose_float64(q @ s @ z.T, original_a, operation_size=2)
        assert_allclose_float64(q @ t @ z.T, original_b, operation_size=2)
        assert_allclose_float64(ai, [0.0, 0.0])
        assert_allclose_float64(ar / beta, [2.0, 3.0])


def test_dggev_computes_generalized_right_eigenvectors(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_ar, prik_ai, prik_beta = np.empty(2), np.empty(2), np.empty(2)
    f2py_ar, f2py_ai, f2py_beta = np.empty(2), np.empty(2), np.empty(2)
    prik_vl, prik_vr = np.empty((1, 2), order="F"), np.empty((2, 2), order="F")
    f2py_vl, f2py_vr = np.empty((1, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dggev(
        "N",
        "V",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        prik_ar,
        prik_ai,
        prik_beta,
        prik_vl,
        np.int32(1),
        prik_vr,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dggev(
        b"N", b"V", 2, f2py_a, f2py_b, f2py_ar, f2py_ai, f2py_beta, f2py_vl, f2py_vr, np.empty(64), 64, 0
    )
    scipy_ar, scipy_ai, scipy_beta, _vl, scipy_vr, _work, scipy_info = scipy_lapack.dggev(
        a.copy(order="F"), b.copy(order="F"), compute_vl=0, compute_vr=1, lwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for ar, ai, beta, vr in (
        (prik_ar, prik_ai, prik_beta, prik_vr),
        (f2py_ar, f2py_ai, f2py_beta, f2py_vr),
        (scipy_ar, scipy_ai, scipy_beta, scipy_vr),
    ):
        assert_allclose_float64(ai, [0.0, 0.0])
        for index in range(2):
            assert_allclose_float64(beta[index] * (a @ vr[:, index]), ar[index] * (b @ vr[:, index]), operation_size=2)


def test_dsygst_reduces_symmetric_generalized_problem(prik_lapack, scipy_lapack, f2py_lapack):
    a, _b = _generalized_problem()
    cholesky = np.diag([1.0, np.sqrt(2.0)]).astype(np.float64, order="F")
    expected = np.diag([2.0, 3.0])
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")

    prik_scalars = prik_lapack.dsygst(
        np.int32(1), "U", np.int32(2), prik_a, np.int32(2), cholesky, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dsygst(1, b"U", 2, f2py_a, cholesky, 0)
    scipy_a, scipy_info = scipy_lapack.dsygst(a.copy(order="F"), cholesky, itype=1, lower=0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, expected, operation_size=2)
    assert_allclose_float64(f2py_a, expected, operation_size=2)
    assert_allclose_float64(scipy_a, expected, operation_size=2)
    assert_allclose_float64(np.linalg.inv(cholesky.T) @ a @ np.linalg.inv(cholesky), expected, operation_size=2)


def test_dsygv_solves_symmetric_generalized_eigenproblem(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dsygv(
        np.int32(1),
        "V",
        "U",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        prik_w,
        np.empty(64),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsygv(1, b"V", b"U", 2, f2py_a, f2py_b, f2py_w, np.empty(64), 64, 0)
    scipy_w, scipy_v, scipy_info = scipy_lapack.dsygv(
        a.copy(order="F"), b.copy(order="F"), itype=1, jobz=b"V", uplo=b"U", lwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_generalized_eigenpairs(a, b, prik_w, prik_a)
    _assert_generalized_eigenpairs(a, b, f2py_w, f2py_a)
    _assert_generalized_eigenpairs(a, b, scipy_w, scipy_v)


def test_dsygvd_solves_divide_and_conquer_generalized_problem(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dsygvd(
        np.int32(1),
        "V",
        "U",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        prik_w,
        np.empty(64),
        np.int32(64),
        np.empty(32, dtype=np.int32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsygvd(
        1, b"V", b"U", 2, f2py_a, f2py_b, f2py_w, np.empty(64), 64, np.empty(32, dtype=np.int32), 32, 0
    )
    scipy_w, scipy_v, scipy_info = scipy_lapack.dsygvd(
        a.copy(order="F"), b.copy(order="F"), itype=1, jobz=b"V", uplo=b"U", lwork=64, liwork=32
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_generalized_eigenpairs(a, b, prik_w, prik_a)
    _assert_generalized_eigenpairs(a, b, f2py_w, f2py_a)
    _assert_generalized_eigenpairs(a, b, scipy_w, scipy_v)


def test_dsygvx_selects_generalized_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_ifail, f2py_ifail = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dsygvx(
        np.int32(1),
        "V",
        "I",
        "U",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        np.float64(0.0),
        np.float64(0.0),
        np.int32(1),
        np.int32(2),
        np.float64(0.0),
        np.int32(0),
        prik_w,
        prik_z,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.empty(10, dtype=np.int32),
        prik_ifail,
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsygvx(
        1,
        b"V",
        b"I",
        b"U",
        2,
        f2py_a,
        f2py_b,
        0.0,
        0.0,
        1,
        2,
        0.0,
        0,
        f2py_w,
        f2py_z,
        np.empty(64),
        64,
        np.empty(10, dtype=np.int32),
        f2py_ifail,
        0,
    )
    scipy_w, scipy_z, scipy_m, scipy_ifail, scipy_info = scipy_lapack.dsygvx(
        a.copy(order="F"), b.copy(order="F"), itype=1, jobz=b"V", range=b"I", uplo=b"U", il=1, iu=2, lwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    # Character selectors are returned too, so the projected scalars sit at
    # their native-argument positions in the returned tuple.
    assert prik_scalars[12] == scipy_m == 2
    _assert_generalized_eigenpairs(a, b, prik_w, prik_z)
    _assert_generalized_eigenpairs(a, b, f2py_w, f2py_z)
    _assert_generalized_eigenpairs(a, b, scipy_w, scipy_z)
    np.testing.assert_array_equal(prik_ifail, scipy_ifail)
    np.testing.assert_array_equal(f2py_ifail, scipy_ifail)


def test_dtgexc_reorders_generalized_schur_blocks(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    identity = np.eye(2, dtype=np.float64, order="F")
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_q, f2py_q = identity.copy(order="F"), identity.copy(order="F")
    prik_z, f2py_z = identity.copy(order="F"), identity.copy(order="F")

    prik_scalars = prik_lapack.dtgexc(
        np.bool_(True),
        np.bool_(True),
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        prik_q,
        np.int32(2),
        prik_z,
        np.int32(2),
        np.int32(1),
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtgexc(1, 1, 2, f2py_a, f2py_b, f2py_q, f2py_z, 1, 2, np.empty(64), 64, 0)
    scipy_a, scipy_b, scipy_q, scipy_z, _work, scipy_info = scipy_lapack.dtgexc(
        a.copy(order="F"),
        b.copy(order="F"),
        identity.copy(order="F"),
        identity.copy(order="F"),
        1,
        2,
        wantq=1,
        wantz=1,
        lwork=64,
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for s, t, q, z in (
        (prik_a, prik_b, prik_q, prik_z),
        (f2py_a, f2py_b, f2py_q, f2py_z),
        (scipy_a, scipy_b, scipy_q, scipy_z),
    ):
        assert_allclose_float64(np.diag(s) / np.diag(t), [3.0, 2.0])
        assert_allclose_float64(q @ s @ z.T, a, operation_size=2)
        assert_allclose_float64(q @ t @ z.T, b, operation_size=2)


def test_dtgsen_reorders_selected_generalized_eigenvalue(prik_lapack, scipy_lapack, f2py_lapack):
    a, b = _generalized_problem()
    identity = np.eye(2, dtype=np.float64, order="F")
    selection = np.array([False, True], dtype=np.bool_)
    prik_selection = selection.copy()
    prik_a, f2py_a = a.copy(order="F"), a.copy(order="F")
    prik_b, f2py_b = b.copy(order="F"), b.copy(order="F")
    prik_q, f2py_q = identity.copy(order="F"), identity.copy(order="F")
    prik_z, f2py_z = identity.copy(order="F"), identity.copy(order="F")
    prik_ar, prik_ai, prik_beta = np.empty(2), np.empty(2), np.empty(2)
    f2py_ar, f2py_ai, f2py_beta = np.empty(2), np.empty(2), np.empty(2)
    prik_dif, f2py_dif = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dtgsen(
        np.int32(0),
        np.bool_(True),
        np.bool_(True),
        prik_selection,
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_b,
        np.int32(2),
        prik_ar,
        prik_ai,
        prik_beta,
        prik_q,
        np.int32(2),
        prik_z,
        np.int32(2),
        np.int32(0),
        np.float64(0.0),
        np.float64(0.0),
        prik_dif,
        np.empty(64),
        np.int32(64),
        np.empty(16, dtype=np.int32),
        np.int32(16),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtgsen(
        0,
        1,
        1,
        selection.astype(np.int32),
        2,
        f2py_a,
        f2py_b,
        f2py_ar,
        f2py_ai,
        f2py_beta,
        f2py_q,
        f2py_z,
        0,
        0.0,
        0.0,
        f2py_dif,
        np.empty(64),
        64,
        np.empty(16, dtype=np.int32),
        16,
        0,
    )
    scipy_a, scipy_b, scipy_ar, scipy_ai, scipy_beta, scipy_q, scipy_z, scipy_m, _pl, _pr, _dif, scipy_info = (
        scipy_lapack.dtgsen(
            selection.astype(np.int32),
            a.copy(order="F"),
            b.copy(order="F"),
            identity.copy(order="F"),
            identity.copy(order="F"),
            ijob=0,
            wantq=1,
            wantz=1,
            lwork=64,
            liwork=16,
        )
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[8] == scipy_m == 1
    for s, t, ar, ai, beta, q, z in (
        (prik_a, prik_b, prik_ar, prik_ai, prik_beta, prik_q, prik_z),
        (f2py_a, f2py_b, f2py_ar, f2py_ai, f2py_beta, f2py_q, f2py_z),
        (scipy_a, scipy_b, scipy_ar, scipy_ai, scipy_beta, scipy_q, scipy_z),
    ):
        assert_allclose_float64(ai, [0.0, 0.0])
        assert_allclose_float64(ar / beta, [3.0, 2.0])
        assert_allclose_float64(q @ s @ z.T, a, operation_size=2)
        assert_allclose_float64(q @ t @ z.T, b, operation_size=2)


def test_dtgsyl_solves_generalized_sylvester_equations(prik_lapack, scipy_lapack, f2py_lapack):
    a = np.array([[2.0]], dtype=np.float64, order="F")
    b = np.array([[3.0]], dtype=np.float64, order="F")
    c = np.array([[-4.0]], dtype=np.float64, order="F")
    d = np.array([[1.0]], dtype=np.float64, order="F")
    e = np.array([[4.0]], dtype=np.float64, order="F")
    f = np.array([[-7.0]], dtype=np.float64, order="F")
    prik_c, f2py_c = c.copy(order="F"), c.copy(order="F")
    prik_f, f2py_f = f.copy(order="F"), f.copy(order="F")

    prik_scalars = prik_lapack.dtgsyl(
        "N",
        np.int32(0),
        np.int32(1),
        np.int32(1),
        a,
        np.int32(1),
        b,
        np.int32(1),
        prik_c,
        np.int32(1),
        d,
        np.int32(1),
        e,
        np.int32(1),
        prik_f,
        np.int32(1),
        np.float64(0.0),
        np.float64(0.0),
        np.empty(8),
        np.int32(8),
        np.empty(2, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtgsyl(
        b"N", 0, 1, 1, a, b, f2py_c, d, e, f2py_f, 0.0, 0.0, np.empty(8), 8, np.empty(2, dtype=np.int32), 0
    )
    scipy_r, scipy_l, scipy_scale, scipy_dif, scipy_info = scipy_lapack.dtgsyl(
        a, b, c.copy(order="F"), d, e, f.copy(order="F"), trans=b"N", ijob=0, lwork=8
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_c, [[1.0]])
    assert_allclose_float64(f2py_c, [[1.0]])
    assert_allclose_float64(scipy_r, [[1.0]])
    assert_allclose_float64(prik_f, [[2.0]])
    assert_allclose_float64(f2py_f, [[2.0]])
    assert_allclose_float64(scipy_l, [[2.0]])
    assert_allclose_float64(a @ prik_c - prik_f @ b, prik_scalars[-4] * c)
    assert_allclose_float64(d @ prik_c - prik_f @ e, prik_scalars[-4] * f)
    assert_allclose_float64(prik_scalars[-4], scipy_scale)
    assert_allclose_float64(prik_scalars[-3], scipy_dif)
