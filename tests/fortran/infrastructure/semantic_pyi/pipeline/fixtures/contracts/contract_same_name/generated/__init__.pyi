from prik.contracts import standalone
from . import contract_same_name

@standalone
def external_ping() -> None: ...
