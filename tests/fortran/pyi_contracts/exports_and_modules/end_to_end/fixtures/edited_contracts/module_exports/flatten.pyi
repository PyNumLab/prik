# Intentional difference: flatten the non-colliding public names.
from prik.contracts import Int32, external
from .module1 import *
from .module2 import *

@external
def standalone() -> Int32: ...
