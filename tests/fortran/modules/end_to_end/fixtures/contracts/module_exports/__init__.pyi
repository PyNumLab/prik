from prik.contracts import Int32, external
from . import module1
from . import module2

@external
def standalone() -> Int32: ...
