#ifndef X2PY_GENERAL_SHAPE_EXPRS_H
#define X2PY_GENERAL_SHAPE_EXPRS_H

#define X2PY_EXPR_N0 4
#define X2PY_EXPR_N1 (X2PY_EXPR_N0 + 2)
#define X2PY_EXPR_A 8
#define X2PY_EXPR_B 3
#define X2PY_EXPR_C 2

void fill_grid(int x[static 1][X2PY_EXPR_N1]);
void update_plane(int n, float x[static 1][n]);

void use_expr(
    int x[static X2PY_EXPR_N1],
    float y[static X2PY_EXPR_N0 * 2]
);

void all_exprs(
    int x1[static X2PY_EXPR_A + X2PY_EXPR_B],
    int x2[static X2PY_EXPR_A - X2PY_EXPR_B],
    int x3[static X2PY_EXPR_B * X2PY_EXPR_C],
    int x4[static X2PY_EXPR_A / X2PY_EXPR_C],
    int x5[static 1 << X2PY_EXPR_B],
    int x6[static (X2PY_EXPR_A + X2PY_EXPR_B) * X2PY_EXPR_C - 1],
    int x7[static -(-X2PY_EXPR_A + X2PY_EXPR_B)],
    int x8[static (X2PY_EXPR_A + X2PY_EXPR_B) * (X2PY_EXPR_C + 1) - 1],
    int x9[static (X2PY_EXPR_A - X2PY_EXPR_B) * (X2PY_EXPR_A - X2PY_EXPR_C)]
);

#endif
