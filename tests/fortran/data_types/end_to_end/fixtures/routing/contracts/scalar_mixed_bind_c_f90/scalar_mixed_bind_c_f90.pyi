from prik.contracts import Addr, Arg, Int32, bind, native_abi, native_call

@native_abi("c")
@bind("scalar_mixed_direct_add")
def direct_add(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def adapted_add(
    value: Int32
) -> Int32: ...
