from prik.contracts import Addr, Arg, Flat, Float64, Int32, native_call

@native_call([Addr(Arg(0)), Arg(1)])
def sum_assumed_size(
    n: Int32,
    values: Float64[Flat]
) -> Float64: ...

@native_call([Addr(Arg(0)), Arg(1)])
def scale_lower(
    n: Int32,
    values: Float64[n]
) -> None: ...

def sum_in(
    values: Float64[::]
) -> Float64: ...

def bump_inout(
    values: Float64[::]
) -> None: ...

def fill_out(
    values: Float64[::]
) -> None: ...

def shift1(
    values: Float64[::],
    out: Float64[::]
) -> None: ...

def shift4(
    values: Float64[::, ::, ::, ::],
    out: Float64[::, ::, ::, ::]
) -> None: ...

def shift15(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

__all__ = ["sum_assumed_size", "scale_lower", "sum_in", "bump_inout", "fill_out", "shift1", "shift4", "shift15"]
