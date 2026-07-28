from x2py.contracts import Addr, Arg, Bool, Float32, Float64, Returns, bind, native_call, overload

@bind("SISNAN")
@native_call([Addr(Arg(0))])
def sisnan(
    x: Float32
) -> tuple[Bool, Returns["x", Float32]]: ...

@bind("DISNAN")
@native_call([Addr(Arg(0))])
def disnan(
    x: Float64
) -> tuple[Bool, Returns["x", Float64]]: ...

@overload("SISNAN")
def la_isnan(
    x: Float32
) -> tuple[Bool, Returns["x", Float32]]: ...

@overload("DISNAN")
def la_isnan(
    x: Float64
) -> tuple[Bool, Returns["x", Float64]]: ...
