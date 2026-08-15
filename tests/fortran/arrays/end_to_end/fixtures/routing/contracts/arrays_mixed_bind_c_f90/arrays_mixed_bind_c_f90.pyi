from prik.contracts import Addr, Arg, Float64, Int32, native_abi, native_call

@native_abi("c")
def direct_sum(
    n: Int32,
    values: Float64[n]
) -> Float64: ...

@native_call([Addr(Arg(0)), Arg(1)])
def adapted_sum(
    n: Int32,
    values: Float64[n]
) -> Float64: ...
