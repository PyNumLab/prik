from x2py.contracts import Addr, Arg, Float64, native_call

class point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

class holder:
    def __init__(
        self,
        *,
        scale: Float64 = ...
    ) -> None: ...

    origin: point
    scale: Float64

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

def set_holder_origin(
    h: holder,
    p: point
) -> None: ...

def holder_origin_x(
    h: holder
) -> Float64: ...
