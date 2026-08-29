from prik.contracts import Arg, Float64, Int32, native_call

@native_call([Int32(Arg(0).shape[0]), Arg(0)])
def fill_vector(values: Float64[:]) -> None: ...
