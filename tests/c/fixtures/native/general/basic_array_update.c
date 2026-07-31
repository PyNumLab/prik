#include "basic_array_update.h"

void add1(int n, double x[static 1])
{
    for (int i = 0; i < n; ++i) {
        x[i] += 1.0;
    }
}

void add1_strided(int n, double *restrict x, int incx)
{
    for (int i = 0; i < n; ++i) {
        x[i * incx] += 1.0;
    }
}
