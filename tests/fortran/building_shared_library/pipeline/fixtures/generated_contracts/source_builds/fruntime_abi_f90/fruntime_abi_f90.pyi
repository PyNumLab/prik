from x2py.contracts import Addr, Arg, Float64, native_call

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
