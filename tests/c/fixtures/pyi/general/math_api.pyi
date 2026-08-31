from prik.contracts import Float64, Int

def norm2(
    n: Int,
    x: Float64[1]
) -> Float64: ...

def scale(
    n: Int,
    alpha: Float64,
    x: Float64[1]
) -> None: ...

def dot(
    n: Int,
    x: Float64[...],
    y: Float64[...]
) -> Float64: ...

def fill_identity3(
    a: Float64[3, 3]
) -> None: ...
