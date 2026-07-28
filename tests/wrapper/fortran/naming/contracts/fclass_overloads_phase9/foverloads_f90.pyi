from x2py.contracts import Addr, Arg, Float64, Int32, Pass, bind, native_call, overload, private


class accumulator:
    def __init__(self, *, total: Float64 = 0.0) -> None: ...

    total: Float64 = 0.0

    @private
    @bind("accumulator_add_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def add_integer(self, value: Int32) -> None: ...

    @private
    @bind("accumulator_add_real")
    @native_call([Pass(), Addr(Arg(0))])
    def add_real(self, value: Float64) -> None: ...

    @bind("add")
    @overload("accumulator_add_integer")
    def add(self, value: Int32) -> None: ...

    @bind("add")
    @overload("accumulator_add_real")
    def add(self, value: Float64) -> None: ...


@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_integer(
    self: accumulator,
    value: Int32,
) -> None: ...


@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_real(
    self: accumulator,
    value: Float64,
) -> None: ...
