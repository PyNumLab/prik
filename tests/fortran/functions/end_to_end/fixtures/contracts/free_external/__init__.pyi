from prik.contracts import Addr, Arg, Int32, native_call, standalone

@standalone
@native_call([Addr(Arg(0))])
def free_square(
    value: Int32
) -> Int32: ...
