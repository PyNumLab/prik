from x2py.contracts import Addr, Arg, Int32, external, native_call

@external
def standalone_ping() -> None: ...

@external
@native_call([Addr(Arg(0))])
def standalone_double(
    value: Int32
) -> Int32: ...
