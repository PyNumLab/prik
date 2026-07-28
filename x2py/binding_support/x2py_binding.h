/* Native mechanics shared by x2py-generated CPython bindings. */

#ifndef X2PY_BINDING_H
#define X2PY_BINDING_H

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <complex.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

#include "numpy_version.h"

#ifndef PY_ARRAY_UNIQUE_SYMBOL
#define PY_ARRAY_UNIQUE_SYMBOL X2PY_BINDING_ARRAY_API
#endif
#ifndef X2PY_BINDING_IMPORT_ARRAY
#define NO_IMPORT_ARRAY
#endif
#include <numpy/arrayobject.h>

#define X2PY_NATIVE_ARRAY_HANDLE_ABI_VERSION 1u
#define X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME "x2py.native_array_handle.v1"
#define X2PY_NATIVE_ARRAY_HANDLE_MAGIC UINT64_C(0x583250594e414831)
#define X2PY_NATIVE_ARRAY_KIND_ALLOCATABLE 1u
#define X2PY_NATIVE_ARRAY_KIND_POINTER 2u

typedef void (*x2py_native_array_release_fn)(void *descriptor);

/*
 * Versioned cross-extension record for one persistent Fortran array
 * descriptor. The descriptor representation remains compiler-owned; this
 * record only makes its metadata, ownership, and validation ABI common to
 * independently generated x2py extensions.
 */
typedef struct {
    uint64_t magic;
    uint32_t abi_version;
    uint32_t struct_size;
    uint32_t descriptor_kind;
    uint32_t rank;
    int32_t cfi_type;
    uint32_t reserved;
    size_t element_size;
    size_t descriptor_size;
    void *descriptor;
    x2py_native_array_release_fn release;
} x2py_native_array_handle;

/* Release descriptor payload and storage at most once while retaining the record. */
static inline void x2py_native_array_handle_release(x2py_native_array_handle *handle)
{
    void *descriptor;

    if (handle == NULL || handle->descriptor == NULL) {
        return;
    }
    descriptor = handle->descriptor;
    handle->descriptor = NULL;
    if (handle->release != NULL) {
        handle->release(descriptor);
    }
    free(descriptor);
}

/* Finalize one native handle record owned by a Python capsule. */
static inline void x2py_native_array_handle_capsule_destructor(PyObject *capsule)
{
    PyObject *error_type = NULL;
    PyObject *error_value = NULL;
    PyObject *error_traceback = NULL;
    x2py_native_array_handle *handle;

    PyErr_Fetch(&error_type, &error_value, &error_traceback);
    handle = (x2py_native_array_handle *)PyCapsule_GetPointer(
        capsule, X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME);
    if (handle == NULL) {
        PyErr_Clear();
    } else {
        x2py_native_array_handle_release(handle);
        handle->magic = 0;
        free(handle);
    }
    PyErr_Restore(error_type, error_value, error_traceback);
}

/*
 * Create a capsule that takes descriptor ownership only on success. The
 * caller remains responsible for descriptor cleanup when this function
 * returns NULL.
 */
static inline PyObject *x2py_native_array_handle_capsule_new(
    uint32_t descriptor_kind,
    uint32_t rank,
    int cfi_type,
    size_t element_size,
    size_t descriptor_size,
    void *descriptor,
    x2py_native_array_release_fn release)
{
    x2py_native_array_handle *handle;
    PyObject *capsule;

    if (descriptor_kind != X2PY_NATIVE_ARRAY_KIND_ALLOCATABLE
        && descriptor_kind != X2PY_NATIVE_ARRAY_KIND_POINTER) {
        PyErr_SetString(PyExc_ValueError, "invalid x2py native array descriptor kind");
        return NULL;
    }
    if (descriptor == NULL || descriptor_size == 0 || element_size == 0 || release == NULL) {
        PyErr_SetString(PyExc_ValueError, "incomplete x2py native array handle storage");
        return NULL;
    }
    handle = (x2py_native_array_handle *)calloc(1, sizeof(*handle));
    if (handle == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    handle->magic = X2PY_NATIVE_ARRAY_HANDLE_MAGIC;
    handle->abi_version = X2PY_NATIVE_ARRAY_HANDLE_ABI_VERSION;
    handle->struct_size = (uint32_t)sizeof(*handle);
    handle->descriptor_kind = descriptor_kind;
    handle->rank = rank;
    handle->cfi_type = (int32_t)cfi_type;
    handle->element_size = element_size;
    handle->descriptor_size = descriptor_size;
    handle->descriptor = descriptor;
    handle->release = release;
    capsule = PyCapsule_New(
        handle,
        X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME,
        x2py_native_array_handle_capsule_destructor);
    if (capsule == NULL) {
        handle->descriptor = NULL;
        handle->magic = 0;
        free(handle);
    }
    return capsule;
}

/* Validate and unwrap one cross-extension native array handle capsule. */
static inline x2py_native_array_handle *x2py_native_array_handle_from_capsule(
    PyObject *capsule,
    uint32_t expected_kind,
    uint32_t expected_rank,
    int expected_cfi_type,
    size_t expected_element_size,
    size_t expected_descriptor_size)
{
    x2py_native_array_handle *handle;

    if (!PyCapsule_IsValid(capsule, X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME)) {
        PyErr_SetString(PyExc_TypeError, "incompatible x2py native array handle capsule");
        return NULL;
    }
    handle = (x2py_native_array_handle *)PyCapsule_GetPointer(
        capsule, X2PY_NATIVE_ARRAY_HANDLE_CAPSULE_NAME);
    if (handle == NULL) {
        return NULL;
    }
    if (handle->magic != X2PY_NATIVE_ARRAY_HANDLE_MAGIC
        || handle->abi_version != X2PY_NATIVE_ARRAY_HANDLE_ABI_VERSION
        || handle->struct_size != sizeof(*handle)) {
        PyErr_SetString(PyExc_TypeError, "incompatible x2py native array handle ABI");
        return NULL;
    }
    if (handle->descriptor_kind != expected_kind) {
        PyErr_SetString(PyExc_TypeError, "x2py native array descriptor kind does not match");
        return NULL;
    }
    if (handle->rank != expected_rank) {
        PyErr_SetString(PyExc_ValueError, "x2py native array descriptor rank does not match");
        return NULL;
    }
    if (handle->cfi_type != expected_cfi_type) {
        PyErr_SetString(PyExc_TypeError, "x2py native array element type does not match");
        return NULL;
    }
    if (expected_element_size != 0 && handle->element_size != expected_element_size) {
        PyErr_SetString(PyExc_TypeError, "x2py native array element size does not match");
        return NULL;
    }
    if (handle->descriptor_size != expected_descriptor_size) {
        PyErr_SetString(PyExc_TypeError, "incompatible Fortran descriptor storage size");
        return NULL;
    }
    if (handle->descriptor == NULL) {
        PyErr_SetString(PyExc_ReferenceError, "x2py native array handle is closed");
        return NULL;
    }
    return handle;
}

/* Return whether value is exactly the NumPy scalar required by numpy_type. */
static inline bool x2py_scalar_matches(PyObject *value, int numpy_type)
{
    switch (numpy_type) {
    case NPY_BOOL:
        return PyBool_Check(value) || PyArray_IsScalar(value, Bool);
    case NPY_INT8:
        return PyArray_IsScalar(value, Int8);
    case NPY_INT16:
        return PyArray_IsScalar(value, Int16);
    case NPY_INT32:
        return PyArray_IsScalar(value, Int);
    case NPY_INT64:
        return PyArray_IsScalar(value, Int64);
    case NPY_FLOAT32:
        return PyArray_IsScalar(value, Float);
    case NPY_FLOAT64:
        return PyArray_IsScalar(value, Double);
    case NPY_COMPLEX64:
        return PyArray_IsScalar(value, CFloat);
    case NPY_COMPLEX128:
        return PyArray_IsScalar(value, CDouble);
    default:
        return false;
    }
}

/* Copy one Python scalar into caller-owned native storage after boundary checks. */
static inline int x2py_scalar_unpack(PyObject *value, int numpy_type, void *destination)
{
    if (destination == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "x2py generated a null scalar destination");
        return -1;
    }

    if (numpy_type == NPY_BOOL) {
        int truth = PyObject_IsTrue(value);
        if (truth < 0) {
            return -1;
        }
        *(bool *)destination = truth != 0;
        return 0;
    }
    if (x2py_scalar_matches(value, numpy_type)) {
        PyArray_ScalarAsCtype(value, destination);
        return PyErr_Occurred() == NULL ? 0 : -1;
    }

    switch (numpy_type) {
    case NPY_INT8:
        *(int8_t *)destination = (int8_t)PyLong_AsLong(value);
        break;
    case NPY_INT16:
        *(int16_t *)destination = (int16_t)PyLong_AsLong(value);
        break;
    case NPY_INT32:
        *(int32_t *)destination = (int32_t)PyLong_AsLong(value);
        break;
    case NPY_INT64:
        *(int64_t *)destination = (int64_t)PyLong_AsLongLong(value);
        break;
    case NPY_FLOAT32:
        *(float *)destination = (float)PyFloat_AsDouble(value);
        break;
    case NPY_FLOAT64:
        *(double *)destination = PyFloat_AsDouble(value);
        break;
    case NPY_COMPLEX64: {
        float real = (float)PyComplex_RealAsDouble(value);
        float imaginary = (float)PyComplex_ImagAsDouble(value);
        *(float complex *)destination = real + imaginary * I;
        break;
    }
    case NPY_COMPLEX128: {
        double real = PyComplex_RealAsDouble(value);
        double imaginary = PyComplex_ImagAsDouble(value);
        *(double complex *)destination = real + imaginary * I;
        break;
    }
    default:
        PyErr_Format(PyExc_TypeError, "unsupported x2py scalar type %d", numpy_type);
        return -1;
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

/* Create a normal Python scalar from native storage. */
static inline PyObject *x2py_scalar_to_python(int numpy_type, const void *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "x2py generated a null scalar value");
        return NULL;
    }

    switch (numpy_type) {
    case NPY_BOOL:
        return PyBool_FromLong(*(const bool *)value);
    case NPY_INT8:
        return PyLong_FromLong(*(const int8_t *)value);
    case NPY_INT16:
        return PyLong_FromLong(*(const int16_t *)value);
    case NPY_INT32:
        return PyLong_FromLong(*(const int32_t *)value);
    case NPY_INT64:
        return PyLong_FromLongLong(*(const int64_t *)value);
    case NPY_FLOAT32:
        return PyFloat_FromDouble(*(const float *)value);
    case NPY_FLOAT64:
        return PyFloat_FromDouble(*(const double *)value);
    case NPY_COMPLEX64: {
        float complex number = *(const float complex *)value;
        return PyComplex_FromDoubles(crealf(number), cimagf(number));
    }
    case NPY_COMPLEX128: {
        double complex number = *(const double complex *)value;
        return PyComplex_FromDoubles(creal(number), cimag(number));
    }
    default:
        PyErr_Format(PyExc_TypeError, "unsupported x2py scalar type %d", numpy_type);
        return NULL;
    }
}

/* Create a NumPy scalar from native storage. */
static inline PyObject *x2py_scalar_to_numpy(int numpy_type, const void *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "x2py generated a null scalar value");
        return NULL;
    }

    PyArray_Descr *descriptor = PyArray_DescrFromType(numpy_type);
    if (descriptor == NULL) {
        return NULL;
    }
    return PyArray_Scalar((void *)value, descriptor, NULL);
}

/* Release a bridge-owned allocation transferred through a NumPy base capsule. */
static inline void x2py_release_owned_memory(PyObject *capsule)
{
    void *memory = PyCapsule_GetPointer(capsule, NULL);
    if (memory == NULL) {
        PyErr_Clear();
        return;
    }
    free(memory);
}

#endif
