# Intentional invalid difference: @private hides Python declarations but does
# not make the native specific procedures callable.
from prik.contracts import Addr, Arg, Float64, Int32, native_call, overload, private


@private
@native_call([Addr(Arg(0))])
def convert_integer(value: Int32) -> Int32: ...


@private
@native_call([Addr(Arg(0))])
def convert_real(value: Float64) -> Float64: ...


@overload("convert_integer")
def convert(value: Int32) -> Int32: ...


@overload("convert_real")
def convert(value: Float64) -> Float64: ...
