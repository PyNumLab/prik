#ifndef X2PY_GENERAL_BASIC_ARRAY_UPDATE_H
#define X2PY_GENERAL_BASIC_ARRAY_UPDATE_H

void add1(int n, double x[static 1]);
void add1_strided(int n, double *restrict x, int incx);

#endif
