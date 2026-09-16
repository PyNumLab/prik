from prik.contracts import Arg, Complex128, Float64, Int32, Value, native_abi, native_call

@native_abi("c")
class Point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        axis: Int32 = ...
    ) -> None: ...

    x: Float64
    axis: Int32

@native_abi("c")
class Tagged_Point:
    def __init__(
        self,
        *,
        weight: Complex128 = ...
    ) -> None: ...

    position: Point
    weight: Complex128

@native_abi("c")
def populate(
    value: Tagged_Point,
    x: Float64,
    axis: Int32,
    weight: Complex128
) -> None: ...

@native_abi("c")
@native_call([Value(Arg(0))])
def score_by_value(
    value: Tagged_Point
) -> Float64: ...

__all__ = ["Point", "Tagged_Point", "populate", "score_by_value"]
