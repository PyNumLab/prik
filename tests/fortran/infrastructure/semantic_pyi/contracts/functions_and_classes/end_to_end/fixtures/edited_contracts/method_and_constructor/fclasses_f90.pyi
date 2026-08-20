# Intentional difference: reuse one module procedure as a direct constructor,
# a renamed method, and a public module function.
from prik.contracts import Addr, Arg, Float64, Pass, bind, native_call


class vector:
    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def __init__(self, dx: Float64, dy: Float64) -> None: ...

    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def shift(self, dx: Float64, dy: Float64) -> None: ...

    x: Float64
    y: Float64


@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def shift_vector(
    dx: Float64,
    owner: vector,
    dy: Float64,
) -> None: ...
