from x2py.contracts import Addr, Allocatable, Arg, Float64, Int32, Return, String, native_call

class output_point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        tag: Int32 = ...
    ) -> None: ...

    x: Float64
    tag: Int32

@native_call([Addr(Arg(0)), Return('status', 0)])
def scalar_status(
    n: Int32
) -> Int32: ...

@native_call([Addr(Arg(0)), Arg(1)])
def fill_vector(
    n: Int32,
    values: Float64[n]
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2)])
def fill_matrix(
    n: Int32,
    m: Int32,
    values: Float64[n, m]
) -> None: ...

@native_call([Addr(Arg(0)), Return('values', 0)])
def build_alloc(
    n: Int32
) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0)), Return('status', 1)])
def with_scalar(
    n: Int32
) -> tuple[Int32, Int32]: ...

@native_call([Addr(Arg(0)), Arg(1), Return('status', 1), Return('built', 2)])
def mixed_outputs(
    n: Int32,
    values: Float64[n]
) -> tuple[Float64, Int32, Allocatable[Float64[:]]]: ...

def increment(
    values: Float64[::]
) -> None: ...

@native_call([Arg(0), Return('status', 0)])
def increment_with_status(
    values: Float64[::]
) -> Int32: ...

@native_call([Return('label', 0)])
def make_label() -> String[8]: ...

@native_call([Addr(Arg(0)), Arg(1)])
def make_point(
    scale: Int32,
    point: output_point
) -> None: ...
