from prik.contracts import Addr, Any, CStruct, CUnion, Final, Float64, Int, Int8, Opaque, SizeT, UInt32, UInt64

class prik_flags(CStruct):
    ready: UInt32
    mode: UInt32
    reserved: UInt32

class prik_context(CStruct, Opaque):
    pass

class prik_scalar(CUnion):
    i32: Int
    u64: UInt64
    f64: Float64

PRIK_STATUS_OK: Final[Int] = 0

PRIK_STATUS_RETRY: Final[Int] = 1

PRIK_STATUS_ERROR: Final[Int] = -1

def prik_slow_path() -> Int: ...

def prik_sort(
    items: Any,
    count: SizeT,
    item_size: SizeT,
    compare: CFunctionPointer
) -> Int: ...

def prik_register_callback(
    context: prik_context,
    callback: CFunctionPointer,
    userdata: Any
) -> Int: ...

def prik_status_message(
    status: Int
) -> Addr(Int8): ...

def prik_fill_matrix(
    rows: SizeT,
    cols: SizeT,
    matrix: Float64[rows, cols]
) -> None: ...
