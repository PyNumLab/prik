from prik.contracts import Arg, Float64, Value, native_abi, native_call

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
@native_call([Value(Arg(0))])
def adapted_sum_by_value(
    value: Point
) -> Float64: ...

__all__ = ["Point", "direct_sum", "adapted_sum_by_value"]
