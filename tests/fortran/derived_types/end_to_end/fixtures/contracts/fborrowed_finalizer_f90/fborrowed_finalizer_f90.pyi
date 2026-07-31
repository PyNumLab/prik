from x2py.contracts import Int32, native_type

@native_type(finalizers=('cleanup_child',))
class child:
    pass

class parent:
    def __init__(self) -> None: ...

    value: child

def get_final_count() -> Int32: ...

def reset_final_count() -> None: ...
