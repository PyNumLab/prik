# Intentional difference: no native-call decorators.  Output slots stay
# visible in native dummy-argument order.
from x2py.contracts import Addr, Float64, Int32, String, bind

class summary_point:
    def __init__(
        self,
        *,
        total: Float64 = ...,
        code: Int32 = ...
    ) -> None: ...

    total: Float64
    code: Int32

def scalar_status(
    base: Int32[()],
    status: Int32[()]
) -> None: ...

@bind("scalar_status")
def scalar_status_raw(
    base: Addr(Int32),
    status: Addr(Int32)
) -> None: ...

def fill_vector(
    n: Int32[()],
    values: Float64[n]
) -> None: ...

@bind("fill_vector")
def fill_vector_raw(
    n: Int32[()],
    values: Addr(Float64[n])
) -> None: ...

def shift_matrix(
    n: Int32[()],
    m: Int32[()],
    values: Float64[n, m],
    out: Float64[n, m]
) -> None: ...

def scale_with_status(
    values: Float64[::],
    status: Int32[()]
) -> None: ...

def fixed_inout(
    label: String[8]
) -> None: ...

@bind("fixed_inout")
def fixed_inout_raw(
    label: Addr(String[8])
) -> None: ...

@bind("fixed_inout")
def fixed_inout_storage(
    label: String[8][()]
) -> None: ...

def make_label(
    label: String[6]
) -> None: ...

def summarize_mixed(
    n: Int32[()],
    values: Float64[n],
    status: Int32[()],
    label: String[6]
) -> Float64: ...

def make_point(
    scale: Int32[()],
    point: summary_point
) -> None: ...
