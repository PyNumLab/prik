from prik.contracts import (
    Allocatable,
    Annotated,
    Float64,
    Int32,
    Pointer,
    PointerAssociation,
    PointerPolicy,
)

def alloc_state(values: Allocatable[Float64[:]] | None = ...) -> Int32: ...
def pointer_state(values: Pointer[Float64[:]] | None = ...) -> Int32: ...
def alloc_fill(values: Allocatable[Float64[:]]) -> None: ...
def pointer_bind(
    values: Annotated[
        Pointer[Float64[:]],
        PointerAssociation("runtime"),
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="module",
            lifetime="module",
            deallocation="never",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="native",
            aliasing="borrowed",
            mutability="view",
        ),
    ],
) -> None: ...
