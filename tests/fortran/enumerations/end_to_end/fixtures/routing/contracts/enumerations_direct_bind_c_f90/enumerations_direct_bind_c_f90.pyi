from prik.contracts import Arg, Final, Int32, Return, native_abi, native_call

terminal: Final[Int32] = 5

stopped: Final[Int32] = -1

ready: Final[Int32] = 0

running: Final[Int32] = 4

@native_abi("c")
def direct_round_trip(
    state: Int32
) -> Int32: ...

@native_abi("c")
@native_call([Arg(0), Return('output', 0)])
def direct_next(
    state: Int32
) -> Int32: ...
