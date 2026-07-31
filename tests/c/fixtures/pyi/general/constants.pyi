from x2py.contracts import Addr, Final, Float64, Int, Int32, Int8, SizeT

COORD_X: Final[Int] = 0

COORD_Y: Final[Int] = 1

COORD_Z: Final[Int] = 2

X2PY_GENERAL_NMAX: Final[Int32] = 100

X2PY_GENERAL_ORIGIN_RANK: Final[Int32] = 3

nmax: Int

origin: Float64[3]

def coordinate_axis_name(
    axis: Int
) -> Addr(Int8): ...

def coordinate_axis_count() -> SizeT: ...
