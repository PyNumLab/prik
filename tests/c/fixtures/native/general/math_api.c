#include "math_api.h"

#include <math.h>

double norm2(int n, const double x[static 1])
{
    double accum = 0.0;
    for (int i = 0; i < n; ++i) {
        accum += x[i] * x[i];
    }
    return sqrt(accum);
}

void scale(int n, double alpha, double x[static 1])
{
    for (int i = 0; i < n; ++i) {
        x[i] *= alpha;
    }
}

double dot(int n, const double *restrict x, const double *restrict y)
{
    double accum = 0.0;
    for (int i = 0; i < n; ++i) {
        accum += x[i] * y[i];
    }
    return accum;
}

void fill_identity3(double a[static 3][3])
{
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            a[row][col] = row == col ? 1.0 : 0.0;
        }
    }
}
