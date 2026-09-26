from prik.contracts import Final, Float64, Int32

class Rgb_Color:
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

black: Final[Rgb_Color]

counter: Int32[()]

scale: Float64[()]

saved_counter: Int32[()]

def summarize() -> Int32: ...

def scaled_counter() -> Float64: ...

def next_local() -> Int32: ...

def black_sum() -> Int32: ...

__all__ = [
    "Rgb_Color",
    "nmax",
    "black",
    "counter",
    "scale",
    "saved_counter",
    "summarize",
    "scaled_counter",
    "next_local",
    "black_sum",
]
