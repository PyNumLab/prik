from x2py.contracts import Addr, Arg, Float64, Int32, Returns, String, native_call

class sample:
    def __init__(
        self,
        *,
        value: Int32 = ...
    ) -> None: ...

    value: Int32

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4)])
def summarize(
    required: Int32,
    scale: Int32 = ...,
    values: Float64[::] = ...,
    label: String = ...,
    item: sample = ...
) -> Int32: ...

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

@native_call([Addr(Arg(0)), Arg(1)])
def optional_status(
    base: Int32,
    status: Int32[()] = ...
) -> tuple[Int32, Returns["status", Int32[()]] | None]: ...
