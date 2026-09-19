from prik.contracts import Addr, Allocatable, Annotated, Arg, Float64, Int64, Pass, Polymorphic, bind, native_call

class Vector:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

    @native_call([Pass(), Addr(Arg(0))])
    def scale(
        self,
        factor: Float64
    ) -> None: ...

    @bind("shift_vector")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def shift(
        self,
        dx: Float64,
        dy: Float64
    ) -> None: ...

    def magnitude(self) -> Float64: ...

class Vector_Store:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]
    matrix: Allocatable[Float64[:, :]]

    @native_call([Pass(), Addr(Arg(0))])
    def allocate_values(
        self,
        n: Int64
    ) -> None: ...

    def set_values(
        self,
        source: Float64[::]
    ) -> None: ...

    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def allocate_matrix(
        self,
        rows: Int64,
        cols: Int64
    ) -> None: ...

    def set_matrix(
        self,
        source: Float64[::, ::]
    ) -> None: ...

    @staticmethod
    @bind("make_vector_store")
    @native_call([Addr(Arg(0)), Addr(Arg(1))])
    def make(
        n: Int64,
        fill_value: Float64
    ) -> Vector_Store: ...

@native_call([Arg(0), Addr(Arg(1))])
def scale(
    self: Annotated[Vector, Polymorphic],
    factor: Float64
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def shift_vector(
    dx: Float64,
    owner: Annotated[Vector, Polymorphic],
    dy: Float64
) -> None: ...

def magnitude(
    self: Annotated[Vector, Polymorphic]
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def allocate_values(
    self: Annotated[Vector_Store, Polymorphic],
    n: Int64
) -> None: ...

def set_values(
    self: Annotated[Vector_Store, Polymorphic],
    source: Float64[::]
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def allocate_matrix(
    self: Annotated[Vector_Store, Polymorphic],
    rows: Int64,
    cols: Int64
) -> None: ...

def set_matrix(
    self: Annotated[Vector_Store, Polymorphic],
    source: Float64[::, ::]
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_vector_store(
    n: Int64,
    fill_value: Float64
) -> Vector_Store: ...

__all__ = [
    "Vector",
    "Vector_Store",
    "scale",
    "shift_vector",
    "magnitude",
    "allocate_values",
    "set_values",
    "allocate_matrix",
    "set_matrix",
    "make_vector_store",
]
