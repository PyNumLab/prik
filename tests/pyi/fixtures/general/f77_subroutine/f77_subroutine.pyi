from x2py.contracts import Addr, Arg, Float64, Int32, Returns, external, native_call

@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3)])
def daxpy(
    n: Int32,
    a: Float64,
    x: Float64[n],
    y: Float64[n]
) -> tuple[Returns["n", Int32], Returns["a", Float64]]: ...
