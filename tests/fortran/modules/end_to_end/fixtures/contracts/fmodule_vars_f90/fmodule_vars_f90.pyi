from x2py.contracts import Final, Float64, Int32

class rgb_color:
    def __init__(
        self,
        *,
        r: Int32 = ...,
        g: Int32 = ...,
        b: Int32 = ...
    ) -> None: ...

    r: Int32
    g: Int32
    b: Int32

nmax: Final[Int32] = 12

black: Final[rgb_color]

counter: Int32

scale: Float64

saved_counter: Int32

def summarize() -> Int32: ...

def scaled_counter() -> Float64: ...

def next_local() -> Int32: ...

def black_sum() -> Int32: ...
