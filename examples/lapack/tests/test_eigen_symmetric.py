"""Symmetric and tridiagonal eigenvalue correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_orthogonal, symmetric_band_storage


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _symmetric_problem():
    matrix = np.array([[2.5, 0.5], [0.5, 2.5]], dtype=np.float64, order="F")
    diagonal = np.array([2.5, 2.5], dtype=np.float64)
    offdiag = np.array([0.5], dtype=np.float64)
    return matrix, diagonal, offdiag


def _assert_eigensystem(matrix, values, vectors):
    assert_allclose_float64(values, [2.0, 3.0])
    assert_orthogonal(vectors)
    assert_allclose_float64(matrix @ vectors, vectors @ np.diag(values), operation_size=2)


def test_dpteqr_diagonalizes_positive_definite_tridiagonal(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, diagonal, offdiag = _symmetric_problem()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = offdiag.copy(), offdiag.copy()
    prik_z, f2py_z = np.eye(2, dtype=np.float64, order="F"), np.eye(2, dtype=np.float64, order="F")

    prik_scalars = prik_lapack.dpteqr("I", np.int32(2), prik_d, prik_e, prik_z, np.int32(2), np.empty(8), np.int32(0))
    f2py_result = f2py_lapack.dpteqr(b"I", 2, f2py_d, f2py_e, f2py_z, np.empty(8), 0)
    scipy_d, _scipy_e, scipy_z, scipy_info = scipy_lapack.dpteqr(diagonal, offdiag, np.eye(2, order="F"), compute_z=1)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    # DPTEQR's contract returns eigenvalues (and matching vectors) in descending order.
    _assert_eigensystem(matrix, prik_d[::-1], prik_z[:, ::-1])
    _assert_eigensystem(matrix, f2py_d[::-1], f2py_z[:, ::-1])
    _assert_eigensystem(matrix, scipy_d[::-1], scipy_z[:, ::-1])


def test_dsbev_diagonalizes_symmetric_band_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    band = symmetric_band_storage(matrix, 1, lower=False)
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dsbev(
        "V", "U", np.int32(2), np.int32(1), prik_ab, np.int32(2), prik_w, prik_z, np.int32(2), np.empty(6), np.int32(0)
    )
    f2py_result = f2py_lapack.dsbev(b"V", b"U", 2, 1, f2py_ab, f2py_w, f2py_z, np.empty(6), 0)
    scipy_w, scipy_z, scipy_info = scipy_lapack.dsbev(band.copy(order="F"), compute_v=1, lower=0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)


def test_dsbevd_diagonalizes_band_matrix_by_divide_and_conquer(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    band = symmetric_band_storage(matrix, 1, lower=False)
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dsbevd(
        "V",
        "U",
        np.int32(2),
        np.int32(1),
        prik_ab,
        np.int32(2),
        prik_w,
        prik_z,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.empty(32, dtype=np.int32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsbevd(
        b"V", b"U", 2, 1, f2py_ab, f2py_w, f2py_z, np.empty(64), 64, np.empty(32, dtype=np.int32), 32, 0
    )
    scipy_w, scipy_z, scipy_info = scipy_lapack.dsbevd(band.copy(order="F"), compute_v=1, lower=0, liwork=32)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)


def test_dsbevx_selects_all_symmetric_band_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    band = symmetric_band_storage(matrix, 1, lower=False)
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_ifail, f2py_ifail = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dsbevx(
        "V",
        "A",
        "U",
        np.int32(2),
        np.int32(1),
        prik_ab,
        np.int32(2),
        np.empty((2, 2), order="F"),
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
        np.empty(14),
        np.empty(10, dtype=np.int32),
        prik_ifail,
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsbevx(
        b"V",
        b"A",
        b"U",
        2,
        1,
        f2py_ab,
        np.empty((2, 2), order="F"),
        0.0,
        0.0,
        1,
        2,
        0.0,
        0,
        f2py_w,
        f2py_z,
        np.empty(14),
        np.empty(10, dtype=np.int32),
        f2py_ifail,
        0,
    )
    scipy_w, scipy_z, scipy_m, scipy_ifail, scipy_info = scipy_lapack.dsbevx(
        band.copy(order="F"), 0.0, 0.0, 1, 2, compute_v=1, range=0, lower=0, mmax=2
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[10] == scipy_m == 2
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)
    np.testing.assert_array_equal(prik_ifail, scipy_ifail)
    np.testing.assert_array_equal(f2py_ifail, scipy_ifail)


def test_dstebz_bisects_tridiagonal_eigenvalues(prik_lapack, scipy_lapack, f2py_lapack):
    _matrix, diagonal, offdiag = _symmetric_problem()
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_iblock, f2py_iblock = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)
    prik_isplit, f2py_isplit = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dstebz(
        "A",
        "E",
        np.int32(2),
        np.float64(0.0),
        np.float64(0.0),
        np.int32(1),
        np.int32(2),
        np.float64(0.0),
        diagonal,
        offdiag,
        np.int32(0),
        np.int32(0),
        prik_w,
        prik_iblock,
        prik_isplit,
        np.empty(8),
        np.empty(6, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dstebz(
        b"A",
        b"E",
        2,
        0.0,
        0.0,
        1,
        2,
        0.0,
        diagonal,
        offdiag,
        0,
        0,
        f2py_w,
        f2py_iblock,
        f2py_isplit,
        np.empty(8),
        np.empty(6, dtype=np.int32),
        0,
    )
    scipy_m, scipy_w, scipy_iblock, scipy_isplit, scipy_info = scipy_lapack.dstebz(
        diagonal, offdiag, 0, 0.0, 0.0, 1, 2, 0.0, b"E"
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    prik_m = int(prik_scalars[6])
    prik_nsplit = int(prik_scalars[7])
    assert prik_m == scipy_m == 2
    assert prik_nsplit == 1
    assert_allclose_float64(prik_w[:2], [2.0, 3.0])
    assert_allclose_float64(f2py_w[:2], [2.0, 3.0])
    assert_allclose_float64(scipy_w[:2], [2.0, 3.0])
    np.testing.assert_array_equal(prik_iblock, scipy_iblock)
    np.testing.assert_array_equal(f2py_iblock, scipy_iblock)
    np.testing.assert_array_equal(prik_isplit[:prik_nsplit], scipy_isplit[:prik_nsplit])
    np.testing.assert_array_equal(f2py_isplit[:prik_nsplit], scipy_isplit[:prik_nsplit])


def test_dstein_computes_tridiagonal_eigenvectors(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, diagonal, offdiag = _symmetric_problem()
    m, values, iblock, isplit, split_info = scipy_lapack.dstebz(diagonal, offdiag, 0, 0.0, 0.0, 1, 2, 0.0, b"E")
    assert split_info == 0 and m == 2
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_ifail, f2py_ifail = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dstein(
        np.int32(2),
        diagonal,
        offdiag,
        np.int32(2),
        values,
        iblock,
        isplit,
        prik_z,
        np.int32(2),
        np.empty(10),
        np.empty(2, dtype=np.int32),
        prik_ifail,
        np.int32(0),
    )
    f2py_result = f2py_lapack.dstein(
        2,
        diagonal,
        offdiag,
        2,
        values,
        iblock,
        isplit,
        f2py_z,
        np.empty(10),
        np.empty(2, dtype=np.int32),
        f2py_ifail,
        0,
    )
    scipy_z, scipy_info = scipy_lapack.dstein(diagonal, offdiag, values, iblock, isplit)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, values, prik_z)
    _assert_eigensystem(matrix, values, f2py_z)
    _assert_eigensystem(matrix, values, scipy_z)
    np.testing.assert_array_equal(prik_ifail, [0, 0])
    np.testing.assert_array_equal(f2py_ifail, [0, 0])


def test_dstemr_computes_robust_tridiagonal_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, diagonal, offdiag = _symmetric_problem()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = np.array([offdiag[0], 0.0]), np.array([offdiag[0], 0.0])
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_support, f2py_support = np.empty(4, dtype=np.int32), np.empty(4, dtype=np.int32)

    prik_scalars = prik_lapack.dstemr(
        "V",
        "A",
        np.int32(2),
        prik_d,
        prik_e,
        np.float64(0.0),
        np.float64(0.0),
        np.int32(1),
        np.int32(2),
        np.int32(0),
        prik_w,
        prik_z,
        np.int32(2),
        np.int32(2),
        prik_support,
        np.bool_(True),
        np.empty(128),
        np.int32(128),
        np.empty(64, dtype=np.int32),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dstemr(
        b"V",
        b"A",
        2,
        f2py_d,
        f2py_e,
        0.0,
        0.0,
        1,
        2,
        0,
        f2py_w,
        f2py_z,
        2,
        f2py_support,
        1,
        np.empty(128),
        128,
        np.empty(64, dtype=np.int32),
        64,
        0,
    )
    scipy_m, scipy_w, scipy_z, scipy_info = scipy_lapack.dstemr(
        diagonal,
        np.array([offdiag[0], 0.0]),
        0,
        0.0,
        0.0,
        1,
        2,
        compute_v=1,
        lwork=128,
        liwork=64,
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[5] == scipy_m == 2
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)


def test_dsterf_computes_tridiagonal_eigenvalues(prik_lapack, scipy_lapack, f2py_lapack):
    _matrix, diagonal, offdiag = _symmetric_problem()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = offdiag.copy(), offdiag.copy()

    prik_scalars = prik_lapack.dsterf(np.int32(2), prik_d, prik_e, np.int32(0))
    f2py_result = f2py_lapack.dsterf(2, f2py_d, f2py_e, 0)
    scipy_values, scipy_info = scipy_lapack.dsterf(diagonal, offdiag)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_d, [2.0, 3.0])
    assert_allclose_float64(f2py_d, [2.0, 3.0])
    assert_allclose_float64(scipy_values, [2.0, 3.0])


def test_dstev_computes_tridiagonal_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, diagonal, offdiag = _symmetric_problem()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = offdiag.copy(), offdiag.copy()
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dstev("V", np.int32(2), prik_d, prik_e, prik_z, np.int32(2), np.empty(4), np.int32(0))
    f2py_result = f2py_lapack.dstev(b"V", 2, f2py_d, f2py_e, f2py_z, np.empty(4), 0)
    scipy_values, scipy_z, scipy_info = scipy_lapack.dstev(diagonal, offdiag, compute_v=1)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, prik_d, prik_z)
    _assert_eigensystem(matrix, f2py_d, f2py_z)
    _assert_eigensystem(matrix, scipy_values, scipy_z)


def test_dstevd_computes_divide_and_conquer_tridiagonal_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, diagonal, offdiag = _symmetric_problem()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = offdiag.copy(), offdiag.copy()
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")

    prik_scalars = prik_lapack.dstevd(
        "V",
        np.int32(2),
        prik_d,
        prik_e,
        prik_z,
        np.int32(2),
        np.empty(64),
        np.int32(64),
        np.empty(32, dtype=np.int32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dstevd(
        b"V", 2, f2py_d, f2py_e, f2py_z, np.empty(64), 64, np.empty(32, dtype=np.int32), 32, 0
    )
    scipy_values, scipy_z, scipy_info = scipy_lapack.dstevd(diagonal, offdiag, compute_v=1, lwork=64, liwork=32)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, prik_d, prik_z)
    _assert_eigensystem(matrix, f2py_d, f2py_z)
    _assert_eigensystem(matrix, scipy_values, scipy_z)


def test_dsyev_returns_orthonormal_eigenvectors(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    expected_w = np.array([1.0, 3.0], dtype=np.float64)
    prik_vectors, f2py_vectors = matrix.copy(order="F"), matrix.copy(order="F")
    prik_w = np.empty(2, dtype=np.float64)
    f2py_w = np.empty(2, dtype=np.float64)

    prik_scalars = prik_lapack.dsyev(
        "V", "U", np.int32(2), prik_vectors, np.int32(2), prik_w, np.empty(16), np.int32(16), np.int32(0)
    )
    f2py_result = f2py_lapack.dsyev(b"V", b"U", 2, f2py_vectors, f2py_w, np.empty(16), 16, 0)
    scipy_w, scipy_vectors, scipy_info = scipy_lapack.dsyev(matrix.copy(order="F"), compute_v=1, lower=0, lwork=16)

    assert prik_scalars == (2, 2, 16, 0)
    assert f2py_result is None
    assert scipy_info == 0
    for values, vectors in (
        (prik_w, prik_vectors),
        (f2py_w, f2py_vectors),
        (scipy_w, scipy_vectors),
    ):
        assert_allclose_float64(values, expected_w, operation_size=2)
        assert_orthogonal(vectors)
        assert_allclose_float64(matrix @ vectors, vectors @ np.diag(values), operation_size=2)


def test_dsyevd_computes_divide_and_conquer_symmetric_eigenpairs(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dsyevd(
        "V",
        "U",
        np.int32(2),
        prik_a,
        np.int32(2),
        prik_w,
        np.empty(64),
        np.int32(64),
        np.empty(32, dtype=np.int32),
        np.int32(32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsyevd(
        b"V", b"U", 2, f2py_a, f2py_w, np.empty(64), 64, np.empty(32, dtype=np.int32), 32, 0
    )
    scipy_w, scipy_a, scipy_info = scipy_lapack.dsyevd(
        matrix.copy(order="F"), compute_v=1, lower=0, lwork=64, liwork=32
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    _assert_eigensystem(matrix, prik_w, prik_a)
    _assert_eigensystem(matrix, f2py_w, f2py_a)
    _assert_eigensystem(matrix, scipy_w, scipy_a)


def test_dsyevr_selects_symmetric_eigenpairs_by_index(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_support, f2py_support = np.empty(4, dtype=np.int32), np.empty(4, dtype=np.int32)

    prik_scalars = prik_lapack.dsyevr(
        "V",
        "I",
        "U",
        np.int32(2),
        prik_a,
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
        prik_support,
        np.empty(128),
        np.int32(128),
        np.empty(64, dtype=np.int32),
        np.int32(64),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dsyevr(
        b"V",
        b"I",
        b"U",
        2,
        f2py_a,
        0.0,
        0.0,
        1,
        2,
        0.0,
        0,
        f2py_w,
        f2py_z,
        f2py_support,
        np.empty(128),
        128,
        np.empty(64, dtype=np.int32),
        64,
        0,
    )
    scipy_w, scipy_z, scipy_m, _support, scipy_info = scipy_lapack.dsyevr(
        matrix.copy(order="F"), compute_v=1, range=b"I", lower=0, il=1, iu=2, lwork=128, liwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[8] == scipy_m == 2
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)


def test_dsyevx_selects_symmetric_eigenpairs_by_value(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _diagonal, _offdiag = _symmetric_problem()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_w, f2py_w = np.empty(2), np.empty(2)
    prik_z, f2py_z = np.empty((2, 2), order="F"), np.empty((2, 2), order="F")
    prik_ifail, f2py_ifail = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dsyevx(
        "V",
        "V",
        "U",
        np.int32(2),
        prik_a,
        np.int32(2),
        np.float64(1.5),
        np.float64(3.5),
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
    f2py_result = f2py_lapack.dsyevx(
        b"V",
        b"V",
        b"U",
        2,
        f2py_a,
        1.5,
        3.5,
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
    scipy_w, scipy_z, scipy_m, scipy_ifail, scipy_info = scipy_lapack.dsyevx(
        matrix.copy(order="F"), compute_v=1, range=b"V", lower=0, vl=1.5, vu=3.5, lwork=64
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[8] == scipy_m == 2
    _assert_eigensystem(matrix, prik_w, prik_z)
    _assert_eigensystem(matrix, f2py_w, f2py_z)
    _assert_eigensystem(matrix, scipy_w, scipy_z)
    np.testing.assert_array_equal(prik_ifail, scipy_ifail)
    np.testing.assert_array_equal(f2py_ifail, scipy_ifail)


def test_dsytrd_reduces_symmetric_matrix_to_tridiagonal(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array(
        [[4.0, 1.0, 2.0], [1.0, 3.0, -1.0], [2.0, -1.0, 5.0]],
        dtype=np.float64,
        order="F",
    )
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_d, f2py_d = np.empty(3), np.empty(3)
    prik_e, f2py_e = np.empty(2), np.empty(2)
    prik_tau, f2py_tau = np.empty(2), np.empty(2)

    prik_scalars = prik_lapack.dsytrd(
        "U", np.int32(3), prik_a, np.int32(3), prik_d, prik_e, prik_tau, np.empty(64), np.int32(64), np.int32(0)
    )
    f2py_result = f2py_lapack.dsytrd(b"U", 3, f2py_a, f2py_d, f2py_e, f2py_tau, np.empty(64), 64, 0)
    scipy_a, scipy_d, scipy_e, scipy_tau, scipy_info = scipy_lapack.dsytrd(matrix.copy(order="F"), lower=0, lwork=64)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    expected_eigenvalues = np.linalg.eigvalsh(matrix)
    for diagonal, offdiagonal in ((prik_d, prik_e), (f2py_d, f2py_e), (scipy_d, scipy_e)):
        tridiagonal = np.diag(diagonal) + np.diag(offdiagonal, 1) + np.diag(offdiagonal, -1)
        assert_allclose_float64(np.linalg.eigvalsh(tridiagonal), expected_eigenvalues, operation_size=3)
        assert np.any(np.abs(offdiagonal) > np.finfo(np.float64).eps)
    assert_allclose_float64(prik_a, scipy_a)
    assert_allclose_float64(f2py_a, scipy_a)
    assert_allclose_float64(prik_tau, scipy_tau)
    assert_allclose_float64(f2py_tau, scipy_tau)
