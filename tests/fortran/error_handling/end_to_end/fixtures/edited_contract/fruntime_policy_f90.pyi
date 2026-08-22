# Intentional difference: exercise runtime policy decorators from an edited contract.
from prik.contracts import Addr, Arg, Hidden, Int32, String, native_call, nogil, raises

@nogil
def pause_for_one_second() -> None: ...

def pause_with_gil() -> None: ...

@raises(status="status", message="message", success=0)
@nogil
@native_call([Addr(Arg(0)), Hidden('status', Int32), Hidden('message', String[32])])
def solve(
    value: Int32
) -> None: ...
