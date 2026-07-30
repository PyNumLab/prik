from x2py.contracts import Addr, Allocatable, Arg, Float64, Int32, native_call

class child:
    id: Int32

class box:
    scalar: Int32
    fixed: Float64[2]
    values: Allocatable[Float64[:]]
    nested: child

current: box

@native_call([Addr(Arg(0))])
def initialise_current(
    n: Int32
) -> None: ...

def mutate_current() -> None: ...

def current_total() -> Float64: ...
