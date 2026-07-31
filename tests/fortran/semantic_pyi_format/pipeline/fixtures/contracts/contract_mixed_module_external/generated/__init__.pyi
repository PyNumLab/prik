from x2py.contracts import Addr, Arg, Int32, external, native_call
from . import contract_math_mod

@external
@native_call([Addr(Arg(0))])
def external_double(
    value: Int32
) -> Int32: ...
