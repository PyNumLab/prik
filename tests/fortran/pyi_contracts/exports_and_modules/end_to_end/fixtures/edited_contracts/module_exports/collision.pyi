# Intentional invalid difference: both wildcard imports export update.
from x2py.contracts import Int32, external
from .module1 import *
from .module2 import *

@external
def standalone() -> Int32: ...
