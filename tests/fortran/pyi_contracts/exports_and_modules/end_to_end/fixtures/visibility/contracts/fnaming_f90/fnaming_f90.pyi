from x2py.contracts import Addr, Annotated, Arg, Int32, SourceName, bind, native_call

class visible_t:
    def __init__(
        self,
        *,
        lambda_: Annotated[Int32, SourceName("lambda")] = 3,
        lambda__2: Annotated[Int32, SourceName("lambda_")] = 4
    ) -> None: ...

    lambda_: Annotated[Int32, SourceName("lambda")] = 3
    lambda__2: Annotated[Int32, SourceName("lambda_")] = 4

    @bind("visible_from")
    def from_(self) -> Int32: ...

value: Int32

@bind("lambda")
@native_call([Addr(Arg(0))])
def lambda_(
    value: Int32
) -> Int32: ...

@bind("lambda_")
@native_call([Addr(Arg(0))])
def lambda__2(
    value: Int32
) -> Int32: ...

def get_value() -> Int32: ...
