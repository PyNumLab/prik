from prik.contracts import Addr, Arg, Float64, Int32, native_call, standalone

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3)])
def daxpy_like(
    n: Int32,
    alpha: Float64,
    x: Float64[n],
    y: Float64[n]
) -> None: ...

@standalone
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def ddot_like(
    n: Int32,
    x: Float64[n],
    y: Float64[n]
) -> Float64: ...
