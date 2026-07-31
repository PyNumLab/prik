from x2py.contracts import Addr, Any, CStruct, CUnion, Final, Float64, Int, Int8, Opaque, SizeT, UInt32, UInt64

class x2py_flags(CStruct):
    ready: UInt32
    mode: UInt32
    reserved: UInt32

class x2py_context(CStruct, Opaque):
    pass

class x2py_scalar(CUnion):
    i32: Int
    u64: UInt64
    f64: Float64

X2PY_STATUS_OK: Final[Int] = 0

X2PY_STATUS_RETRY: Final[Int] = 1

X2PY_STATUS_ERROR: Final[Int] = -1

def x2py_slow_path() -> Int: ...

def x2py_sort(
    items: Any,
    count: SizeT,
    item_size: SizeT,
    compare: CFunctionPointer
) -> Int: ...

def x2py_register_callback(
    context: x2py_context,
    callback: CFunctionPointer,
    userdata: Any
) -> Int: ...

def x2py_status_message(
    status: Int
) -> Addr(Int8): ...

def x2py_fill_matrix(
    rows: SizeT,
    cols: SizeT,
    matrix: Float64[rows, cols]
) -> None: ...
