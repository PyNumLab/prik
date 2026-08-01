from prik.contracts import (
    Allocatable,
    Annotated,
    Arg,
    Destruction,
    Float64,
    Int32,
    Ownership,
    Pointer,
    Transfer,
    native_call,
)

@native_call([Allocatable(Arg(0))])
def alloc_state(value: Float64 | None = ...) -> Int32: ...

@native_call([Pointer(Arg(0))])
def pointer_state(
    value: Annotated[
        Float64,
        Ownership("caller"),
        Transfer("call_local"),
        Destruction("call_local")
    ] | None = ...
) -> Int32: ...
