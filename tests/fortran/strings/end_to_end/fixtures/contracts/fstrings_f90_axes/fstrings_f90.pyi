from x2py.contracts import Allocatable, Int32, Returns, String

def string_len_assumed(
    text: String
) -> Int32: ...

def string_len_fixed(
    text: String[8]
) -> Int32: ...

def fixed_array_extent(
    labels: String[8][:]
) -> Int32: ...

def replace_names(
    names: Allocatable[String[:][:]]
) -> Returns[
    "names", Allocatable[String[:][:]]
]: ...

def rewrite_storage(
    label: String[8][()]
) -> None: ...
