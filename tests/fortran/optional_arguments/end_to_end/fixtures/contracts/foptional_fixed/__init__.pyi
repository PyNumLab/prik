from prik.contracts import Addr, Arg, Int32, native_call, standalone

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def optional_scale(
    base: Int32,
    factor: Int32 = ...
) -> Int32: ...
