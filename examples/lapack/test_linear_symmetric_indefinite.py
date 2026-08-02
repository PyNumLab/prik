"""Symmetric-indefinite factorization and solve correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _negative_scalar_factor():
    matrix = np.array([[-4.0]], dtype=np.float64, order="F")
    return matrix, np.array([1], dtype=np.int32)


def test_dsycon_estimates_symmetric_reciprocal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    factor, native_ipiv = _negative_scalar_factor()

    prik_scalars = prik_lapack.dsycon(
        "U", 1, factor.copy(order="F"), 1, native_ipiv, 4.0, 0.0, np.empty(2), np.empty(1, dtype=np.int32), 0
    )
    f2py_result = f2py_lapack.dsycon(
        b"U", 1, factor.copy(order="F"), 1, native_ipiv, 4.0, 0.0, np.empty(2), np.empty(1, dtype=np.int32), 0
    )
    scipy_rcond, scipy_info = scipy_lapack.dsycon(factor.copy(order="F"), native_ipiv, 4.0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], 1.0)
    assert_allclose_float64(scipy_rcond, 1.0)


def test_dsyconv_converts_bunch_kaufman_storage(prik_lapack, scipy_lapack, f2py_lapack):
    factor, native_ipiv = _negative_scalar_factor()
    prik_a, f2py_a = factor.copy(order="F"), factor.copy(order="F")
    prik_e, f2py_e = np.full(1, np.nan), np.full(1, np.nan)

    prik_scalars = prik_lapack.dsyconv("U", "C", 1, prik_a, 1, native_ipiv, prik_e, 0)
    f2py_result = f2py_lapack.dsyconv(b"U", b"C", 1, f2py_a, 1, native_ipiv, f2py_e, 0)
    scipy_a, scipy_e, scipy_info = scipy_lapack.dsyconv(factor.copy(order="F"), native_ipiv, lower=0, way=0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, scipy_a)
    assert_allclose_float64(f2py_a, scipy_a)
    assert_allclose_float64(prik_e, scipy_e)
    assert_allclose_float64(f2py_e, scipy_e)


def test_dsyequb_scales_symmetric_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[4.0]], dtype=np.float64, order="F")
    prik_s, f2py_s = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dsyequb("U", 1, matrix.copy(order="F"), 1, prik_s, 0.0, 0.0, np.empty(3), 0)
    f2py_result = f2py_lapack.dsyequb(b"U", 1, matrix.copy(order="F"), 1, f2py_s, 0.0, 0.0, np.empty(3), 0)
    scipy_s, scipy_scond, scipy_amax, scipy_info = scipy_lapack.dsyequb(matrix.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_s, scipy_s)
    assert_allclose_float64(f2py_s, scipy_s)
    assert_allclose_float64(prik_scalars[-3:-1], [scipy_scond, scipy_amax])
    assert_allclose_float64(prik_s * matrix * prik_s, [[1.0]])


def test_dsysv_solves_symmetric_indefinite_system(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[-4.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dsysv("U", 1, 1, prik_a, 1, prik_piv, prik_b, 1, np.empty(8), 8, 0)
    f2py_result = f2py_lapack.dsysv(b"U", 1, 1, f2py_a, 1, f2py_piv, f2py_b, 1, np.empty(8), 8, 0)
    scipy_factor, _scipy_piv, scipy_x, scipy_info = scipy_lapack.dsysv(
        matrix.copy(order="F"), rhs.copy(order="F"), lwork=8
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[-2.0]])
    assert_allclose_float64(f2py_b, [[-2.0]])
    assert_allclose_float64(scipy_x, [[-2.0]])
    assert_allclose_float64(prik_a, scipy_factor)
    assert_allclose_float64(f2py_a, scipy_factor)
    assert_allclose_float64(matrix @ prik_b, rhs)


def test_dsysvx_solves_and_bounds_symmetric_error(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[-4.0]], dtype=np.float64, order="F")
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_af, f2py_af = np.empty_like(matrix), np.empty_like(matrix)
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)
    prik_x, f2py_x = np.empty_like(rhs), np.empty_like(rhs)
    prik_ferr, f2py_ferr = np.empty(1), np.empty(1)
    prik_berr, f2py_berr = np.empty(1), np.empty(1)

    prik_scalars = prik_lapack.dsysvx(
        "N",
        "U",
        1,
        1,
        matrix.copy(order="F"),
        1,
        prik_af,
        1,
        prik_piv,
        rhs.copy(order="F"),
        1,
        prik_x,
        1,
        0.0,
        prik_ferr,
        prik_berr,
        np.empty(3),
        3,
        np.empty(1, dtype=np.int32),
        0,
    )
    f2py_result = f2py_lapack.dsysvx(
        b"N",
        b"U",
        1,
        1,
        matrix.copy(order="F"),
        1,
        f2py_af,
        1,
        f2py_piv,
        rhs.copy(order="F"),
        1,
        f2py_x,
        1,
        0.0,
        f2py_ferr,
        f2py_berr,
        np.empty(3),
        3,
        np.empty(1, dtype=np.int32),
        0,
    )
    _a, scipy_factor, _piv, _b, scipy_x, scipy_rcond, scipy_ferr, scipy_berr, scipy_info = scipy_lapack.dsysvx(
        matrix.copy(order="F"), rhs.copy(order="F"), lwork=3
    )

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_x, [[-2.0]])
    assert_allclose_float64(f2py_x, [[-2.0]])
    assert_allclose_float64(scipy_x, [[-2.0]])
    assert_allclose_float64(prik_af, scipy_factor)
    assert_allclose_float64(f2py_af, scipy_factor)
    assert_allclose_float64(prik_scalars[-3], scipy_rcond)
    assert_allclose_float64(prik_ferr, scipy_ferr)
    assert_allclose_float64(prik_berr, scipy_berr)


def test_dsytf2_factorizes_symmetric_indefinite_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _native_ipiv = _negative_scalar_factor()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dsytf2("U", 1, prik_a, 1, prik_piv, 0)
    f2py_result = f2py_lapack.dsytf2(b"U", 1, f2py_a, 1, f2py_piv, 0)
    scipy_factor, _scipy_piv, scipy_info = scipy_lapack.dsytf2(matrix.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[-4.0]])
    assert_allclose_float64(f2py_a, [[-4.0]])
    assert_allclose_float64(scipy_factor, [[-4.0]])
    np.testing.assert_array_equal(prik_piv, [1])
    np.testing.assert_array_equal(f2py_piv, [1])


def test_dsytrf_factorizes_symmetric_indefinite_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    matrix, _native_ipiv = _negative_scalar_factor()
    prik_a, f2py_a = matrix.copy(order="F"), matrix.copy(order="F")
    prik_piv, f2py_piv = np.empty(1, dtype=np.int32), np.empty(1, dtype=np.int32)

    prik_scalars = prik_lapack.dsytrf("U", 1, prik_a, 1, prik_piv, np.empty(8), 8, 0)
    f2py_result = f2py_lapack.dsytrf(b"U", 1, f2py_a, 1, f2py_piv, np.empty(8), 8, 0)
    scipy_factor, _scipy_piv, scipy_info = scipy_lapack.dsytrf(matrix.copy(order="F"), lwork=8)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, scipy_factor)
    assert_allclose_float64(f2py_a, scipy_factor)
    np.testing.assert_array_equal(prik_piv, [1])
    np.testing.assert_array_equal(f2py_piv, [1])


def test_dsytri_inverts_symmetric_indefinite_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor, native_ipiv = _negative_scalar_factor()
    prik_a, f2py_a = factor.copy(order="F"), factor.copy(order="F")

    prik_scalars = prik_lapack.dsytri("U", 1, prik_a, 1, native_ipiv, np.empty(1), 0)
    f2py_result = f2py_lapack.dsytri(b"U", 1, f2py_a, 1, native_ipiv, np.empty(1), 0)
    scipy_inverse, scipy_info = scipy_lapack.dsytri(factor.copy(order="F"), native_ipiv)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_a, [[-0.25]])
    assert_allclose_float64(f2py_a, [[-0.25]])
    assert_allclose_float64(scipy_inverse, [[-0.25]])


def test_dsytrs_solves_from_symmetric_indefinite_factor(prik_lapack, scipy_lapack, f2py_lapack):
    factor, native_ipiv = _negative_scalar_factor()
    rhs = np.array([[8.0]], dtype=np.float64, order="F")
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dsytrs("U", 1, 1, factor.copy(order="F"), 1, native_ipiv, prik_b, 1, 0)
    f2py_result = f2py_lapack.dsytrs(b"U", 1, 1, factor.copy(order="F"), 1, native_ipiv, f2py_b, 1, 0)
    scipy_x, scipy_info = scipy_lapack.dsytrs(factor.copy(order="F"), native_ipiv, rhs.copy(order="F"))

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, [[-2.0]])
    assert_allclose_float64(f2py_b, [[-2.0]])
    assert_allclose_float64(scipy_x, [[-2.0]])
