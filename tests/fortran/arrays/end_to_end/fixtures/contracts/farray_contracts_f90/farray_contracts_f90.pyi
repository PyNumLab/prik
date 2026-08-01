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

def shift2(
    values: Float64[::, ::],
    out: Float64[::, ::]
) -> None: ...

def shift3(
    values: Float64[::, ::, ::],
    out: Float64[::, ::, ::]
) -> None: ...

def shift4(
    values: Float64[::, ::, ::, ::],
    out: Float64[::, ::, ::, ::]
) -> None: ...

def shift5(
    values: Float64[::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::]
) -> None: ...

def shift6(
    values: Float64[::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::]
) -> None: ...

def shift7(
    values: Float64[::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift8(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift9(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift10(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift11(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift12(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift13(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift14(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...

def shift15(
    values: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::],
    out: Float64[::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::, ::]
) -> None: ...
