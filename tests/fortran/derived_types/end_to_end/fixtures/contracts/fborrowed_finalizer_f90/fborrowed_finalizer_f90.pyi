from prik.contracts import Int32, destroy

class Child:
    @destroy
    def cleanup_child(self) -> None: ...

class Parent:
    def __init__(self) -> None: ...

    value: Child

def get_final_count() -> Int32: ...

def reset_final_count() -> None: ...

__all__ = ["Child", "Parent", "get_final_count", "reset_final_count"]
