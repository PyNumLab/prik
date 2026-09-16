from prik.contracts import Float64, native_abi

@native_abi("c")
class Point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

@native_abi("c")
def direct_sum(
    value: Point
) -> Float64: ...

@native_abi("c")
def direct_shift(
    value: Point,
    delta: Float64
) -> None: ...

__all__ = ["Point", "direct_sum", "direct_shift"]
