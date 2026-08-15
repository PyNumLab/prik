from prik.contracts import Addr, Float64, Int32, native_abi

@native_abi("c")
def pointer_state(
    address: Addr(Float64)
) -> Int32: ...

@native_abi("c")
def increment_pointer(
    address: Addr(Float64)
) -> None: ...
