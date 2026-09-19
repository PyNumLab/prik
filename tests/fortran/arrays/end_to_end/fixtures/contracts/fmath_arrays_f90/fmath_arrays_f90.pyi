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

__all__ = [
    "square_r4_contiguous",
    "square_r8_contiguous",
    "square_i4_contiguous",
    "square_c4_contiguous",
    "square_c8_contiguous",
    "cube_r4_contiguous",
    "cube_r8_contiguous",
    "cube_i4_contiguous",
    "add_r4_contiguous",
    "add_r8_contiguous",
    "add_i4_contiguous",
    "add_c4_contiguous",
    "add_c8_contiguous",
    "sub_r4_contiguous",
    "sub_r8_contiguous",
    "sub_i4_contiguous",
    "mul_r4_contiguous",
    "mul_r8_contiguous",
    "mul_i4_contiguous",
    "div_r4_contiguous",
    "div_r8_contiguous",
    "pow_r4_contiguous",
    "pow_r8_contiguous",
    "abs_r4_contiguous",
    "abs_r8_contiguous",
    "abs_i4_contiguous",
    "neg_r4_contiguous",
    "neg_r8_contiguous",
    "neg_i4_contiguous",
    "sin_r4_contiguous",
    "sin_r8_contiguous",
    "cos_r4_contiguous",
    "cos_r8_contiguous",
    "tan_r4_contiguous",
    "tan_r8_contiguous",
    "asin_r4_contiguous",
    "asin_r8_contiguous",
    "acos_r4_contiguous",
    "acos_r8_contiguous",
    "atan_r4_contiguous",
    "atan_r8_contiguous",
    "atan2_r4_contiguous",
    "atan2_r8_contiguous",
    "exp_r4_contiguous",
    "exp_r8_contiguous",
    "log_r4_contiguous",
    "log_r8_contiguous",
    "log10_r4_contiguous",
    "log10_r8_contiguous",
    "sqrt_r4_contiguous",
    "sqrt_r8_contiguous",
    "hypot_r4_contiguous",
    "hypot_r8_contiguous",
    "min_r4_contiguous",
    "min_r8_contiguous",
    "min_i4_contiguous",
    "max_r4_contiguous",
    "max_r8_contiguous",
    "max_i4_contiguous",
    "sign_r4_contiguous",
    "sign_r8_contiguous",
    "mod_i4_contiguous",
    "mod_r4_contiguous",
    "mod_r8_contiguous",
    "deg2rad_r4_contiguous",
    "deg2rad_r8_contiguous",
    "rad2deg_r4_contiguous",
    "rad2deg_r8_contiguous",
    "dist2_r4_contiguous",
    "dist2_r8_contiguous",
    "dot2_r4_contiguous",
    "dot2_r8_contiguous",
    "dot3_r4_contiguous",
    "dot3_r8_contiguous",
    "conj_c4_contiguous",
    "conj_c8_contiguous",
    "real_c4_contiguous",
    "real_c8_contiguous",
    "aimag_c4_contiguous",
    "aimag_c8_contiguous",
    "abs_c4_contiguous",
    "abs_c8_contiguous",
    "is_positive_r4_contiguous",
    "is_positive_r8_contiguous",
    "is_even_i4_contiguous",
    "square_r4_strided",
    "square_r8_strided",
    "square_i4_strided",
    "square_c4_strided",
    "square_c8_strided",
    "cube_r4_strided",
    "cube_r8_strided",
    "cube_i4_strided",
    "add_r4_strided",
    "add_r8_strided",
    "add_i4_strided",
    "add_c4_strided",
    "add_c8_strided",
    "sub_r4_strided",
    "sub_r8_strided",
    "sub_i4_strided",
    "mul_r4_strided",
    "mul_r8_strided",
    "mul_i4_strided",
    "div_r4_strided",
    "div_r8_strided",
    "pow_r4_strided",
    "pow_r8_strided",
    "abs_r4_strided",
    "abs_r8_strided",
    "abs_i4_strided",
    "neg_r4_strided",
    "neg_r8_strided",
    "neg_i4_strided",
    "sin_r4_strided",
    "sin_r8_strided",
    "cos_r4_strided",
    "cos_r8_strided",
    "tan_r4_strided",
    "tan_r8_strided",
    "asin_r4_strided",
    "asin_r8_strided",
    "acos_r4_strided",
    "acos_r8_strided",
    "atan_r4_strided",
    "atan_r8_strided",
    "atan2_r4_strided",
    "atan2_r8_strided",
    "exp_r4_strided",
    "exp_r8_strided",
    "log_r4_strided",
    "log_r8_strided",
    "log10_r4_strided",
    "log10_r8_strided",
    "sqrt_r4_strided",
    "sqrt_r8_strided",
    "hypot_r4_strided",
    "hypot_r8_strided",
    "min_r4_strided",
    "min_r8_strided",
    "min_i4_strided",
    "max_r4_strided",
    "max_r8_strided",
    "max_i4_strided",
    "sign_r4_strided",
    "sign_r8_strided",
    "mod_i4_strided",
    "mod_r4_strided",
    "mod_r8_strided",
    "deg2rad_r4_strided",
    "deg2rad_r8_strided",
    "rad2deg_r4_strided",
    "rad2deg_r8_strided",
    "dist2_r4_strided",
    "dist2_r8_strided",
    "dot2_r4_strided",
    "dot2_r8_strided",
    "dot3_r4_strided",
    "dot3_r8_strided",
    "conj_c4_strided",
    "conj_c8_strided",
    "real_c4_strided",
    "real_c8_strided",
    "aimag_c4_strided",
    "aimag_c8_strided",
    "abs_c4_strided",
    "abs_c8_strided",
    "is_positive_r4_strided",
    "is_positive_r8_strided",
    "is_even_i4_strided",
]
