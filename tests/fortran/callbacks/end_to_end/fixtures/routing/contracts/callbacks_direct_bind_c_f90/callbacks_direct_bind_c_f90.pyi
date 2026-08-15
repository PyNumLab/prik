from prik.contracts import Float64, In, Int32, native_abi, prototype

@native_abi("c")
@prototype
def direct_callback(
    value: In(Float64)
) -> Float64: ...

@native_abi("c")
@prototype
def direct_notify(
    value: In(Int32)
) -> None: ...

@native_abi("c")
def direct_apply(
    callback: direct_callback,
    value: Float64
) -> Float64: ...

@native_abi("c")
def direct_call_notify(
    callback: direct_notify,
    value: Int32
) -> None: ...
