from prik.contracts import Addr, Arg, Int32, Return, Returns, native_abi, native_call

@native_abi("c")
@native_call([Addr(Arg(0)), Return('doubled', 1)])
def direct_outputs(
    value: Int32
) -> tuple[Returns["value", Int32], Int32]: ...

@native_call([Addr(Arg(0)), Return('doubled', 1)])
def adapted_outputs(
    value: Int32
) -> tuple[Returns["value", Int32], Int32]: ...
