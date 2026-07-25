from x2py.contracts import Addr, Arg, Bool, Complex64, Float32, Int32, Returns, String, native_call, overload

class same_name:
    def __init__(
        self,
        *,
        payload: Int32 = ...
    ) -> None: ...

    payload: Int32

same_name_i: Int32

same_name_r: Float32

same_name_l: Bool

same_name_c: Complex64

same_name_s: String[8]

@native_call([Addr(Arg(0))])
def do_work_i(
    same_name: Int32
) -> Returns["same_name", Int32]: ...

@native_call([Addr(Arg(0))])
def do_work_r(
    same_name: Float32
) -> None: ...

@native_call([Addr(Arg(0))])
def do_work_l(
    same_name: Bool
) -> None: ...

@native_call([Addr(Arg(0))])
def host_one(
    same_name: Int32
) -> Returns["same_name", Int32]: ...

@native_call([Addr(Arg(0))])
def host_two(
    same_name: Float32
) -> Returns["same_name", Float32]: ...

@native_call([Addr(Arg(0))])
def convert_to_complex(
    same_name: Int32
) -> Complex64: ...

@native_call([Addr(Arg(0))])
def convert_to_char(
    same_name: Float32
) -> String[16]: ...

def convert_to_logical(
    same_name: String
) -> Bool: ...

@overload("do_work_i")
def do_work(
    same_name: Int32
) -> Returns["same_name", Int32]: ...

@overload("do_work_r")
def do_work(
    same_name: Float32
) -> None: ...

@overload("do_work_l")
def do_work(
    same_name: Bool
) -> None: ...
