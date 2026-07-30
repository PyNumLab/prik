# Intentional difference: every handle context states its complete owner,
# boundary-transfer, and destruction policy explicitly.
from x2py.contracts import Addr, Aliased, Allocatable, Annotated, Arg, Destruction, Float64, Int32, Ownership, Pass, Return, Transfer, native_call

class buffer:
    def __init__(
        self,
        *,
        values: Annotated[
            Allocatable[Float64[:]],
            Ownership("wrapper"),
            Transfer("borrowed_view"),
            Destruction("wrapper_dealloc"),
        ] = ...
    ) -> None: ...

    values: Annotated[
        Allocatable[Float64[:]],
        Ownership("wrapper"),
        Transfer("borrowed_view"),
        Destruction("wrapper_dealloc"),
    ]

    @native_call([Pass(), Addr(Arg(0))])
    def allocate_values(
        self,
        n: Int32
    ) -> None: ...

    def deallocate_values(self) -> None: ...

    @native_call([Pass(), Addr(Arg(0))])
    def scale_values(
        self,
        scale: Float64
    ) -> None: ...

    def values_sum(self) -> Float64: ...

module_values: Annotated[
    Allocatable[Float64[:]],
    Aliased,
    Ownership("native"),
    Transfer("borrowed_view"),
    Destruction("native_owner"),
]

@native_call([Addr(Arg(0))])
def allocate_module_values(
    n: Int32
) -> None: ...

def deallocate_module_values() -> None: ...

def module_values_sum() -> Float64: ...

@native_call([Addr(Arg(0)), Return('values', 0)])
def build_values(
    n: Int32
) -> Annotated[
    Allocatable[Float64[:]],
    Ownership("wrapper"),
    Transfer("wrapper_instance"),
    Destruction("wrapper_dealloc"),
]: ...
