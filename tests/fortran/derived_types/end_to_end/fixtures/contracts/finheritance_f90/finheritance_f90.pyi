from x2py.contracts import Addr, Annotated, Arg, Float64, Pass, Polymorphic, bind, native_call

class base_shape:
    def __init__(
        self,
        *,
        size: Float64 = ...
    ) -> None: ...

    size: Float64

    @bind("base_area")
    def area(self) -> Float64: ...

    @bind("base_set_size")
    @native_call([Pass(), Addr(Arg(0))])
    def set_size(
        self,
        value: Float64
    ) -> None: ...

class circle(base_shape):
    def __init__(
        self,
        *,
        radius: Float64 = ...
    ) -> None: ...

    radius: Float64

    @bind("circle_area")
    def area(self) -> Float64: ...

class box(base_shape):
    def __init__(
        self,
        *,
        width: Float64 = ...
    ) -> None: ...

    width: Float64

    @bind("box_area")
    def area(self) -> Float64: ...

def base_area(
    self: Annotated[base_shape, Polymorphic]
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def base_set_size(
    self: Annotated[base_shape, Polymorphic],
    value: Float64
) -> None: ...

def circle_area(
    self: Annotated[circle, Polymorphic]
) -> Float64: ...

def box_area(
    self: Annotated[box, Polymorphic]
) -> Float64: ...

def describe_shape(
    item: Annotated[base_shape, Polymorphic]
) -> Float64: ...
