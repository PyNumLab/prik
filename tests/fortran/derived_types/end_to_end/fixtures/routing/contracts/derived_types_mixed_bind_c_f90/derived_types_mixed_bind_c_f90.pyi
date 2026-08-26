from prik.contracts import Arg, Float64, Value, native_abi, native_call

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
@native_call([Value(Arg(0))])
def adapted_sum_by_value(
    value: point
) -> Float64: ...
