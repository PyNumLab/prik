from x2py.contracts import Addr, Aliased, Allocatable, Annotated, Arg, Float64, Int32, native_call

class box:
    values: Allocatable[Float64[:]]

current: Annotated[box, Aliased]

@native_call([Addr(Arg(0))])
def allocate_current(
    n: Int32
) -> None: ...

def deallocate_current() -> None: ...

def current_sum() -> Float64: ...
