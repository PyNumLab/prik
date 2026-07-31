from x2py.contracts import Addr, Arg, Int32, native_call

class box:
    def __init__(
        self,
        *,
        value: Int32 = ...
    ) -> None: ...

    value: Int32

@native_call([Addr(Arg(0))])
def make_box(
    value: Int32
) -> box: ...
