from x2py.contracts import Float64, prototype

class point_t:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

@prototype
def point_callback(
    value: point_t
) -> point_t: ...

def apply_point(
    callback: point_callback,
    value: point_t,
    output: point_t
) -> None: ...
