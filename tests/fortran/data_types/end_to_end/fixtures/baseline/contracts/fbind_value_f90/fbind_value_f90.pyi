from prik.contracts import Addr, Arg, Bool8, Complex128, Float64, Int32, String, native_call

def plus_value(
    n: Int32
) -> Int32: ...

def double_value(
    n: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def plus_reference(
    n: Int32
) -> Int32: ...

def scale_real(
    x: Float64
) -> Float64: ...

def conjugate_value(
    z: Complex128
) -> Complex128: ...

def invert_flag(
    flag: Bool8
) -> Bool8: ...

def char_code(
    ch: String[1]
) -> Int32: ...
