from x2py.contracts import Arg, Float64, native_call

@native_call([Arg(1)])
def scale(value: Float64) -> Float64: ...
