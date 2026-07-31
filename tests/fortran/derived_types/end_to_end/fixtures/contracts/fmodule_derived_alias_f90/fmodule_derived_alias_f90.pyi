from x2py.contracts import Addr, Aliased, Allocatable, Annotated, Arg, Float64, Int32, Pass, native_call

class box:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]

    @native_call([Pass(), Addr(Arg(0))])
    def allocate_values(
        self,
        n: Int32
    ) -> None: ...

    def values_sum(self) -> Float64: ...

current: Annotated[box, Aliased]

@native_call([Addr(Arg(0))])
def allocate_current(
    n: Int32
) -> None: ...

def deallocate_current() -> None: ...

def current_sum() -> Float64: ...
