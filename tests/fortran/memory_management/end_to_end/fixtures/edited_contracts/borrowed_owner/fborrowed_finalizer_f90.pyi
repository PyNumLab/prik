# Intentional difference: the borrowed child states that its containing wrapper
# owns and ultimately finalizes the native instance.
from x2py.contracts import Annotated, Destruction, Int32, Ownership, Transfer, native_type

@native_type(finalizers=('cleanup_child',))
class child:
    pass

class parent:
    def __init__(
        self,
        *,
        value: Annotated[
            child,
            Ownership("wrapper"),
            Transfer("borrowed_view"),
            Destruction("wrapper_dealloc"),
        ] = ...
    ) -> None: ...

    value: Annotated[
        child,
        Ownership("wrapper"),
        Transfer("borrowed_view"),
        Destruction("wrapper_dealloc"),
    ]

def get_final_count() -> Int32: ...

def reset_final_count() -> None: ...
