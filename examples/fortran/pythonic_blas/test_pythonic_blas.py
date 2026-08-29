"""Independent NumPy checks for the Pythonic linear-algebra API."""

from __future__ import annotations

import numpy as np
import pytest

import prik_linalg as linalg


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]

MATRIX = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
WIDE = np.asfortranarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
TALL = np.asfortranarray([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float64)


def test_dot_matches_numpy():
    x = np.array([1.0, -2.0, 4.0], dtype=np.float64)
    y = np.array([3.0, 5.0, -1.0], dtype=np.float64)
    original_x = x.copy()
    original_y = y.copy()

    assert linalg.dot(x, y) == pytest.approx(np.dot(x, y))
    assert linalg.dot(np.empty(0), np.empty(0)) == 0.0
    np.testing.assert_array_equal(x, original_x)
    np.testing.assert_array_equal(y, original_y)


def test_norm_matches_numpy():
    x = np.array([3.0, -4.0, 12.0], dtype=np.float64)
    original = x.copy()

    assert linalg.norm(x) == pytest.approx(np.linalg.norm(x))
    np.testing.assert_array_equal(x, original)


def test_matvec_matches_numpy():
    vector = np.array([1.0, 2.0], dtype=np.float64)
    wide_vector = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    np.testing.assert_allclose(linalg.matvec(MATRIX, vector), MATRIX @ vector)
    np.testing.assert_allclose(linalg.matvec(WIDE, wide_vector), WIDE @ wide_vector)
    np.testing.assert_allclose(linalg.matvec(TALL, vector), TALL @ vector)


def test_matmul_matches_numpy():
    np.testing.assert_allclose(linalg.matmul(MATRIX, MATRIX), MATRIX @ MATRIX)
    np.testing.assert_allclose(linalg.matmul(WIDE, TALL), WIDE @ TALL)
    np.testing.assert_allclose(linalg.matmul(TALL, WIDE), TALL @ WIDE)


def test_results_are_new_and_inputs_are_unchanged():
    matrix = MATRIX.copy(order="F")
    vector = np.array([1.0, 2.0], dtype=np.float64)

    vector_product = linalg.matvec(matrix, vector)
    matrix_product = linalg.matmul(matrix, matrix)
    vector_product[0] = -1.0
    matrix_product[0, 0] = -1.0

    np.testing.assert_array_equal(matrix, MATRIX)
    np.testing.assert_array_equal(vector, np.array([1.0, 2.0]))
    np.testing.assert_allclose(linalg.matvec(matrix, vector), matrix @ vector)
    np.testing.assert_allclose(linalg.matmul(matrix, matrix), matrix @ matrix)


def test_dtype_rank_and_shape_are_validated():
    with pytest.raises(TypeError, match=r"numpy\.float64"):
        linalg.dot(np.array([1.0, 2.0], dtype=np.float32), np.array([1.0, 2.0], dtype=np.float32))
    with pytest.raises(TypeError, match=r"numpy\.float64"):
        linalg.norm(np.array([1, 2, 3], dtype=np.int64))
    with pytest.raises(TypeError, match=r"numpy\.float64"):
        linalg.dot(MATRIX, MATRIX)
    with pytest.raises(TypeError, match=r"numpy\.float64"):
        linalg.matvec(np.array([1.0, 2.0]), np.array([1.0, 2.0]))
    with pytest.raises(TypeError, match="incompatible shape"):
        linalg.dot(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))
    with pytest.raises(TypeError, match="incompatible shape"):
        linalg.matvec(MATRIX, np.array([1.0, 2.0, 3.0]))
    with pytest.raises(TypeError, match="incompatible shape"):
        linalg.matmul(WIDE, WIDE)


def test_matrix_layout_is_validated():
    with pytest.raises(TypeError, match="expected ordering"):
        linalg.matvec(np.array(MATRIX, order="C"), np.array([1.0, 2.0]))


def test_dense_matrix_forwards_to_the_functional_api(monkeypatch):
    matrix = np.array(MATRIX, order="C")
    right = np.asfortranarray(matrix)
    vector = np.array([1.0, 2.0], dtype=np.float64)
    dense = linalg.DenseMatrix(matrix)

    assert dense.values is not matrix
    assert dense.values.flags.f_contiguous
    np.testing.assert_array_equal(dense.values, matrix)
    already_fortran = MATRIX.copy(order="F")
    assert linalg.DenseMatrix(already_fortran).values is already_fortran
    np.testing.assert_allclose(dense.dot(vector), matrix @ vector)
    np.testing.assert_allclose(dense @ vector, matrix @ vector)
    np.testing.assert_allclose(dense @ right, matrix @ right)

    calls = []
    monkeypatch.setattr(linalg, "matvec", lambda *arguments: calls.append(("matvec", arguments)))
    monkeypatch.setattr(linalg, "matmul", lambda *arguments: calls.append(("matmul", arguments)))
    dense.dot(vector)
    dense @ matrix

    assert [name for name, _ in calls] == ["matvec", "matmul"]
    assert all(arguments[0] is dense.values for _, arguments in calls)


def test_public_api_takes_only_the_mathematical_operands():
    """Every BLAS bookkeeping argument is owned by the contract.

    The four operations are the generated extension's own functions, so their
    documented signatures are the contract's Python surface with no wrapper in
    between.
    """
    signatures = [
        operation.__doc__.splitlines()[0] for operation in (linalg.dot, linalg.norm, linalg.matvec, linalg.matmul)
    ]

    assert signatures == [
        "dot(x, y) -> float64",
        "norm(x) -> float64",
        "matvec(matrix, vector) -> ndarray[float64]",
        "matmul(left, right) -> ndarray[float64]",
    ]
