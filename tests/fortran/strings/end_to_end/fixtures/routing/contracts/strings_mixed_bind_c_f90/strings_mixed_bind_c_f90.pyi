from prik.contracts import Arg, Int32, String, Value, native_abi, native_call

@native_abi("c")
@native_call([Value(Arg(0))])
def direct_char_code(
    ch: String[1]
) -> Int32: ...

def adapted_fixed_code(
    text: String[4]
) -> Int32: ...
