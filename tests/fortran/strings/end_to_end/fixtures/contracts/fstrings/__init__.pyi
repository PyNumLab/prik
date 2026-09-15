from prik.contracts import Int32, Returns, String, standalone

@standalone
def char_code_default(
    C: String[1]
) -> tuple[Int32, Returns["C", String[1]]]: ...

@standalone
def char_code_star1(
    C: String[1]
) -> tuple[Int32, Returns["C", String[1]]]: ...

@standalone
def string_len_star8(
    TEXT: String[8]
) -> tuple[Int32, Returns["TEXT", String[8]]]: ...

@standalone
def string_len_assumed(
    TEXT: String
) -> tuple[Int32, Returns["TEXT", String]]: ...

@standalone
def string_len_entity(
    TEXT: String[6]
) -> tuple[Int32, Returns["TEXT", String[6]]]: ...

@standalone
def char_result_default() -> String[1]: ...

@standalone
def string_result_star8() -> String[8]: ...

@standalone
def string_result_padded() -> String[8]: ...

@standalone
def string_result_declared() -> String[6]: ...
