from x2py.contracts import Addr, Arg, Bool, Float64, Int32, Pass, Returns, bind, native_call, overload, private

class vector:
    def __init__(
        self,
        *,
        value: Float64 = 0.0
    ) -> None: ...

    value: Float64 = 0.0

    @overload("add_vectors")
    def __add__(
        self,
        right: vector
    ) -> vector: ...

    @overload("add_vector_integer")
    def __add__(
        self,
        right: Int32
    ) -> vector: ...

    @overload("add_vector_real")
    def __add__(
        self,
        right: Float64
    ) -> vector: ...

    @overload("add_real_vector")
    def __radd__(
        self,
        left: Float64
    ) -> vector: ...

    @overload("add_vector_array")
    def __add__(
        self,
        right: Float64[::]
    ) -> vector: ...

    @overload("add_vector_offset")
    def __add__(
        self,
        right: offset
    ) -> vector: ...

    @overload("positive_vector")
    def __pos__(self) -> vector: ...

    @overload("subtract_vector_real")
    def __sub__(
        self,
        right: Float64
    ) -> vector: ...

    @overload("subtract_real_vector")
    def __rsub__(
        self,
        left: Float64
    ) -> vector: ...

    @overload("negative_vector")
    def __neg__(self) -> vector: ...

    @overload("multiply_vector_real")
    def __mul__(
        self,
        right: Float64
    ) -> vector: ...

    @overload("divide_vector_real")
    def __truediv__(
        self,
        right: Float64
    ) -> vector: ...

    @overload("power_vector_integer")
    def __pow__(
        self,
        right: Int32
    ) -> vector: ...

    @overload("equal_vectors")
    def __eq__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("equivalent_vector_offset", generic="operator(.eqv.)")
    def __eq__(
        self,
        right: offset
    ) -> Bool: ...

    @overload("not_equal_vectors")
    def __ne__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("not_equivalent_vector_integer", generic="operator(.neqv.)")
    def __ne__(
        self,
        right: Int32
    ) -> Bool: ...

    @overload("less_vectors")
    def __lt__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("less_vector_real")
    def __lt__(
        self,
        right: Float64
    ) -> Bool: ...

    @overload("less_real_vector")
    def __gt__(
        self,
        left: Float64
    ) -> Bool: ...

    @overload("greater_vectors")
    def __gt__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("less_equal_vectors")
    def __le__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("greater_equal_vectors")
    def __ge__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("and_vectors")
    def __and__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("or_vectors")
    def __or__(
        self,
        right: vector
    ) -> Bool: ...

    @overload("not_vector")
    def __invert__(self) -> Bool: ...

    @overload("dot_vectors")
    def operator_dot(
        self,
        right: vector
    ) -> Float64: ...

    @overload("shift_real_vector")
    def r_operator_shift(
        self,
        left: Float64
    ) -> vector: ...

    @overload("assign_vector_integer")
    def assign(
        self,
        right: Int32
    ) -> vector: ...

    @overload("assign_vector_real")
    def assign(
        self,
        right: Float64
    ) -> vector: ...

class offset:
    def __init__(
        self,
        *,
        value: Float64 = 0.0
    ) -> None: ...

    value: Float64 = 0.0

    @overload("add_vector_offset")
    def __radd__(
        self,
        left: vector
    ) -> vector: ...

    @overload("equivalent_vector_offset", generic="operator(.eqv.)")
    def __eq__(
        self,
        left: vector
    ) -> Bool: ...

class counter:
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
    ) -> counter: ...

    @overload("counter_add_integer")
    def __add__(
        self,
        right: Int32
    ) -> counter: ...

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
    left: vector,
    right: vector
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def add_vector_integer(
    left: vector,
    right: Int32
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def add_vector_real(
    left: vector,
    right: Float64
) -> vector: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def add_real_vector(
    left: Float64,
    right: vector
) -> vector: ...

@private
def add_vector_array(
    left: vector,
    right: Float64[::]
) -> vector: ...

@private
def add_vector_offset(
    left: vector,
    right: offset
) -> vector: ...

@private
def positive_vector(
    value: vector
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def subtract_vector_real(
    left: vector,
    right: Float64
) -> vector: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def subtract_real_vector(
    left: Float64,
    right: vector
) -> vector: ...

@private
def negative_vector(
    value: vector
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def multiply_vector_real(
    left: vector,
    right: Float64
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def divide_vector_real(
    left: vector,
    right: Float64
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def power_vector_integer(
    left: vector,
    right: Int32
) -> vector: ...

@private
def equal_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def not_equal_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def less_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def less_vector_real(
    left: vector,
    right: Float64
) -> Bool: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def less_real_vector(
    left: Float64,
    right: vector
) -> Bool: ...

@private
def less_equal_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def greater_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def greater_equal_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def and_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def or_vectors(
    left: vector,
    right: vector
) -> Bool: ...

@private
def not_vector(
    value: vector
) -> Bool: ...

@private
def equivalent_vector_offset(
    left: vector,
    right: offset
) -> Bool: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def not_equivalent_vector_integer(
    left: vector,
    right: Int32
) -> Bool: ...

@private
def dot_vectors(
    left: vector,
    right: vector
) -> Float64: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def shift_real_vector(
    left: Float64,
    right: vector
) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_integer(
    left: vector,
    right: Int32
) -> Returns["left", vector]: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_real(
    left: vector,
    right: Float64
) -> Returns["left", vector]: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def counter_add_integer(
    self: counter,
    right: Int32
) -> counter: ...

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
