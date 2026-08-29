"""A small Pythonic linear-algebra API backed by Reference BLAS.

`_prik_linalg_native.pyi` owns the entire native mapping: names, argument
order, extents, leading dimensions, transposition modes, the fixed BLAS
scalars, dtype/rank/shape/layout validation and result allocation.
`DenseMatrix` adds only a one-time conversion to BLAS's preferred layout.
"""

from __future__ import annotations

import numpy as np

from _prik_linalg_native import dot, matmul, matvec, norm

__all__ = ["DenseMatrix", "dot", "matmul", "matvec", "norm"]


class DenseMatrix:
    """Hold one float64 matrix and forward to the functional API."""

    def __init__(self, values):
        self.values = np.asfortranarray(values)

    def dot(self, other):
        """Multiply this matrix by a vector or another matrix."""
        return matmul(self.values, other) if other.ndim == 2 else matvec(self.values, other)

    def __matmul__(self, other):
        return self.dot(other)
