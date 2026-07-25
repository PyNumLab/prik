from x2py.contracts import Addr, Arg, Complex128, Float64, Int32, Pass, bind, native_call, overload, private

class accumulator:
    def __init__(
        self,
        *,
        total: Float64 = 0.0
    ) -> None: ...

    total: Float64 = 0.0

    @private
    @bind("accumulator_add_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def add_integer(
        self,
        value: Int32
    ) -> None: ...

    @private
    @bind("accumulator_add_real")
    @native_call([Pass(), Addr(Arg(0))])
    def add_real(
        self,
        value: Float64
    ) -> None: ...

    @overload("accumulator_add_integer")
    def add(
        self,
        value: Int32
    ) -> None: ...

    @overload("accumulator_add_real")
    def add(
        self,
        value: Float64
    ) -> None: ...

class sample:
    def __init__(
        self,
        *,
        value: Float64 = 0.0
    ) -> None: ...

    value: Float64 = 0.0

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
@native_call([Addr(Arg(0))])
def convert_complex(
    value: Complex128
) -> Complex128: ...

@private
@native_call([Addr(Arg(0))])
def summarize_scalar(
    value: Float64
) -> Float64: ...

@private
def summarize_vector(
    values: Float64[::]
) -> Float64: ...

@private
def inspect_accumulator(
    value: accumulator
) -> Float64: ...

@private
def inspect_sample(
    value: sample
) -> Float64: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_integer(
    self: accumulator,
    value: Int32
) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_real(
    self: accumulator,
    value: Float64
) -> None: ...

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

@bind("convert")
@overload("convert_complex")
def convert(
    value: Complex128
) -> Complex128: ...

@bind("summarize")
@overload("summarize_scalar")
def summarize(
    value: Float64
) -> Float64: ...

@bind("summarize")
@overload("summarize_vector")
def summarize(
    values: Float64[::]
) -> Float64: ...

@bind("inspect")
@overload("inspect_accumulator")
def inspect(
    value: accumulator
) -> Float64: ...

@bind("inspect")
@overload("inspect_sample")
def inspect(
    value: sample
) -> Float64: ...
