from prik.contracts import Addr, Arg, Bool8, Complex128, Complex64, Float32, Float64, Int32, Returns, native_call, standalone

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_i4(
    N: Int32,
    X: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c4(
    N: Int32,
    Z: Complex64[N],
    R: Complex64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c8(
    N: Int32,
    Z: Complex128[N],
    R: Complex128[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_i4(
    N: Int32,
    X: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c4(
    N: Int32,
    X: Complex64[N],
    Y: Complex64[N],
    R: Complex64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c8(
    N: Int32,
    X: Complex128[N],
    Y: Complex128[N],
    R: Complex128[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_i4(
    N: Int32,
    X: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_i4(
    N: Int32,
    X: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r4(
    N: Int32,
    Y: Float32[N],
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r8(
    N: Int32,
    Y: Float64[N],
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_i4(
    N: Int32,
    X: Int32[N],
    Y: Int32[N],
    R: Int32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r4(
    N: Int32,
    X: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r8(
    N: Int32,
    X: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r4(
    N: Int32,
    X: Float32[N],
    Y: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r8(
    N: Int32,
    X: Float64[N],
    Y: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r4(
    N: Int32,
    X1: Float32[N],
    X2: Float32[N],
    Y1: Float32[N],
    Y2: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r8(
    N: Int32,
    X1: Float64[N],
    X2: Float64[N],
    Y1: Float64[N],
    Y2: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r4(
    N: Int32,
    X1: Float32[N],
    X2: Float32[N],
    X3: Float32[N],
    Y1: Float32[N],
    Y2: Float32[N],
    Y3: Float32[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7)])
def dot3_r8(
    N: Int32,
    X1: Float64[N],
    X2: Float64[N],
    X3: Float64[N],
    Y1: Float64[N],
    Y2: Float64[N],
    Y3: Float64[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c4(
    N: Int32,
    Z: Complex64[N],
    R: Complex64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c8(
    N: Int32,
    Z: Complex128[N],
    R: Complex128[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c4(
    N: Int32,
    Z: Complex64[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c8(
    N: Int32,
    Z: Complex128[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c4(
    N: Int32,
    Z: Complex64[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c8(
    N: Int32,
    Z: Complex128[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c4(
    N: Int32,
    Z: Complex64[N],
    R: Float32[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c8(
    N: Int32,
    Z: Complex128[N],
    R: Float64[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r4(
    N: Int32,
    X: Float32[N],
    R: Bool8[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r8(
    N: Int32,
    X: Float64[N],
    R: Bool8[N]
) -> Returns["N", Int32]: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_even_i4(
    N: Int32,
    X: Int32[N],
    R: Bool8[N]
) -> Returns["N", Int32]: ...

__all__ = [
    "square_r4",
    "square_r8",
    "square_i4",
    "square_c4",
    "square_c8",
    "cube_r4",
    "cube_r8",
    "cube_i4",
    "add_r4",
    "add_r8",
    "add_i4",
    "add_c4",
    "add_c8",
    "sub_r4",
    "sub_r8",
    "sub_i4",
    "mul_r4",
    "mul_r8",
    "mul_i4",
    "div_r4",
    "div_r8",
    "pow_r4",
    "pow_r8",
    "abs_r4",
    "abs_r8",
    "abs_i4",
    "neg_r4",
    "neg_r8",
    "neg_i4",
    "sin_r4",
    "sin_r8",
    "cos_r4",
    "cos_r8",
    "tan_r4",
    "tan_r8",
    "asin_r4",
    "asin_r8",
    "acos_r4",
    "acos_r8",
    "atan_r4",
    "atan_r8",
    "atan2_r4",
    "atan2_r8",
    "exp_r4",
    "exp_r8",
    "log_r4",
    "log_r8",
    "log10_r4",
    "log10_r8",
    "sqrt_r4",
    "sqrt_r8",
    "hypot_r4",
    "hypot_r8",
    "min_r4",
    "min_r8",
    "min_i4",
    "max_r4",
    "max_r8",
    "max_i4",
    "sign_r4",
    "sign_r8",
    "mod_i4",
    "mod_r4",
    "mod_r8",
    "deg2rad_r4",
    "deg2rad_r8",
    "rad2deg_r4",
    "rad2deg_r8",
    "dist2_r4",
    "dist2_r8",
    "dot2_r4",
    "dot2_r8",
    "dot3_r4",
    "dot3_r8",
    "conj_c4",
    "conj_c8",
    "real_c4",
    "real_c8",
    "aimag_c4",
    "aimag_c8",
    "abs_c4",
    "abs_c8",
    "is_positive_r4",
    "is_positive_r8",
    "is_even_i4",
]
