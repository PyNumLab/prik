from prik.contracts import Addr, Arg, Bool8, Complex128, Complex64, Float32, Float64, Int16, Int32, Int64, Int8, native_call

@native_call([Addr(Arg(0))])
def id_i8(
    value: Int8
) -> Int8: ...

@native_call([Addr(Arg(0))])
def id_i16(
    value: Int16
) -> Int16: ...

@native_call([Addr(Arg(0))])
def id_i32(
    value: Int32
) -> Int32: ...

def id_i32_value(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def id_i64(
    value: Int64
) -> Int64: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def copy_i16(
    n: Int32,
    values: Int16[n],
    out: Int16[n]
) -> None: ...

@native_call([Addr(Arg(0))])
def not_flag(
    value: Bool8
) -> Bool8: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def invert_flags(
    n: Int32,
    values: Bool8[n],
    out: Bool8[n]
) -> None: ...

@native_call([Addr(Arg(0))])
def id_r32(
    value: Float32
) -> Float32: ...

@native_call([Addr(Arg(0))])
def id_r64(
    value: Float64
) -> Float64: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def copy_r64(
    n: Int32,
    values: Float64[n],
    out: Float64[n]
) -> None: ...

@native_call([Addr(Arg(0))])
def conj_c64(
    value: Complex64
) -> Complex64: ...

@native_call([Addr(Arg(0))])
def shift_c128(
    value: Complex128
) -> Complex128: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def copy_c128(
    n: Int32,
    values: Complex128[n],
    out: Complex128[n]
) -> None: ...

@native_call([Addr(Arg(0))])
def id_c_i32(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def id_c_float(
    value: Float32
) -> Float32: ...

@native_call([Addr(Arg(0))])
def id_c_double(
    value: Float64
) -> Float64: ...

@native_call([Addr(Arg(0))])
def conj_c_float_complex(
    value: Complex64
) -> Complex64: ...

@native_call([Addr(Arg(0))])
def conj_c_double_complex(
    value: Complex128
) -> Complex128: ...

__all__ = [
    "id_i8",
    "id_i16",
    "id_i32",
    "id_i32_value",
    "id_i64",
    "copy_i16",
    "not_flag",
    "invert_flags",
    "id_r32",
    "id_r64",
    "copy_r64",
    "conj_c64",
    "shift_c128",
    "copy_c128",
    "id_c_i32",
    "id_c_float",
    "id_c_double",
    "conj_c_float_complex",
    "conj_c_double_complex",
]
