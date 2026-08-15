from prik.contracts import Addr, Arg, Float64, Int32, Returns, bind, native_abi, native_call, overload

@native_abi("c")
@bind("direct_convert_integer")
def convert_integer(
    value: Int32
) -> Int32: ...

@native_abi("c")
@bind("direct_convert_real")
def convert_real(
    value: Float64
) -> Float64: ...

@native_abi("c")
@bind("direct_increment_integer")
@native_call([Addr(Arg(0))])
def increment_integer(
    value: Int32
) -> Returns["value", Int32]: ...

@native_abi("c")
@bind("direct_increment_real")
@native_call([Addr(Arg(0))])
def increment_real(
    value: Float64
) -> Returns["value", Float64]: ...

@native_abi("c")
@bind("direct_convert_integer")
@overload("convert_integer")
def convert(
    value: Int32
) -> Int32: ...

@native_abi("c")
@bind("direct_convert_real")
@overload("convert_real")
def convert(
    value: Float64
) -> Float64: ...

@native_abi("c")
@bind("direct_increment_integer")
@overload("increment_integer")
def increment(
    value: Int32
) -> Returns["value", Int32]: ...

@native_abi("c")
@bind("direct_increment_real")
@overload("increment_real")
def increment(
    value: Float64
) -> Returns["value", Float64]: ...
