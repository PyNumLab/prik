---
title: Design a Pythonic BLAS API
audience: users, advanced users
prerequisites: arrays, editing .pyi contracts
related: ../examples/fortran/blas-wrapper.md, ../reference/pyi-format.md, ../reference/pyi-contracts/calls-and-results.md, ../guide/arrays.md
status: maintained
publication: reviewed
---

# Design a Pythonic BLAS API

This tutorial turns four Reference BLAS routines into a small Python API:

```python
from prik_linalg import DenseMatrix, dot, matmul, matvec, norm
```

The native sources stay unchanged. The runnable example contains four working
files:

```text
examples/fortran/pythonic_blas/
├── _prik_linalg_native.pyi   # edited native contract
├── prik_linalg.py            # public Python API
├── build.sh                  # builds the extension
└── test_pythonic_blas.py     # checks the result with NumPy
```

## 1. Choose the native operations

| BLAS routine | Python operation |
| --- | --- |
| `DDOT` | `dot(x, y)` |
| `DNRM2` | `norm(x)` |
| `DGEMV` | `matvec(matrix, vector)` |
| `DGEMM` | `matmul(left, right)` |

For example, `DGEMV` expects eleven native arguments:

```fortran
SUBROUTINE DGEMV(TRANS,M,N,ALPHA,A,LDA,X,INCX,BETA,Y,INCY)
DOUBLE PRECISION ALPHA,BETA
INTEGER INCX,INCY,LDA,M,N
CHARACTER TRANS
DOUBLE PRECISION A(LDA,*),X(*),Y(*)
```

A Python caller should provide only the matrix and vector. The transposition
mode, dimensions, increments, product scalars and output storage are
implementation details.

## 2. Inspect the generated contract

Run `generate --pyi` without `--out` to print the starting contract instead of
creating another file:

```bash
python3 -m prik generate --pyi \
  examples/fortran/blas/native/ddot.f \
  examples/fortran/blas/native/dnrm2.f90 \
  examples/fortran/blas/native/dgemv.f \
  examples/fortran/blas/native/dgemm.f
```

The generated declarations follow the native signatures. Use them as the
starting point for the one edited contract,
[`_prik_linalg_native.pyi`](../../../examples/fortran/pythonic_blas/_prik_linalg_native.pyi).

## 3. Edit the `.pyi` contract

The edited `DGEMV` declaration is:

```python
@bind("DGEMV")
@standalone
@native_call([
    String[1]("N"), Int32(Arg(0).shape[0]), Int32(Arg(0).shape[1]),
    Float64(1.0), Arg(0), Int32(Arg(0).shape[0]),
    Arg(1), Int32(1), Float64(0.0),
    Return("y", 0), Int32(1),
])
def matvec(
    matrix: Float64[:, :],
    vector: Float64[matrix.shape[1]],
) -> Float64[matrix.shape[0]]: ...
```

Eleven native arguments become two, and this one declaration does the whole
redesign:

| Contract edit | Result |
| --- | --- |
| `@bind("DGEMV")` | Renames the Python operation without changing the native symbol. |
| `@native_call([...])` | Defines the exact BLAS argument order. |
| `String[1]("N")` | Declares the transposition mode, so `TRANS` never reaches Python. |
| Typed shape projections | Read `M`, `N` and `LDA` from the NumPy shape as the default Fortran `INTEGER` the dummies declare. |
| `Int32(1)` | Fixes both vector increments to one. |
| `Float64(1.0)` and `Float64(0.0)` | Selects an ordinary matrix product. |
| `Return("y", 0)` | Allocates and returns the output vector. |
| Array dimensions | Reject incompatible shapes before BLAS runs. |
| `Float64[:, :]` | Uses the default Fortran layout, which BLAS consumes directly. |

Two entries deserve a note. Wrapping the extent in `Int32(...)` is what lets it
stay hidden: a bare `Arg(0).shape[0]` is materialized as `size_t`, the right
identity for a C `size_t` parameter but not for the four-byte `INTEGER` BLAS
declares. And `String[1]("N")` is a declaration, not a conversion — it states
the character the native parameter receives, and it crosses as an
interoperable `char` that a `character(len=1)` dummy takes directly.

`DDOT`, `DNRM2` and `DGEMM` use the same mechanisms. Their complete
declarations are in the same `.pyi` file.

The [`.pyi` format](../reference/pyi-format.md) defines these entries, [Calls
and Results](../reference/pyi-contracts/calls-and-results.md) explains native
argument mappings, and [Arrays](../guide/arrays.md) covers shapes and layout.

## 4. Add the small Python API

The contract now owns every native fact, so all four operations are the
extension's own functions. [`prik_linalg.py`](../../../examples/fortran/pythonic_blas/prik_linalg.py)
re-exports them and adds one convenience class:

```python
import numpy as np

from _prik_linalg_native import dot, matmul, matvec, norm


class DenseMatrix:
    """Hold one float64 matrix and forward to the functional API."""

    def __init__(self, values):
        self.values = np.asfortranarray(values)

    def dot(self, other):
        return matmul(self.values, other) if other.ndim == 2 else matvec(self.values, other)

    def __matmul__(self, other):
        return self.dot(other)
```

There is no native argument translation left to do. Native ordering, extents,
leading dimensions, transposition modes, numeric constants, validation and
output allocation all live in the contract. `DenseMatrix` adds one Python
convenience: it converts its matrix to Fortran order once when constructed, so
repeated operations pass that storage directly to BLAS.

## 5. Build it

From the repository root, source the single build script:

```bash
source examples/fortran/pythonic_blas/build.sh
```

It builds the private `_prik_linalg_native` extension from the edited contract
and Reference BLAS sources, then adds the extension and `prik_linalg.py` to
`PYTHONPATH`.

## 6. Use the API

```python
import numpy as np

from prik_linalg import DenseMatrix, dot, matmul, matvec, norm

x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
y = np.array([4.0, 5.0, 6.0], dtype=np.float64)
matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
matrix_f = np.asfortranarray(matrix)

print(dot(x, y))
print(norm(x))
print(matvec(matrix_f, x[:2]))
print(matmul(matrix_f, matrix_f))

A = DenseMatrix(matrix)
print(A @ x[:2])
```

Result:

```text
32.0
3.7416573867739413
[ 5. 11.]
[[ 7. 10.]
 [15. 22.]]
[ 5. 11.]
```

There are no public dimensions, increments, leading dimensions, mode
characters, product scalars or output buffers.

## 7. Test it

The one test file compares every operation with NumPy and also checks shape,
dtype, rank, layout, result allocation, unchanged inputs, the public signatures,
the one-time `DenseMatrix` layout conversion and method forwarding:

```bash
python3 -m pytest -q examples/fortran/pythonic_blas/test_pythonic_blas.py
```

The final API is small even though the underlying routines are not:

```python
dot(x, y)
norm(x)
matvec(matrix_f, vector)
matmul(left_f, right_f)

A = DenseMatrix(matrix)
A.dot(vector)
A @ vector
```

Next, see the [complete BLAS wrapper](../examples/fortran/blas-wrapper.md) for
the full 155-routine surface or [Editing `.pyi`
Contracts](../reference/pyi-contracts/index.md) for other API transformations.
