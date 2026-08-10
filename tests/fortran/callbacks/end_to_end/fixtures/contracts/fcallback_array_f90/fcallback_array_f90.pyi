from prik.contracts import Addr, Arg, Float64, In, Int32, native_call, prototype

@prototype
def reduce_callback(
    count: In(Addr(Int32)),
    values: In(Float64[count])
) -> Float64: ...

@prototype
def transform_callback(
    count: In(Addr(Int32)),
    values: In(Float64[count])
) -> Float64[count]: ...

@native_call([Arg(0), Addr(Arg(1)), Arg(2)])
def apply_reduce(
    callback: reduce_callback,
    count: Int32,
    values: Float64[count]
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def apply_transform(
    callback: transform_callback,
    count: Int32,
    values: Float64[count],
    output: Float64[count]
) -> None: ...
