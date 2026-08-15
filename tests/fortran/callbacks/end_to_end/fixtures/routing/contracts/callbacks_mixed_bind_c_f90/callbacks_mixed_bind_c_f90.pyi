from prik.contracts import Addr, Arg, Float64, In, native_abi, native_call, prototype

@native_abi("c")
@prototype
def direct_callback(
    value: In(Float64)
) -> Float64: ...

@prototype
def adapted_callback(
    value: In(Addr(Float64))
) -> Float64: ...

@native_abi("c")
def direct_apply(
    callback: direct_callback,
    value: Float64
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def adapted_apply(
    callback: adapted_callback,
    value: Float64
) -> Float64: ...
