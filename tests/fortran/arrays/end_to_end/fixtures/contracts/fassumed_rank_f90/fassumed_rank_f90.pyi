from prik.contracts import Allocatable, Annotated, Float64, Int32, Pointer, PointerAssociation

def allocatable_handle() -> Allocatable[Float64[:]]: ...

def pointer_handle() -> Annotated[Pointer[Float64[:]], PointerAssociation("runtime")]: ...

def optional_rank(
    values: Float64[...] = ...
) -> Int32: ...

def rank_weighted_sum(
    values: Float64[...]
) -> Float64: ...

def bump_assumed_rank(
    values: Float64[...]
) -> None: ...

def rank_pair_score(
    left: Float64[...],
    right: Float64[...]
) -> Int32: ...

__all__ = [
    "allocatable_handle",
    "pointer_handle",
    "optional_rank",
    "rank_weighted_sum",
    "bump_assumed_rank",
    "rank_pair_score",
]
