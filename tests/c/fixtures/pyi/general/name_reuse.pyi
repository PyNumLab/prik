from prik.contracts import Bool, CStruct, Complex128, Float32, Int, Int8

class same_name(CStruct):
    payload: Int

same_name_i: Int

same_name_r: Float32

same_name_l: Bool

same_name_c: Complex128

same_name_s: Int8[8]

def do_work_i(
    same_name: Int[...]
) -> None: ...

def do_work_r(
    same_name: Float32
) -> None: ...

def do_work_l(
    same_name: Bool,
    shared: same_name
) -> None: ...

def convert_to_complex(
    same_name: Int
) -> Complex128: ...

def convert_to_string(
    same_name: Float32,
    shared: Int8[16]
) -> Int: ...

def convert_to_logical(
    same_name: Int8[...]
) -> Bool: ...
