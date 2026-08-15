from prik.contracts import Arg, Int32, Returns, String, Value, native_abi, native_call

@native_abi("c")
@native_call([Value(Arg(0))])
def direct_char_code(
    ch: String[1]
) -> Int32: ...

@native_abi("c")
def direct_uppercase(
    ch: String[1]
) -> Returns["ch", String[1]]: ...

@native_abi("c")
def direct_buffer_sum(
    n: Int32,
    text: String[1][n]
) -> Int32: ...

@native_abi("c")
def direct_uppercase_buffer(
    n: Int32,
    text: String[1][n]
) -> None: ...
