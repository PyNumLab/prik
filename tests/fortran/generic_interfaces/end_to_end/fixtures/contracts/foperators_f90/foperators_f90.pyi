from prik.contracts import Addr, Annotated, Arg, Bool32, Float64, Int32, Pass, Polymorphic, Returns, bind, native_call, overload, private

class Vector:
    def __init__(
        self,
        *,
        value: Float64 = 0.0
    ) -> None: ...

    value: Float64 = 0.0

    @overload("add_vectors")
    def __add__(
        self,
        right: Vector
    ) -> Vector: ...

    @overload("add_vector_integer")
    def __add__(
        self,
        right: Int32
    ) -> Vector: ...

    @overload("add_vector_real")
    def __add__(
        self,
        right: Float64
    ) -> Vector: ...

    @overload("add_real_vector")
    def __radd__(
        self,
        left: Float64
    ) -> Vector: ...

    @overload("add_vector_array")
    def __add__(
        self,
        right: Float64[::]
    ) -> Vector: ...

    @overload("add_vector_offset")
    def __add__(
        self,
        right: Offset
    ) -> Vector: ...

    @overload("positive_vector")
    def __pos__(self) -> Vector: ...

    @overload("subtract_vector_real")
    def __sub__(
        self,
        right: Float64
    ) -> Vector: ...

    @overload("subtract_real_vector")
    def __rsub__(
        self,
        left: Float64
    ) -> Vector: ...

    @overload("negative_vector")
    def __neg__(self) -> Vector: ...

    @overload("multiply_vector_real")
    def __mul__(
        self,
        right: Float64
    ) -> Vector: ...

    @overload("divide_vector_real")
    def __truediv__(
        self,
        right: Float64
    ) -> Vector: ...

    @overload("power_vector_integer")
    def __pow__(
        self,
        right: Int32
    ) -> Vector: ...

    @overload("equal_vectors")
    def __eq__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("equivalent_vector_offset", generic="operator(.eqv.)")
    def __eq__(
        self,
        right: Offset
    ) -> Bool32: ...

    @overload("not_equal_vectors")
    def __ne__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("not_equivalent_vector_integer", generic="operator(.neqv.)")
    def __ne__(
        self,
        right: Int32
    ) -> Bool32: ...

    @overload("less_vectors")
    def __lt__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("less_vector_real")
    def __lt__(
        self,
        right: Float64
    ) -> Bool32: ...

    @overload("less_real_vector")
    def __gt__(
        self,
        left: Float64
    ) -> Bool32: ...

    @overload("greater_vectors")
    def __gt__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("less_equal_vectors")
    def __le__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("greater_equal_vectors")
    def __ge__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("and_vectors")
    def __and__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("or_vectors")
    def __or__(
        self,
        right: Vector
    ) -> Bool32: ...

    @overload("not_vector")
    def __invert__(self) -> Bool32: ...

    @overload("dot_vectors")
    def operator_dot(
        self,
        right: Vector
    ) -> Float64: ...

    @overload("shift_real_vector")
    def r_operator_shift(
        self,
        left: Float64
    ) -> Vector: ...

    @overload("assign_vector_integer")
    def assign(
        self,
        right: Int32
    ) -> Vector: ...

    @overload("assign_vector_real")
    def assign(
        self,
        right: Float64
    ) -> Vector: ...

class Offset:
    def __init__(
        self,
        *,
        value: Float64 = 0.0
    ) -> None: ...

    value: Float64 = 0.0

    @overload("add_vector_offset")
    def __radd__(
        self,
        left: Vector
    ) -> Vector: ...

    @overload("equivalent_vector_offset", generic="operator(.eqv.)")
    def __eq__(
        self,
        left: Vector
    ) -> Bool32: ...

class Counter:
    def __init__(
        self,
        *,
        value: Int32 = 0
    ) -> None: ...

    value: Int32 = 0

    @private
    @bind("counter_add_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def add_integer(
        self,
        right: Int32
    ) -> Counter: ...

    @overload("counter_add_integer")
    def __add__(
        self,
        right: Int32
    ) -> Counter: ...

@private
@native_call([Addr(Arg(0))])
def convert_integer(
    value: Int32
) -> Int32: ...

@private
@native_call([Addr(Arg(0))])
def convert_real(
    value: Float64
) -> Float64: ...

@private
def add_vectors(
    left: Vector,
    right: Vector
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def add_vector_integer(
    left: Vector,
    right: Int32
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def add_vector_real(
    left: Vector,
    right: Float64
) -> Vector: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def add_real_vector(
    left: Float64,
    right: Vector
) -> Vector: ...

@private
def add_vector_array(
    left: Vector,
    right: Float64[::]
) -> Vector: ...

@private
def add_vector_offset(
    left: Vector,
    right: Offset
) -> Vector: ...

@private
def positive_vector(
    value: Vector
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def subtract_vector_real(
    left: Vector,
    right: Float64
) -> Vector: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def subtract_real_vector(
    left: Float64,
    right: Vector
) -> Vector: ...

@private
def negative_vector(
    value: Vector
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def multiply_vector_real(
    left: Vector,
    right: Float64
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def divide_vector_real(
    left: Vector,
    right: Float64
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def power_vector_integer(
    left: Vector,
    right: Int32
) -> Vector: ...

@private
def equal_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def not_equal_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def less_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def less_vector_real(
    left: Vector,
    right: Float64
) -> Bool32: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def less_real_vector(
    left: Float64,
    right: Vector
) -> Bool32: ...

@private
def less_equal_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def greater_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def greater_equal_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def and_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def or_vectors(
    left: Vector,
    right: Vector
) -> Bool32: ...

@private
def not_vector(
    value: Vector
) -> Bool32: ...

@private
def equivalent_vector_offset(
    left: Vector,
    right: Offset
) -> Bool32: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def not_equivalent_vector_integer(
    left: Vector,
    right: Int32
) -> Bool32: ...

@private
def dot_vectors(
    left: Vector,
    right: Vector
) -> Float64: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def shift_real_vector(
    left: Float64,
    right: Vector
) -> Vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_integer(
    left: Vector,
    right: Int32
) -> Returns["left", Vector]: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_real(
    left: Vector,
    right: Float64
) -> Returns["left", Vector]: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def counter_add_integer(
    self: Annotated[Counter, Polymorphic],
    right: Int32
) -> Counter: ...

@bind("convert")
@overload("convert_integer")
def convert(
    value: Int32
) -> Int32: ...

@bind("convert")
@overload("convert_real")
def convert(
    value: Float64
) -> Float64: ...

__all__ = ["Vector", "Offset", "Counter", "convert"]
