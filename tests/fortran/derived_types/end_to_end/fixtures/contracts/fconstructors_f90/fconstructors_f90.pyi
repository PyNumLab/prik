from x2py.contracts import Float64, Int32, native_type

@native_type(finalizers=('cleanup_initialized',))
class initialized:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5

def get_final_count() -> Int32: ...

def reset_final_count() -> None: ...
