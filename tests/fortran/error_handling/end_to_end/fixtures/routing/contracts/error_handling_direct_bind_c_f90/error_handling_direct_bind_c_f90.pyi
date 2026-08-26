from prik.contracts import Arg, Hidden, Int32, Return, Value, native_abi, native_call, nogil, raises

@native_abi("c")
@raises(status="status", success=0)
@nogil
@native_call([Value(Arg(0)), Return("output", 0), Hidden("status", Int32)])
def direct_solve(
    value: Int32
) -> Int32: ...
