from prik.contracts import Int32, Returns, String, bind, standalone

@bind("CHAR_CODE_DEFAULT")
@standalone
def char_code_default(
    C: String[1]
) -> tuple[Int32, Returns["C", String[1]]]: ...

@bind("CHAR_CODE_STAR1")
@standalone
def char_code_star1(
    C: String[1]
) -> tuple[Int32, Returns["C", String[1]]]: ...

@bind("STRING_LEN_STAR8")
@standalone
def string_len_star8(
    TEXT: String[8]
) -> tuple[Int32, Returns["TEXT", String[8]]]: ...

@bind("STRING_LEN_ASSUMED")
@standalone
def string_len_assumed(
    TEXT: String
) -> tuple[Int32, Returns["TEXT", String]]: ...

@bind("STRING_LEN_ENTITY")
@standalone
def string_len_entity(
    TEXT: String[6]
) -> tuple[Int32, Returns["TEXT", String[6]]]: ...

@bind("CHAR_RESULT_DEFAULT")
@standalone
def char_result_default() -> String[1]: ...

@bind("STRING_RESULT_STAR8")
@standalone
def string_result_star8() -> String[8]: ...

@bind("STRING_RESULT_PADDED")
@standalone
def string_result_padded() -> String[8]: ...

@bind("STRING_RESULT_DECLARED")
@standalone
def string_result_declared() -> String[6]: ...
