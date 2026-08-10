from prik.contracts import Addr, Arg, Float64, In, InOut, Int32, Out, Return, Returns, String, native_call, prototype

class point_t:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

@prototype
def value_callback(
    value: In(Int32)
) -> Int32: ...

@prototype
def scalar_storage_callback(
    value: InOut(Addr(Float64)),
    output: Out(Addr(Float64)),
    missing: Addr(Float64)
) -> None: ...

@prototype
def array_storage_callback(
    count: In(Addr(Int32)),
    values: In(Float64[count]),
    output: Out(Float64[count])
) -> None: ...

@prototype
def string_storage_callback(
    read_label: In(String[8]),
    write_label: Out(String[8]),
    update_label: InOut(String[8])
) -> None: ...

@prototype
def point_callback(
    value: In(point_t)
) -> point_t: ...

@native_call([Arg(0), Addr(Arg(1))])
def apply_value_callback(
    callback: value_callback,
    value: Int32
) -> Int32: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Return('output', 2)])
def apply_scalar_storage_callback(
    callback: scalar_storage_callback,
    value: Float64,
    missing: Float64
) -> tuple[Returns["value", Float64], Returns["missing", Float64], Float64]: ...

@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def apply_array_storage_callback(
    callback: array_storage_callback,
    count: Int32,
    values: Float64[count],
    output: Float64[count]
) -> None: ...

@native_call([Arg(0), Arg(1), Return('write_label', 1)])
def apply_string_storage_callback(
    callback: string_storage_callback,
    update_label: String[8]
) -> tuple[Returns["update_label", String[8]], String[8]]: ...

def apply_point_callback(
    callback: point_callback,
    value: point_t,
    output: point_t
) -> None: ...
