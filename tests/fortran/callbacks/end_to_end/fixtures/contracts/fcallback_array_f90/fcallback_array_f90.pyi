from prik.contracts import Addr, Arg, Float64, In, Int32, Out, native_call, prototype

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

@prototype
def assumed_shape_callback(
    values: In(Float64[::]),
    doubled: Out(Float64[::])
) -> None: ...

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

def apply_assumed_shape(
    callback: assumed_shape_callback,
    values: Float64[::],
    doubled: Float64[::]
) -> None: ...

__all__ = [
    "reduce_callback",
    "transform_callback",
    "assumed_shape_callback",
    "apply_reduce",
    "apply_transform",
    "apply_assumed_shape",
]
