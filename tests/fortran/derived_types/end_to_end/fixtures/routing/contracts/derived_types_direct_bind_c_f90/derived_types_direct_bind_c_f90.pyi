from prik.contracts import Float64, native_abi

@native_abi("c")
class point:
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
    value: point
) -> Float64: ...

@native_abi("c")
def direct_shift(
    value: point,
    delta: Float64
) -> None: ...
