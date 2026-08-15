from prik.contracts import Addr, Arg, Bool8, Complex128, Float64, Int32, String, Value, bind, native_abi, native_call

@native_abi("c")
@bind("prik_plus_value")
def plus_value(
    n: Int32
) -> Int32: ...

@native_abi("c")
def double_value(
    n: Int32
) -> Int32: ...

@native_abi("c")
@native_call([Addr(Arg(0))])
def plus_reference(
    n: Int32
) -> Int32: ...

@native_abi("c")
@bind("prik_scale_real")
def scale_real(
    x: Float64
) -> Float64: ...

@native_abi("c")
@bind("prik_conjugate_value")
def conjugate_value(
    z: Complex128
) -> Complex128: ...

@native_abi("c")
@bind("prik_invert_flag")
def invert_flag(
    flag: Bool8
) -> Bool8: ...

@native_abi("c")
@native_call([Value(Arg(0))])
def char_code(
    ch: String[1]
) -> Int32: ...
