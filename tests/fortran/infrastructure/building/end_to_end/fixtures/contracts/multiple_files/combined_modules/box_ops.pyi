from prik.contracts import Addr, Arg, Int32, native_call
from .shared_types import Box

def box_value(
    item: Box
) -> Int32: ...

@native_call([Addr(Arg(0))])
def boxed(
    value: Int32
) -> Box: ...

__all__ = ["box_value", "boxed"]
