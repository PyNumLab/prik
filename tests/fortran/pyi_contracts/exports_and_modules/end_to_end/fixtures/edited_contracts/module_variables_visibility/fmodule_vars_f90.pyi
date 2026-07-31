# Intentional difference: hide scale and scaled_counter, and remove next_local.
from x2py.contracts import Final, Float64, Int32, private

nmax: Final[Int32] = 12

counter: Int32 = 9

scale: private[Float64]

saved_counter: Int32

def summarize() -> Int32: ...

@private
def scaled_counter() -> Float64: ...
