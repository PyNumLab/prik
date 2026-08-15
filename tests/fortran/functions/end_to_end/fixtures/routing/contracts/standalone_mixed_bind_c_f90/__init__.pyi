from prik.contracts import Addr, Arg, Int32, bind, native_abi, native_call, standalone

@native_abi("c")
@bind("standalone_mixed_direct")
@standalone
def standalone_direct(
    value: Int32
) -> Int32: ...

@standalone
@native_call([Addr(Arg(0))])
def standalone_adapted(
    value: Int32
) -> Int32: ...
