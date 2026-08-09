from prik.contracts import Addr, Arg, Int32, Returns, native_call, standalone

@standalone
@native_call([Addr(Arg(0))])
def add_one(
    value: Int32
) -> tuple[Int32, Returns["value", Int32]]: ...
