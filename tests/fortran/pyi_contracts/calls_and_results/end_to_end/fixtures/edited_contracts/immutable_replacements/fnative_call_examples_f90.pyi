# Intentional difference: writable scalar, string, array, and derived-type
# arguments use immutable Python-visible inputs and explicit replacement results.
from x2py.contracts import Addr, Annotated, Arg, Float64, Immutable, Int32, Return, Returns, String, native_call

class summary_point:
    def __init__(
        self,
        *,
        total: Float64 = ...,
        code: Int32 = ...
    ) -> None: ...

    total: Float64
    code: Int32

@native_call([Addr(Arg(0)), Return("status", 0)])
def scalar_status(
    base: Int32
) -> Returns["status", Int32]: ...

def fixed_inout(
    label: Annotated[String[8], Immutable]
) -> Returns["label", String[8]]: ...

def scale_with_status(
    values: Annotated[Float64[:], Immutable],
    status: Int32[()]
) -> Returns["values", Float64[:]]: ...

@native_call([Addr(Arg(0)), Return("point", 0)])
def make_point(
    scale: Int32
) -> Returns["point", summary_point]: ...
