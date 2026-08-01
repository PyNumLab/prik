#ifndef PRIK_GENERAL_SHAPE_EXPRS_H
#define PRIK_GENERAL_SHAPE_EXPRS_H

#define PRIK_EXPR_N0 4
#define PRIK_EXPR_N1 (PRIK_EXPR_N0 + 2)
#define PRIK_EXPR_A 8
#define PRIK_EXPR_B 3
#define PRIK_EXPR_C 2

void fill_grid(int x[static 1][PRIK_EXPR_N1]);
void update_plane(int n, float x[static 1][n]);

void use_expr(
    int x[static PRIK_EXPR_N1],
    float y[static PRIK_EXPR_N0 * 2]
);

void all_exprs(
    int x1[static PRIK_EXPR_A + PRIK_EXPR_B],
    int x2[static PRIK_EXPR_A - PRIK_EXPR_B],
    int x3[static PRIK_EXPR_B * PRIK_EXPR_C],
    int x4[static PRIK_EXPR_A / PRIK_EXPR_C],
    int x5[static 1 << PRIK_EXPR_B],
    int x6[static (PRIK_EXPR_A + PRIK_EXPR_B) * PRIK_EXPR_C - 1],
    int x7[static -(-PRIK_EXPR_A + PRIK_EXPR_B)],
    int x8[static (PRIK_EXPR_A + PRIK_EXPR_B) * (PRIK_EXPR_C + 1) - 1],
    int x9[static (PRIK_EXPR_A - PRIK_EXPR_B) * (PRIK_EXPR_A - PRIK_EXPR_C)]
);

#endif
