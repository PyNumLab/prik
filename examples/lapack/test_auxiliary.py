"""Auxiliary, norm, reflector, rotation, and permutation correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, column_major, general_band_storage, native_pivots


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_dlamch_reports_float64_machine_epsilon(prik_lapack, scipy_lapack, f2py_lapack):
    expected = np.finfo(np.float64).eps / 2.0

    prik_value = prik_lapack.dlamch("E")
    f2py_value = f2py_lapack.dlamch(b"E")
    scipy_value = scipy_lapack.dlamch(b"E")

    assert_allclose_float64(prik_value, expected)
    assert_allclose_float64(f2py_value, expected)
    assert_allclose_float64(scipy_value, expected)


def test_dlangb_computes_frobenius_norm_of_band_storage(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[2.0, -1.0, 0.0], [3.0, 4.0, 5.0], [0.0, 6.0, -2.0]], dtype=np.float64)
    expected = float(np.sqrt(sum(float(value * value) for value in matrix.flat)))
    prik_ab = general_band_storage(matrix, 1, 1)
    f2py_ab = prik_ab.copy(order="F")
    scipy_ab = prik_ab.copy(order="F")

    prik_result = prik_lapack.dlangb("F", 3, 1, 1, prik_ab, 3, np.empty(3, dtype=np.float64))
    f2py_value = f2py_lapack.dlangb(b"F", 3, 1, 1, f2py_ab, 3, np.empty(3, dtype=np.float64))
    scipy_value = scipy_lapack.dlangb(b"F", 1, 1, scipy_ab)

    assert prik_result[1:] == (3, 1, 1, 3)
    assert_allclose_float64(prik_result[0], expected, operation_size=7)
    assert_allclose_float64(f2py_value, expected, operation_size=7)
    assert_allclose_float64(scipy_value, expected, operation_size=7)


def test_dlange_computes_one_norm(prik_lapack, scipy_lapack, f2py_lapack):
    matrix = np.array([[1.0, -5.0], [3.0, 2.0], [-2.0, 4.0]], dtype=np.float64, order="F")
    expected = 11.0
    work = np.empty(3, dtype=np.float64)

    prik_result = prik_lapack.dlange("1", 3, 2, matrix.copy(order="F"), 3, work.copy())
    f2py_value = f2py_lapack.dlange(b"1", 3, 2, matrix.copy(order="F"), 3, work.copy())
    scipy_value = scipy_lapack.dlange(b"1", matrix.copy(order="F"))

    assert prik_result[1:] == (3, 2, 3)
    assert_allclose_float64(prik_result[0], expected, operation_size=3)
    assert_allclose_float64(f2py_value, expected, operation_size=3)
    assert_allclose_float64(scipy_value, expected, operation_size=3)


def test_dlantr_ignores_unused_triangle_and_unit_diagonal(prik_lapack, scipy_lapack, f2py_lapack):
    stored = np.array([[np.nan, 2.0, -1.0], [np.nan, np.nan, 3.0], [np.nan, np.nan, np.nan]], order="F")
    expected = float(np.sqrt(1.0 + 4.0 + 1.0 + 1.0 + 9.0 + 1.0))
    work = np.empty(3, dtype=np.float64)

    prik_result = prik_lapack.dlantr("F", "U", "U", 3, 3, stored.copy(order="F"), 3, work.copy())
    f2py_value = f2py_lapack.dlantr(b"F", b"U", b"U", 3, 3, stored.copy(order="F"), 3, work.copy())
    scipy_value = scipy_lapack.dlantr(b"F", stored.copy(order="F"), uplo=b"U", diag=b"U")

    assert prik_result[1:] == (3, 3, 3)
    assert_allclose_float64(prik_result[0], expected, operation_size=6)
    assert_allclose_float64(f2py_value, expected, operation_size=6)
    assert_allclose_float64(scipy_value, expected, operation_size=6)


def test_dlarf_applies_householder_reflector_from_left(prik_lapack, scipy_lapack, f2py_lapack):
    vector = np.array([1.0, 2.0], dtype=np.float64)
    tau = 0.4
    original = np.array([[1.0, 3.0], [2.0, -1.0]], dtype=np.float64)
    reflector = np.eye(2, dtype=np.float64) - tau * np.outer(vector, vector)
    expected = reflector @ original
    prik_c, f2py_c = column_major(original), column_major(original)

    prik_scalars = prik_lapack.dlarf("L", 2, 2, vector, 1, tau, prik_c, 2, np.empty(2))
    f2py_result = f2py_lapack.dlarf(b"L", 2, 2, vector, 1, tau, f2py_c, 2, np.empty(2))
    scipy_c = scipy_lapack.dlarf(vector, tau, original.copy(order="F"), np.empty(2), side=b"L")

    assert prik_scalars == (2, 2, 1, tau, 2)
    assert f2py_result is None
    assert_allclose_float64(prik_c, expected, operation_size=2)
    assert_allclose_float64(f2py_c, expected, operation_size=2)
    assert_allclose_float64(scipy_c, expected, operation_size=2)


def test_dlarfg_constructs_a_valid_householder_reflector(prik_lapack, scipy_lapack, f2py_lapack):
    alpha = 4.0
    original_x = np.array([3.0, 0.0], dtype=np.float64)
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_scalars = prik_lapack.dlarfg(3, alpha, prik_x, 1, 0.0)
    f2py_result = f2py_lapack.dlarfg(3, alpha, f2py_x, 1, 0.0)
    scipy_beta, scipy_x, scipy_tau = scipy_lapack.dlarfg(3, alpha, original_x.copy())

    _, prik_beta, _, prik_tau = prik_scalars
    prik_vector = np.concatenate(([1.0], prik_x))
    original = np.concatenate(([alpha], original_x))
    expected = np.array([prik_beta, 0.0, 0.0], dtype=np.float64)
    assert f2py_result is None  # raw f2py cannot project the scalar ALPHA and TAU writebacks
    assert_allclose_float64((np.eye(3) - prik_tau * np.outer(prik_vector, prik_vector)) @ original, expected)
    assert_allclose_float64(prik_beta, scipy_beta)
    assert_allclose_float64(prik_x, scipy_x)
    assert_allclose_float64(f2py_x, scipy_x)
    assert_allclose_float64(prik_tau, scipy_tau)


def test_dlartg_constructs_a_givens_rotation(prik_lapack, scipy_lapack, f2py_lapack):
    f, g = 3.0, 4.0

    prik_scalars = prik_lapack.dlartg(f, g, 0.0, 0.0, 0.0)
    f2py_result = f2py_lapack.dlartg(f, g, 0.0, 0.0, 0.0)
    scipy_c, scipy_s, scipy_r = scipy_lapack.dlartg(f, g)

    _, _, prik_c, prik_s, prik_r = prik_scalars
    assert f2py_result is None  # raw f2py cannot project scalar-only subroutine outputs
    assert_allclose_float64(prik_c * f + prik_s * g, prik_r)
    assert_allclose_float64(-prik_s * f + prik_c * g, 0.0)
    assert_allclose_float64(prik_c * prik_c + prik_s * prik_s, 1.0)
    assert_allclose_float64([prik_c, prik_s, prik_r], [scipy_c, scipy_s, scipy_r])


def test_dlaswp_applies_native_one_based_row_pivots(prik_lapack, scipy_lapack, f2py_lapack):
    original = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]], dtype=np.float64)
    scipy_pivots = np.array([2, 2], dtype=np.int32)
    native_ipiv = native_pivots(scipy_pivots)
    expected = original[[2, 0, 1], :]
    prik_a, f2py_a = column_major(original), column_major(original)

    prik_scalars = prik_lapack.dlaswp(2, prik_a, 3, 1, 2, native_ipiv, 1)
    f2py_result = f2py_lapack.dlaswp(2, f2py_a, 3, 1, 2, native_ipiv, 1)
    scipy_a = scipy_lapack.dlaswp(original.copy(order="F"), scipy_pivots, k1=0, k2=1)

    assert prik_scalars == (2, 3, 1, 2, 1)
    assert f2py_result is None
    assert_allclose_float64(prik_a, expected)
    assert_allclose_float64(f2py_a, expected)
    assert_allclose_float64(scipy_a, expected)
