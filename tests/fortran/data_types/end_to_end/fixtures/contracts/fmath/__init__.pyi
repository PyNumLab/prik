from prik.contracts import Addr, Arg, Bool32, Complex128, Complex64, Float32, Float64, Int32, Returns, native_call, standalone

@standalone
@native_call([Addr(Arg(0))])
def square_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def square_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def square_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def square_c4(
    Z: Complex64
) -> tuple[Complex64, Returns["Z", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def square_c8(
    Z: Complex128
) -> tuple[Complex128, Returns["Z", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0))])
def cube_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def cube_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def cube_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_c4(
    X: Complex64,
    Y: Complex64
) -> tuple[Complex64, Returns["X", Complex64], Returns["Y", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_c8(
    X: Complex128,
    Y: Complex128
) -> tuple[Complex128, Returns["X", Complex128], Returns["Y", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def div_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def div_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def pow_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def pow_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def abs_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def abs_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def abs_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def neg_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def neg_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def neg_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def sin_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def sin_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def cos_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def cos_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def tan_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def tan_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def asin_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def asin_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def acos_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def acos_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def atan_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def atan_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def atan2_r4(
    Y: Float32,
    X: Float32
) -> tuple[Float32, Returns["Y", Float32], Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def atan2_r8(
    Y: Float64,
    X: Float64
) -> tuple[Float64, Returns["Y", Float64], Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def exp_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def exp_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def log_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def log_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def log10_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def log10_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def sqrt_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def sqrt_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def hypot_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def hypot_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sign_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sign_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def deg2rad_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def deg2rad_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def rad2deg_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def rad2deg_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dist2_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dist2_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3))])
def dot2_r4(
    X1: Float32,
    X2: Float32,
    Y1: Float32,
    Y2: Float32
) -> tuple[Float32, Returns["X1", Float32], Returns["X2", Float32], Returns["Y1", Float32], Returns["Y2", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3))])
def dot2_r8(
    X1: Float64,
    X2: Float64,
    Y1: Float64,
    Y2: Float64
) -> tuple[Float64, Returns["X1", Float64], Returns["X2", Float64], Returns["Y1", Float64], Returns["Y2", Float64]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dot3_r4(
    X1: Float32,
    X2: Float32,
    X3: Float32,
    Y1: Float32,
    Y2: Float32,
    Y3: Float32
) -> tuple[Float32, Returns["X1", Float32], Returns["X2", Float32], Returns["X3", Float32], Returns["Y1", Float32], Returns["Y2", Float32], Returns["Y3", Float32]]: ...

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dot3_r8(
    X1: Float64,
    X2: Float64,
    X3: Float64,
    Y1: Float64,
    Y2: Float64,
    Y3: Float64
) -> tuple[Float64, Returns["X1", Float64], Returns["X2", Float64], Returns["X3", Float64], Returns["Y1", Float64], Returns["Y2", Float64], Returns["Y3", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def conj_c4(
    Z: Complex64
) -> tuple[Complex64, Returns["Z", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def conj_c8(
    Z: Complex128
) -> tuple[Complex128, Returns["Z", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0))])
def real_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def real_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0))])
def aimag_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def aimag_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0))])
def abs_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def abs_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@standalone
@native_call([Addr(Arg(0))])
def is_positive_r4(
    X: Float32
) -> tuple[Bool32, Returns["X", Float32]]: ...

@standalone
@native_call([Addr(Arg(0))])
def is_positive_r8(
    X: Float64
) -> tuple[Bool32, Returns["X", Float64]]: ...

@standalone
@native_call([Addr(Arg(0))])
def is_even_i4(
    X: Int32
) -> tuple[Bool32, Returns["X", Int32]]: ...

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
