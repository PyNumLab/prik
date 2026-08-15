from prik.contracts import Addr, Arg, Int32, Return, Returns, Value, native_abi, native_call, nogil, raises

@native_abi("c")
@raises(status="status", success=0)
@nogil
@native_call([Value(Arg(0)), Return("output", 0), Return("status", 1)])
def direct_solve(
    value: Int32
) -> tuple[Int32, Returns["status", Int32]]: ...

@raises(status="status", success=0)
@nogil
@native_call([Addr(Arg(0)), Return("output", 0), Return("status", 1)])
def adapted_solve(
    value: Int32
) -> tuple[Int32, Returns["status", Int32]]: ...
