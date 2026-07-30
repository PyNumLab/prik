from x2py.contracts import Addr, Arg, Final, Int32, native_call

class paint:
    def __init__(
        self,
        *,
        color: Int32 = ...
    ) -> None: ...

    color: Int32

red: Final[Int32] = -1

blue: Final[Int32] = 0

green: Final[Int32] = 10

yellow: Final[Int32] = 11

@native_call([Addr(Arg(0))])
def round_trip_color(
    color: Int32
) -> Int32: ...
