from x2py.contracts import Addr, Arg, Float64, Int32, native_call

@native_call([Addr(Arg(0)), Arg(1)])
def add1(
    n: Int32,
    x: Float64[n]
) -> None: ...
