from prik.contracts import Addr, Arg, Int32, native_call, standalone

@standalone
@native_call([Addr(Arg(0))])
def triple_value(
    value: Int32
) -> Int32: ...

@standalone
@native_call([Addr(Arg(0))])
def offset_value(
    value: Int32
) -> Int32: ...
