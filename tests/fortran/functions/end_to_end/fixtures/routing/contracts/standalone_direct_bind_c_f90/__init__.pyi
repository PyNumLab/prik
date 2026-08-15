from prik.contracts import Arg, Int32, Return, bind, native_abi, native_call, standalone

@native_abi("c")
@bind("standalone_direct_symbol")
@standalone
def standalone_direct(
    value: Int32
) -> Int32: ...

@native_abi("c")
@standalone
@native_call([Arg(0), Return('output', 0)])
def standalone_output(
    value: Int32
) -> Int32: ...
