from prik.contracts import Allocatable, Arg, Int32, Return, Returns, String, native_call

def char_code_default(
    c: String[1]
) -> Int32: ...

def char_code_len1(
    c: String[1]
) -> Int32: ...

def char_code_kind1(
    c: String[1]
) -> Int32: ...

def char_code_c_char(
    c: String[1]
) -> Int32: ...

def string_len_fixed(
    text: String[8]
) -> Int32: ...

def string_len_assumed(
    text: String
) -> Int32: ...

def string_len_c_char(
    text: String[8]
) -> Int32: ...

def char_result_default() -> String[1]: ...

def char_result_c_char() -> String[1]: ...

def string_result_fixed() -> String[8]: ...

def string_result_padded() -> String[8]: ...

def string_result_c_char() -> String[8]: ...

@native_call([Arg(0), Allocatable(Return('value', 0))])
def string_result_deferred(
    text: String
) -> String | None: ...

def fixed_array_extent(
    labels: String[8][::]
) -> Int32: ...

def replace_names(
    names: Allocatable[String[:][:]]
) -> Returns["names", Allocatable[String[:][:]]]: ...

def rewrite_storage(
    label: String[8]
) -> Returns["label", String[8]]: ...
