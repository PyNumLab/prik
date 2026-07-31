from x2py.contracts import external
from . import contract_same_name

@external
def external_ping() -> None: ...
