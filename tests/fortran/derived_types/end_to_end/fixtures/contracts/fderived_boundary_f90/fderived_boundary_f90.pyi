from prik.contracts import Addr, Arg, Float64, native_call

class Point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

class Holder:
    def __init__(
        self,
        *,
        scale: Float64 = ...
    ) -> None: ...

    origin: Point
    scale: Float64

def point_sum(
    p: Point
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move_point(
    p: Point,
    dx: Float64,
    dy: Float64
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def make_point_out(
    p: Point,
    x: Float64,
    y: Float64
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_point(
    x: Float64,
    y: Float64
) -> Point: ...

def set_holder_origin(
    h: Holder,
    p: Point
) -> None: ...

def holder_origin_x(
    h: Holder
) -> Float64: ...

__all__ = [
    "Point",
    "Holder",
    "point_sum",
    "move_point",
    "make_point_out",
    "make_point",
    "set_holder_origin",
    "holder_origin_x",
]
