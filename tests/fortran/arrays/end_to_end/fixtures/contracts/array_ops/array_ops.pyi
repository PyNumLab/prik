from prik.contracts import Addr, Arg, Flat, Float64, Int32, native_call

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2)])
def scale_matrix(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, columns]
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1)])
def shift(
    size: Int32,
    values: Float64[size]
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sum_columns(
    size: Int32,
    values: Float64[size, size],
    result: Float64[size]
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1)])
def sum_flat(
    count: Int32,
    values: Float64[Flat]
) -> Float64: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2)])
def sum_flat_columns(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, Flat]
) -> Float64: ...

def scale_visible_rows(
    values: Float64[::, ::],
    out: Float64[::, ::]
) -> None: ...

def scale_without_intent(
    values: Float64[::]
) -> None: ...

@native_call([Arg(0), Addr(Arg(1))])
def mutate_optional(
    values: Float64[::] = ...,
    amount: Float64 = ...
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1)])
def fill_optional(
    n: Int32,
    values: Float64[::] = ...
) -> None: ...

@native_call([Addr(Arg(0))])
def automatic_vector(
    count: Int32
) -> Float64[count]: ...
