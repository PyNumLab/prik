from x2py.contracts import Aliased, Allocatable, Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, bind

class pointer_box:
    def __init__(self) -> None: ...

    values: Annotated[
        Pointer[Float64[:]],
        PointerAssociation("runtime"),
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="parent",
            lifetime="parent",
            deallocation="never",
            shape_source="pointer_bounds",
            contiguity="strided",
            reassociation="never",
            aliasing="borrowed",
            mutability="view",
        ),
    ]

    @bind("box_associate_values")
    def associate_values(self) -> None: ...

    @bind("box_associate_values_strided")
    def associate_values_strided(self) -> None: ...

module_storage: Annotated[Float64[5], Aliased]
field_storage: Annotated[Float64[4], Aliased]
module_values: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]
module_allocatable: Annotated[Allocatable[Float64[:]], Aliased]

def associate_module_slice() -> None: ...
def associate_module_contiguous() -> None: ...
def allocate_module_values() -> None: ...

def box_associate_values(self: pointer_box) -> None: ...
def box_associate_values_strided(self: pointer_box) -> None: ...

def sum_values(values: Float64[::]) -> Float64: ...
def sum_pointer_descriptor(values: Pointer[Float64[:]]) -> Float64: ...
def sum_allocatable_descriptor(values: Allocatable[Float64[:]]) -> Float64: ...
