# Intentional difference: select an added binding, alias two exports, and rename a standalone procedure.
from prik.contracts import Int32, bind, standalone
from . import facade as m2
from .module1 import solve, update as update_module1
from .module2 import update as update_module2

@standalone
@bind("standalone")
def renamed_standalone() -> Int32: ...
