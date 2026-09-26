from prik.contracts import Addr, Annotated, Arg, Int32, SourceName, bind, native_call

class Visible_T:
    def __init__(
        self,
        *,
        lambda_: Annotated[Int32, SourceName("lambda")] = 3,
        lambda__2: Annotated[Int32, SourceName("lambda_")] = 4
    ) -> None: ...

    lambda_: Annotated[Int32, SourceName("lambda")] = 3
    lambda__2: Annotated[Int32, SourceName("lambda_")] = 4

    @bind("Visible_T.from")
    def from_(self) -> Int32: ...

value: Int32[()]

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

__all__ = ["Visible_T", "value", "lambda_", "lambda__2", "get_value"]
