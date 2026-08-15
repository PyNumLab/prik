from prik.contracts import Final, Int32, native_abi

limit: Final[Int32] = 12

counter: Int32

@native_abi("c")
def direct_total(
    value: Int32
) -> Int32: ...

@native_abi("c")
def direct_set_counter(
    value: Int32
) -> None: ...
