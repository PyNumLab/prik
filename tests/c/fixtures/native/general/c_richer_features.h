#ifndef PRIK_GENERAL_C_RICHER_FEATURES_H
#define PRIK_GENERAL_C_RICHER_FEATURES_H

#include <stddef.h>

#define PRIK_API(ret) ret
#define PRIK_STRINGIFY(value) #value

#ifdef PRIK_ENABLE_FAST_PATH
int prik_fast_path(void);
#else
int prik_slow_path(void);
#endif

typedef int (*prik_compare_fn)(const void *left, const void *right);

enum prik_status {
    PRIK_STATUS_OK = 0,
    PRIK_STATUS_RETRY = 1,
    PRIK_STATUS_ERROR = -1
};

union prik_scalar {
    int i32;
    unsigned long u64;
    double f64;
};

struct prik_flags {
    unsigned ready : 1;
    unsigned mode : 3;
    unsigned reserved : 28;
};

struct prik_context;
typedef struct prik_context *prik_context_handle;

/* Raw mode must defer this macro-shaped declaration. It is a future supported
   case only after compiler preprocessing expands PRIK_API into ordinary C. */
PRIK_API(int) prik_sort(
    void *items,
    size_t count,
    size_t item_size,
    prik_compare_fn compare
);

int prik_register_callback(
    prik_context_handle context,
    void (*callback)(void *userdata, enum prik_status status),
    void *userdata
);

const char *prik_status_message(enum prik_status status);
void prik_fill_matrix(size_t rows, size_t cols, double matrix[static rows][cols]);

#undef PRIK_API

#endif
