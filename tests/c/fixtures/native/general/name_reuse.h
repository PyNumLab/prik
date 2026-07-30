#ifndef X2PY_GENERAL_NAME_REUSE_H
#define X2PY_GENERAL_NAME_REUSE_H

#include <stdbool.h>

struct same_name {
    int payload;
};

extern int same_name_i;
extern float same_name_r;
extern bool same_name_l;
extern double _Complex same_name_c;
extern char same_name_s[8];

void do_work_i(int *same_name);
void do_work_r(float same_name);
void do_work_l(bool same_name, struct same_name *shared);
double _Complex convert_to_complex(int same_name);
int convert_to_string(float same_name, char shared[static 16]);
bool convert_to_logical(const char *same_name);

#endif
