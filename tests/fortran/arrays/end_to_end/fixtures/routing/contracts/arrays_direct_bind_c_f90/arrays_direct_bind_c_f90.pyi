from prik.contracts import Bool8, Float64, Int32, native_abi

@native_abi("c")
def sum_values(
    n: Int32,
    values: Float64[n]
) -> Float64: ...

@native_abi("c")
def scale_values(
    n: Int32,
    values: Float64[n]
) -> None: ...

@native_abi("c")
def all_flags(
    n: Int32,
    values: Bool8[n]
) -> Bool8: ...

@native_abi("c")
def invert_flags(
    n: Int32,
    values: Bool8[n]
) -> None: ...

@native_abi("c")
def scale_matrix(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, columns]
) -> None: ...
