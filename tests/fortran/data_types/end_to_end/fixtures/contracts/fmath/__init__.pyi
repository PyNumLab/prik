from prik.contracts import Addr, Arg, Bool32, Complex128, Complex64, Float32, Float64, Int32, Returns, bind, native_call, standalone

@bind("SQUARE_R4")
@standalone
@native_call([Addr(Arg(0))])
def square_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("SQUARE_R8")
@standalone
@native_call([Addr(Arg(0))])
def square_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("SQUARE_I4")
@standalone
@native_call([Addr(Arg(0))])
def square_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@bind("SQUARE_C4")
@standalone
@native_call([Addr(Arg(0))])
def square_c4(
    Z: Complex64
) -> tuple[Complex64, Returns["Z", Complex64]]: ...

@bind("SQUARE_C8")
@standalone
@native_call([Addr(Arg(0))])
def square_c8(
    Z: Complex128
) -> tuple[Complex128, Returns["Z", Complex128]]: ...

@bind("CUBE_R4")
@standalone
@native_call([Addr(Arg(0))])
def cube_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("CUBE_R8")
@standalone
@native_call([Addr(Arg(0))])
def cube_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("CUBE_I4")
@standalone
@native_call([Addr(Arg(0))])
def cube_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@bind("ADD_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("ADD_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("ADD_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("ADD_C4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_c4(
    X: Complex64,
    Y: Complex64
) -> tuple[Complex64, Returns["X", Complex64], Returns["Y", Complex64]]: ...

@bind("ADD_C8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def add_c8(
    X: Complex128,
    Y: Complex128
) -> tuple[Complex128, Returns["X", Complex128], Returns["Y", Complex128]]: ...

@bind("SUB_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("SUB_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("SUB_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sub_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("MUL_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("MUL_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("MUL_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mul_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("DIV_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def div_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("DIV_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def div_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("POW_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def pow_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("POW_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def pow_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("ABS_R4")
@standalone
@native_call([Addr(Arg(0))])
def abs_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("ABS_R8")
@standalone
@native_call([Addr(Arg(0))])
def abs_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("ABS_I4")
@standalone
@native_call([Addr(Arg(0))])
def abs_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@bind("NEG_R4")
@standalone
@native_call([Addr(Arg(0))])
def neg_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("NEG_R8")
@standalone
@native_call([Addr(Arg(0))])
def neg_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("NEG_I4")
@standalone
@native_call([Addr(Arg(0))])
def neg_i4(
    X: Int32
) -> tuple[Int32, Returns["X", Int32]]: ...

@bind("SIN_R4")
@standalone
@native_call([Addr(Arg(0))])
def sin_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("SIN_R8")
@standalone
@native_call([Addr(Arg(0))])
def sin_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("COS_R4")
@standalone
@native_call([Addr(Arg(0))])
def cos_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("COS_R8")
@standalone
@native_call([Addr(Arg(0))])
def cos_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("TAN_R4")
@standalone
@native_call([Addr(Arg(0))])
def tan_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("TAN_R8")
@standalone
@native_call([Addr(Arg(0))])
def tan_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("ASIN_R4")
@standalone
@native_call([Addr(Arg(0))])
def asin_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("ASIN_R8")
@standalone
@native_call([Addr(Arg(0))])
def asin_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("ACOS_R4")
@standalone
@native_call([Addr(Arg(0))])
def acos_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("ACOS_R8")
@standalone
@native_call([Addr(Arg(0))])
def acos_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("ATAN_R4")
@standalone
@native_call([Addr(Arg(0))])
def atan_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("ATAN_R8")
@standalone
@native_call([Addr(Arg(0))])
def atan_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("ATAN2_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def atan2_r4(
    Y: Float32,
    X: Float32
) -> tuple[Float32, Returns["Y", Float32], Returns["X", Float32]]: ...

@bind("ATAN2_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def atan2_r8(
    Y: Float64,
    X: Float64
) -> tuple[Float64, Returns["Y", Float64], Returns["X", Float64]]: ...

@bind("EXP_R4")
@standalone
@native_call([Addr(Arg(0))])
def exp_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("EXP_R8")
@standalone
@native_call([Addr(Arg(0))])
def exp_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("LOG_R4")
@standalone
@native_call([Addr(Arg(0))])
def log_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("LOG_R8")
@standalone
@native_call([Addr(Arg(0))])
def log_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("LOG10_R4")
@standalone
@native_call([Addr(Arg(0))])
def log10_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("LOG10_R8")
@standalone
@native_call([Addr(Arg(0))])
def log10_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("SQRT_R4")
@standalone
@native_call([Addr(Arg(0))])
def sqrt_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("SQRT_R8")
@standalone
@native_call([Addr(Arg(0))])
def sqrt_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("HYPOT_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def hypot_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("HYPOT_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def hypot_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("MIN_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("MIN_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("MIN_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def min_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("MAX_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("MAX_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("MAX_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def max_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("SIGN_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sign_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("SIGN_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def sign_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("MOD_I4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_i4(
    X: Int32,
    Y: Int32
) -> tuple[Int32, Returns["X", Int32], Returns["Y", Int32]]: ...

@bind("MOD_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("MOD_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def mod_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("DEG2RAD_R4")
@standalone
@native_call([Addr(Arg(0))])
def deg2rad_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("DEG2RAD_R8")
@standalone
@native_call([Addr(Arg(0))])
def deg2rad_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("RAD2DEG_R4")
@standalone
@native_call([Addr(Arg(0))])
def rad2deg_r4(
    X: Float32
) -> tuple[Float32, Returns["X", Float32]]: ...

@bind("RAD2DEG_R8")
@standalone
@native_call([Addr(Arg(0))])
def rad2deg_r8(
    X: Float64
) -> tuple[Float64, Returns["X", Float64]]: ...

@bind("DIST2_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dist2_r4(
    X: Float32,
    Y: Float32
) -> tuple[Float32, Returns["X", Float32], Returns["Y", Float32]]: ...

@bind("DIST2_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dist2_r8(
    X: Float64,
    Y: Float64
) -> tuple[Float64, Returns["X", Float64], Returns["Y", Float64]]: ...

@bind("DOT2_R4")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3))])
def dot2_r4(
    X1: Float32,
    X2: Float32,
    Y1: Float32,
    Y2: Float32
) -> tuple[Float32, Returns["X1", Float32], Returns["X2", Float32], Returns["Y1", Float32], Returns["Y2", Float32]]: ...

@bind("DOT2_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3))])
def dot2_r8(
    X1: Float64,
    X2: Float64,
    Y1: Float64,
    Y2: Float64
) -> tuple[Float64, Returns["X1", Float64], Returns["X2", Float64], Returns["Y1", Float64], Returns["Y2", Float64]]: ...

@bind("DOT3_R4")
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

@bind("DOT3_R8")
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

@bind("CONJ_C4")
@standalone
@native_call([Addr(Arg(0))])
def conj_c4(
    Z: Complex64
) -> tuple[Complex64, Returns["Z", Complex64]]: ...

@bind("CONJ_C8")
@standalone
@native_call([Addr(Arg(0))])
def conj_c8(
    Z: Complex128
) -> tuple[Complex128, Returns["Z", Complex128]]: ...

@bind("REAL_C4")
@standalone
@native_call([Addr(Arg(0))])
def real_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@bind("REAL_C8")
@standalone
@native_call([Addr(Arg(0))])
def real_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@bind("AIMAG_C4")
@standalone
@native_call([Addr(Arg(0))])
def aimag_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@bind("AIMAG_C8")
@standalone
@native_call([Addr(Arg(0))])
def aimag_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@bind("ABS_C4")
@standalone
@native_call([Addr(Arg(0))])
def abs_c4(
    Z: Complex64
) -> tuple[Float32, Returns["Z", Complex64]]: ...

@bind("ABS_C8")
@standalone
@native_call([Addr(Arg(0))])
def abs_c8(
    Z: Complex128
) -> tuple[Float64, Returns["Z", Complex128]]: ...

@bind("IS_POSITIVE_R4")
@standalone
@native_call([Addr(Arg(0))])
def is_positive_r4(
    X: Float32
) -> tuple[Bool32, Returns["X", Float32]]: ...

@bind("IS_POSITIVE_R8")
@standalone
@native_call([Addr(Arg(0))])
def is_positive_r8(
    X: Float64
) -> tuple[Bool32, Returns["X", Float64]]: ...

@bind("IS_EVEN_I4")
@standalone
@native_call([Addr(Arg(0))])
def is_even_i4(
    X: Int32
) -> tuple[Bool32, Returns["X", Int32]]: ...
