from prik.contracts import Addr, Annotated, Arg, Float64, Pass, Polymorphic, bind, native_call

class Base_Shape:
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

class Circle(Base_Shape):
    def __init__(
        self,
        *,
        radius: Float64 = ...
    ) -> None: ...

    radius: Float64

    @bind("circle_area")
    def area(self) -> Float64: ...

class Box(Base_Shape):
    def __init__(
        self,
        *,
        width: Float64 = ...
    ) -> None: ...

    width: Float64

    @bind("box_area")
    def area(self) -> Float64: ...

def base_area(
    self: Annotated[Base_Shape, Polymorphic]
) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def base_set_size(
    self: Annotated[Base_Shape, Polymorphic],
    value: Float64
) -> None: ...

def circle_area(
    self: Annotated[Circle, Polymorphic]
) -> Float64: ...

def box_area(
    self: Annotated[Box, Polymorphic]
) -> Float64: ...

def describe_shape(
    item: Annotated[Base_Shape, Polymorphic]
) -> Float64: ...

__all__ = ["Base_Shape", "Circle", "Box", "base_area", "base_set_size", "circle_area", "box_area", "describe_shape"]
