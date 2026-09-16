from prik.contracts import Addr, Aliased, Allocatable, Annotated, Arg, Float64, Int32, Pass, native_call

class Box:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]

    @native_call([Pass(), Addr(Arg(0))])
    def allocate_values(
        self,
        n: Int32
    ) -> None: ...

    def values_sum(self) -> Float64: ...

current: Annotated[Box, Aliased]

@native_call([Addr(Arg(0))])
def allocate_current(
    n: Int32
) -> None: ...

def deallocate_current() -> None: ...

def current_sum() -> Float64: ...

__all__ = ["Box", "current", "allocate_current", "deallocate_current", "current_sum"]
