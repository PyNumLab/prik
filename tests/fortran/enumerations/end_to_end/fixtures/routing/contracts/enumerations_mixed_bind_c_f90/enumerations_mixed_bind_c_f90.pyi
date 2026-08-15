from prik.contracts import Addr, Arg, Final, Int32, native_abi, native_call

stopped: Final[Int32] = -1

ready: Final[Int32] = 0

running: Final[Int32] = 4

@native_abi("c")
def direct_round_trip(
    state: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def adapted_next(
    state: Int32
) -> Int32: ...
