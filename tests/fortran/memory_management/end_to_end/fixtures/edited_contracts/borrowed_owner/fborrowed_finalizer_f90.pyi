# Intentional difference: the borrowed child states that its containing wrapper
# owns and ultimately finalizes the native instance.
from prik.contracts import Annotated, Destruction, Int32, Ownership, Transfer, destroy

class child:
    @destroy
    def cleanup_child(self) -> None: ...

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
