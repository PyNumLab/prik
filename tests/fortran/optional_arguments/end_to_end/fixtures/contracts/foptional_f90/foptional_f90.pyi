from prik.contracts import Addr, Arg, Float64, Int32, Returns, String, native_call

class Sample:
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
    item: Sample = ...
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

@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def three_optional(
    first: Int32 = ...,
    second: Int32 = ...,
    third: Int32 = ...
) -> Int32: ...

__all__ = ["Sample", "summarize", "mutate_optional", "fill_optional", "optional_status", "three_optional"]
