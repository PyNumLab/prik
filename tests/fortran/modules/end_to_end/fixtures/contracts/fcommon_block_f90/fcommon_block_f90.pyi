from x2py.contracts import Addr, Arg, Int32, native_call

@native_call([Addr(Arg(0))])
def write_shared(
    value: Int32
) -> None: ...

def read_shared() -> Int32: ...
