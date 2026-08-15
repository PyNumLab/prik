from prik.contracts import Addr, Arg, Bool8, Float64, Int32, Return, bind, native_abi, native_call

@native_abi("c")
@bind("scalar_direct_add")
def renamed_add(
    value: Int32
) -> Int32: ...

@native_abi("c")
@native_call([Addr(Arg(0))])
def reference_add(
    value: Int32
) -> Int32: ...

@native_abi("c")
@native_call([Arg(0), Return('output', 0)])
def scale_output(
    value: Float64
) -> Float64: ...

@native_abi("c")
def invert_flag(
    value: Bool8
) -> Bool8: ...

@native_abi("c")
@native_call([Addr(Arg(0)), Return('state', 0)])
def optional_state(
    value: Float64 = ...
) -> Int32: ...
