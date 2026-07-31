from x2py.contracts import Int32, String, bind, external

@bind("CHAR_CODE_DEFAULT")
@external
def char_code_default(
    C: String[1]
) -> Int32: ...

@bind("CHAR_CODE_STAR1")
@external
def char_code_star1(
    C: String[1]
) -> Int32: ...

@bind("STRING_LEN_STAR8")
@external
def string_len_star8(
    TEXT: String[8]
) -> Int32: ...

@bind("STRING_LEN_ASSUMED")
@external
def string_len_assumed(
    TEXT: String
) -> Int32: ...

@bind("STRING_LEN_ENTITY")
@external
def string_len_entity(
    TEXT: String[6]
) -> Int32: ...

@bind("CHAR_RESULT_DEFAULT")
@external
def char_result_default() -> String[1]: ...

@bind("STRING_RESULT_STAR8")
@external
def string_result_star8() -> String[8]: ...

@bind("STRING_RESULT_PADDED")
@external
def string_result_padded() -> String[8]: ...

@bind("STRING_RESULT_DECLARED")
@external
def string_result_declared() -> String[6]: ...
