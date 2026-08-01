#ifndef PRIK_GENERAL_CONSTANTS_H
#define PRIK_GENERAL_CONSTANTS_H

#include <stddef.h>

#define PRIK_GENERAL_NMAX 100
#define PRIK_GENERAL_ORIGIN_RANK 3

typedef int c_int_like;
typedef double c_double_like;

enum coordinate_axis {
    COORD_X = 0,
    COORD_Y = 1,
    COORD_Z = 2
};

extern c_int_like nmax;
extern c_double_like origin[3];
extern const char *coordinate_axis_name(enum coordinate_axis axis);
size_t coordinate_axis_count(void);

#endif
