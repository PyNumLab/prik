from x2py.contracts import Addr, Arg, Float64, Int32, bind, native_call, overload, private

@private
@native_call([Addr(Arg(0))])
def convert_integer(
    value: Int32
) -> Int32: ...

@private
@native_call([Addr(Arg(0))])
def convert_real(
    value: Float64
) -> Float64: ...

@bind("convert")
@overload("convert_integer")
def convert(
    value: Int32
) -> Int32: ...

@bind("convert")
@overload("convert_real")
def convert(
    value: Float64
) -> Float64: ...
