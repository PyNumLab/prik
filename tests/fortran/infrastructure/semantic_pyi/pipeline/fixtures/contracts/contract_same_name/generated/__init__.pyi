from prik.contracts import standalone
from . import contract_same_name

@standalone
def external_ping() -> None: ...

__all__ = ["contract_same_name", "external_ping"]
