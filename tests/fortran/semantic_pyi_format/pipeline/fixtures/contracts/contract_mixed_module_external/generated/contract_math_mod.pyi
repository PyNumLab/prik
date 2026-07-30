from x2py.contracts import Addr, Arg, Int32, native_call

@native_call([Addr(Arg(0))])
def module_increment(
    value: Int32
) -> Int32: ...
