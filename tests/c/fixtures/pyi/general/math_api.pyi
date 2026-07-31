from x2py.contracts import Addr, Arg, Float64, Int, native_call

def norm2(
    n: Int,
    x: Float64[1]
) -> Float64: ...

def scale(
    n: Int,
    alpha: Float64,
    x: Float64[1]
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def dot(
    n: Int,
    x: Float64,
    y: Float64
) -> Float64: ...

def fill_identity3(
    a: Float64[3, 3]
) -> None: ...
