from prik.contracts import Addr, Allocatable, Arg, Float64, Int32, Return, Returns, native_call

optional_scale: Allocatable[Float64]

def clear_module_value() -> None: ...

@native_call([Addr(Arg(0))])
def set_module_value(
    value: Float64
) -> None: ...

def bump_module_value() -> None: ...

@native_call([Allocatable(Arg(0))])
def echo_allocatable(
    value: Float64 | None
) -> Float64: ...

@native_call([Allocatable(Arg(0))])
def update_allocatable(
    value: Float64 | None
) -> Returns["value", Float64] | None: ...

@native_call([Allocatable(Arg(0))])
def clear_allocatable_value(
    value: Float64 | None
) -> Returns["value", Float64] | None: ...

@native_call([Allocatable(Return('value', 0))])
def create_allocatable() -> Float64 | None: ...

@native_call([Addr(Arg(0)), Allocatable(Return('value', 0))])
def maybe_allocatable(
    flag: Int32
) -> Float64 | None: ...
