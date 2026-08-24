from prik.contracts import Addr, Arg, Bool8, Complex128, Complex64, Float32, Float64, Int32, Returns, bind, native_call

@bind("SQUARE_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("SQUARE_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("SQUARE_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("SQUARE_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@bind("SQUARE_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@bind("CUBE_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("CUBE_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("CUBE_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("ADD_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ADD_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ADD_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("ADD_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c4_contiguous(
    N: Int32,
    X: Complex64[:],
    Y: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@bind("ADD_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c8_contiguous(
    N: Int32,
    X: Complex128[:],
    Y: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@bind("SUB_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("SUB_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("SUB_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("MUL_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("MUL_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("MUL_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("DIV_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("DIV_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("POW_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("POW_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ABS_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ABS_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ABS_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("NEG_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("NEG_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("NEG_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("SIN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("SIN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("COS_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("COS_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("TAN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("TAN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ASIN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ASIN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ACOS_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ACOS_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ATAN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ATAN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ATAN2_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r4_contiguous(
    N: Int32,
    Y: Float32[:],
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ATAN2_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r8_contiguous(
    N: Int32,
    Y: Float64[:],
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("EXP_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("EXP_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("LOG_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("LOG_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("LOG10_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("LOG10_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("SQRT_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("SQRT_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("HYPOT_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("HYPOT_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("MIN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("MIN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("MIN_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("MAX_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("MAX_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("MAX_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("SIGN_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("SIGN_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("MOD_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_i4_contiguous(
    N: Int32,
    X: Int32[:],
    Y: Int32[:],
    R: Int32[:]
) -> Returns["N", Int32]: ...

@bind("MOD_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("MOD_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("DEG2RAD_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("DEG2RAD_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("RAD2DEG_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("RAD2DEG_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("DIST2_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r4_contiguous(
    N: Int32,
    X: Float32[:],
    Y: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("DIST2_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r8_contiguous(
    N: Int32,
    X: Float64[:],
    Y: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("DOT2_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r4_contiguous(
    N: Int32,
    X1: Float32[:],
    X2: Float32[:],
    Y1: Float32[:],
    Y2: Float32[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("DOT2_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r8_contiguous(
    N: Int32,
    X1: Float64[:],
    X2: Float64[:],
    Y1: Float64[:],
    Y2: Float64[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("DOT3_R4_CONTIGUOUS")
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

@bind("DOT3_R8_CONTIGUOUS")
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

@bind("CONJ_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Complex64[:]
) -> Returns["N", Int32]: ...

@bind("CONJ_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Complex128[:]
) -> Returns["N", Int32]: ...

@bind("REAL_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("REAL_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("AIMAG_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("AIMAG_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("ABS_C4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c4_contiguous(
    N: Int32,
    Z: Complex64[:],
    R: Float32[:]
) -> Returns["N", Int32]: ...

@bind("ABS_C8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c8_contiguous(
    N: Int32,
    Z: Complex128[:],
    R: Float64[:]
) -> Returns["N", Int32]: ...

@bind("IS_POSITIVE_R4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r4_contiguous(
    N: Int32,
    X: Float32[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@bind("IS_POSITIVE_R8_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r8_contiguous(
    N: Int32,
    X: Float64[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@bind("IS_EVEN_I4_CONTIGUOUS")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_even_i4_contiguous(
    N: Int32,
    X: Int32[:],
    R: Bool8[:]
) -> Returns["N", Int32]: ...

@bind("SQUARE_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("SQUARE_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("SQUARE_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("SQUARE_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@bind("SQUARE_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def square_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@bind("CUBE_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("CUBE_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("CUBE_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cube_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("ADD_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ADD_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ADD_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("ADD_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c4_strided(
    N: Int32,
    X: Complex64[::],
    Y: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@bind("ADD_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def add_c8_strided(
    N: Int32,
    X: Complex128[::],
    Y: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@bind("SUB_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("SUB_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("SUB_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sub_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("MUL_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("MUL_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("MUL_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mul_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("DIV_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("DIV_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def div_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("POW_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("POW_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def pow_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ABS_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ABS_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ABS_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("NEG_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("NEG_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("NEG_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def neg_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("SIN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("SIN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sin_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("COS_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("COS_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def cos_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("TAN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("TAN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def tan_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ASIN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ASIN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def asin_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ACOS_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ACOS_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def acos_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ATAN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ATAN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def atan_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ATAN2_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r4_strided(
    N: Int32,
    Y: Float32[::],
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ATAN2_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def atan2_r8_strided(
    N: Int32,
    Y: Float64[::],
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("EXP_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("EXP_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def exp_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("LOG_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("LOG_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("LOG10_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("LOG10_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def log10_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("SQRT_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("SQRT_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sqrt_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("HYPOT_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("HYPOT_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def hypot_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("MIN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("MIN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("MIN_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def min_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("MAX_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("MAX_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("MAX_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def max_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("SIGN_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("SIGN_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sign_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("MOD_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_i4_strided(
    N: Int32,
    X: Int32[::],
    Y: Int32[::],
    R: Int32[::]
) -> Returns["N", Int32]: ...

@bind("MOD_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("MOD_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def mod_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("DEG2RAD_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("DEG2RAD_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def deg2rad_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("RAD2DEG_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("RAD2DEG_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def rad2deg_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("DIST2_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r4_strided(
    N: Int32,
    X: Float32[::],
    Y: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("DIST2_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dist2_r8_strided(
    N: Int32,
    X: Float64[::],
    Y: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("DOT2_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r4_strided(
    N: Int32,
    X1: Float32[::],
    X2: Float32[::],
    Y1: Float32[::],
    Y2: Float32[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("DOT2_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5)])
def dot2_r8_strided(
    N: Int32,
    X1: Float64[::],
    X2: Float64[::],
    Y1: Float64[::],
    Y2: Float64[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("DOT3_R4_STRIDED")
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

@bind("DOT3_R8_STRIDED")
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

@bind("CONJ_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Complex64[::]
) -> Returns["N", Int32]: ...

@bind("CONJ_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def conj_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Complex128[::]
) -> Returns["N", Int32]: ...

@bind("REAL_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("REAL_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def real_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("AIMAG_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("AIMAG_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def aimag_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("ABS_C4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c4_strided(
    N: Int32,
    Z: Complex64[::],
    R: Float32[::]
) -> Returns["N", Int32]: ...

@bind("ABS_C8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def abs_c8_strided(
    N: Int32,
    Z: Complex128[::],
    R: Float64[::]
) -> Returns["N", Int32]: ...

@bind("IS_POSITIVE_R4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r4_strided(
    N: Int32,
    X: Float32[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...

@bind("IS_POSITIVE_R8_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_positive_r8_strided(
    N: Int32,
    X: Float64[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...

@bind("IS_EVEN_I4_STRIDED")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def is_even_i4_strided(
    N: Int32,
    X: Int32[::],
    R: Bool8[::]
) -> Returns["N", Int32]: ...
