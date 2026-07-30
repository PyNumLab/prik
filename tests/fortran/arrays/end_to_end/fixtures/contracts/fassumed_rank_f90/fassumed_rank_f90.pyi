from x2py.contracts import Float64, Int32

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
