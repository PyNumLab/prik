#ifndef X2PY_GENERAL_C_RICHER_FEATURES_H
#define X2PY_GENERAL_C_RICHER_FEATURES_H

#include <stddef.h>

#define X2PY_API(ret) ret
#define X2PY_STRINGIFY(value) #value

#ifdef X2PY_ENABLE_FAST_PATH
int x2py_fast_path(void);
#else
int x2py_slow_path(void);
#endif

typedef int (*x2py_compare_fn)(const void *left, const void *right);

enum x2py_status {
    X2PY_STATUS_OK = 0,
    X2PY_STATUS_RETRY = 1,
    X2PY_STATUS_ERROR = -1
};

union x2py_scalar {
    int i32;
    unsigned long u64;
    double f64;
};

struct x2py_flags {
    unsigned ready : 1;
    unsigned mode : 3;
    unsigned reserved : 28;
};

struct x2py_context;
typedef struct x2py_context *x2py_context_handle;

/* Raw mode must defer this macro-shaped declaration. It is a future supported
   case only after compiler preprocessing expands X2PY_API into ordinary C. */
X2PY_API(int) x2py_sort(
    void *items,
    size_t count,
    size_t item_size,
    x2py_compare_fn compare
);

int x2py_register_callback(
    x2py_context_handle context,
    void (*callback)(void *userdata, enum x2py_status status),
    void *userdata
);

const char *x2py_status_message(enum x2py_status status);
void x2py_fill_matrix(size_t rows, size_t cols, double matrix[static rows][cols]);

#undef X2PY_API

#endif
