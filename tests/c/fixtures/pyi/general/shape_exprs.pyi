from x2py.contracts import Final, Float32, Int, Int32

X2PY_EXPR_N0: Final[Int32] = 4

X2PY_EXPR_N1: Final[Int32] = X2PY_EXPR_N0 + 2

X2PY_EXPR_A: Final[Int32] = 8

X2PY_EXPR_B: Final[Int32] = 3

X2PY_EXPR_C: Final[Int32] = 2

def fill_grid(
    x: Int[1, 4 + 2]
) -> None: ...

def update_plane(
    n: Int,
    x: Float32[1, n]
) -> None: ...

def use_expr(
    x: Int[4 + 2],
    y: Float32[4 * 2]
) -> None: ...

def all_exprs(
    x1: Int[8 + 3],
    x2: Int[8 - 3],
    x3: Int[3 * 2],
    x4: Int[8 / 2],
    x5: Int[1 << 3],
    x6: Int[(8 + 3) * 2 - 1],
    x7: Int[-(-8 + 3)],
    x8: Int[(8 + 3) * (2 + 1) - 1],
    x9: Int[(8 - 3) * (8 - 2)]
) -> None: ...
