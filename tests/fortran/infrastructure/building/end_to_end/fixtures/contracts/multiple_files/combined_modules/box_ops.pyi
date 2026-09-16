from prik.contracts import Int32
from .shared_types import Box as box

def box_value(
    item: box
) -> Int32: ...

__all__ = ["box_value"]
