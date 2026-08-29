from prik.contracts import Arg, Float64, Return, String, bind, native_call

@bind("select_value")
@native_call([String[1]("L"), Arg(0), Arg(1), Return("chosen", 0)])
def take_left(left: Float64, right: Float64) -> Float64: ...

@bind("select_value")
@native_call([String[1]("R"), Arg(0), Arg(1), Return("chosen", 0)])
def take_right(left: Float64, right: Float64) -> Float64: ...
