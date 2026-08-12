/* Native mechanics shared by prik-generated CPython bindings. */

#ifndef PRIK_BINDING_H
#define PRIK_BINDING_H

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <complex.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

#include "numpy_version.h"

#ifndef PY_ARRAY_UNIQUE_SYMBOL
#define PY_ARRAY_UNIQUE_SYMBOL PRIK_BINDING_ARRAY_API
#endif
#ifndef PRIK_BINDING_IMPORT_ARRAY
#define NO_IMPORT_ARRAY
#endif
#include <numpy/arrayobject.h>

#define PRIK_NATIVE_ARRAY_HANDLE_ABI_VERSION 1u
#define PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME "prik.native_array_handle.v1"
#define PRIK_NATIVE_ARRAY_HANDLE_MAGIC UINT64_C(0x583250594e414831)
#define PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE 1u
#define PRIK_NATIVE_ARRAY_KIND_POINTER 2u

#if defined(_MSC_VER)
#define PRIK_NO_INLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define PRIK_NO_INLINE __attribute__((noinline))
#else
#define PRIK_NO_INLINE
#endif

typedef void (*prik_native_array_release_fn)(void *descriptor);

/*
 * Versioned cross-extension record for one persistent Fortran array
 * descriptor. The descriptor representation remains compiler-owned; this
 * record only makes its metadata, ownership, and validation ABI common to
 * independently generated prik extensions.
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
    prik_native_array_release_fn release;
} prik_native_array_handle;

#define PRIK_MAX_ARRAY_RANK 15

#ifdef PRIK_BINDING_NATIVE_ARRAY_ACTUAL

/* Mechanical result of the normal-array native-handle slow path. */
typedef struct {
    void *data;
    int64_t rank;
    int64_t itemsize;
    int64_t extents[PRIK_MAX_ARRAY_RANK];
    int64_t upper_bounds[PRIK_MAX_ARRAY_RANK];
    int64_t strides[PRIK_MAX_ARRAY_RANK];
} prik_array_actual;
#endif

/* Release descriptor payload and storage at most once while retaining the record. */
static inline void prik_native_array_handle_release(prik_native_array_handle *handle)
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
static inline void prik_native_array_handle_capsule_destructor(PyObject *capsule)
{
    PyObject *error_type = NULL;
    PyObject *error_value = NULL;
    PyObject *error_traceback = NULL;
    prik_native_array_handle *handle;

    PyErr_Fetch(&error_type, &error_value, &error_traceback);
    handle = (prik_native_array_handle *)PyCapsule_GetPointer(
        capsule, PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME);
    if (handle == NULL) {
        PyErr_Clear();
    } else {
        prik_native_array_handle_release(handle);
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
static inline PyObject *prik_native_array_handle_capsule_new(
    uint32_t descriptor_kind,
    uint32_t rank,
    int cfi_type,
    size_t element_size,
    size_t descriptor_size,
    void *descriptor,
    prik_native_array_release_fn release)
{
    prik_native_array_handle *handle;
    PyObject *capsule;

    if (descriptor_kind != PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE
        && descriptor_kind != PRIK_NATIVE_ARRAY_KIND_POINTER) {
        PyErr_SetString(PyExc_ValueError, "invalid prik native array descriptor kind");
        return NULL;
    }
    if (descriptor == NULL || descriptor_size == 0 || element_size == 0 || release == NULL) {
        PyErr_SetString(PyExc_ValueError, "incomplete prik native array handle storage");
        return NULL;
    }
    handle = (prik_native_array_handle *)calloc(1, sizeof(*handle));
    if (handle == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    handle->magic = PRIK_NATIVE_ARRAY_HANDLE_MAGIC;
    handle->abi_version = PRIK_NATIVE_ARRAY_HANDLE_ABI_VERSION;
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
        PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME,
        prik_native_array_handle_capsule_destructor);
    if (capsule == NULL) {
        handle->descriptor = NULL;
        handle->magic = 0;
        free(handle);
    }
    return capsule;
}

/* Validate and unwrap one cross-extension native array handle capsule. */
static inline prik_native_array_handle *prik_native_array_handle_from_capsule(
    PyObject *capsule,
    uint32_t expected_kind,
    uint32_t expected_rank,
    int expected_cfi_type,
    size_t expected_element_size,
    size_t expected_descriptor_size)
{
    prik_native_array_handle *handle;

    if (!PyCapsule_IsValid(capsule, PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME)) {
        PyErr_SetString(PyExc_TypeError, "incompatible prik native array handle capsule");
        return NULL;
    }
    handle = (prik_native_array_handle *)PyCapsule_GetPointer(
        capsule, PRIK_NATIVE_ARRAY_HANDLE_CAPSULE_NAME);
    if (handle == NULL) {
        return NULL;
    }
    if (handle->magic != PRIK_NATIVE_ARRAY_HANDLE_MAGIC
        || handle->abi_version != PRIK_NATIVE_ARRAY_HANDLE_ABI_VERSION
        || handle->struct_size != sizeof(*handle)) {
        PyErr_SetString(PyExc_TypeError, "incompatible prik native array handle ABI");
        return NULL;
    }
    if (handle->descriptor_kind != expected_kind) {
        PyErr_SetString(PyExc_TypeError, "prik native array descriptor kind does not match");
        return NULL;
    }
    if (handle->rank != expected_rank) {
        PyErr_SetString(PyExc_ValueError, "prik native array descriptor rank does not match");
        return NULL;
    }
    if (handle->cfi_type != expected_cfi_type) {
        PyErr_SetString(PyExc_TypeError, "prik native array element type does not match");
        return NULL;
    }
    if (expected_element_size != 0 && handle->element_size != expected_element_size) {
        PyErr_SetString(PyExc_TypeError, "prik native array element size does not match");
        return NULL;
    }
    if (handle->descriptor_size != expected_descriptor_size) {
        PyErr_SetString(PyExc_TypeError, "incompatible Fortran descriptor storage size");
        return NULL;
    }
    if (handle->descriptor == NULL) {
        PyErr_SetString(PyExc_ReferenceError, "prik native array handle is closed");
        return NULL;
    }
    return handle;
}

/*
 * Execute the Python native-handle handoff once per slow-path call site.
 * The completed wrapper plan supplies every contract selector; this helper
 * only performs reference management and decodes the returned ABI fields.
 */
#ifdef PRIK_BINDING_NATIVE_ARRAY_ACTUAL
PRIK_NO_INLINE static int prik_array_actual_unpack(
    PyObject *value,
    const char *dtype,
    int expected_rank,
    PyObject *expected_shape,
    const char *expected_layout,
    int require_writeable,
    int require_native_byte_order,
    int require_aligned,
    int include_rank,
    int include_itemsize,
    int include_strides,
    int require_contiguous,
    int flatten_storage,
    int flat_axis,
    prik_array_actual *actual)
{
    PyObject *runtime = NULL;
    PyObject *helper = NULL;
    PyObject *layout = NULL;
    PyObject *packed = NULL;
    PyObject *item;
    Py_ssize_t expected_fields;
    Py_ssize_t position;
    int axis;

    if (expected_shape == NULL || actual == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "prik generated an incomplete native array actual");
        return -1;
    }
    if (expected_rank < 1 || expected_rank > PRIK_MAX_ARRAY_RANK) {
        PyErr_SetString(PyExc_RuntimeError, "prik generated an invalid native array rank");
        return -1;
    }

    actual->data = NULL;
    actual->rank = 0;
    actual->itemsize = 0;
    for (axis = 0; axis < PRIK_MAX_ARRAY_RANK; axis++) {
        actual->extents[axis] = 0;
        actual->upper_bounds[axis] = 0;
        actual->strides[axis] = 1;
    }

    if (expected_layout == NULL) {
        layout = Py_None;
        Py_INCREF(layout);
    } else {
        layout = PyUnicode_FromString(expected_layout);
        if (layout == NULL) {
            return -1;
        }
    }
    runtime = PyImport_ImportModule("prik.runtime.handles");
    if (runtime == NULL) {
        Py_DECREF(layout);
        return -1;
    }
    helper = PyObject_GetAttrString(runtime, "_native_array_actual_argument_for_binding_positional");
    Py_DECREF(runtime);
    if (helper == NULL) {
        Py_DECREF(layout);
        return -1;
    }
    packed = PyObject_CallFunction(
        helper,
        "OsiOOiiiiiiiii",
        value,
        dtype,
        expected_rank,
        expected_shape,
        layout,
        require_writeable,
        require_native_byte_order,
        require_aligned,
        include_rank,
        include_itemsize,
        include_strides,
        require_contiguous,
        flatten_storage,
        flat_axis);
    Py_DECREF(helper);
    Py_DECREF(layout);
    if (packed == NULL) {
        return -1;
    }

    expected_fields = 1 + include_rank + include_itemsize + expected_rank;
    if (include_strides) {
        expected_fields += 2 * expected_rank;
    }
    if (!PyTuple_Check(packed) || PyTuple_GET_SIZE(packed) != expected_fields) {
        PyErr_SetString(PyExc_RuntimeError, "prik native array handoff returned invalid ABI fields");
        Py_DECREF(packed);
        return -1;
    }

    position = 0;
    actual->data = PyLong_AsVoidPtr(PyTuple_GET_ITEM(packed, position++));
    if (actual->data == NULL && PyErr_Occurred()) {
        Py_DECREF(packed);
        return -1;
    }
    if (include_rank) {
        actual->rank = (int64_t)PyLong_AsLongLong(PyTuple_GET_ITEM(packed, position++));
        if (PyErr_Occurred()) {
            Py_DECREF(packed);
            return -1;
        }
    }
    if (include_itemsize) {
        actual->itemsize = (int64_t)PyLong_AsLongLong(PyTuple_GET_ITEM(packed, position++));
        if (PyErr_Occurred()) {
            Py_DECREF(packed);
            return -1;
        }
    }
    for (axis = 0; axis < expected_rank; axis++) {
        item = PyTuple_GET_ITEM(packed, position++);
        actual->extents[axis] = (int64_t)PyLong_AsLongLong(item);
        if (PyErr_Occurred()) {
            Py_DECREF(packed);
            return -1;
        }
    }
    if (include_strides) {
        for (axis = 0; axis < expected_rank; axis++) {
            item = PyTuple_GET_ITEM(packed, position++);
            actual->upper_bounds[axis] = (int64_t)PyLong_AsLongLong(item);
            if (PyErr_Occurred()) {
                Py_DECREF(packed);
                return -1;
            }
        }
        for (axis = 0; axis < expected_rank; axis++) {
            item = PyTuple_GET_ITEM(packed, position++);
            actual->strides[axis] = (int64_t)PyLong_AsLongLong(item);
            if (PyErr_Occurred()) {
                Py_DECREF(packed);
                return -1;
            }
        }
    }
    Py_DECREF(packed);
    return 0;
}
#endif

/* Completed selectors for compact ordinary NumPy-array validation. */
#define PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS 0
#define PRIK_ARRAY_LAYOUT_C_CONTIGUOUS 1
#define PRIK_ARRAY_LAYOUT_F_CONTIGUOUS 2
#define PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F 3

/*
 * Validate mechanics shared by every ordinary NumPy-array argument. The
 * generated wrapper supplies completed policy selectors and retains its
 * call-local shape and ABI-field lowering.
 */
static inline int prik_array_validate(
    PyObject *value,
    int numpy_type,
    int minimum_rank,
    int maximum_rank,
    int layout,
    int require_contiguous,
    int require_writeable,
    const char *python_type,
    const char *argument_name)
{
    PyArrayObject *array;
    int axis;
    int rank;
    const char *expected_order;
    const char *contiguous_suffix;

    if (minimum_rank < 0 || maximum_rank < minimum_rank || maximum_rank > PRIK_MAX_ARRAY_RANK
        || layout < PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS
        || layout > PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F
        || python_type == NULL || argument_name == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "prik generated invalid NumPy-array validation selectors");
        return -1;
    }
    if (!PyArray_Check(value)) {
        PyErr_Format(
            PyExc_TypeError,
            "Expected a compatible numpy.ndarray of dtype %s for argument %s. Received <class '%s'>",
            python_type,
            argument_name,
            Py_TYPE(value)->tp_name);
        return -1;
    }
    array = (PyArrayObject *)value;
    rank = PyArray_NDIM(array);
    if (PyArray_TYPE(array) != numpy_type || rank < minimum_rank || rank > maximum_rank) {
        PyErr_Format(
            PyExc_TypeError,
            "Expected a compatible numpy.ndarray of dtype %s for argument %s. Received <class '%s'>",
            python_type,
            argument_name,
            Py_TYPE(value)->tp_name);
        return -1;
    }
    if (layout == PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F) {
        for (axis = 0; axis < rank; axis++) {
            npy_intp stride = PyArray_STRIDE(array, axis);
            if ((stride % PyArray_ITEMSIZE(array)) != 0
                || (PyArray_SIZE(array) > 0 && PyArray_DIM(array, axis) > 1 && stride <= 0)) {
                PyErr_Format(
                    PyExc_TypeError,
                    "Argument %s has incompatible layout; expected ordering (F)",
                    argument_name);
                return -1;
            }
            if (axis > 0 && PyArray_SIZE(array) > 0 && PyArray_DIM(array, axis - 1) > 0
                && stride < PyArray_STRIDE(array, axis - 1) * PyArray_DIM(array, axis - 1)) {
                PyErr_Format(
                    PyExc_TypeError,
                    "Argument %s has incompatible layout; expected ordering (F)",
                    argument_name);
                return -1;
            }
        }
    } else {
        int valid_layout =
            (layout == PRIK_ARRAY_LAYOUT_C_CONTIGUOUS && PyArray_IS_C_CONTIGUOUS(array))
            || (layout == PRIK_ARRAY_LAYOUT_F_CONTIGUOUS && PyArray_IS_F_CONTIGUOUS(array))
            || (layout == PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS
                && (PyArray_IS_C_CONTIGUOUS(array) || PyArray_IS_F_CONTIGUOUS(array)));
        if (!valid_layout) {
            expected_order = layout == PRIK_ARRAY_LAYOUT_C_CONTIGUOUS ? "C"
                : layout == PRIK_ARRAY_LAYOUT_F_CONTIGUOUS ? "F" : "C or F";
            contiguous_suffix = require_contiguous ? "; array must be contiguous" : "";
            PyErr_Format(
                PyExc_TypeError,
                "Argument %s has incompatible layout; expected ordering (%s)%s",
                argument_name,
                expected_order,
                contiguous_suffix);
            return -1;
        }
    }

    if (!PyArray_ISNOTSWAPPED(array)) {
        PyErr_Format(PyExc_TypeError, "Argument %s must use native byte order", argument_name);
        return -1;
    }
    if (!PyArray_ISALIGNED(array)) {
        PyErr_Format(PyExc_TypeError, "Argument %s must be aligned", argument_name);
        return -1;
    }
    if (require_writeable && !PyArray_ISWRITEABLE(array)) {
        PyErr_Format(PyExc_TypeError, "Argument %s must be writeable", argument_name);
        return -1;
    }
    return 0;
}

/* Exact typed scalar input conversion. A mismatch deliberately sets no error. */
static inline int prik_bool_unpack_exact(PyObject *value, bool *destination)
{
    int truth;
    if (!PyBool_Check(value) && !PyArray_IsScalar(value, Bool)) {
        return -1;
    }
    truth = PyObject_IsTrue(value);
    if (truth < 0) {
        return -1;
    }
    *destination = truth != 0;
    return 0;
}

static inline int prik_int8_unpack_exact(PyObject *value, int8_t *destination)
{
    if (!PyArray_IsScalar(value, Int8)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int16_unpack_exact(PyObject *value, int16_t *destination)
{
    if (!PyArray_IsScalar(value, Int16)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int32_unpack_exact(PyObject *value, int32_t *destination)
{
    if (!PyArray_IsScalar(value, Int)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int64_unpack_exact(PyObject *value, int64_t *destination)
{
    if (!PyArray_IsScalar(value, Int64)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_float32_unpack_exact(PyObject *value, float *destination)
{
    if (!PyArray_IsScalar(value, Float)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_float64_unpack_exact(PyObject *value, double *destination)
{
    if (!PyArray_IsScalar(value, Double)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_complex64_unpack_exact(PyObject *value, float complex *destination)
{
    if (!PyArray_IsScalar(value, CFloat)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_complex128_unpack_exact(PyObject *value, double complex *destination)
{
    if (!PyArray_IsScalar(value, CDouble)) {
        return -1;
    }
    PyArray_ScalarAsCtype(value, destination);
    return PyErr_Occurred() == NULL ? 0 : -1;
}

/* Type-specific coercive conversion for boundaries that permit Python scalars. */
static inline int prik_bool_unpack(PyObject *value, bool *destination)
{
    int truth = PyObject_IsTrue(value);
    if (truth < 0) {
        return -1;
    }
    *destination = truth != 0;
    return 0;
}

static inline int prik_int8_unpack(PyObject *value, int8_t *destination)
{
    if (PyArray_IsScalar(value, Int8)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (int8_t)PyLong_AsLong(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int16_unpack(PyObject *value, int16_t *destination)
{
    if (PyArray_IsScalar(value, Int16)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (int16_t)PyLong_AsLong(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int32_unpack(PyObject *value, int32_t *destination)
{
    if (PyArray_IsScalar(value, Int)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (int32_t)PyLong_AsLong(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_int64_unpack(PyObject *value, int64_t *destination)
{
    if (PyArray_IsScalar(value, Int64)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (int64_t)PyLong_AsLongLong(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_float32_unpack(PyObject *value, float *destination)
{
    if (PyArray_IsScalar(value, Float)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (float)PyFloat_AsDouble(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_float64_unpack(PyObject *value, double *destination)
{
    if (PyArray_IsScalar(value, Double)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = PyFloat_AsDouble(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_complex64_unpack(PyObject *value, float complex *destination)
{
    if (PyArray_IsScalar(value, CFloat)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        float real = (float)PyComplex_RealAsDouble(value);
        float imaginary = (float)PyComplex_ImagAsDouble(value);
        *destination = real + imaginary * I;
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline int prik_complex128_unpack(PyObject *value, double complex *destination)
{
    if (PyArray_IsScalar(value, CDouble)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        double real = PyComplex_RealAsDouble(value);
        double imaginary = PyComplex_ImagAsDouble(value);
        *destination = real + imaginary * I;
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

/* Create normal Python scalars without a runtime dtype switch. */
static inline PyObject *prik_bool_to_python(const bool *value)
{
    return PyBool_FromLong(*value);
}

static inline PyObject *prik_int8_to_python(const int8_t *value)
{
    return PyLong_FromLong(*value);
}

static inline PyObject *prik_int16_to_python(const int16_t *value)
{
    return PyLong_FromLong(*value);
}

static inline PyObject *prik_int32_to_python(const int32_t *value)
{
    return PyLong_FromLong(*value);
}

static inline PyObject *prik_int64_to_python(const int64_t *value)
{
    return PyLong_FromLongLong(*value);
}

static inline PyObject *prik_float32_to_python(const float *value)
{
    return PyFloat_FromDouble(*value);
}

static inline PyObject *prik_float64_to_python(const double *value)
{
    return PyFloat_FromDouble(*value);
}

static inline PyObject *prik_complex64_to_python(const float complex *value)
{
    return PyComplex_FromDoubles(crealf(*value), cimagf(*value));
}

static inline PyObject *prik_complex128_to_python(const double complex *value)
{
    return PyComplex_FromDoubles(creal(*value), cimag(*value));
}

/* Create typed NumPy scalars without a runtime dtype argument. */
static inline PyObject *prik_bool_to_numpy(const bool *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_BOOL);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_int8_to_numpy(const int8_t *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_INT8);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_int16_to_numpy(const int16_t *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_INT16);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_int32_to_numpy(const int32_t *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_INT32);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_int64_to_numpy(const int64_t *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_INT64);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_float32_to_numpy(const float *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_FLOAT32);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_float64_to_numpy(const double *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_FLOAT64);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_complex64_to_numpy(const float complex *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_COMPLEX64);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

static inline PyObject *prik_complex128_to_numpy(const double complex *value)
{
    PyArray_Descr *descriptor = PyArray_DescrFromType(NPY_COMPLEX128);
    return descriptor == NULL ? NULL : PyArray_Scalar((void *)value, descriptor, NULL);
}

/* Release a bridge-owned allocation transferred through a NumPy base capsule. */
static inline void prik_release_owned_memory(PyObject *capsule)
{
    void *memory = PyCapsule_GetPointer(capsule, NULL);
    if (memory == NULL) {
        PyErr_Clear();
        return;
    }
    free(memory);
}

#endif
