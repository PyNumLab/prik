# Intentional difference: select an added binding, alias two exports, and rename an external.
from x2py.contracts import Int32, bind, external
from . import facade as m2
from .module1 import solve, update as update_module1
from .module2 import update as update_module2

@external
@bind("standalone")
def renamed_standalone() -> Int32: ...
