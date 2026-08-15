from prik.contracts import Addr, Arg, Int32, native_abi, native_call

counter: Int32

@native_abi("c")
def direct_total(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def adapted_total(
    value: Int32
) -> Int32: ...
