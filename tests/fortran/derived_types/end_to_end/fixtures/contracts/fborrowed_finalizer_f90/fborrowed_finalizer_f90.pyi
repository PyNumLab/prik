from prik.contracts import Int32, destroy

class child:
    @destroy
    def cleanup_child(self) -> None: ...

class parent:
    def __init__(self) -> None: ...

    value: child

def get_final_count() -> Int32: ...

def reset_final_count() -> None: ...

__all__ = ["child", "parent", "get_final_count", "reset_final_count"]
