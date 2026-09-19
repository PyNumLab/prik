from prik.contracts import Addr, Arg, Int32, native_call
from .shared_types import Box as box

def box_value(
    item: box
) -> Int32: ...

@native_call([Addr(Arg(0))])
def boxed(
    value: Int32
) -> box: ...

__all__ = ["box_value", "boxed"]
