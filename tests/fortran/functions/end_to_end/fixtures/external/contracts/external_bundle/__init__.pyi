from x2py.contracts import Addr, Arg, Int32, external, native_call

@external
@native_call([Addr(Arg(0))])
def triple_value(
    value: Int32
) -> Int32: ...

@external
@native_call([Addr(Arg(0))])
def offset_value(
    value: Int32
) -> Int32: ...
