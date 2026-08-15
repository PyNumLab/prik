from prik.contracts import Allocatable, Annotated, Destruction, Float64, Int32, Ownership, Pointer, PointerAssociation, Returns, Transfer, native_abi

@native_abi("c")
def direct_optional_state(
    values: Allocatable[Float64[:]] | None = ...
) -> Int32: ...

@native_abi("c")
def direct_allocate(
    values: Allocatable[Float64[:]]
) -> Returns["values", Allocatable[Float64[:]]]: ...

@native_abi("c")
def direct_pointer_sum(
    values: Annotated[Pointer[Float64[:]], PointerAssociation("runtime"), Ownership("caller"), Transfer("call_local"), Destruction("none")]
) -> Float64: ...
