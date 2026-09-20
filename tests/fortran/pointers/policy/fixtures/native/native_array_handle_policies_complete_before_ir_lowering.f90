values: Allocatable[Float64[:]]
target_values: Annotated[Allocatable[Float64[:]], Aliased]

class box:
    values: Allocatable[Float64[:]]
    target: Pointer[Float64[:]]

def consume(
    values: Allocatable[Float64[:]],
    managed_target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="caller",
            lifetime="call",
            deallocation="deallocate_resize",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="allocate_resize",
            aliasing="descriptor",
            mutability="mutable",
        ),
    ],
    maybe_target: Pointer[Float64[:]] | None = ...,
) -> None: ...

def make_values() -> Allocatable[Float64[:]]: ...
def make_target() -> Pointer[Float64[:]]: ...
