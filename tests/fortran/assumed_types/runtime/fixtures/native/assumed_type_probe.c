#define PRIK_BINDING_IMPORT_ARRAY 1
#define PRIK_BINDING_ASSUMED_TYPE 1
#include <Python.h>
#include <stdint.h>
#include <stdbool.h>
#include <complex.h>
#include <stdatomic.h>
#include <ISO_Fortran_binding.h>
#include "prik_binding.h"

static PyObject *describe(PyObject *self, PyObject *object)
{
    prik_assumed_type_actual actual;
    PyObject *result;
    (void)self;
    if (prik_assumed_type_actual_from_object(object, &actual) < 0) return NULL;
    result = Py_BuildValue("(iKni)", actual.cfi_type,
                           (unsigned long long)actual.type_tag,
                           (Py_ssize_t)actual.element_size, actual.rank);
    prik_assumed_type_actual_clear(&actual);
    return result;
}

static PyMethodDef methods[] = {
    {"describe", (PyCFunction)describe, METH_O, "Describe one native actual."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "assumed_type_probe", NULL, -1, methods};

PyMODINIT_FUNC PyInit_assumed_type_probe(void)
{
    import_array();
    return PyModule_Create(&module);
}
