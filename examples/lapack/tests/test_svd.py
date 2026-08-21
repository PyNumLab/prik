"""Singular-value-decomposition correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_orthogonal


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgejsv_reconstructs_matrix_with_jacobi_svd(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[3.0, 1.0], [0.0, 2.0]], dtype=np.float64, order="F")
    expected_values = np.linalg.svd(matrix, compute_uv=False)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_s, f2py_s = np.empty(2), np.empty(2)
    prik_u, f2py_u = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_v, f2py_v = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dgejsv(
        "A",
        "U",
        "V",
        "N",
        "N",
        "N",
        np.int32(2),
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_s,
        prik_u,
        np.int32(2),
        prik_v,
        np.int32(2),
        np.empty(128),
        np.int32(128),
        np.empty(16, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgejsv(
        b"A",
        b"U",
        b"V",
        b"N",
        b"N",
        b"N",
        2,
        f2py_a,
        f2py_s,
        f2py_u,
        f2py_v,
        np.empty(128),
        np.empty(16, dtype=np.int32),
        0,
    )
    scipy_s, scipy_u, scipy_v, _work, _iwork, scipy_info = scipy_lapack.dgejsv(
        matrix.copy(order="F"), joba=4, jobu=0, jobv=0, jobr=1, jobt=0, jobp=1, lwork=128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for values, u, v in ((prik_s, prik_u, prik_v), (f2py_s, f2py_u, f2py_v), (scipy_s, scipy_u, scipy_v)):
        assert_allclose_float64(values, expected_values, operation_size=2)
        assert_orthogonal(u)
        assert_orthogonal(v)
        assert_allclose_float64(u @ np.diag(values) @ v.T, matrix, operation_size=2)


def test_dgesdd_reconstructs_matrix_with_divide_and_conquer_svd(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_s, f2py_s = np.empty(2), np.empty(2)
    prik_u, f2py_u = np.empty((3, 3), order="F"), np.empty((3, 3), order="F")
    prik_vt, f2py_vt = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dgesdd(
        "A",
        np.int32(3),
        np.int32(2),
        prik_a,
        np.int32(3),
        prik_s,
        prik_u,
        np.int32(3),
        prik_vt,
        np.int32(2),
        np.empty(128),
        np.int32(128),
        np.empty(16, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgesdd(
        b"A", 3, 2, f2py_a, f2py_s, f2py_u, f2py_vt, np.empty(128), 128, np.empty(16, dtype=np.int32), 0
    )
    scipy_u, scipy_s, scipy_vt, scipy_info = scipy_lapack.dgesdd(
        matrix.copy(order="F"), compute_uv=1, full_matrices=1, lwork=128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for u, values, vt in ((prik_u, prik_s, prik_vt), (f2py_u, f2py_s, f2py_vt), (scipy_u, scipy_s, scipy_vt)):
        assert_orthogonal(u)
        assert_orthogonal(vt.T)
        assert_allclose_float64(u[:, :2] @ np.diag(values) @ vt, matrix, operation_size=3)
    assert_allclose_float64(prik_s, scipy_s, operation_size=3)
    assert_allclose_float64(f2py_s, scipy_s, operation_size=3)


def test_dgesvd_reconstructs_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]], dtype=np.float64)
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_s, f2py_s = np.empty(2, dtype=np.float64), np.empty(2, dtype=np.float64)
    prik_u, f2py_u = np.zeros((3, 3), dtype=np.float64, order="F"), np.zeros((3, 3), dtype=np.float64, order="F")
    prik_vt, f2py_vt = np.zeros((2, 2), dtype=np.float64, order="F"), np.zeros((2, 2), dtype=np.float64, order="F")

    prik_scalars = prik_lapack.dgesvd(
        "A",
        "A",
        np.int32(3),
        np.int32(2),
        prik_a,
        np.int32(3),
        prik_s,
        prik_u,
        np.int32(3),
        prik_vt,
        np.int32(2),
        np.empty(32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgesvd(b"A", b"A", 3, 2, f2py_a, f2py_s, f2py_u, f2py_vt, np.empty(32), 32, 0)
    scipy_u, scipy_s, scipy_vt, scipy_info = scipy_lapack.dgesvd(
        matrix.copy(order="F"), compute_uv=1, full_matrices=1, lwork=32
    )

    # LAPACK declares no intent on its dummies, so the conservative
    # intent(inout) default returns every scalar, character selectors included.
    assert prik_scalars == ("A", "A", 3, 2, 3, 3, 2, 32, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for u, values, vt in (
        (prik_u, prik_s, prik_vt),
        (f2py_u, f2py_s, f2py_vt),
        (scipy_u, scipy_s, scipy_vt),
    ):
        assert np.all(np.diff(values) <= 0.0)
        assert_orthogonal(u)
        assert_orthogonal(vt.T)
        assert_allclose_float64(u[:, :2] @ np.diag(values) @ vt, matrix, operation_size=3)
    assert_allclose_float64(prik_s, scipy_s, operation_size=3)
    assert_allclose_float64(f2py_s, scipy_s, operation_size=3)


def test_dorcsd_decomposes_partitioned_orthogonal_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    angle = 0.4
    cosine_value = np.cos(angle)
    sine_value = np.sin(angle)
    x11 = np.array([[cosine_value]], dtype=np.float64, order="F")
    x12 = np.array([[-sine_value]], dtype=np.float64, order="F")
    x21 = np.array([[sine_value]], dtype=np.float64, order="F")
    x22 = np.array([[cosine_value]], dtype=np.float64, order="F")
    prik_blocks = [block.copy(order="F") for block in (x11, x12, x21, x22)]
    f2py_blocks = [block.copy(order="F") for block in (x11, x12, x21, x22)]
    prik_theta, f2py_theta = np.empty(1), np.empty(1)
    prik_u1, prik_u2, prik_v1t, prik_v2t = (np.empty((1, 1), order="F") for _ in range(4))
    f2py_u1, f2py_u2, f2py_v1t, f2py_v2t = (np.empty((1, 1), order="F") for _ in range(4))

    prik_scalars = prik_lapack.dorcsd(
        "Y",
        "Y",
        "Y",
        "Y",
        "N",
        "O",
        np.int32(2),
        np.int32(1),
        np.int32(1),
        prik_blocks[0],
        np.int32(1),
        prik_blocks[1],
        np.int32(1),
        prik_blocks[2],
        np.int32(1),
        prik_blocks[3],
        np.int32(1),
        prik_theta,
        prik_u1,
        np.int32(1),
        prik_u2,
        np.int32(1),
        prik_v1t,
        np.int32(1),
        prik_v2t,
        np.int32(1),
        np.empty(128),
        np.int32(128),
        np.empty(16, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dorcsd(
        b"Y",
        b"Y",
        b"Y",
        b"Y",
        b"N",
        b"O",
        2,
        1,
        1,
        f2py_blocks[0],
        f2py_blocks[1],
        f2py_blocks[2],
        f2py_blocks[3],
        f2py_theta,
        f2py_u1,
        f2py_u2,
        f2py_v1t,
        f2py_v2t,
        np.empty(128),
        128,
        np.empty(16, dtype=np.int32),
        0,
    )
    _c11, _c12, _c21, _c22, scipy_theta, scipy_u1, scipy_u2, scipy_v1t, scipy_v2t, scipy_info = scipy_lapack.dorcsd(
        x11, x12, x21, x22, compute_u1=1, compute_u2=1, compute_v1t=1, compute_v2t=1, trans=0, signs=0, lwork=128
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    for theta, u1, u2, v1t, v2t in (
        (prik_theta, prik_u1, prik_u2, prik_v1t, prik_v2t),
        (f2py_theta, f2py_u1, f2py_u2, f2py_v1t, f2py_v2t),
        (scipy_theta, scipy_u1, scipy_u2, scipy_v1t, scipy_v2t),
    ):
        cosine = np.array([[np.cos(theta[0])]])
        sine = np.array([[np.sin(theta[0])]])
        assert_allclose_float64(theta, [angle])
        for factor in (u1, u2, v1t, v2t):
            assert_allclose_float64(factor.T @ factor, np.eye(1))
        assert_allclose_float64(np.abs(u1 @ cosine @ v1t), np.abs(x11))
        assert_allclose_float64(np.abs(u1 @ sine @ v2t), np.abs(x12))
        assert_allclose_float64(np.abs(u2 @ sine @ v1t), np.abs(x21))
        assert_allclose_float64(np.abs(u2 @ cosine @ v2t), np.abs(x22))


def test_dlasd4_solves_rank_one_secular_equation(prik_lapack, scipy_lapack, f2py_lapack):
    diagonal = np.array([1.0, 3.0], dtype=np.float64)
    update = np.array([0.6, 0.8], dtype=np.float64)
    rho = 1.0
    expected = float(np.sqrt(np.linalg.eigvalsh(np.diag(diagonal * diagonal) + rho * np.outer(update, update))[0]))
    prik_delta, f2py_delta = np.empty(2), np.empty(2)
    prik_work, f2py_work = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dlasd4(
        np.int32(2), np.int32(1), diagonal, update, prik_delta, np.float64(rho), np.float64(0.0), prik_work, np.int32(0)
    )
    f2py_result = f2py_lapack.dlasd4(2, 1, diagonal, update, f2py_delta, rho, 0.0, f2py_work, 0)
    scipy_delta, scipy_sigma, scipy_work, scipy_info = scipy_lapack.dlasd4(0, diagonal, update, rho=rho)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    prik_sigma = prik_scalars[-2]
    assert_allclose_float64(prik_sigma, expected, operation_size=2)
    assert_allclose_float64(scipy_sigma, expected, operation_size=2)
    assert_allclose_float64(prik_delta, diagonal - prik_sigma)
    assert_allclose_float64(prik_work, diagonal + prik_sigma)
    assert_allclose_float64(f2py_delta, scipy_delta)
    assert_allclose_float64(f2py_work, scipy_work)
    secular = 1.0 + rho * np.sum(update * update / (diagonal * diagonal - prik_sigma * prik_sigma))
    assert_allclose_float64(secular, 0.0, operation_size=2)
