from x2py.contracts import Addr, Arg, Float64, native_call, prototype

@prototype
def scalar_callback(
    value: Addr(Float64)
) -> Float64: ...

@prototype
def notify_callback(
    value: Addr(Float64)
) -> None: ...

@prototype
def callback(
    value: Addr(Float64)
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def apply_scalar(
    callback: scalar_callback,
    value: Float64
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def apply_explicit(
    callback: callback,
    value: Float64
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def call_notify(
    callback: notify_callback,
    value: Float64
) -> None: ...
