from prik.contracts import Allocatable, Float64, Returns, native_abi

@native_abi("c")
def direct_allocate(
    values: Allocatable[Float64[:]]
) -> Returns["values", Allocatable[Float64[:]]]: ...

def adapted_sum(
    values: Allocatable[Float64[:]]
) -> Float64: ...
