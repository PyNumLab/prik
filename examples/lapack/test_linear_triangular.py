"""Triangular solve, inverse, condition, packed, and RFP correctness tests."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import assert_allclose_float64, assert_storage_unchanged


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _upper_triangular():
    logical = np.array([[2.0, 1.0], [0.0, 3.0]], dtype=np.float64)
    stored = np.array([[2.0, 1.0], [np.nan, 3.0]], dtype=np.float64, order="F")
    packed = np.array([2.0, 1.0, 3.0], dtype=np.float64)
    return logical, stored, packed


def test_dtfsm_solves_with_rfp_triangular_factor(prik_lapack, scipy_lapack, f2py_lapack):
    logical, stored, _packed = _upper_triangular()
    rfp, convert_info = scipy_lapack.dtrttf(stored.copy(order="F"), transr=b"N", uplo=b"U")
    assert convert_info == 0
    rhs = np.array([[4.0], [6.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dtfsm(
        "N", "L", "U", "N", "N", np.int32(2), np.int32(1), np.float64(1.0), rfp, prik_b, np.int32(2)
    )
    f2py_result = f2py_lapack.dtfsm(b"N", b"L", b"U", b"N", b"N", 2, 1, 1.0, rfp, f2py_b)
    scipy_x = scipy_lapack.dtfsm(
        1.0, rfp, rhs.copy(order="F"), transr=b"N", side=b"L", uplo=b"U", trans=b"N", diag=b"N"
    )

    assert f2py_result is None
    assert prik_scalars == (2, 1, 1.0, 2)
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(logical @ prik_b, rhs, operation_size=2)


def test_dtfttp_converts_rfp_to_packed(prik_lapack, scipy_lapack, f2py_lapack):
    _logical, stored, expected_packed = _upper_triangular()
    rfp, convert_info = scipy_lapack.dtrttf(stored.copy(order="F"), transr=b"N", uplo=b"U")
    assert convert_info == 0
    prik_ap, f2py_ap = np.empty(3), np.empty(3)

    prik_scalars = prik_lapack.dtfttp("N", "U", np.int32(2), rfp, prik_ap, np.int32(0))
    f2py_result = f2py_lapack.dtfttp(b"N", b"U", 2, rfp, f2py_ap, 0)
    scipy_ap, scipy_info = scipy_lapack.dtfttp(2, rfp, transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ap, expected_packed)
    assert_allclose_float64(f2py_ap, expected_packed)
    assert_allclose_float64(scipy_ap, expected_packed)


def test_dtfttr_converts_rfp_to_full_triangular(prik_lapack, scipy_lapack, f2py_lapack):
    logical, stored, _packed = _upper_triangular()
    rfp, convert_info = scipy_lapack.dtrttf(stored.copy(order="F"), transr=b"N", uplo=b"U")
    assert convert_info == 0
    prik_a = np.full((2, 2), np.nan, dtype=np.float64, order="F")
    f2py_a = prik_a.copy(order="F")

    prik_scalars = prik_lapack.dtfttr("N", "U", np.int32(2), rfp, prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dtfttr(b"N", b"U", 2, rfp, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dtfttr(2, rfp, transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(np.triu(prik_a), logical)
    assert_allclose_float64(np.triu(f2py_a), logical)
    assert_allclose_float64(np.triu(scipy_a), logical)
    assert_storage_unchanged(np.tril(prik_a, -1), np.tril(stored, -1))
    assert_storage_unchanged(np.tril(f2py_a, -1), np.tril(stored, -1))


def test_dtpttf_converts_packed_to_rfp(prik_lapack, scipy_lapack, f2py_lapack):
    _logical, _stored, packed = _upper_triangular()
    prik_rfp, f2py_rfp = np.empty(3), np.empty(3)

    prik_scalars = prik_lapack.dtpttf("N", "U", np.int32(2), packed, prik_rfp, np.int32(0))
    f2py_result = f2py_lapack.dtpttf(b"N", b"U", 2, packed, f2py_rfp, 0)
    scipy_rfp, scipy_info = scipy_lapack.dtpttf(2, packed, transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_rfp, scipy_rfp)
    assert_allclose_float64(f2py_rfp, scipy_rfp)


def test_dtpttr_converts_packed_to_full_triangular(prik_lapack, scipy_lapack, f2py_lapack):
    logical, stored, packed = _upper_triangular()
    prik_a = np.full((2, 2), np.nan, dtype=np.float64, order="F")
    f2py_a = prik_a.copy(order="F")

    prik_scalars = prik_lapack.dtpttr("U", np.int32(2), packed, prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dtpttr(b"U", 2, packed, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dtpttr(2, packed, uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(np.triu(prik_a), logical)
    assert_allclose_float64(np.triu(f2py_a), logical)
    assert_allclose_float64(np.triu(scipy_a), logical)
    assert_storage_unchanged(np.tril(prik_a, -1), np.tril(stored, -1))
    assert_storage_unchanged(np.tril(f2py_a, -1), np.tril(stored, -1))


def test_dtrcon_estimates_triangular_reciprocal_condition(prik_lapack, scipy_lapack, f2py_lapack):
    _logical, stored, _packed = _upper_triangular()

    prik_scalars = prik_lapack.dtrcon(
        "1",
        "U",
        "N",
        np.int32(2),
        stored.copy(order="F"),
        np.int32(2),
        np.float64(0.0),
        np.empty(6),
        np.empty(2, dtype=np.int32),
        np.int32(0),
    )
    f2py_result = f2py_lapack.dtrcon(
        b"1", b"U", b"N", 2, stored.copy(order="F"), 0.0, np.empty(6), np.empty(2, dtype=np.int32), 0
    )
    scipy_rcond, scipy_info = scipy_lapack.dtrcon(stored.copy(order="F"), norm=b"1", uplo=b"U", diag=b"N")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_scalars[-2], scipy_rcond, operation_size=2)
    assert 0.0 < scipy_rcond <= 1.0


def test_dtrtri_inverts_triangular_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    logical, stored, _packed = _upper_triangular()
    prik_a, f2py_a = stored.copy(order="F"), stored.copy(order="F")

    prik_scalars = prik_lapack.dtrtri("U", "N", np.int32(2), prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dtrtri(b"U", b"N", 2, f2py_a, 0)
    scipy_a, scipy_info = scipy_lapack.dtrtri(stored.copy(order="F"), lower=0, unitdiag=0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(logical @ np.triu(prik_a), np.eye(2), operation_size=2)
    assert_allclose_float64(logical @ np.triu(f2py_a), np.eye(2), operation_size=2)
    assert_allclose_float64(logical @ np.triu(scipy_a), np.eye(2), operation_size=2)


def test_dtrtrs_solves_triangular_system(prik_lapack, scipy_lapack, f2py_lapack):
    logical, stored, _packed = _upper_triangular()
    rhs = np.array([[4.0], [6.0]], dtype=np.float64, order="F")
    expected = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_b, f2py_b = rhs.copy(order="F"), rhs.copy(order="F")

    prik_scalars = prik_lapack.dtrtrs(
        "U", "N", "N", np.int32(2), np.int32(1), stored.copy(order="F"), np.int32(2), prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dtrtrs(b"U", b"N", b"N", 2, 1, stored.copy(order="F"), f2py_b, 0)
    scipy_x, scipy_info = scipy_lapack.dtrtrs(stored.copy(order="F"), rhs.copy(order="F"), lower=0, trans=0, unitdiag=0)

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_b, expected, operation_size=2)
    assert_allclose_float64(f2py_b, expected, operation_size=2)
    assert_allclose_float64(scipy_x, expected, operation_size=2)
    assert_allclose_float64(logical @ prik_b, rhs, operation_size=2)


def test_dtrttf_converts_full_triangular_to_rfp(prik_lapack, scipy_lapack, f2py_lapack):
    _logical, stored, _packed = _upper_triangular()
    prik_rfp, f2py_rfp = np.empty(3), np.empty(3)

    prik_scalars = prik_lapack.dtrttf("N", "U", np.int32(2), stored.copy(order="F"), np.int32(2), prik_rfp, np.int32(0))
    f2py_result = f2py_lapack.dtrttf(b"N", b"U", 2, stored.copy(order="F"), f2py_rfp, 0)
    scipy_rfp, scipy_info = scipy_lapack.dtrttf(stored.copy(order="F"), transr=b"N", uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_rfp, scipy_rfp)
    assert_allclose_float64(f2py_rfp, scipy_rfp)


def test_dtrttp_converts_full_triangular_to_packed(prik_lapack, scipy_lapack, f2py_lapack):
    _logical, stored, expected_packed = _upper_triangular()
    prik_ap, f2py_ap = np.empty(3), np.empty(3)

    prik_scalars = prik_lapack.dtrttp("U", np.int32(2), stored.copy(order="F"), np.int32(2), prik_ap, np.int32(0))
    f2py_result = f2py_lapack.dtrttp(b"U", 2, stored.copy(order="F"), f2py_ap, 0)
    scipy_ap, scipy_info = scipy_lapack.dtrttp(stored.copy(order="F"), uplo=b"U")

    assert f2py_result is None
    assert prik_scalars[-1] == scipy_info == 0
    assert_allclose_float64(prik_ap, expected_packed)
    assert_allclose_float64(f2py_ap, expected_packed)
    assert_allclose_float64(scipy_ap, expected_packed)
