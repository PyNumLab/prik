from prik.contracts import Addr, Arg, Float64, native_call

class point:
    x: Float64
    y: Float64

def point_sum(
    p: point
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move_point(
    p: point,
    dx: Float64,
    dy: Float64
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def make_point_out(
    p: point,
    x: Float64,
    y: Float64
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_point(
    x: Float64,
    y: Float64
) -> point: ...
