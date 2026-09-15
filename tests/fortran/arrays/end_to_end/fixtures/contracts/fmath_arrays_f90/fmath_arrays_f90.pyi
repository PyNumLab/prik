from prik.contracts import Addr, Arg, Bool8, Complex128, Complex64, Float32, Float64, Int32, Returns, native_call

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c4_contiguous(
    N: Int32,
    X: Complex64[:],
    Y: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c8_contiguous(
    N: Int32,
    X: Complex128[:],
    Y: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r4_contiguous(
    N: Int32,
    Y: Float32[:],
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r8_contiguous(
    N: Int32,
    Y: Float64[:],
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r4_contiguous(
    N: Int32,
    X1: Float32[:],
    X2: Float32[:],
    Y1: Float32[:],
    Y2: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r8_contiguous(
    N: Int32,
    X1: Float64[:],
    X2: Float64[:],
    Y1: Float64[:],
    Y2: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r4_contiguous(
    N: Int32,
    X1: Float32[:],
    X2: Float32[:],
    X3: Float32[:],
    Y1: Float32[:],
    Y2: Float32[:],
    Y3: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r8_contiguous(
    N: Int32,
    X1: Float64[:],
    X2: Float64[:],
    X3: Float64[:],
    Y1: Float64[:],
    Y2: Float64[:],
    Y3: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_even_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c4_strided(
    N: Int32,
    X: Complex64[::],
    Y: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c8_strided(
    N: Int32,
    X: Complex128[::],
    Y: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r4_strided(
    N: Int32,
    Y: Float32[::],
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r8_strided(
    N: Int32,
    Y: Float64[::],
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r4_strided(
    N: Int32,
    X1: Float32[::],
    X2: Float32[::],
    Y1: Float32[::],
    Y2: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r8_strided(
    N: Int32,
    X1: Float64[::],
    X2: Float64[::],
    Y1: Float64[::],
    Y2: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r4_strided(
    N: Int32,
    X1: Float32[::],
    X2: Float32[::],
    X3: Float32[::],
    Y1: Float32[::],
    Y2: Float32[::],
    Y3: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r8_strided(
    N: Int32,
    X1: Float64[::],
    X2: Float64[::],
    X3: Float64[::],
    Y1: Float64[::],
    Y2: Float64[::],
    Y3: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_even_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...
