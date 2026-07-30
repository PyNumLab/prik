# Intentional difference: exercise runtime policy decorators from an edited contract.
from x2py.contracts import Addr, Arg, Int32, Return, String, hold_gil, native_call, raises

def pause_for_one_second() -> None: ...

@hold_gil
def pause_with_gil() -> None: ...

@raises(status="status", message="message", success=0)
@native_call([Addr(Arg(0)), Return('status', 0), Return('message', 1)])
def solve(
    value: Int32
) -> tuple[Int32, String[32]]: ...
