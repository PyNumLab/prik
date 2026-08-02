"""Readable independent and differential checks for triangular BLAS Level 2."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import assert_allclose_for_dtype, assert_storage_unchanged, triangular_from_triangle


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_strmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0], [91.0, 92.0]], dtype=np.float32)
    original_x = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_triangle(original_a, 2, "U", unit_diagonal=False)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.strmv("U", "N", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.strmv(b"U", b"N", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_dtrmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[np.nan, np.nan], [-1.0, np.nan], [91.0, 92.0]], dtype=np.float64)
    original_x = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_triangle(original_a, 2, "L", unit_diagonal=True)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.dtrmv("L", "T", "U", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.dtrmv(b"L", b"T", b"U", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a.T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ctrmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray(
        [[2.0 + 1.0j, -1.0 + 2.0j], [np.nan + 1.0j * np.nan, 3.0 - 1.0j], [91.0j, 92.0j]], dtype=np.complex64
    )
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_triangle(original_a, 2, "U", unit_diagonal=False)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ctrmv("U", "C", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ctrmv(b"U", b"C", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a.conj().T @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ztrmv(prik_blas, f2py_blas):
    original_a = np.asfortranarray(
        [[np.nan + 1.0j * np.nan, np.nan + 1.0j * np.nan], [-1.0 + 2.0j, np.nan + 1.0j * np.nan], [91.0j, 92.0j]],
        dtype=np.complex128,
    )
    original_x = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_triangle(original_a, 2, "L", unit_diagonal=True)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_x.copy(), original_x.copy()

    prik_blas.ztrmv("L", "N", "U", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ztrmv(b"L", b"N", b"U", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    expected_x = logical_a @ original_x
    assert_allclose_for_dtype(prik_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_x, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_strsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0], [91.0, 92.0]], dtype=np.float32)
    expected_solution = np.array([4.0, -2.0], dtype=np.float32)
    logical_a = triangular_from_triangle(original_a, 2, "U", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.strsv("U", "N", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.strsv(b"U", b"N", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_dtrsv_upper_nonunit(prik_blas, f2py_blas):
    original_a = np.asfortranarray([[2.0, -1.0], [np.nan, 3.0], [91.0, 92.0]], dtype=np.float64)
    expected_solution = np.array([4.0, -2.0], dtype=np.float64)
    logical_a = triangular_from_triangle(original_a, 2, "U", unit_diagonal=False)
    original_b = logical_a.T @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.dtrsv("U", "T", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.dtrsv(b"U", b"T", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a.T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ctrsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray(
        [[np.nan + 1.0j * np.nan, np.nan + 1.0j * np.nan], [-1.0 + 2.0j, np.nan + 1.0j * np.nan], [91.0j, 92.0j]],
        dtype=np.complex64,
    )
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex64)
    logical_a = triangular_from_triangle(original_a, 2, "L", unit_diagonal=True)
    original_b = logical_a.conj().T @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ctrsv("L", "C", "U", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ctrsv(b"L", b"C", b"U", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a.conj().T @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a.conj().T @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)


def test_ztrsv(prik_blas, f2py_blas):
    original_a = np.asfortranarray(
        [[2.0 + 1.0j, np.nan + 1.0j * np.nan], [-1.0 + 2.0j, 3.0 - 1.0j], [91.0j, 92.0j]], dtype=np.complex128
    )
    expected_solution = np.array([4.0 + 1.0j, -2.0 + 0.5j], dtype=np.complex128)
    logical_a = triangular_from_triangle(original_a, 2, "L", unit_diagonal=False)
    original_b = logical_a @ expected_solution
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_x, f2py_x = original_b.copy(), original_b.copy()

    prik_blas.ztrsv("L", "N", "N", np.int32(2), prik_a, np.int32(3), prik_x, np.int32(1))
    f2py_blas.ztrsv(b"L", b"N", b"N", np.int32(2), f2py_a, f2py_x, np.int32(1), lda=np.int32(3))

    assert_allclose_for_dtype(logical_a @ prik_x, original_b, operation_size=2)
    assert_allclose_for_dtype(logical_a @ f2py_x, original_b, operation_size=2)
    assert_allclose_for_dtype(prik_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(f2py_x, expected_solution, operation_size=2)
    assert_allclose_for_dtype(prik_x, f2py_x, operation_size=2)
    assert_storage_unchanged(prik_a, original_a)
    assert_storage_unchanged(f2py_a, original_a)
