from prik.contracts import Addr, Arg, Float64, Int32, native_abi, native_call

@native_abi("c")
def pointer_state(
    address: Addr(Float64)
) -> Int32: ...

@native_call([Addr(Arg(0))])
def adapted_value(
    value: Int32
) -> Int32: ...
