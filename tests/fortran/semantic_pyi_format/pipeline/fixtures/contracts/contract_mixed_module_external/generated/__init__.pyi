from prik.contracts import Addr, Arg, Int32, native_call, standalone
from . import contract_math_mod

@standalone
@native_call([Addr(Arg(0))])
def external_double(
    value: Int32
) -> Int32: ...
