# Intentional invalid difference: both wildcard imports export update.
from prik.contracts import Int32, standalone
from .module1 import *
from .module2 import *

@standalone
def standalone() -> Int32: ...
