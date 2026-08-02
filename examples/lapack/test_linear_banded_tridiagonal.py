"""General-banded, positive-banded, and tridiagonal correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import (
    assert_allclose_float64,
    general_band_storage,
    native_pivots,
    symmetric_band_storage,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _general_tridiagonal():
    lower = np.array([1.0], dtype=np.float64)
    diagonal = np.array([4.0, 3.0], dtype=np.float64)
    upper = np.array([1.0], dtype=np.float64)
    rhs = np.array([[6.0], [7.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    return lower, diagonal, upper, rhs, expected


def _general_tridiagonal_factorization():
    lower = np.array([1.0, 1.0], dtype=np.float64)
    diagonal = np.array([4.0, 3.0, 2.0], dtype=np.float64)
    upper = np.array([1.0, 1.0], dtype=np.float64)
    rhs = np.array([[6.0], [10.0], [8.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0], [3.0]], dtype=np.float64)
    return lower, diagonal, upper, rhs, expected


def test_dgbcon_estimates_general_band_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[4.0]], dtype=np.float64, order="F")
    native_ipiv = np.array([1], dtype=np.int32)

    prik_scalars = prik_lapack.dgbcon(
        "1",
        np.int32(1),
        np.int32(0),
        np.int32(0),
        factor.copy(order="F"),
        np.int32(1),
        native_ipiv,
        np.float64(4.0),
        np.float64(0.0),
        np.empty(3),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgbcon(
        b"1", 1, 0, 0, factor.copy(order="F"), native_ipiv, 4.0, 0.0, np.empty(3), np.empty(1, dtype=np.int32), 0
    )
    scipy_rcond, scipy_info = scipy_lapack.dgbcon(0, 0, factor.copy(order="F"), np.array([0], dtype=np.int32), 4.0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], 1.0)
    assert_allclose_float64(scipy_rcond, 1.0)


def test_dgbsv_solves_general_band_system(prik_lapack, scipy_lapack, f2py_lapack):
    prik_ab, f2py_ab = np.array([[4.0]], order="F"), np.array([[4.0]], order="F")
    prik_b, f2py_b = np.array([[8.0]], order="F"), np.array([[8.0]], order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dgbsv(
        np.int32(1),
        np.int32(0),
        np.int32(0),
        np.int32(1),
        prik_ab,
        np.int32(1),
        prik_piv,
        prik_b,
        np.int32(1),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgbsv(1, 0, 0, 1, f2py_ab, f2py_piv, f2py_b, 0)
    scipy_lu, scipy_piv, scipy_x, scipy_info = scipy_lapack.dgbsv(
        0, 0, np.array([[4.0]], order="F"), np.array([[8.0]], order="F")
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])
    assert_allclose_float64(prik_ab, scipy_lu)
    assert_allclose_float64(f2py_ab, scipy_lu)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))


def test_dgbtrf_factorizes_general_band_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    band = general_band_storage(matrix, 1, 1, factor=True)
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")
    prik_piv, f2py_piv = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgbtrf(
        np.int32(2), np.int32(2), np.int32(1), np.int32(1), prik_ab, np.int32(4), prik_piv, np.int32(0)
    )
    f2py_result = f2py_lapack.dgbtrf(2, 2, 1, 1, f2py_ab, f2py_piv, 0)
    scipy_lu, scipy_piv, scipy_info = scipy_lapack.dgbtrf(band.copy(order="F"), 1, 1)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ab, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_ab, scipy_lu, operation_size=2)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))
    np.testing.assert_array_equal(f2py_piv, native_pivots(scipy_piv))


def test_dgbtrs_solves_from_general_band_lu(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    band = general_band_storage(matrix, 1, 1, factor=True)
    scipy_lu, scipy_piv, factor_info = scipy_lapack.dgbtrf(band.copy(order="F"), 1, 1)
    assert factor_info == 0
    native_ipiv = native_pivots(scipy_piv)
    rhs = np.array([[6.0], [7.0]], dtype=np.float64, order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dgbtrs(
        "N",
        np.int32(2),
        np.int32(1),
        np.int32(1),
        np.int32(1),
        scipy_lu.copy(order="F"),
        np.int32(4),
        native_ipiv,
        prik_b,
        np.int32(2),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgbtrs(b"N", 2, 1, 1, 1, scipy_lu.copy(order="F"), native_ipiv, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dgbtrs(scipy_lu, 1, 1, rhs.copy(order="F"), scipy_piv)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(f2py_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(scipy_x, [[1.0], [2.0]], operation_size=2)


def test_dgtcon_estimates_tridiagonal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, _rhs, _expected = _general_tridiagonal_factorization()
    scipy_dl, scipy_d, scipy_du, scipy_du2, scipy_piv, factor_info = scipy_lapack.dgttrf(lower, diagonal, upper)
    assert factor_info == 0
    native_ipiv = native_pivots(scipy_piv)
    anorm = 5.0

    prik_scalars = prik_lapack.dgtcon(
        "1",
        np.int32(3),
        scipy_dl,
        scipy_d,
        scipy_du,
        scipy_du2,
        native_ipiv,
        np.float64(anorm),
        np.float64(0.0),
        np.empty(6),
        np.empty(3, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgtcon(
        b"1",
        3,
        scipy_dl,
        scipy_d,
        scipy_du,
        scipy_du2,
        native_ipiv,
        anorm,
        0.0,
        np.empty(6),
        np.empty(3, dtype=np.int32),
        0,
    )
    scipy_rcond, scipy_info = scipy_lapack.dgtcon(scipy_dl, scipy_d, scipy_du, scipy_du2, scipy_piv, anorm)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], scipy_rcond, operation_size=3)
    assert 0.0 < scipy_rcond <= 1.0


def test_dgtsv_solves_general_tridiagonal_system(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, rhs, expected = _general_tridiagonal()
    prik_dl, prik_d, prik_du = lower.copy(), diagonal.copy(), upper.copy()
    f2py_dl, f2py_d, f2py_du = lower.copy(), diagonal.copy(), upper.copy()
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dgtsv(
        np.int32(2), np.int32(1), prik_dl, prik_d, prik_du, prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dgtsv(2, 1, f2py_dl, f2py_d, f2py_du, f2py_b, 0)
    _du2, _d, _du, scipy_x, scipy_info = scipy_lapack.dgtsv(lower, diagonal, upper, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)


def test_dgtsvx_solves_and_bounds_tridiagonal_error(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, rhs, expected = _general_tridiagonal()
    prik_dlf, f2py_dlf = np.empty(1), np.empty(1)
    prik_df, f2py_df = np.empty(2), np.empty(2)
    prik_duf, f2py_duf = np.empty(1), np.empty(1)
    prik_du2, f2py_du2 = np.empty(0), np.empty(0)
    prik_piv, f2py_piv = np.empty(2, dtype=np.int32), np.empty(2, dtype=np.int32)
    prik_x, f2py_x = np.empty_like(rhs), np.empty_like(rhs)
    prik_ferr, f2py_ferr = np.empty(1), np.empty(1)
    prik_berr, f2py_berr = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgtsvx(
        "N",
        "N",
        np.int32(2),
        np.int32(1),
        lower,
        diagonal,
        upper,
        prik_dlf,
        prik_df,
        prik_duf,
        prik_du2,
        prik_piv,
        rhs.copy(order="F"),
        np.int32(2),
        prik_x,
        np.int32(2),
        np.float64(0.0),
        prik_ferr,
        prik_berr,
        np.empty(6),
        np.empty(2, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgtsvx(
        b"N",
        b"N",
        2,
        1,
        lower,
        diagonal,
        upper,
        f2py_dlf,
        f2py_df,
        f2py_duf,
        f2py_du2,
        f2py_piv,
        rhs.copy(order="F"),
        f2py_x,
        0.0,
        f2py_ferr,
        f2py_berr,
        np.empty(6),
        np.empty(2, dtype=np.int32),
        0,
    )
    _dlf, _df, _duf, _du2, _piv, scipy_x, scipy_rcond, scipy_ferr, scipy_berr, scipy_info = scipy_lapack.dgtsvx(
        lower, diagonal, upper, rhs.copy(order="F")
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_x, expected, operation_size=2)
    assert_allclose_float64(f2py_x, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(prik_scalars[-2], scipy_rcond, operation_size=2)
    assert_allclose_float64(prik_ferr, scipy_ferr)
    assert_allclose_float64(prik_berr, scipy_berr)


def test_dgttrf_factorizes_general_tridiagonal_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, _rhs, _expected = _general_tridiagonal_factorization()
    prik_dl, prik_d, prik_du = lower.copy(), diagonal.copy(), upper.copy()
    f2py_dl, f2py_d, f2py_du = lower.copy(), diagonal.copy(), upper.copy()
    prik_du2, f2py_du2 = np.empty(1), np.empty(1)
    prik_piv, f2py_piv = np.empty(3, dtype=np.int32), np.empty(3, dtype=np.int32)

    prik_scalars = prik_lapack.dgttrf(np.int32(3), prik_dl, prik_d, prik_du, prik_du2, prik_piv, np.int32(0))
    f2py_result = f2py_lapack.dgttrf(3, f2py_dl, f2py_d, f2py_du, f2py_du2, f2py_piv, 0)
    scipy_dl, scipy_d, scipy_du, _scipy_du2, scipy_piv, scipy_info = scipy_lapack.dgttrf(lower, diagonal, upper)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_dl, scipy_dl)
    assert_allclose_float64(prik_d, scipy_d)
    assert_allclose_float64(prik_du, scipy_du)
    assert_allclose_float64(f2py_dl, scipy_dl)
    assert_allclose_float64(f2py_d, scipy_d)
    assert_allclose_float64(f2py_du, scipy_du)
    # SciPy preserves LAPACK's one-based IPIV convention for DGTTRF.
    np.testing.assert_array_equal(prik_piv, scipy_piv)
    np.testing.assert_array_equal(f2py_piv, scipy_piv)


def test_dgttrs_solves_from_tridiagonal_lu(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, rhs, expected = _general_tridiagonal_factorization()
    dl, d, du, du2, scipy_piv, factor_info = scipy_lapack.dgttrf(lower, diagonal, upper)
    assert factor_info == 0
    # DGTTRF/DGTTRS preserve native one-based pivots across all three wrappers.
    native_ipiv = scipy_piv.copy()
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dgttrs(
        "N", np.int32(3), np.int32(1), dl, d, du, du2, native_ipiv, prik_b, np.int32(3), np.int32(0)
    )
    f2py_result = f2py_lapack.dgttrs(b"N", 3, 1, dl, d, du, du2, native_ipiv, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dgttrs(dl, d, du, du2, scipy_piv, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=3)
    assert_allclose_float64(f2py_b, expected, operation_size=3)
    assert_allclose_float64(scipy_x, expected, operation_size=3)


def test_dpbsv_solves_positive_definite_band_system(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    band = symmetric_band_storage(matrix, 1, lower=False)
    rhs = np.array([[6.0], [7.0]], dtype=np.float64, order="F")
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dpbsv(
        "U", np.int32(2), np.int32(1), np.int32(1), prik_ab, np.int32(2), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dpbsv(b"U", 2, 1, 1, f2py_ab, f2py_b, 0)
    scipy_factor, scipy_x, scipy_info = scipy_lapack.dpbsv(band.copy(order="F"), rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ab, scipy_factor, operation_size=2)
    assert_allclose_float64(f2py_ab, scipy_factor, operation_size=2)
    assert_allclose_float64(prik_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(f2py_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(scipy_x, [[1.0], [2.0]], operation_size=2)


def test_dpbtrf_factorizes_positive_definite_band_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    band = symmetric_band_storage(matrix, 1, lower=False)
    prik_ab, f2py_ab = band.copy(order="F"), band.copy(order="F")

    prik_scalars = prik_lapack.dpbtrf("U", np.int32(2), np.int32(1), prik_ab, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpbtrf(b"U", 2, 1, f2py_ab, 0)
    scipy_factor, scipy_info = scipy_lapack.dpbtrf(band.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ab, scipy_factor, operation_size=2)
    assert_allclose_float64(f2py_ab, scipy_factor, operation_size=2)


def test_dpbtrs_solves_from_positive_definite_band_factor(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    band = symmetric_band_storage(matrix, 1, lower=False)
    factor, factor_info = scipy_lapack.dpbtrf(band.copy(order="F"))
    assert factor_info == 0
    rhs = np.array([[6.0], [7.0]], dtype=np.float64, order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dpbtrs(
        "U", np.int32(2), np.int32(1), np.int32(1), factor, np.int32(2), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dpbtrs(b"U", 2, 1, 1, factor, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dpbtrs(factor, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(f2py_b, [[1.0], [2.0]], operation_size=2)
    assert_allclose_float64(scipy_x, [[1.0], [2.0]], operation_size=2)


def test_dptsv_solves_spd_tridiagonal_system(prik_lapack, scipy_lapack, f2py_lapack):
    lower, diagonal, upper, rhs, expected = _general_tridiagonal()
    assert_allclose_float64(lower, upper)
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = upper.copy(), upper.copy()
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dptsv(np.int32(2), np.int32(1), prik_d, prik_e, prik_b, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dptsv(2, 1, f2py_d, f2py_e, f2py_b, 0)
    _d, _e, scipy_x, scipy_info = scipy_lapack.dptsv(diagonal, upper, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)


def test_dptsvx_solves_and_bounds_spd_tridiagonal_error(prik_lapack, scipy_lapack, f2py_lapack):
    _lower, diagonal, offdiag, rhs, expected = _general_tridiagonal()
    prik_df, f2py_df = np.empty(2), np.empty(2)
    prik_ef, f2py_ef = np.empty(1), np.empty(1)
    prik_x, f2py_x = np.empty_like(rhs), np.empty_like(rhs)
    prik_ferr, f2py_ferr = np.empty(1), np.empty(1)
    prik_berr, f2py_berr = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dptsvx(
        "N",
        np.int32(2),
        np.int32(1),
        diagonal,
        offdiag,
        prik_df,
        prik_ef,
        rhs.copy(order="F"),
        np.int32(2),
        prik_x,
        np.int32(2),
        np.float64(0.0),
        prik_ferr,
        prik_berr,
        np.empty(4),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dptsvx(
        b"N",
        2,
        1,
        diagonal,
        offdiag,
        f2py_df,
        f2py_ef,
        rhs.copy(order="F"),
        f2py_x,
        0.0,
        f2py_ferr,
        f2py_berr,
        np.empty(4),
        0,
    )
    _df, _ef, scipy_x, scipy_rcond, scipy_ferr, scipy_berr, scipy_info = scipy_lapack.dptsvx(
        diagonal, offdiag, rhs.copy(order="F")
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_x, expected, operation_size=2)
    assert_allclose_float64(f2py_x, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(prik_scalars[-2], scipy_rcond, operation_size=2)
    assert_allclose_float64(prik_ferr, scipy_ferr)
    assert_allclose_float64(prik_berr, scipy_berr)


def test_dpttrf_factorizes_spd_tridiagonal_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    _lower, diagonal, offdiag, _rhs, _expected = _general_tridiagonal()
    prik_d, f2py_d = diagonal.copy(), diagonal.copy()
    prik_e, f2py_e = offdiag.copy(), offdiag.copy()

    prik_scalars = prik_lapack.dpttrf(np.int32(2), prik_d, prik_e, np.int32(0))
    f2py_result = f2py_lapack.dpttrf(2, f2py_d, f2py_e, 0)
    scipy_d, scipy_e, scipy_info = scipy_lapack.dpttrf(diagonal, offdiag)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_d, scipy_d)
    assert_allclose_float64(prik_e, scipy_e)
    assert_allclose_float64(f2py_d, scipy_d)
    assert_allclose_float64(f2py_e, scipy_e)


def test_dpttrs_solves_from_spd_tridiagonal_factor(prik_lapack, scipy_lapack, f2py_lapack):
    _lower, diagonal, offdiag, rhs, expected = _general_tridiagonal()
    factor_d, factor_e, factor_info = scipy_lapack.dpttrf(diagonal, offdiag)
    assert factor_info == 0
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dpttrs(np.int32(2), np.int32(1), factor_d, factor_e, prik_b, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpttrs(2, 1, factor_d, factor_e, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dpttrs(factor_d, factor_e, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)


def test_dtbtrs_solves_triangular_band_system(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, 1.0], [0.0, 3.0]], dtype=np.float64)
    band = symmetric_band_storage(matrix, 1, lower=False)
    rhs = np.array([[4.0], [6.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dtbtrs(
        "U", "N", "N", np.int32(2), np.int32(1), np.int32(1), band, np.int32(2), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dtbtrs(b"U", b"N", b"N", 2, 1, 1, band, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dtbtrs(band, rhs.copy(order="F"), uplo=b"U", trans=b"N", diag=b"N")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(matrix @ prik_b, rhs, operation_size=2)
