"""Symmetric positive-definite linear-equation correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_storage_unchanged, column_major


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dlauum_forms_triangular_product(prik_lapack, scipy_lapack, f2py_lapack):
    triangular = np.array([[2.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = triangular.copy(order="F"), triangular.copy(order="F")

    prik_scalars = prik_lapack.dlauum("U", np.int32(1), prik_a, np.int32(1), np.int32(0))
    f2py_result = f2py_lapack.dlauum(b"U", 1, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dlauum(triangular.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[4.0]])
    assert_allclose_float64(f2py_a, [[4.0]])
    assert_allclose_float64(scipy_a, [[4.0]])


def test_dpftrf_factorizes_rfp_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    prik_a, f2py_a = np.array([4.0]), np.array([4.0])

    prik_scalars = prik_lapack.dpftrf("N", "U", np.int32(1), prik_a, np.int32(0))
    f2py_result = f2py_lapack.dpftrf(b"N", b"U", 1, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dpftrf(1, np.array([4.0]), transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [2.0])
    assert_allclose_float64(f2py_a, [2.0])
    assert_allclose_float64(scipy_a, [2.0])


def test_dpftri_inverts_rfp_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    prik_a, f2py_a = np.array([2.0]), np.array([2.0])

    prik_scalars = prik_lapack.dpftri("N", "U", np.int32(1), prik_a, np.int32(0))
    f2py_result = f2py_lapack.dpftri(b"N", b"U", 1, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dpftri(1, np.array([2.0]), transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [0.25])
    assert_allclose_float64(f2py_a, [0.25])
    assert_allclose_float64(scipy_a, [0.25])


def test_dpftrs_solves_from_rfp_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([2.0])
    prik_b = np.array([[8.0]], dtype=np.float64, order="F")
    f2py_b = prik_b.copy(order="F")

    prik_scalars = prik_lapack.dpftrs("N", "U", np.int32(1), np.int32(1), factor, prik_b, np.int32(1), np.int32(0))
    f2py_result = f2py_lapack.dpftrs(b"N", b"U", 1, 1, factor, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dpftrs(1, factor, np.array([[8.0]], order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])


def test_dpocon_estimates_spd_reciprocal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[2.0]], dtype=np.float64, order="F")

    prik_scalars = prik_lapack.dpocon(
        "U",
        np.int32(1),
        factor.copy(order="F"),
        np.int32(1),
        np.float64(4.0),
        np.float64(0.0),
        np.empty(3),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dpocon(
        b"U", 1, factor.copy(order="F"), 4.0, 0.0, np.empty(3), np.empty(1, dtype=np.int32), 0
    )
    scipy_rcond, scipy_info = scipy_lapack.dpocon(factor.copy(order="F"), 4.0, uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], 1.0)
    assert_allclose_float64(scipy_rcond, 1.0)


def test_dposv_solves_spd_system(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dposv(
        "U", np.int32(1), np.int32(1), prik_a, np.int32(1), prik_b, np.int32(1), np.int32(0)
    )
    f2py_result = f2py_lapack.dposv(b"U", 1, 1, f2py_a, f2py_b, 0)
    scipy_factor, scipy_x, scipy_info = scipy_lapack.dposv(matrix.copy(order="F"), rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, scipy_factor)
    assert_allclose_float64(f2py_a, scipy_factor)
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])


def test_dposvx_solves_and_bounds_spd_error(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_af, f2py_af = np.empty_like(matrix), np.empty_like(matrix)
    prik_x, f2py_x = np.empty_like(rhs), np.empty_like(rhs)
    prik_ferr, f2py_ferr = np.empty(1), np.empty(1)
    prik_berr, f2py_berr = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dposvx(
        "N",
        "U",
        np.int32(1),
        np.int32(1),
        matrix.copy(order="F"),
        np.int32(1),
        prik_af,
        np.int32(1),
        "N",
        np.ones(1),
        rhs.copy(order="F"),
        np.int32(1),
        prik_x,
        np.int32(1),
        np.float64(0.0),
        prik_ferr,
        prik_berr,
        np.empty(3),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dposvx(
        b"N",
        b"U",
        1,
        1,
        matrix.copy(order="F"),
        f2py_af,
        b"N",
        np.ones(1),
        rhs.copy(order="F"),
        f2py_x,
        0.0,
        f2py_ferr,
        f2py_berr,
        np.empty(3),
        np.empty(1, dtype=np.int32),
        0,
    )
    _a, scipy_factor, _equed, _s, _b, scipy_x, scipy_rcond, scipy_ferr, scipy_berr, scipy_info = scipy_lapack.dposvx(
        matrix.copy(order="F"), rhs.copy(order="F"), fact=b"N"
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_af, scipy_factor)
    assert_allclose_float64(f2py_af, scipy_factor)
    assert_allclose_float64(prik_x, [[2.0]])
    assert_allclose_float64(f2py_x, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])
    assert_allclose_float64(prik_scalars[-2], scipy_rcond)
    assert_allclose_float64(prik_ferr, scipy_ferr)
    assert_allclose_float64(prik_berr, scipy_berr)


def test_dpotrf_reconstructs_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    logical = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    stored = np.array([[4.0, np.nan], [1.0, 3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = column_major(stored), column_major(stored)

    prik_scalars = prik_lapack.dpotrf("L", np.int32(2), prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpotrf(b"L", 2, f2py_a, 0)
    scipy_factor, scipy_info = scipy_lapack.dpotrf(stored.copy(order="F"), lower=1, clean=0)

    assert prik_scalars == (2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    prik_lower = np.tril(prik_a)
    f2py_lower = np.tril(f2py_a)
    scipy_lower = np.tril(scipy_factor)
    assert_allclose_float64(prik_lower @ prik_lower.T, logical, operation_size=2)
    assert_allclose_float64(f2py_lower @ f2py_lower.T, logical, operation_size=2)
    assert_allclose_float64(scipy_lower @ scipy_lower.T, logical, operation_size=2)
    assert_allclose_float64(prik_lower, scipy_lower, operation_size=2)
    assert_allclose_float64(f2py_lower, scipy_lower, operation_size=2)
    assert_storage_unchanged(np.triu(prik_a, 1), np.triu(stored, 1))
    assert_storage_unchanged(np.triu(f2py_a, 1), np.triu(stored, 1))


def test_dpotri_inverts_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[2.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = factor.copy(order="F"), factor.copy(order="F")

    prik_scalars = prik_lapack.dpotri("U", np.int32(1), prik_a, np.int32(1), np.int32(0))
    f2py_result = f2py_lapack.dpotri(b"U", 1, f2py_a, 0)
    scipy_inverse, scipy_info = scipy_lapack.dpotri(factor.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[0.25]])
    assert_allclose_float64(f2py_a, [[0.25]])
    assert_allclose_float64(scipy_inverse, [[0.25]])


def test_dpotrs_solves_from_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[2.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dpotrs(
        "U", np.int32(1), np.int32(1), factor.copy(order="F"), np.int32(1), prik_b, np.int32(1), np.int32(0)
    )
    f2py_result = f2py_lapack.dpotrs(b"U", 1, 1, factor.copy(order="F"), f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dpotrs(factor.copy(order="F"), rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])


def test_dppcon_estimates_packed_spd_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([2.0])

    prik_scalars = prik_lapack.dppcon(
        "U",
        np.int32(1),
        factor,
        np.float64(4.0),
        np.float64(0.0),
        np.empty(3),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dppcon(b"U", 1, factor, 4.0, 0.0, np.empty(3), np.empty(1, dtype=np.int32), 0)
    scipy_rcond, scipy_info = scipy_lapack.dppcon(1, factor, 4.0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], 1.0)
    assert_allclose_float64(scipy_rcond, 1.0)


def test_dppsv_solves_packed_spd_system(prik_lapack, scipy_lapack, f2py_lapack):
    prik_ap, f2py_ap = np.array([4.0]), np.array([4.0])
    prik_b = np.array([[8.0]], dtype=np.float64, order="F")
    f2py_b = prik_b.copy(order="F")

    prik_scalars = prik_lapack.dppsv("U", np.int32(1), np.int32(1), prik_ap, prik_b, np.int32(1), np.int32(0))
    f2py_result = f2py_lapack.dppsv(b"U", 1, 1, f2py_ap, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dppsv(1, np.array([4.0]), np.array([[8.0]], order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ap, [2.0])
    assert_allclose_float64(f2py_ap, [2.0])
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])


def test_dpptrf_factorizes_packed_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    prik_ap, f2py_ap = np.array([4.0]), np.array([4.0])

    prik_scalars = prik_lapack.dpptrf("U", np.int32(1), prik_ap, np.int32(0))
    f2py_result = f2py_lapack.dpptrf(b"U", 1, f2py_ap, 0)
    scipy_ap, scipy_info = scipy_lapack.dpptrf(1, np.array([4.0]))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ap, [2.0])
    assert_allclose_float64(f2py_ap, [2.0])
    assert_allclose_float64(scipy_ap, [2.0])


def test_dpptri_inverts_packed_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    prik_ap, f2py_ap = np.array([2.0]), np.array([2.0])

    prik_scalars = prik_lapack.dpptri("U", np.int32(1), prik_ap, np.int32(0))
    f2py_result = f2py_lapack.dpptri(b"U", 1, f2py_ap, 0)
    scipy_ap, scipy_info = scipy_lapack.dpptri(1, np.array([2.0]))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ap, [0.25])
    assert_allclose_float64(f2py_ap, [0.25])
    assert_allclose_float64(scipy_ap, [0.25])


def test_dpptrs_solves_from_packed_cholesky_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([2.0])
    prik_b = np.array([[8.0]], dtype=np.float64, order="F")
    f2py_b = prik_b.copy(order="F")

    prik_scalars = prik_lapack.dpptrs("U", np.int32(1), np.int32(1), factor, prik_b, np.int32(1), np.int32(0))
    f2py_result = f2py_lapack.dpptrs(b"U", 1, 1, factor, f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dpptrs(1, factor, np.array([[8.0]], order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[2.0]])
    assert_allclose_float64(f2py_b, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])


def test_dpstf2_reconstructs_pivoted_cholesky(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dpstf2(
        "U", np.int32(1), prik_a, np.int32(1), prik_piv, np.int32(0), np.float64(-1.0), np.empty(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dpstf2(b"U", f2py_a, f2py_piv, 0, -1.0, np.empty(2), 0)
    scipy_a, _scipy_piv, scipy_rank, scipy_info = scipy_lapack.dpstf2(matrix.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[2] == scipy_rank == 1
    assert_allclose_float64(prik_a.T @ prik_a, matrix)
    assert_allclose_float64(f2py_a.T @ f2py_a, matrix)
    assert_allclose_float64(scipy_a.T @ scipy_a, matrix)
    np.testing.assert_array_equal(prik_piv, [1])
    np.testing.assert_array_equal(f2py_piv, [1])


def test_dpstrf_reconstructs_blocked_pivoted_cholesky(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dpstrf(
        "U", np.int32(1), prik_a, np.int32(1), prik_piv, np.int32(0), np.float64(-1.0), np.empty(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dpstrf(b"U", f2py_a, f2py_piv, 0, -1.0, np.empty(2), 0)
    scipy_a, _scipy_piv, scipy_rank, scipy_info = scipy_lapack.dpstrf(matrix.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert prik_scalars[2] == scipy_rank == 1
    assert_allclose_float64(prik_a.T @ prik_a, matrix)
    assert_allclose_float64(f2py_a.T @ f2py_a, matrix)
    assert_allclose_float64(scipy_a.T @ scipy_a, matrix)
    np.testing.assert_array_equal(prik_piv, [1])
    np.testing.assert_array_equal(f2py_piv, [1])


def test_dsfrk_updates_spd_matrix_in_rfp_storage(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, 3.0]], dtype=np.float64, order="F")
    prik_c, f2py_c = np.array([1.0]), np.array([1.0])
    expected = np.array([14.0])

    prik_scalars = prik_lapack.dsfrk(
        "N", "U", "N", np.int32(1), np.int32(2), np.float64(1.0), matrix, np.int32(1), np.float64(1.0), prik_c
    )
    f2py_result = f2py_lapack.dsfrk(b"N", b"U", b"N", 1, 2, 1.0, matrix, 1.0, f2py_c)
    scipy_c = scipy_lapack.dsfrk(1, 2, 1.0, matrix, 1.0, np.array([1.0]))

    assert f2py_result is None
    assert prik_scalars == (1, 2, 1.0, 1, 1.0)
    assert_allclose_float64(prik_c, expected, operation_size=2)
    assert_allclose_float64(f2py_c, expected, operation_size=2)
    assert_allclose_float64(scipy_c, expected, operation_size=2)
