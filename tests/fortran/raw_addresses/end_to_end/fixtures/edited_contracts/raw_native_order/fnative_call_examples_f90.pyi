from x2py.contracts import Addr, Float64, Int32, String, bind

@bind("scalar_status")
def scalar_status_raw(base: Addr(Int32), status: Addr(Int32)) -> None: ...

@bind("fill_vector")
def fill_vector_raw(n: Int32[()], values: Addr(Float64[n])) -> None: ...

@bind("shift_matrix")
def shift_matrix_raw_c(
    n: Int32[()],
    m: Int32[()],
    values: Addr(Float64[n, m]),
    out: Addr(Float64[n, m])
) -> None: ...

@bind("shift_matrix")
def shift_matrix_raw_f(
    n: Int32[()],
    m: Int32[()],
    values: Addr(Float64[n, m]),
    out: Addr(Float64[n, m])
) -> None: ...

@bind("fixed_inout")
def fixed_inout_raw(label: Addr(String[8])) -> None: ...

@bind("fixed_inout")
def fixed_inout_storage(label: String[8][()]) -> None: ...
