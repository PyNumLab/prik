from x2py.contracts import Addr, Aliased, Allocatable, Annotated, Arg, Float64, Int32, Pass, Return, native_call

class buffer:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]

    @native_call([Pass(), Addr(Arg(0))])
    def allocate_values(
        self,
        n: Int32
    ) -> None: ...

    def deallocate_values(self) -> None: ...

    @native_call([Pass(), Addr(Arg(0))])
    def scale_values(
        self,
        scale: Float64
    ) -> None: ...

    def values_sum(self) -> Float64: ...

module_values: Annotated[Allocatable[Float64[:]], Aliased]

@native_call([Addr(Arg(0))])
def allocate_module_values(
    n: Int32
) -> None: ...

def deallocate_module_values() -> None: ...

@native_call([Addr(Arg(0))])
def scale_module_values(
    scale: Float64
) -> None: ...

def module_values_sum() -> Float64: ...

@native_call([Addr(Arg(0)), Return('values', 0)])
def build_values(
    n: Int32
) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Return('values', 0)])
def build_matrix(
    n: Int32,
    m: Int32
) -> Allocatable[Float64[:, :]]: ...

@native_call([Addr(Arg(0))])
def make_values(
    n: Int32
) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Return('values', 0)])
def make_matrix(
    n: Int32,
    m: Int32
) -> Allocatable[Float64[:, :]]: ...
