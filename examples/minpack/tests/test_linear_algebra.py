"""Factorization and update helpers validated with linear-algebra invariants."""

from __future__ import annotations

import numpy as np
import pytest

from .helpers import FLOAT, INT


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
TWO = INT(2)


def _apply_r1_rotations(values: np.ndarray, v: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Apply MINPACK's encoded right-side Givens rotations in NumPy."""
    result = values.copy()
    last = result.shape[1] - 1
    for column in range(last - 1, -1, -1):
        encoded = v[column]
        if abs(encoded) > 1.0:
            cosine = 1.0 / encoded
            sine = np.sqrt(1.0 - cosine**2)
        else:
            sine = encoded
            cosine = np.sqrt(1.0 - sine**2)
        current, final = result[:, column].copy(), result[:, last].copy()
        result[:, column] = cosine * current - sine * final
        result[:, last] = sine * current + cosine * final
    for column in range(last):
        encoded = w[column]
        if abs(encoded) > 1.0:
            cosine = 1.0 / encoded
            sine = np.sqrt(1.0 - cosine**2)
        else:
            sine = encoded
            cosine = np.sqrt(1.0 - sine**2)
        current, final = result[:, column].copy(), result[:, last].copy()
        result[:, column] = cosine * current + sine * final
        result[:, last] = -sine * current + cosine * final
    return result


def test_dogleg(minpack):
    r = np.array([1.0, 0.0, 1.0], dtype=np.float64)
    diagonal = np.ones(2, dtype=np.float64)
    qtb = np.array([3.0, 4.0], dtype=np.float64)
    x = np.empty(2, dtype=np.float64)

    minpack.dogleg(TWO, r, INT(3), diagonal, qtb, FLOAT(1.0), x, np.empty(2), np.empty(2))

    np.testing.assert_allclose(x, np.array([0.6, 0.8]), rtol=0.0, atol=1.0e-12)
    assert np.linalg.norm(x) == pytest.approx(1.0)


def test_lmpar(minpack):
    r = np.eye(2, dtype=np.float64, order="F")
    x = np.empty(2, dtype=np.float64)
    sdiag = np.empty(2, dtype=np.float64)

    delta, par = minpack.lmpar(
        TWO,
        r,
        TWO,
        np.array([1, 2], dtype=np.int32),
        np.ones(2),
        np.array([3.0, 4.0]),
        FLOAT(1.0),
        FLOAT(0.0),
        x,
        sdiag,
        np.empty(2),
        np.empty(2),
    )

    assert (delta, par) == (FLOAT(1.0), FLOAT(4.0))
    np.testing.assert_allclose(x, np.array([0.6, 0.8]), rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(sdiag, np.sqrt(5.0), rtol=0.0, atol=1.0e-12)


def test_qrfac(minpack):
    values = np.asfortranarray([[3.0, 0.0], [4.0, 5.0]], dtype=np.float64)
    pivots = np.zeros(2, dtype=np.int32)
    diagonal = np.zeros(2, dtype=np.float64)
    norms = np.zeros(2, dtype=np.float64)
    workspace = np.zeros(2, dtype=np.float64)

    minpack.qrfac(TWO, TWO, values, TWO, True, pivots, TWO, diagonal, norms, workspace)

    np.testing.assert_array_equal(pivots, np.array([1, 2], dtype=np.int32))
    np.testing.assert_allclose(norms, np.array([5.0, 5.0]))
    np.testing.assert_allclose(diagonal, np.array([-5.0, -3.0]), atol=1.0e-12)


def test_qform(minpack):
    values = np.asfortranarray([[3.0, 0.0], [4.0, 5.0]], dtype=np.float64)
    workspace = np.zeros(2, dtype=np.float64)
    minpack.qrfac(
        TWO,
        TWO,
        values,
        TWO,
        True,
        np.zeros(2, dtype=np.int32),
        TWO,
        np.zeros(2),
        np.zeros(2),
        np.zeros(2),
    )

    minpack.qform(TWO, TWO, values, TWO, workspace)

    np.testing.assert_allclose(values.T @ values, np.eye(2), rtol=0.0, atol=1.0e-12)


def test_qrsolv(minpack):
    x = np.empty(2, dtype=np.float64)
    sdiag = np.empty(2, dtype=np.float64)

    minpack.qrsolv(
        TWO,
        np.eye(2, dtype=np.float64, order="F"),
        TWO,
        np.array([1, 2], dtype=np.int32),
        np.ones(2),
        np.array([3.0, 4.0]),
        x,
        sdiag,
        np.empty(2),
    )

    np.testing.assert_allclose(x, np.array([1.5, 2.0]), rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(sdiag, np.sqrt(2.0), rtol=0.0, atol=1.0e-12)


def test_r1mpyq(minpack):
    values = np.asfortranarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    original = values.copy(order="F")
    v = np.array([0.6, 0.0], dtype=np.float64)
    w = np.array([-0.8, 0.0], dtype=np.float64)
    expected = _apply_r1_rotations(original, v, w)

    minpack.r1mpyq(TWO, TWO, values, TWO, v, w)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(np.linalg.norm(values, axis=1), np.linalg.norm(original, axis=1))


def test_r1updt(minpack):
    packed_lower = np.array([2.0, 1.0, 3.0], dtype=np.float64)
    original = np.array([[2.0, 0.0], [1.0, 3.0]], dtype=np.float64)
    u = np.array([0.5, -1.0], dtype=np.float64)
    v = np.array([0.25, 0.75], dtype=np.float64)
    original_v = v.copy()
    work = np.empty(2, dtype=np.float64)

    singular = minpack.r1updt(TWO, TWO, packed_lower, INT(3), u, v, work)

    assert singular is False
    expected = _apply_r1_rotations(original + np.outer(u, original_v), v, work)
    updated_lower = np.array([[packed_lower[0], 0.0], [packed_lower[1], packed_lower[2]]])
    np.testing.assert_allclose(expected, updated_lower, rtol=0.0, atol=1.0e-12)


def test_rwupdt(minpack):
    r = np.zeros((2, 2), dtype=np.float64, order="F")
    b = np.array([3.0, 4.0], dtype=np.float64)
    original_norm = np.linalg.norm(np.array([*b, 5.0]))

    alpha = minpack.rwupdt(TWO, r, TWO, np.array([1.0, 2.0]), b, FLOAT(5.0), np.empty(2), np.empty(2))

    assert np.linalg.norm(np.array([*b, alpha])) == pytest.approx(original_norm)
    np.testing.assert_allclose(r, np.array([[1.0, 2.0], [0.0, 0.0]]), rtol=0.0, atol=1.0e-12)
