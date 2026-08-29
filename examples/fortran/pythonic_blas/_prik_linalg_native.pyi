# A deliberately small float64 interface over four Reference BLAS routines.
#
# The contract owns every native fact: argument order, extents, leading
# dimensions, transposition modes, typed constants, array validation, layout
# requirements and result allocation. prik_linalg.py adds only DenseMatrix.

from prik.contracts import (
    Arg,
    Float64,
    Int32,
    Return,
    String,
    bind,
    native_call,
    standalone,
)

# DDOT(N, DX, INCX, DY, INCY)
@bind("DDOT")
@standalone
@native_call(
    [
        Int32(Arg(0).shape[0]),  # N     - default Fortran INTEGER, from len(x)
        Arg(0),  # DX
        Int32(1),  # INCX  - unit stride
        Arg(1),  # DY
        Int32(1),  # INCY  - unit stride
    ]
)
def dot(x: Float64[:], y: Float64[x.shape[0]]) -> Float64: ...

# DNRM2(N, X, INCX)
@bind("DNRM2")
@standalone
@native_call(
    [
        Int32(Arg(0).shape[0]),  # N
        Arg(0),  # X
        Int32(1),  # INCX
    ]
)
def norm(x: Float64[:]) -> Float64: ...

# DGEMV(TRANS, M, N, ALPHA, A, LDA, X, INCX, BETA, Y, INCY)
@bind("DGEMV")
@standalone
@native_call(
    [
        String[1]("N"),  # TRANS - no transposition
        Int32(Arg(0).shape[0]),  # M     - rows of matrix
        Int32(Arg(0).shape[1]),  # N     - columns of matrix
        Float64(1.0),  # ALPHA - fixed: y = matrix @ vector
        Arg(0),  # A
        Int32(Arg(0).shape[0]),  # LDA   - the column-major matrix is packed
        Arg(1),  # X
        Int32(1),  # INCX
        Float64(0.0),  # BETA  - no accumulation into y
        Return("y", 0),  # Y     - allocated by PRIK, returned to Python
        Int32(1),  # INCY
    ]
)
def matvec(
    matrix: Float64[:, :],
    vector: Float64[matrix.shape[1]],
) -> Float64[matrix.shape[0]]: ...

# DGEMM(TRANSA, TRANSB, M, N, K, ALPHA, A, LDA, B, LDB, BETA, C, LDC)
@bind("DGEMM")
@standalone
@native_call(
    [
        String[1]("N"),  # TRANSA
        String[1]("N"),  # TRANSB
        Int32(Arg(0).shape[0]),  # M
        Int32(Arg(1).shape[1]),  # N
        Int32(Arg(0).shape[1]),  # K
        Float64(1.0),  # ALPHA
        Arg(0),  # A
        Int32(Arg(0).shape[0]),  # LDA
        Arg(1),  # B
        Int32(Arg(1).shape[0]),  # LDB
        Float64(0.0),  # BETA
        Return("product", 0),  # C
        Int32(Arg(0).shape[0]),  # LDC
    ]
)
def matmul(
    left: Float64[:, :],
    right: Float64[left.shape[1], :],
) -> Float64[left.shape[0], right.shape[1]]: ...
