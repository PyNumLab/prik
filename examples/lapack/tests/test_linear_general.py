"""General dense linear-equation correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import (
    active,
    assert_allclose_float64,
    assert_small_residual,
    assert_storage_unchanged,
    column_major,
    native_pivots,
    pivot_matrix,
    unpack_lu,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dgecon_estimates_reciprocal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[4.0]], dtype=np.float64, order="F")
    expected = 1.0
    f2py_rcond = np.array(0.0, dtype=np.float64)
    f2py_info = np.array(0, dtype=np.int32)

    prik_scalars = prik_lapack.dgecon(
        "1",
        np.int32(1),
        factor.copy(order="F"),
        np.int32(1),
        np.float64(4.0),
        np.float64(0.0),
        np.empty(4),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgecon(
        b"1", 1, factor.copy(order="F"), 4.0, f2py_rcond, np.empty(4), np.empty(1, dtype=np.int32), f2py_info
    )
    scipy_rcond, scipy_info = scipy_lapack.dgecon(factor.copy(order="F"), 4.0, norm=b"1")

    assert f2py_result is None
    assert prik_scalars[-1] == f2py_info == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], expected)
    assert_allclose_float64(f2py_rcond, expected)
    assert_allclose_float64(scipy_rcond, expected)


def test_dgeequ_computes_row_and_column_scaling(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_r, prik_c = np.empty(1), np.empty(1)
    f2py_r, f2py_c = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgeequ(
        np.int32(1),
        np.int32(1),
        matrix.copy(order="F"),
        np.int32(1),
        prik_r,
        prik_c,
        np.float64(0.0),
        np.float64(0.0),
        np.float64(0.0),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgeequ(1, 1, matrix.copy(order="F"), f2py_r, f2py_c, 0.0, 0.0, 0.0, 0)
    scipy_r, scipy_c, scipy_rowcnd, scipy_colcnd, scipy_amax, scipy_info = scipy_lapack.dgeequ(matrix)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_r, [0.25])
    assert_allclose_float64(f2py_r, [0.25])
    assert_allclose_float64(prik_c, [1.0])
    assert_allclose_float64(f2py_c, [1.0])
    assert_allclose_float64(prik_scalars[3:6], [scipy_rowcnd, scipy_colcnd, scipy_amax])
    assert_allclose_float64(scipy_r, [0.25])
    assert_allclose_float64(scipy_c, [1.0])


def test_dgeequb_computes_radix_scaling(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_r, prik_c = np.empty(1), np.empty(1)
    f2py_r, f2py_c = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgeequb(
        np.int32(1),
        np.int32(1),
        matrix.copy(order="F"),
        np.int32(1),
        prik_r,
        prik_c,
        np.float64(0.0),
        np.float64(0.0),
        np.float64(0.0),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgeequb(1, 1, matrix.copy(order="F"), f2py_r, f2py_c, 0.0, 0.0, 0.0, 0)
    scipy_r, scipy_c, scipy_rowcnd, scipy_colcnd, scipy_amax, scipy_info = scipy_lapack.dgeequb(matrix)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_r, scipy_r)
    assert_allclose_float64(f2py_r, scipy_r)
    assert_allclose_float64(prik_c, scipy_c)
    assert_allclose_float64(f2py_c, scipy_c)
    assert_allclose_float64(prik_scalars[3:6], [scipy_rowcnd, scipy_colcnd, scipy_amax])
    assert_allclose_float64(prik_r * matrix * prik_c, [[1.0]])


def test_dgesc2_solves_complete_pivot_lu_system(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[4.0]], dtype=np.float64, order="F")
    native_ipiv = np.array([1], dtype=np.int32)
    prik_rhs, f2py_rhs = np.array([8.0]), np.array([8.0])

    prik_scalars = prik_lapack.dgesc2(
        np.int32(1), factor.copy(order="F"), np.int32(1), prik_rhs, native_ipiv, native_ipiv, np.float64(0.0)
    )
    f2py_result = f2py_lapack.dgesc2(1, factor.copy(order="F"), f2py_rhs, native_ipiv, native_ipiv, 0.0)
    scipy_x, scipy_scale = scipy_lapack.dgesc2(
        factor.copy(order="F"), np.array([8.0]), np.array([0], dtype=np.int32), np.array([0], dtype=np.int32)
    )

    assert f2py_result is None
    assert_allclose_float64(prik_rhs, [2.0])
    assert_allclose_float64(f2py_rhs, [2.0])
    assert_allclose_float64(scipy_x, [2.0])
    assert_allclose_float64(prik_scalars[-1], scipy_scale)


def test_dgesvx_solves_and_reports_error_bounds(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_af, f2py_af = np.empty_like(matrix), np.empty_like(matrix)
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)
    prik_x, f2py_x = np.empty_like(rhs), np.empty_like(rhs)
    prik_ferr, f2py_ferr = np.empty(1), np.empty(1)
    prik_berr, f2py_berr = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dgesvx(
        "N",
        "N",
        np.int32(1),
        np.int32(1),
        matrix.copy(order="F"),
        np.int32(1),
        prik_af,
        np.int32(1),
        prik_piv,
        "N",
        np.ones(1),
        np.ones(1),
        rhs.copy(order="F"),
        np.int32(1),
        prik_x,
        np.int32(1),
        np.float64(0.0),
        prik_ferr,
        prik_berr,
        np.empty(4),
        np.empty(1, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dgesvx(
        b"N",
        b"N",
        1,
        1,
        matrix.copy(order="F"),
        f2py_af,
        f2py_piv,
        b"N",
        np.ones(1),
        np.ones(1),
        rhs.copy(order="F"),
        f2py_x,
        0.0,
        f2py_ferr,
        f2py_berr,
        np.empty(4),
        np.empty(1, dtype=np.int32),
        0,
    )
    _a, scipy_lu, scipy_piv, _equed, _r, _c, _b, scipy_x, scipy_rcond, scipy_ferr, scipy_berr, scipy_info = (
        scipy_lapack.dgesvx(matrix.copy(order="F"), rhs.copy(order="F"), fact=b"N", trans=b"N")
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_x, [[2.0]])
    assert_allclose_float64(f2py_x, [[2.0]])
    assert_allclose_float64(scipy_x, [[2.0]])
    assert_allclose_float64(prik_af, scipy_lu)
    assert_allclose_float64(f2py_af, scipy_lu)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))
    np.testing.assert_array_equal(f2py_piv, native_pivots(scipy_piv))
    assert_allclose_float64(prik_scalars[-2], scipy_rcond)
    assert_allclose_float64(prik_ferr, scipy_ferr)
    assert_allclose_float64(prik_berr, scipy_berr)


def test_dgetc2_factorizes_with_complete_pivoting(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_ipiv, prik_jpiv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)
    f2py_ipiv, f2py_jpiv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dgetc2(np.int32(1), prik_a, np.int32(1), prik_ipiv, prik_jpiv, np.int32(0))
    f2py_result = f2py_lapack.dgetc2(1, f2py_a, f2py_ipiv, f2py_jpiv, 0)
    scipy_lu, scipy_ipiv, scipy_jpiv, scipy_info = scipy_lapack.dgetc2(matrix.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[4.0]])
    assert_allclose_float64(f2py_a, [[4.0]])
    assert_allclose_float64(scipy_lu, [[4.0]])
    np.testing.assert_array_equal(prik_ipiv, native_pivots(scipy_ipiv))
    np.testing.assert_array_equal(prik_jpiv, native_pivots(scipy_jpiv))


def test_dgetri_inverts_lu_factorization(prik_lapack, scipy_lapack, f2py_lapack):
    factor = np.array([[4.0]], dtype=np.float64, order="F")
    native_ipiv = np.array([1], dtype=np.int32)
    prik_a, f2py_a = factor.copy(order="F"), factor.copy(order="F")

    prik_scalars = prik_lapack.dgetri(
        np.int32(1), prik_a, np.int32(1), native_ipiv, np.empty(8), np.int32(8), np.int32(0)
    )
    f2py_result = f2py_lapack.dgetri(1, f2py_a, native_ipiv, np.empty(8), 8, 0)
    scipy_inverse, scipy_info = scipy_lapack.dgetri(factor.copy(order="F"), np.array([0], dtype=np.int32), lwork=8)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[0.25]])
    assert_allclose_float64(f2py_a, [[0.25]])
    assert_allclose_float64(scipy_inverse, [[0.25]])
    assert_allclose_float64(np.array([[4.0]]) @ prik_a, np.eye(1))


def test_dgesv_solves_general_system(prik_lapack, scipy_lapack, f2py_lapack):
    original_a = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    original_b = np.array([[5.0], [5.0]], dtype=np.float64)
    expected_x = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(original_a), column_major(original_a)
    prik_b, f2py_b = column_major(original_b), column_major(original_b)
    prik_piv = np.empty(2, dtype=np.int32)
    f2py_piv = np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgesv(
        np.int32(2), np.int32(1), prik_a, np.int32(2), prik_piv, prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dgesv(2, 1, f2py_a, f2py_piv, f2py_b, 0)
    scipy_lu, scipy_piv, scipy_x, scipy_info = scipy_lapack.dgesv(
        original_a.copy(order="F"), original_b.copy(order="F")
    )

    assert prik_scalars == (2, 1, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    assert_allclose_float64(active(prik_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(active(f2py_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(scipy_x, expected_x, operation_size=2)
    assert_allclose_float64(prik_a, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_a, scipy_lu, operation_size=2)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))
    np.testing.assert_array_equal(f2py_piv, native_pivots(scipy_piv))
    assert_small_residual(
        original_a @ prik_b - original_b,
        matrix_norm=np.linalg.norm(original_a, ord=np.inf),
        solution_norm=np.linalg.norm(prik_b, ord=np.inf),
        operation_size=2,
    )


def test_dgetrf_reconstructs_pivoted_lu(prik_lapack, scipy_lapack, f2py_lapack):
    original = np.array([[0.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(original), column_major(original)
    prik_piv = np.empty(2, dtype=np.int32)
    f2py_piv = np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgetrf(np.int32(2), np.int32(2), prik_a, np.int32(2), prik_piv, np.int32(0))
    f2py_result = f2py_lapack.dgetrf(2, 2, f2py_a, f2py_piv, 0)
    scipy_lu, scipy_piv, scipy_info = scipy_lapack.dgetrf(original.copy(order="F"))

    assert prik_scalars == (2, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    expected_native_piv = native_pivots(scipy_piv)
    np.testing.assert_array_equal(prik_piv, expected_native_piv)
    np.testing.assert_array_equal(f2py_piv, expected_native_piv)
    assert_allclose_float64(prik_a, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_a, scipy_lu, operation_size=2)
    lower, upper = unpack_lu(prik_a)
    permutation = pivot_matrix(prik_piv, 2, one_based=True)
    assert_allclose_float64(permutation @ original, lower @ upper, operation_size=2)


def test_dgetrs_solves_from_native_lu(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    original_b = np.array([[5.0], [5.0]], dtype=np.float64)
    expected_x = np.array([[1.0], [2.0]], dtype=np.float64)
    scipy_lu, scipy_piv, factor_info = scipy_lapack.dgetrf(matrix.copy(order="F"))
    assert factor_info == 0
    native_ipiv = native_pivots(scipy_piv)
    prik_lu, f2py_lu = column_major(scipy_lu), column_major(scipy_lu)
    prik_b, f2py_b = column_major(original_b), column_major(original_b)

    prik_scalars = prik_lapack.dgetrs(
        "N", np.int32(2), np.int32(1), prik_lu, np.int32(2), native_ipiv.copy(), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dgetrs(b"N", 2, 1, f2py_lu, native_ipiv.copy(), f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dgetrs(scipy_lu, scipy_piv, original_b.copy(order="F"), trans=0)

    assert prik_scalars == (2, 1, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    assert_allclose_float64(prik_b, expected_x, operation_size=2)
    assert_allclose_float64(f2py_b, expected_x, operation_size=2)
    assert_allclose_float64(scipy_x, expected_x, operation_size=2)
    assert_storage_unchanged(prik_lu, scipy_lu)
    assert_storage_unchanged(f2py_lu, scipy_lu)
