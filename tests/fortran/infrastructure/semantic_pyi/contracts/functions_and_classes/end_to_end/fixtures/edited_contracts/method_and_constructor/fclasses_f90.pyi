# Intentional difference: reuse module procedures as a direct constructor,
# renamed and same-name methods, and public module functions.
from prik.contracts import Addr, Arg, Float64, Pass, bind, native_call


class vector:
    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def __init__(self, dx: Float64, dy: Float64) -> None: ...

    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def shift(self, dx: Float64, dy: Float64) -> None: ...

    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def shift_vector(self, dx: Float64, dy: Float64) -> None: ...

    @bind("magnitude")
    @native_call([Pass()])
    def magnitude(self) -> Float64: ...

    x: Float64
    y: Float64


@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def shift_vector(
    dx: Float64,
    owner: vector,
    dy: Float64,
) -> None: ...
