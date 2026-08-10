from prik.contracts import Int32, standalone as prik_standalone
from . import module1
from . import module2

@prik_standalone
def standalone() -> Int32: ...
