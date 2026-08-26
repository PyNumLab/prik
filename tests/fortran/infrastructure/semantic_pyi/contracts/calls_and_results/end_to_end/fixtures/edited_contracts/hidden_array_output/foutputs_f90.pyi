from prik.contracts import Addr, Arg, Float64, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("values", 0)])
def fill_vector(n: Int32) -> Float64[n]: ...
