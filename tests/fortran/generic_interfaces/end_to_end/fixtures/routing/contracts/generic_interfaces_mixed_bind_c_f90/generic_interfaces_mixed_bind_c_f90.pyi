from prik.contracts import Addr, Arg, Float64, Int32, bind, native_abi, native_call, overload

@native_abi("c")
@bind("mixed_convert_integer")
def convert_integer(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def convert_real(
    value: Float64
) -> Float64: ...

@native_abi("c")
@bind("mixed_convert_integer")
@overload("convert_integer")
def convert(
    value: Int32
) -> Int32: ...

@overload("convert_real")
def convert(
    value: Float64
) -> Float64: ...
