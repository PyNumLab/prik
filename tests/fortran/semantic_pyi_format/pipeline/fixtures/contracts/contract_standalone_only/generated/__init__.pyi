from prik.contracts import Addr, Arg, Int32, native_call, standalone

@standalone
def standalone_ping() -> None: ...

@standalone
@native_call([Addr(Arg(0))])
def standalone_double(
    value: Int32
) -> Int32: ...
