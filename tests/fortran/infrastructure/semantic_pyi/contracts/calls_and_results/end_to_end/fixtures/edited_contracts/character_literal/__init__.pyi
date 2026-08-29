from prik.contracts import Arg, Float64, String, bind, native_abi, native_call, standalone

from . import fcharacter_literal_f90

@bind("pick_bind_c")
@standalone
@native_abi("c")
@native_call([String[1]("L"), Arg(0), Arg(1)])
def pick_left(left: Float64, right: Float64) -> Float64: ...

@bind("pick_bind_c")
@standalone
@native_abi("c")
@native_call([String[1]("R"), Arg(0), Arg(1)])
def pick_right(left: Float64, right: Float64) -> Float64: ...
