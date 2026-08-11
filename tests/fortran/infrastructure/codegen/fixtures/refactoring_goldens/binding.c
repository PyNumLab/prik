#define PRIK_BINDING_IMPORT_ARRAY 1

#define PRIK_BINDING_NATIVE_ARRAY_ACTUAL 1

#include <Python.h>

#include <stdint.h>

#include <stdbool.h>

#include <complex.h>

#include <stdatomic.h>

#include <string.h>

#include <stdlib.h>

#include <ISO_Fortran_binding.h>

#include "binding_support/prik_binding.h"

#include "refactoring_goldens_wrapper.h"

typedef struct prik_callback_context_callback_83b3d1d9 {
    PyObject * callable;
    PyObject * module;
    unsigned long thread_id;
    struct prik_callback_context_callback_83b3d1d9 * previous;
    PyObject * last_result;
} prik_callback_context_callback_83b3d1d9;

static _Thread_local prik_callback_context_callback_83b3d1d9 * prik_callback_current_callback_83b3d1d9 = NULL;

typedef int (*prik_derived_consumer_fn)(void *, void *);

typedef int (*prik_derived_scoped_fn)(prik_derived_consumer_fn, void *);

typedef int (*prik_derived_checkout_fn)(void **);

typedef int (*prik_derived_restore_fn)(void *);

typedef int (*prik_derived_present_fn)(void);

typedef void * (*prik_derived_address_fn)(void);

typedef struct prik_derived_origin_ops {
    const char * type_symbol;
    prik_derived_present_fn present;
    prik_derived_address_fn address;
    prik_derived_scoped_fn scoped;
    prik_derived_checkout_fn checkout;
    prik_derived_restore_fn restore;
} prik_derived_origin_ops;

typedef struct prik_derived_call_case {
    const char * origin;
    int access;
    const char * capsule_name;
    int uses_ops;
    int requires_present;
    const char * failure_kind;
    const char * failure_message;
} prik_derived_call_case;

typedef struct prik_derived_alias_entry {
    void * identity;
    int writable;
    const char * argument_name;
} prik_derived_alias_entry;

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_summarize_item[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_reset_allocatable_item_value[] = {{"direct", 0, "prik.derived.holder_item", 0, 0, "allocatable-derived-actual-required", "requires allocatable storage"}, {"allocatable_holder", 3, "prik.derived.holder_item.allocatable_holder", 0, 0, NULL, NULL}, {"pointer_holder", 0, "prik.derived.holder_item.pointer_holder", 0, 0, "allocatable-derived-actual-required", "requires allocatable storage"}, {"module_proxy", 0, NULL, 1, 0, "allocatable-derived-actual-required", "requires allocatable storage"}, {"module_target", 0, "prik.derived.holder_item", 0, 0, "allocatable-derived-actual-required", "requires allocatable storage"}, {"module_allocatable", 5, NULL, 1, 0, NULL, NULL}, {"module_allocatable_target", 5, NULL, 1, 0, NULL, NULL}, {"module_pointer", 0, NULL, 1, 0, "allocatable-derived-actual-required", "requires allocatable storage"}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_shift_pointer_item_value[] = {{"direct", 0, "prik.derived.holder_item", 0, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"allocatable_holder", 0, "prik.derived.holder_item.allocatable_holder", 0, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"pointer_holder", 4, "prik.derived.holder_item.pointer_holder", 0, 0, NULL, NULL}, {"module_proxy", 0, NULL, 1, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"module_target", 0, "prik.derived.holder_item", 0, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"module_allocatable", 0, NULL, 1, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"module_allocatable_target", 0, NULL, 1, 0, "pointer-derived-actual-required", "projected pointer association writeback requires pointer storage"}, {"module_pointer", 6, NULL, 1, 0, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___method___scale_self[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___method___shift_owner[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___method___magnitude_self[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___method___replace_samples_self[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___add___add_vectors_left[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

static const prik_derived_call_case prik_derived_cases_refactoring_goldens_vector___add___add_vectors_right[] = {{"direct", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"allocatable_holder", 3, "prik.derived.vector.allocatable_holder", 0, 1, NULL, NULL}, {"pointer_holder", 4, "prik.derived.vector.pointer_holder", 0, 1, NULL, NULL}, {"module_proxy", 2, NULL, 1, 0, NULL, NULL}, {"module_target", 1, "prik.derived.vector", 0, 0, NULL, NULL}, {"module_allocatable", 2, NULL, 1, 1, NULL, NULL}, {"module_allocatable_target", 1, NULL, 1, 1, NULL, NULL}, {"module_pointer", 2, NULL, 1, 1, NULL, NULL}};

bool bind_c_prik_origin_active_vector_26504a12_present(void);

int bind_c_prik_origin_active_vector_26504a12_scoped(prik_derived_consumer_fn consumer, void * context);

int bind_c_prik_origin_active_vector_26504a12_checkout(void ** holder);

int bind_c_prik_origin_active_vector_26504a12_restore(void * holder);

static int prik_origin_active_vector_26504a12_present(void);

static int prik_origin_active_vector_26504a12_scoped(prik_derived_consumer_fn consumer, void * context);

static int prik_origin_active_vector_26504a12_checkout(void ** holder);

static int prik_origin_active_vector_26504a12_restore(void * holder);

static PyObject * _prik_origin_active_vector_26504a12_native_ops(PyObject * self, PyObject * args);

static atomic_bool prik_origin_active_vector_26504a12_active = false;

static atomic_bool prik_origin_active_vector_26504a12_poisoned = false;

static prik_derived_origin_ops prik_origin_active_vector_26504a12_ops = {"vector", prik_origin_active_vector_26504a12_present, NULL, prik_origin_active_vector_26504a12_scoped, prik_origin_active_vector_26504a12_checkout, prik_origin_active_vector_26504a12_restore};

bool bind_c_prik_origin_selected_vector_d2fd3c9d_present(void);

int bind_c_prik_origin_selected_vector_d2fd3c9d_scoped(prik_derived_consumer_fn consumer, void * context);

int bind_c_prik_origin_selected_vector_d2fd3c9d_checkout(void ** holder);

int bind_c_prik_origin_selected_vector_d2fd3c9d_restore(void * holder);

static int prik_origin_selected_vector_d2fd3c9d_present(void);

static int prik_origin_selected_vector_d2fd3c9d_scoped(prik_derived_consumer_fn consumer, void * context);

static int prik_origin_selected_vector_d2fd3c9d_checkout(void ** holder);

static int prik_origin_selected_vector_d2fd3c9d_restore(void * holder);

static PyObject * _prik_origin_selected_vector_d2fd3c9d_native_ops(PyObject * self, PyObject * args);

static atomic_bool prik_origin_selected_vector_d2fd3c9d_active = false;

static atomic_bool prik_origin_selected_vector_d2fd3c9d_poisoned = false;

static prik_derived_origin_ops prik_origin_selected_vector_d2fd3c9d_ops = {"vector", prik_origin_selected_vector_d2fd3c9d_present, NULL, prik_origin_selected_vector_d2fd3c9d_scoped, prik_origin_selected_vector_d2fd3c9d_checkout, prik_origin_selected_vector_d2fd3c9d_restore};

int32_t bind_c_summarize(int32_t required, void * scale, void * values, int values_dense_actual, int64_t values_extent_0, int64_t values_upper_bound_0, int64_t values_stride_0, const char * label, int64_t label_length, void * item, int item_access, void * item_identity, prik_derived_scoped_fn item_scoped, prik_derived_checkout_fn item_checkout, prik_derived_restore_fn item_restore, int * item_status);

void bind_c_make_values(int32_t count, double fill_value, CFI_cdesc_t * result);

double bind_c_apply_callback(double value);

void bind_c_split_value(double value, double * doubled, int32_t * status);

void bind_c_reset_allocatable_item(void * value, int value_access, void * value_identity, prik_derived_scoped_fn value_scoped, prik_derived_checkout_fn value_checkout, prik_derived_restore_fn value_restore, int * value_status, void ** value_output, int * value_output_present);

void bind_c_shift_pointer_item(void * value, int value_access, void * value_identity, prik_derived_scoped_fn value_scoped, prik_derived_checkout_fn value_checkout, prik_derived_restore_fn value_restore, int * value_status, void ** value_output, int * value_output_present, double amount);

void bind_c__prik_class_vector_scale(void * self, int self_access, void * self_identity, int self_polymorphic, prik_derived_scoped_fn self_scoped, prik_derived_checkout_fn self_checkout, prik_derived_restore_fn self_restore, int * self_status, double factor);

void bind_c__prik_class_vector_shift(double dx, void * owner, int owner_access, void * owner_identity, int owner_polymorphic, prik_derived_scoped_fn owner_scoped, prik_derived_checkout_fn owner_checkout, prik_derived_restore_fn owner_restore, int * owner_status, double dy);

double bind_c__prik_class_vector_magnitude(void * self, int self_access, void * self_identity, int self_polymorphic, prik_derived_scoped_fn self_scoped, prik_derived_checkout_fn self_checkout, prik_derived_restore_fn self_restore, int * self_status);

void bind_c__prik_class_vector_replace_samples(void * self, int self_access, void * self_identity, int self_polymorphic, prik_derived_scoped_fn self_scoped, prik_derived_checkout_fn self_checkout, prik_derived_restore_fn self_restore, int * self_status, void * values, int values_dense_actual, int64_t values_extent_0, int64_t values_upper_bound_0, int64_t values_stride_0);

void * bind_c__prik_class_vector___add___0(void * left, int left_access, void * left_identity, int left_polymorphic, prik_derived_scoped_fn left_scoped, prik_derived_checkout_fn left_checkout, prik_derived_restore_fn left_restore, int * left_status, void * right, int right_access, void * right_identity, prik_derived_scoped_fn right_scoped, prik_derived_checkout_fn right_checkout, prik_derived_restore_fn right_restore, int * right_status);

double bind_c__prik_overload_convert_0(int32_t value);

int32_t bind_c__prik_overload_convert_1(double value);

void * bind_c_prik_create_holder_item(void);

static PyObject * _prik_create_holder_item(PyObject * self, PyObject * args);

void * bind_c_prik_create_vector(void);

static PyObject * _prik_create_vector(PyObject * self, PyObject * args);

void bind_c_prik_destroy_holder_item(void * address);

void bind_c_prik_destroy_vector(void * address);

void bind_c_prik_destroy_holder_item_allocatable_holder(void * address);

void bind_c_prik_destroy_holder_item_pointer_holder(void * address);

bool bind_c_prik_holder_item_allocatable_holder_present(void * address);

bool bind_c_prik_holder_item_pointer_holder_present(void * address);

bool bind_c_owned_result_5531b6b6_allocated(CFI_cdesc_t * result);

void bind_c_owned_result_5531b6b6_deallocate(CFI_cdesc_t * result);

void bind_c_owned_result_5531b6b6_destroy(CFI_cdesc_t * result);

void bind_c_owned_result_5531b6b6_shape(CFI_cdesc_t * result, int64_t * extent_0);

int32_t bind_c_prik_field_holder_item_code_get(void * owner);

void bind_c_prik_field_holder_item_code_set(void * owner, int32_t value);

double bind_c_prik_field_holder_item_weight_get(void * owner);

void bind_c_prik_field_holder_item_weight_set(void * owner, double value);

double bind_c_prik_field_vector_x_get(void * owner);

void bind_c_prik_field_vector_x_set(void * owner, double value);

double bind_c_prik_field_vector_y_get(void * owner);

void bind_c_prik_field_vector_y_set(void * owner, double value);

bool bind_c_prik_field_handle_vector_samples_allocated(void * owner);

void bind_c_prik_field_handle_vector_samples_deallocate(void * owner);

void bind_c_prik_field_handle_vector_samples_descriptor(void * owner, void (*callback)(CFI_cdesc_t *, void *), void * context);

void bind_c_prik_field_handle_vector_samples_resize(void * owner, int64_t extent_0);

void bind_c_prik_field_handle_vector_samples_shape(void * owner, int64_t * extent_0);

double bind_c_prik_module_field_active_vector_x_get(void);

void bind_c_prik_module_field_active_vector_x_set(double value);

double bind_c_prik_module_field_active_vector_y_get(void);

void bind_c_prik_module_field_active_vector_y_set(double value);

bool bind_c_prik_module_field_handle_active_vector_samples_allocated(void);

void bind_c_prik_module_field_handle_active_vector_samples_deallocate(void);

void bind_c_prik_module_field_handle_active_vector_samples_descriptor(void (*callback)(CFI_cdesc_t *, void *), void * context);

void bind_c_prik_module_field_handle_active_vector_samples_resize(int64_t extent_0);

void bind_c_prik_module_field_handle_active_vector_samples_shape(int64_t * extent_0);

double bind_c_prik_module_field_selected_vector_x_get(void);

void bind_c_prik_module_field_selected_vector_x_set(double value);

double bind_c_prik_module_field_selected_vector_y_get(void);

void bind_c_prik_module_field_selected_vector_y_set(double value);

bool bind_c_prik_module_field_handle_selected_vector_samples_allocated(void);

void bind_c_prik_module_field_handle_selected_vector_samples_deallocate(void);

void bind_c_prik_module_field_handle_selected_vector_samples_descriptor(void (*callback)(CFI_cdesc_t *, void *), void * context);

void bind_c_prik_module_field_handle_selected_vector_samples_resize(int64_t extent_0);

void bind_c_prik_module_field_handle_selected_vector_samples_shape(int64_t * extent_0);

int32_t bind_c_prik_allocatable_holder_field_holder_item_code_get(void * owner);

void bind_c_prik_allocatable_holder_field_holder_item_code_set(void * owner, int32_t value);

double bind_c_prik_allocatable_holder_field_holder_item_weight_get(void * owner);

void bind_c_prik_allocatable_holder_field_holder_item_weight_set(void * owner, double value);

int32_t bind_c_prik_pointer_holder_field_holder_item_code_get(void * owner_address);

void bind_c_prik_pointer_holder_field_holder_item_code_set(void * owner_address, int32_t value);

double bind_c_prik_pointer_holder_field_holder_item_weight_get(void * owner_address);

void bind_c_prik_pointer_holder_field_holder_item_weight_set(void * owner_address, double value);

static PyObject * _prik_field_holder_item_code_get(PyObject * self, PyObject * args);

static PyObject * _prik_field_holder_item_code_set(PyObject * self, PyObject * args);

static PyObject * _prik_field_holder_item_weight_get(PyObject * self, PyObject * args);

static PyObject * _prik_field_holder_item_weight_set(PyObject * self, PyObject * args);

static PyObject * _prik_field_vector_x_get(PyObject * self, PyObject * args);

static PyObject * _prik_field_vector_x_set(PyObject * self, PyObject * args);

static PyObject * _prik_field_vector_y_get(PyObject * self, PyObject * args);

static PyObject * _prik_field_vector_y_set(PyObject * self, PyObject * args);

static PyObject * _prik_field_vector_samples_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_active_vector_x_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_active_vector_x_set(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_active_vector_y_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_active_vector_y_set(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_active_vector_samples_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_selected_vector_x_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_selected_vector_x_set(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_selected_vector_y_get(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_selected_vector_y_set(PyObject * self, PyObject * args);

static PyObject * _prik_module_field_selected_vector_samples_get(PyObject * self, PyObject * args);

static PyObject * _prik_holder_item_allocatable_holder_require_present(PyObject * self, PyObject * args);

static PyObject * _prik_allocatable_holder_field_holder_item_code_get(PyObject * self, PyObject * args);

static PyObject * _prik_allocatable_holder_field_holder_item_code_set(PyObject * self, PyObject * args);

static PyObject * _prik_allocatable_holder_field_holder_item_weight_get(PyObject * self, PyObject * args);

static PyObject * _prik_allocatable_holder_field_holder_item_weight_set(PyObject * self, PyObject * args);

static PyObject * _prik_holder_item_pointer_holder_require_present(PyObject * self, PyObject * args);

static PyObject * _prik_pointer_holder_field_holder_item_code_get(PyObject * self, PyObject * args);

static PyObject * _prik_pointer_holder_field_holder_item_code_set(PyObject * self, PyObject * args);

static PyObject * _prik_pointer_holder_field_holder_item_weight_get(PyObject * self, PyObject * args);

static PyObject * _prik_pointer_holder_field_holder_item_weight_set(PyObject * self, PyObject * args);

static PyObject * _prik_module_active_vector_require_present(PyObject * self, PyObject * args);

static PyObject * _prik_module_selected_vector_require_present(PyObject * self, PyObject * args);

static PyObject * wrap__prik_dispatch_convert_d27e6413(PyObject * self, PyObject * args, PyObject * kwargs);

static PyObject * wrap__prik_dispatch_add_eeb3bbc5(PyObject * self, PyObject * args, PyObject * kwargs);

static void prik_field_handle_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context);

static void prik_field_handle_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context);

static PyObject * prik_field_handle_vector_samples_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_aligned_def = {"prik_field_handle_vector_samples_aligned", (PyCFunction)prik_field_handle_vector_samples_aligned, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_allocated(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_allocated_def = {"prik_field_handle_vector_samples_allocated", (PyCFunction)prik_field_handle_vector_samples_allocated, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_array_actual_def = {"prik_field_handle_vector_samples_array_actual", (PyCFunction)prik_field_handle_vector_samples_array_actual, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_deallocate(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_deallocate_def = {"prik_field_handle_vector_samples_deallocate", (PyCFunction)prik_field_handle_vector_samples_deallocate, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_descriptor_def = {"prik_field_handle_vector_samples_descriptor", (PyCFunction)prik_field_handle_vector_samples_descriptor, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_layout_def = {"prik_field_handle_vector_samples_layout", (PyCFunction)prik_field_handle_vector_samples_layout, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_native_byte_order_def = {"prik_field_handle_vector_samples_native_byte_order", (PyCFunction)prik_field_handle_vector_samples_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_resize(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_resize_def = {"prik_field_handle_vector_samples_resize", (PyCFunction)prik_field_handle_vector_samples_resize, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_shape_def = {"prik_field_handle_vector_samples_shape", (PyCFunction)prik_field_handle_vector_samples_shape, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_to_numpy_def = {"prik_field_handle_vector_samples_to_numpy", (PyCFunction)prik_field_handle_vector_samples_to_numpy, METH_VARARGS, ""};

static PyObject * prik_field_handle_vector_samples_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_field_handle_vector_samples_writeable_def = {"prik_field_handle_vector_samples_writeable", (PyCFunction)prik_field_handle_vector_samples_writeable, METH_VARARGS, ""};

static void prik_module_field_handle_active_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context);

static void prik_module_field_handle_active_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context);

static PyObject * prik_module_field_handle_active_vector_samples_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_aligned_def = {"prik_module_field_handle_active_vector_samples_aligned", (PyCFunction)prik_module_field_handle_active_vector_samples_aligned, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_allocated(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_allocated_def = {"prik_module_field_handle_active_vector_samples_allocated", (PyCFunction)prik_module_field_handle_active_vector_samples_allocated, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_array_actual_def = {"prik_module_field_handle_active_vector_samples_array_actual", (PyCFunction)prik_module_field_handle_active_vector_samples_array_actual, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_deallocate(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_deallocate_def = {"prik_module_field_handle_active_vector_samples_deallocate", (PyCFunction)prik_module_field_handle_active_vector_samples_deallocate, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_descriptor_def = {"prik_module_field_handle_active_vector_samples_descriptor", (PyCFunction)prik_module_field_handle_active_vector_samples_descriptor, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_layout_def = {"prik_module_field_handle_active_vector_samples_layout", (PyCFunction)prik_module_field_handle_active_vector_samples_layout, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_native_byte_order_def = {"prik_module_field_handle_active_vector_samples_native_byte_order", (PyCFunction)prik_module_field_handle_active_vector_samples_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_resize(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_resize_def = {"prik_module_field_handle_active_vector_samples_resize", (PyCFunction)prik_module_field_handle_active_vector_samples_resize, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_shape_def = {"prik_module_field_handle_active_vector_samples_shape", (PyCFunction)prik_module_field_handle_active_vector_samples_shape, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_to_numpy_def = {"prik_module_field_handle_active_vector_samples_to_numpy", (PyCFunction)prik_module_field_handle_active_vector_samples_to_numpy, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_active_vector_samples_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_active_vector_samples_writeable_def = {"prik_module_field_handle_active_vector_samples_writeable", (PyCFunction)prik_module_field_handle_active_vector_samples_writeable, METH_VARARGS, ""};

static void prik_module_field_handle_selected_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context);

static void prik_module_field_handle_selected_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context);

static PyObject * prik_module_field_handle_selected_vector_samples_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_aligned_def = {"prik_module_field_handle_selected_vector_samples_aligned", (PyCFunction)prik_module_field_handle_selected_vector_samples_aligned, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_allocated(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_allocated_def = {"prik_module_field_handle_selected_vector_samples_allocated", (PyCFunction)prik_module_field_handle_selected_vector_samples_allocated, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_array_actual_def = {"prik_module_field_handle_selected_vector_samples_array_actual", (PyCFunction)prik_module_field_handle_selected_vector_samples_array_actual, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_deallocate(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_deallocate_def = {"prik_module_field_handle_selected_vector_samples_deallocate", (PyCFunction)prik_module_field_handle_selected_vector_samples_deallocate, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_descriptor_def = {"prik_module_field_handle_selected_vector_samples_descriptor", (PyCFunction)prik_module_field_handle_selected_vector_samples_descriptor, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_layout_def = {"prik_module_field_handle_selected_vector_samples_layout", (PyCFunction)prik_module_field_handle_selected_vector_samples_layout, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_native_byte_order_def = {"prik_module_field_handle_selected_vector_samples_native_byte_order", (PyCFunction)prik_module_field_handle_selected_vector_samples_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_resize(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_resize_def = {"prik_module_field_handle_selected_vector_samples_resize", (PyCFunction)prik_module_field_handle_selected_vector_samples_resize, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_shape_def = {"prik_module_field_handle_selected_vector_samples_shape", (PyCFunction)prik_module_field_handle_selected_vector_samples_shape, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_to_numpy_def = {"prik_module_field_handle_selected_vector_samples_to_numpy", (PyCFunction)prik_module_field_handle_selected_vector_samples_to_numpy, METH_VARARGS, ""};

static PyObject * prik_module_field_handle_selected_vector_samples_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_module_field_handle_selected_vector_samples_writeable_def = {"prik_module_field_handle_selected_vector_samples_writeable", (PyCFunction)prik_module_field_handle_selected_vector_samples_writeable, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_active_vector_derived_owner = NULL;

static PyObject * prik_module_refactoring_goldens_selected_vector_derived_owner = NULL;

int32_t bind_c_get_counter(void);

void bind_c_set_counter(int32_t value);

bool bind_c_workspace_allocated(void);

void bind_c_workspace_array_actual(void (*callback)(CFI_cdesc_t *, void *), void * context);

void bind_c_workspace_deallocate(void);

void bind_c_workspace_descriptor(void (*callback)(CFI_cdesc_t *, void *), void * context);

void bind_c_workspace_resize(int64_t extent_0);

void bind_c_workspace_shape(int64_t * extent_0);

void * bind_c_selected_array_actual(void);

void bind_c_selected_associate(CFI_cdesc_t * source);

bool bind_c_selected_associated(void);

bool bind_c_selected_contiguous(void);

void bind_c_selected_descriptor(CFI_cdesc_t * descriptor);

void bind_c_selected_nullify(void);

void bind_c_selected_shape(int64_t * extent_0);

bool bind_c_prik_module_active_vector_present(void);

bool bind_c_prik_module_selected_vector_present(void);

static PyObject * module_get_counter(void);

static int module_set_counter(PyObject * value_obj);

static PyObject * module_get_workspace(void);

static PyObject * module_get_selected(void);

static PyObject * module_get_active_vector(void);

static PyObject * module_get_selected_vector(void);

static PyObject * prik_module_refactoring_goldens_workspace_handle = NULL;

static PyObject * prik_module_refactoring_goldens_workspace_owner = NULL;

static PyObject * prik_module_refactoring_goldens_workspace_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_aligned_def = {"prik_module_refactoring_goldens_workspace_aligned", (PyCFunction)prik_module_refactoring_goldens_workspace_aligned, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_allocated(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_allocated_def = {"prik_module_refactoring_goldens_workspace_allocated", (PyCFunction)prik_module_refactoring_goldens_workspace_allocated, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_array_actual_def = {"prik_module_refactoring_goldens_workspace_array_actual", (PyCFunction)prik_module_refactoring_goldens_workspace_array_actual, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_deallocate(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_deallocate_def = {"prik_module_refactoring_goldens_workspace_deallocate", (PyCFunction)prik_module_refactoring_goldens_workspace_deallocate, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_descriptor_def = {"prik_module_refactoring_goldens_workspace_descriptor", (PyCFunction)prik_module_refactoring_goldens_workspace_descriptor, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_layout_def = {"prik_module_refactoring_goldens_workspace_layout", (PyCFunction)prik_module_refactoring_goldens_workspace_layout, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_native_byte_order_def = {"prik_module_refactoring_goldens_workspace_native_byte_order", (PyCFunction)prik_module_refactoring_goldens_workspace_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_resize(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_resize_def = {"prik_module_refactoring_goldens_workspace_resize", (PyCFunction)prik_module_refactoring_goldens_workspace_resize, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_shape_def = {"prik_module_refactoring_goldens_workspace_shape", (PyCFunction)prik_module_refactoring_goldens_workspace_shape, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_to_numpy_def = {"prik_module_refactoring_goldens_workspace_to_numpy", (PyCFunction)prik_module_refactoring_goldens_workspace_to_numpy, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_workspace_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_workspace_writeable_def = {"prik_module_refactoring_goldens_workspace_writeable", (PyCFunction)prik_module_refactoring_goldens_workspace_writeable, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_handle = NULL;

static PyObject * prik_module_refactoring_goldens_selected_owner = NULL;

static PyObject * prik_module_refactoring_goldens_selected_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_aligned_def = {"prik_module_refactoring_goldens_selected_aligned", (PyCFunction)prik_module_refactoring_goldens_selected_aligned, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_array_actual_def = {"prik_module_refactoring_goldens_selected_array_actual", (PyCFunction)prik_module_refactoring_goldens_selected_array_actual, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_associate(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_associate_def = {"prik_module_refactoring_goldens_selected_associate", (PyCFunction)prik_module_refactoring_goldens_selected_associate, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_associated(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_associated_def = {"prik_module_refactoring_goldens_selected_associated", (PyCFunction)prik_module_refactoring_goldens_selected_associated, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_contiguous(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_contiguous_def = {"prik_module_refactoring_goldens_selected_contiguous", (PyCFunction)prik_module_refactoring_goldens_selected_contiguous, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_descriptor_def = {"prik_module_refactoring_goldens_selected_descriptor", (PyCFunction)prik_module_refactoring_goldens_selected_descriptor, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_layout_def = {"prik_module_refactoring_goldens_selected_layout", (PyCFunction)prik_module_refactoring_goldens_selected_layout, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_native_byte_order_def = {"prik_module_refactoring_goldens_selected_native_byte_order", (PyCFunction)prik_module_refactoring_goldens_selected_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_nullify(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_nullify_def = {"prik_module_refactoring_goldens_selected_nullify", (PyCFunction)prik_module_refactoring_goldens_selected_nullify, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_shape_def = {"prik_module_refactoring_goldens_selected_shape", (PyCFunction)prik_module_refactoring_goldens_selected_shape, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_to_numpy_def = {"prik_module_refactoring_goldens_selected_to_numpy", (PyCFunction)prik_module_refactoring_goldens_selected_to_numpy, METH_VARARGS, ""};

static PyObject * prik_module_refactoring_goldens_selected_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_module_refactoring_goldens_selected_writeable_def = {"prik_module_refactoring_goldens_selected_writeable", (PyCFunction)prik_module_refactoring_goldens_selected_writeable, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_aligned(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_aligned_def = {"prik_owned_refactoring_goldens_make_values_return_aligned", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_aligned, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_allocated(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_allocated_def = {"prik_owned_refactoring_goldens_make_values_return_allocated", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_allocated, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_array_actual(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_array_actual_def = {"prik_owned_refactoring_goldens_make_values_return_array_actual", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_array_actual, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_deallocate(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_deallocate_def = {"prik_owned_refactoring_goldens_make_values_return_deallocate", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_deallocate, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_descriptor(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_descriptor_def = {"prik_owned_refactoring_goldens_make_values_return_descriptor", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_descriptor, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_destroy(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_destroy_def = {"prik_owned_refactoring_goldens_make_values_return_destroy", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_destroy, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_layout(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_layout_def = {"prik_owned_refactoring_goldens_make_values_return_layout", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_layout, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_native_byte_order(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_native_byte_order_def = {"prik_owned_refactoring_goldens_make_values_return_native_byte_order", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_native_byte_order, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_resize(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_resize_def = {"prik_owned_refactoring_goldens_make_values_return_resize", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_resize, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_shape(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_shape_def = {"prik_owned_refactoring_goldens_make_values_return_shape", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_shape, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_to_numpy(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_to_numpy_def = {"prik_owned_refactoring_goldens_make_values_return_to_numpy", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_to_numpy, METH_VARARGS, ""};

static PyObject * prik_owned_refactoring_goldens_make_values_return_writeable(PyObject * self, PyObject * args);

static PyMethodDef prik_owned_refactoring_goldens_make_values_return_writeable_def = {"prik_owned_refactoring_goldens_make_values_return_writeable", (PyCFunction)prik_owned_refactoring_goldens_make_values_return_writeable, METH_VARARGS, ""};

static PyMethodDef refactoring_goldens_root_methods[] = {
    {"summarize", (PyCFunction)wrap_summarize, METH_VARARGS | METH_KEYWORDS, "summarize(required, scale=..., values=..., label=..., item=...) -> int32\n\nParameters\n----------\nrequired : int32\nscale : int32 or None\n    May be omitted or passed as None.\nvalues : ndarray[float64] or None\n    Rank: 1\n    Shape: (::Strided)\n    May be omitted or passed as None.\n    Ownership: Caller-owned.\nlabel : str or None\n    May be omitted or passed as None.\nitem : vector or None\n    May be omitted or passed as None.\n    Ownership: Wrapper-owned.\n\nReturns\n-------\nresult : int32\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nValueError\n    If rank, shape, layout, or descriptor state violates the contract.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"make_values", (PyCFunction)wrap_make_values, METH_VARARGS | METH_KEYWORDS, "make_values(count, fill_value) -> AllocatableArray[float64] | None\n\nParameters\n----------\ncount : int32\nfill_value : float64\n\nReturns\n-------\nresult : AllocatableArray[float64] or None\n    Rank: 1\n    Descriptor ownership: owned.\n    Unallocated state remains inside the returned handle.\n    Ownership: Wrapper-owned.\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nValueError\n    If rank, shape, layout, or descriptor state violates the contract."},
    {"apply_callback", (PyCFunction)wrap_apply_callback, METH_VARARGS | METH_KEYWORDS, "apply_callback(callback, value) -> float64\n\nParameters\n----------\ncallback : scalar_callback\nvalue : float64\n\nReturns\n-------\nresult : float64\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype."},
    {"split_value", (PyCFunction)wrap_split_value, METH_VARARGS | METH_KEYWORDS, "split_value(value) -> tuple[float64, int32]\n\nParameters\n----------\nvalue : float64\n\nReturns\n-------\ndoubled : float64\nstatus : int32\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype."},
    {"reset_allocatable_item", (PyCFunction)wrap_reset_allocatable_item, METH_VARARGS | METH_KEYWORDS, "reset_allocatable_item(value) -> holder_item\n\nParameters\n----------\nvalue : holder_item or None\n    Pass None for an unallocated or unassociated required descriptor.\n    Native code may update this value; the updated value is returned.\n    Ownership: Wrapper-owned.\n\nReturns\n-------\nvalue : holder_item\n    Ownership: Wrapper-owned.\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"shift_pointer_item", (PyCFunction)wrap_shift_pointer_item, METH_VARARGS | METH_KEYWORDS, "shift_pointer_item(value, amount) -> holder_item\n\nParameters\n----------\nvalue : holder_item or None\n    Pass None for an unallocated or unassociated required descriptor.\n    Native code may update this value; the updated value is returned.\n    Ownership: Wrapper-owned.\namount : float64\n\nReturns\n-------\nvalue : holder_item\n    Ownership: Wrapper-owned.\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_class_vector_scale", (PyCFunction)wrap__prik_class_vector_scale, METH_VARARGS | METH_KEYWORDS, "_prik_class_vector_scale(self, factor) -> None\n\nParameters\n----------\nself : vector\n    Native code may update the supplied storage in place.\n    Ownership: Wrapper-owned.\nfactor : float64\n\nReturns\n-------\nNone\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_class_vector_shift", (PyCFunction)wrap__prik_class_vector_shift, METH_VARARGS | METH_KEYWORDS, "_prik_class_vector_shift(dx, owner, dy) -> None\n\nParameters\n----------\ndx : float64\nowner : vector\n    Native code may update the supplied storage in place.\n    Ownership: Wrapper-owned.\ndy : float64\n\nReturns\n-------\nNone\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_class_vector_magnitude", (PyCFunction)wrap__prik_class_vector_magnitude, METH_VARARGS | METH_KEYWORDS, "_prik_class_vector_magnitude(self) -> float64\n\nParameters\n----------\nself : vector\n    Ownership: Wrapper-owned.\n\nReturns\n-------\nresult : float64\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_class_vector_replace_samples", (PyCFunction)wrap__prik_class_vector_replace_samples, METH_VARARGS | METH_KEYWORDS, "_prik_class_vector_replace_samples(self, values) -> None\n\nParameters\n----------\nself : vector\n    Native code may update the supplied storage in place.\n    Ownership: Wrapper-owned.\nvalues : ndarray[float64]\n    Rank: 1\n    Shape: (::Strided)\n    Ownership: Caller-owned.\n\nReturns\n-------\nNone\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nValueError\n    If rank, shape, layout, or descriptor state violates the contract.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_class_vector___add___0", (PyCFunction)wrap__prik_class_vector___add___0, METH_VARARGS | METH_KEYWORDS, "_prik_class_vector___add___0(left, right) -> vector\n\nParameters\n----------\nleft : vector\n    Ownership: Wrapper-owned.\nright : vector\n    Ownership: Wrapper-owned.\n\nReturns\n-------\nresult : vector\n    Ownership: Wrapper-owned.\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype.\nRuntimeError\n    If a derived-object transaction cannot be acquired or restored."},
    {"_prik_overload_convert_0", (PyCFunction)wrap__prik_overload_convert_0, METH_VARARGS | METH_KEYWORDS, "_prik_overload_convert_0(value) -> float64\n\nParameters\n----------\nvalue : int32\n\nReturns\n-------\nresult : float64\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype."},
    {"_prik_overload_convert_1", (PyCFunction)wrap__prik_overload_convert_1, METH_VARARGS | METH_KEYWORDS, "_prik_overload_convert_1(value) -> int32\n\nParameters\n----------\nvalue : float64\n\nReturns\n-------\nresult : int32\n\nRaises\n------\nTypeError\n    If an argument has an incompatible Python type or dtype."},
    {"convert", (PyCFunction)wrap__prik_dispatch_convert_d27e6413, METH_VARARGS | METH_KEYWORDS, "convert(*args, **kwargs)\n\nSupported Signatures\n--------------------\nconvert(value: int32) -> float64\nconvert(value: float64) -> int32\n\nRaises\n------\nTypeError\n    If no supported signature matches the supplied arguments."},
    {"_prik_dispatch_add_eeb3bbc5", (PyCFunction)wrap__prik_dispatch_add_eeb3bbc5, METH_VARARGS | METH_KEYWORDS, ""},
    {"_prik_create_holder_item", (PyCFunction)_prik_create_holder_item, METH_VARARGS, ""},
    {"_prik_create_vector", (PyCFunction)_prik_create_vector, METH_VARARGS, ""},
    {"_prik_field_holder_item_code_get", (PyCFunction)_prik_field_holder_item_code_get, METH_VARARGS, ""},
    {"_prik_field_holder_item_code_set", (PyCFunction)_prik_field_holder_item_code_set, METH_VARARGS, ""},
    {"_prik_field_holder_item_weight_get", (PyCFunction)_prik_field_holder_item_weight_get, METH_VARARGS, ""},
    {"_prik_field_holder_item_weight_set", (PyCFunction)_prik_field_holder_item_weight_set, METH_VARARGS, ""},
    {"_prik_field_vector_x_get", (PyCFunction)_prik_field_vector_x_get, METH_VARARGS, ""},
    {"_prik_field_vector_x_set", (PyCFunction)_prik_field_vector_x_set, METH_VARARGS, ""},
    {"_prik_field_vector_y_get", (PyCFunction)_prik_field_vector_y_get, METH_VARARGS, ""},
    {"_prik_field_vector_y_set", (PyCFunction)_prik_field_vector_y_set, METH_VARARGS, ""},
    {"_prik_field_vector_samples_get", (PyCFunction)_prik_field_vector_samples_get, METH_VARARGS, ""},
    {"_prik_module_field_active_vector_x_get", (PyCFunction)_prik_module_field_active_vector_x_get, METH_VARARGS, ""},
    {"_prik_module_field_active_vector_x_set", (PyCFunction)_prik_module_field_active_vector_x_set, METH_VARARGS, ""},
    {"_prik_module_field_active_vector_y_get", (PyCFunction)_prik_module_field_active_vector_y_get, METH_VARARGS, ""},
    {"_prik_module_field_active_vector_y_set", (PyCFunction)_prik_module_field_active_vector_y_set, METH_VARARGS, ""},
    {"_prik_module_field_active_vector_samples_get", (PyCFunction)_prik_module_field_active_vector_samples_get, METH_VARARGS, ""},
    {"_prik_module_field_selected_vector_x_get", (PyCFunction)_prik_module_field_selected_vector_x_get, METH_VARARGS, ""},
    {"_prik_module_field_selected_vector_x_set", (PyCFunction)_prik_module_field_selected_vector_x_set, METH_VARARGS, ""},
    {"_prik_module_field_selected_vector_y_get", (PyCFunction)_prik_module_field_selected_vector_y_get, METH_VARARGS, ""},
    {"_prik_module_field_selected_vector_y_set", (PyCFunction)_prik_module_field_selected_vector_y_set, METH_VARARGS, ""},
    {"_prik_module_field_selected_vector_samples_get", (PyCFunction)_prik_module_field_selected_vector_samples_get, METH_VARARGS, ""},
    {"_prik_allocatable_holder_field_holder_item_code_get", (PyCFunction)_prik_allocatable_holder_field_holder_item_code_get, METH_VARARGS, ""},
    {"_prik_allocatable_holder_field_holder_item_code_set", (PyCFunction)_prik_allocatable_holder_field_holder_item_code_set, METH_VARARGS, ""},
    {"_prik_allocatable_holder_field_holder_item_weight_get", (PyCFunction)_prik_allocatable_holder_field_holder_item_weight_get, METH_VARARGS, ""},
    {"_prik_allocatable_holder_field_holder_item_weight_set", (PyCFunction)_prik_allocatable_holder_field_holder_item_weight_set, METH_VARARGS, ""},
    {"_prik_holder_item_allocatable_holder_require_present", (PyCFunction)_prik_holder_item_allocatable_holder_require_present, METH_VARARGS, ""},
    {"_prik_pointer_holder_field_holder_item_code_get", (PyCFunction)_prik_pointer_holder_field_holder_item_code_get, METH_VARARGS, ""},
    {"_prik_pointer_holder_field_holder_item_code_set", (PyCFunction)_prik_pointer_holder_field_holder_item_code_set, METH_VARARGS, ""},
    {"_prik_pointer_holder_field_holder_item_weight_get", (PyCFunction)_prik_pointer_holder_field_holder_item_weight_get, METH_VARARGS, ""},
    {"_prik_pointer_holder_field_holder_item_weight_set", (PyCFunction)_prik_pointer_holder_field_holder_item_weight_set, METH_VARARGS, ""},
    {"_prik_holder_item_pointer_holder_require_present", (PyCFunction)_prik_holder_item_pointer_holder_require_present, METH_VARARGS, ""},
    {"_prik_module_active_vector_require_present", (PyCFunction)_prik_module_active_vector_require_present, METH_VARARGS, ""},
    {"_prik_module_selected_vector_require_present", (PyCFunction)_prik_module_selected_vector_require_present, METH_VARARGS, ""},
    {"_prik_origin_active_vector_26504a12_native_ops", (PyCFunction)_prik_origin_active_vector_26504a12_native_ops, METH_VARARGS, ""},
    {"_prik_origin_selected_vector_d2fd3c9d_native_ops", (PyCFunction)_prik_origin_selected_vector_d2fd3c9d_native_ops, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef refactoring_goldens_root_module = {
    PyModuleDef_HEAD_INIT,
    "refactoring_goldens",
    "refactoring_goldens\n\nModule Attributes\n-----------------\ndefault_count : int32\n    Read-only constant.\ncounter : int32\nworkspace : AllocatableArray[float64]\n    Persistent allocatable descriptor handle.\n    Replacement assignment is not supported.\nselected : PointerArray[float64]\n    Persistent pointer descriptor handle.\n    Replacement assignment is not supported.\nactive_vector : vector\n    Live native module object.\n    Replacement assignment is not supported.\nselected_vector : vector\n    Live native module object.\n    Replacement assignment is not supported.\n\nFunctions\n---------\nsummarize(required, scale=..., values=..., label=..., item=...) -> int32\nmake_values(count, fill_value) -> AllocatableArray[float64] | None\napply_callback(callback, value) -> float64\nsplit_value(value) -> tuple[float64, int32]\nreset_allocatable_item(value) -> holder_item\nshift_pointer_item(value, amount) -> holder_item\nconvert(*args, **kwargs)\n\nClasses\n-------\nholder_item\nvector",
    0,
    refactoring_goldens_root_methods,
};

static PyObject *refactoring_goldens_root_module_property_setup_getattro(PyObject *self, PyObject *name)
{
    if (PyUnicode_Check(name)) {
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "counter");
            if (comparison == -1 && PyErr_Occurred()) return NULL;
            if (comparison == 0) return module_get_counter();
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "workspace");
            if (comparison == -1 && PyErr_Occurred()) return NULL;
            if (comparison == 0) return module_get_workspace();
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "selected");
            if (comparison == -1 && PyErr_Occurred()) return NULL;
            if (comparison == 0) return module_get_selected();
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "active_vector");
            if (comparison == -1 && PyErr_Occurred()) return NULL;
            if (comparison == 0) return module_get_active_vector();
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "selected_vector");
            if (comparison == -1 && PyErr_Occurred()) return NULL;
            if (comparison == 0) return module_get_selected_vector();
        }
    }
    return PyModule_Type.tp_getattro(self, name);
}

static int refactoring_goldens_root_module_property_setup_setattro(PyObject *self, PyObject *name, PyObject *value)
{
    if (PyUnicode_Check(name)) {
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "counter");
            if (comparison == -1 && PyErr_Occurred()) return -1;
            if (comparison == 0) {
                if (value == NULL) {
                    PyErr_SetString(PyExc_AttributeError, "module variable counter cannot be deleted");
                    return -1;
                }
                return module_set_counter(value);
            }
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "workspace");
            if (comparison == -1 && PyErr_Occurred()) return -1;
            if (comparison == 0) {
                PyErr_SetString(PyExc_AttributeError, "module variable workspace is read-only");
                return -1;
            }
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "selected");
            if (comparison == -1 && PyErr_Occurred()) return -1;
            if (comparison == 0) {
                PyErr_SetString(PyExc_AttributeError, "module variable selected is read-only");
                return -1;
            }
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "active_vector");
            if (comparison == -1 && PyErr_Occurred()) return -1;
            if (comparison == 0) {
                PyErr_SetString(PyExc_AttributeError, "module variable active_vector is read-only");
                return -1;
            }
        }
        {
            int comparison = PyUnicode_CompareWithASCIIString(name, "selected_vector");
            if (comparison == -1 && PyErr_Occurred()) return -1;
            if (comparison == 0) {
                PyErr_SetString(PyExc_AttributeError, "module variable selected_vector is read-only");
                return -1;
            }
        }
    }
    return PyModule_Type.tp_setattro(self, name, value);
}

static PyType_Slot refactoring_goldens_root_module_property_setup_slots[] = {
    {Py_tp_getattro, (void *)refactoring_goldens_root_module_property_setup_getattro},
    {Py_tp_setattro, (void *)refactoring_goldens_root_module_property_setup_setattro},
    {0, NULL}
};
static PyType_Spec refactoring_goldens_root_module_property_setup_spec = {
    "refactoring_goldens.__prik_module_type",
    0,
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    refactoring_goldens_root_module_property_setup_slots
};
static int refactoring_goldens_root_module_property_setup(PyObject *module)
{
    PyObject *bases = PyTuple_Pack(1, (PyObject *)&PyModule_Type);
    if (bases == NULL) return -1;
    PyObject *module_type = PyType_FromSpecWithBases(&refactoring_goldens_root_module_property_setup_spec, bases);
    Py_DECREF(bases);
    if (module_type == NULL) return -1;
    int status = PyObject_SetAttrString(module, "__class__", module_type);
    Py_DECREF(module_type);
    return status;
}

void * prik_malloc(size_t size) {
    const char * fail_alloc = getenv("PRIK_WRAPPER_FAIL_ALLOC");
    if (fail_alloc != NULL && fail_alloc[0] != '\0' && fail_alloc[0] != '0') {
        return NULL;
    }
    return malloc(size == 0 ? 1 : size);
}

static void prik_callback_abort_callback_83b3d1d9(const char * message) {
    if (!PyErr_Occurred()) {
        PyErr_SetString(PyExc_RuntimeError, message);
    }
    PyErr_PrintEx(0);
    abort();
}

double prik_callback_trampoline_callback_83b3d1d9(void * value_data) {
    prik_callback_context_callback_83b3d1d9 * callback_context = prik_callback_current_callback_83b3d1d9;
    if (callback_context == NULL || callback_context->thread_id != PyThread_get_thread_ident()) {
        PyGILState_Ensure();
        PyErr_SetString(PyExc_RuntimeError, "callback invoked outside its entering Python thread");
        prik_callback_abort_callback_83b3d1d9("callback thread violation");
    }
    PyGILState_STATE callback_gil = PyGILState_Ensure();
    PyObject * callback_args = PyTuple_New(1);
    if (callback_args == NULL) {
        prik_callback_abort_callback_83b3d1d9("failed to allocate callback arguments");
    }
    PyObject * callback_arg_0 = prik_float64_to_numpy(value_data);
    if (callback_arg_0 == NULL) {
        prik_callback_abort_callback_83b3d1d9("failed to convert callback argument");
    }
    PyTuple_SET_ITEM(callback_args, 0, callback_arg_0);
    PyObject * callback_result = PyObject_CallObject(callback_context->callable, callback_args);
    Py_DECREF(callback_args);
    if (callback_result == NULL) {
        prik_callback_abort_callback_83b3d1d9("Python callback raised an exception");
    }
    double callback_value;
    if (prik_float64_unpack(callback_result, &callback_value) < 0) {
        prik_callback_abort_callback_83b3d1d9("invalid callback return value");
    }
    Py_DECREF(callback_result);
    PyGILState_Release(callback_gil);
    return callback_value;
}

static int prik_extract_derived_argument(PyObject * object, const char * type_name, const char * type_symbol, const char * direct_capsule_name, const char * argument_name, const prik_derived_call_case * cases, size_t case_count, void ** carrier, int * access, prik_derived_origin_ops ** ops) {
    *carrier = NULL;
    *access = 0;
    *ops = NULL;
    PyObject * origin_object = PyObject_GetAttrString(object, "_prik_origin");
    if (origin_object == NULL) {
        PyErr_Clear();
        PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", type_name, argument_name);
        return -1;
    }
    const char * origin = PyUnicode_AsUTF8(origin_object);
    if (origin == NULL) {
        Py_DECREF(origin_object);
        return -1;
    }
    const prik_derived_call_case * selected = NULL;
    for (size_t index = 0; index < case_count; ++index) {
        if (strcmp(origin, cases[index].origin) == 0) {
            selected = &cases[index];
            break;
        }
    }
    if (selected == NULL) {
        Py_DECREF(origin_object);
        PyErr_Format(PyExc_TypeError, "Unknown native origin %s for argument %s", origin, argument_name);
        return -1;
    }
    if (selected->access == 0) {
        PyErr_Format(PyExc_TypeError, "%s: %s", selected->failure_kind, selected->failure_message);
        Py_DECREF(origin_object);
        return -1;
    }
    if (selected->uses_ops) {
        PyObject * operation_map = PyObject_GetAttrString(object, "_prik_ops");
        if (operation_map == NULL) {
            Py_DECREF(origin_object);
            return -1;
        }
        PyObject * ops_capsule = PyDict_GetItemString(operation_map, "_native_ops");
        if (ops_capsule == NULL) {
            Py_DECREF(operation_map);
            Py_DECREF(origin_object);
            PyErr_Format(PyExc_TypeError, "module origin for argument %s has no native operations", argument_name);
            return -1;
        }
        *ops = (prik_derived_origin_ops *)PyCapsule_GetPointer(ops_capsule, "prik.derived_origin_ops");
        Py_DECREF(operation_map);
        if (*ops == NULL) {
            Py_DECREF(origin_object);
            return -1;
        }
        if (selected->access == 1) {
            if ((*ops)->address == NULL) {
                Py_DECREF(origin_object);
                PyErr_Format(PyExc_RuntimeError, "module origin for argument %s has no address operation", argument_name);
                return -1;
            }
            *carrier = (*ops)->address();
        }
    } else {
        const char * capsule_name = selected->access == 1 ? direct_capsule_name : selected->capsule_name;
        PyObject * carrier_capsule = PyObject_GetAttrString(object, "_prik_capsule");
        if (carrier_capsule == NULL) {
            Py_DECREF(origin_object);
            return -1;
        }
        if (!PyCapsule_IsValid(carrier_capsule, capsule_name)) {
            Py_DECREF(carrier_capsule);
            Py_DECREF(origin_object);
            PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", type_name, argument_name);
            return -1;
        }
        *carrier = PyCapsule_GetPointer(carrier_capsule, capsule_name);
        Py_DECREF(carrier_capsule);
        if (*carrier == NULL) {
            Py_DECREF(origin_object);
            return -1;
        }
    }
    if (*ops != NULL && ((*ops)->type_symbol == NULL || strcmp((*ops)->type_symbol, type_symbol) != 0)) {
        Py_DECREF(origin_object);
        PyErr_Format(PyExc_TypeError, "Expected exact wrapper type %s for argument %s", type_name, argument_name);
        return -1;
    }
    if (selected->requires_present && *ops != NULL && (*ops)->present != NULL && !(*ops)->present()) {
        Py_DECREF(origin_object);
        PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", argument_name);
        return -1;
    }
    if (selected->requires_present && selected->access == 1 && *carrier == NULL) {
        Py_DECREF(origin_object);
        PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", argument_name);
        return -1;
    }
    *access = selected->access;
    Py_DECREF(origin_object);
    return 0;
}

static int prik_validate_derived_aliases(const prik_derived_alias_entry * entries, size_t count) {
    for (size_t left = 0; left < count; ++left) {
        if (entries[left].identity != NULL) {
            for (size_t right = left + 1; right < count; ++right) {
                if (entries[left].identity == entries[right].identity && (entries[left].writable || entries[right].writable)) {
                    PyErr_Format(PyExc_TypeError, "derived origin is repeated in writable arguments %s and %s", entries[left].argument_name, entries[right].argument_name);
                    return -1;
                }
            }
        }
    }
    return 0;
}

static int prik_origin_active_vector_26504a12_present(void) {
    return bind_c_prik_origin_active_vector_26504a12_present() ? 1 : 0;
}

static int prik_origin_active_vector_26504a12_scoped(prik_derived_consumer_fn consumer, void * context) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (prik_derived_fault != NULL && strcmp(prik_derived_fault, "scoped:before:active_vector") == 0) {
        return 7;
    }
    if (atomic_load(&prik_origin_active_vector_26504a12_poisoned)) {
        return 3;
    }
    bool expected = false;
    if (!atomic_compare_exchange_strong(&prik_origin_active_vector_26504a12_active, &expected, true)) {
        return 2;
    }
    int status = bind_c_prik_origin_active_vector_26504a12_scoped(consumer, context);
    if (status == 0 && prik_derived_fault != NULL && strcmp(prik_derived_fault, "scoped:after:active_vector") == 0) {
        status = 7;
    }
    atomic_store(&prik_origin_active_vector_26504a12_active, false);
    return status;
}

static int prik_origin_active_vector_26504a12_checkout(void ** holder) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (prik_derived_fault != NULL && strcmp(prik_derived_fault, "checkout:before:active_vector") == 0) {
        return 7;
    }
    if (atomic_load(&prik_origin_active_vector_26504a12_poisoned)) {
        return 3;
    }
    bool expected = false;
    if (!atomic_compare_exchange_strong(&prik_origin_active_vector_26504a12_active, &expected, true)) {
        return 2;
    }
    int status = bind_c_prik_origin_active_vector_26504a12_checkout(holder);
    if (status != 0) {
        atomic_store(&prik_origin_active_vector_26504a12_active, false);
    }
    return status;
}

static int prik_origin_active_vector_26504a12_restore(void * holder) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (!atomic_load(&prik_origin_active_vector_26504a12_active)) {
        return 6;
    }
    int status = bind_c_prik_origin_active_vector_26504a12_restore(holder);
    if (status == 0 && prik_derived_fault != NULL && strcmp(prik_derived_fault, "restore:after:active_vector") == 0) {
        status = 7;
    }
    if (status != 0) {
        atomic_store(&prik_origin_active_vector_26504a12_poisoned, true);
    }
    atomic_store(&prik_origin_active_vector_26504a12_active, false);
    return status;
}

static PyObject * _prik_origin_active_vector_26504a12_native_ops(PyObject * self, PyObject * args) {
    return PyCapsule_New((void *)&prik_origin_active_vector_26504a12_ops, "prik.derived_origin_ops", NULL);
}

static int prik_origin_selected_vector_d2fd3c9d_present(void) {
    return bind_c_prik_origin_selected_vector_d2fd3c9d_present() ? 1 : 0;
}

static int prik_origin_selected_vector_d2fd3c9d_scoped(prik_derived_consumer_fn consumer, void * context) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (prik_derived_fault != NULL && strcmp(prik_derived_fault, "scoped:before:selected_vector") == 0) {
        return 7;
    }
    if (atomic_load(&prik_origin_selected_vector_d2fd3c9d_poisoned)) {
        return 3;
    }
    bool expected = false;
    if (!atomic_compare_exchange_strong(&prik_origin_selected_vector_d2fd3c9d_active, &expected, true)) {
        return 2;
    }
    int status = bind_c_prik_origin_selected_vector_d2fd3c9d_scoped(consumer, context);
    if (status == 0 && prik_derived_fault != NULL && strcmp(prik_derived_fault, "scoped:after:selected_vector") == 0) {
        status = 7;
    }
    atomic_store(&prik_origin_selected_vector_d2fd3c9d_active, false);
    return status;
}

static int prik_origin_selected_vector_d2fd3c9d_checkout(void ** holder) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (prik_derived_fault != NULL && strcmp(prik_derived_fault, "checkout:before:selected_vector") == 0) {
        return 7;
    }
    if (atomic_load(&prik_origin_selected_vector_d2fd3c9d_poisoned)) {
        return 3;
    }
    bool expected = false;
    if (!atomic_compare_exchange_strong(&prik_origin_selected_vector_d2fd3c9d_active, &expected, true)) {
        return 2;
    }
    int status = bind_c_prik_origin_selected_vector_d2fd3c9d_checkout(holder);
    if (status != 0) {
        atomic_store(&prik_origin_selected_vector_d2fd3c9d_active, false);
    }
    return status;
}

static int prik_origin_selected_vector_d2fd3c9d_restore(void * holder) {
    const char * prik_derived_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_ORIGIN");
    if (!atomic_load(&prik_origin_selected_vector_d2fd3c9d_active)) {
        return 6;
    }
    int status = bind_c_prik_origin_selected_vector_d2fd3c9d_restore(holder);
    if (status == 0 && prik_derived_fault != NULL && strcmp(prik_derived_fault, "restore:after:selected_vector") == 0) {
        status = 7;
    }
    if (status != 0) {
        atomic_store(&prik_origin_selected_vector_d2fd3c9d_poisoned, true);
    }
    atomic_store(&prik_origin_selected_vector_d2fd3c9d_active, false);
    return status;
}

static PyObject * _prik_origin_selected_vector_d2fd3c9d_native_ops(PyObject * self, PyObject * args) {
    return PyCapsule_New((void *)&prik_origin_selected_vector_d2fd3c9d_ops, "prik.derived_origin_ops", NULL);
}

static void prik_destroy_holder_item_capsule(PyObject * capsule) {
    void * address = PyCapsule_GetPointer(capsule, "prik.derived.holder_item");
    if (address != NULL) {
        bind_c_prik_destroy_holder_item(address);
    } else {
        PyErr_Clear();
    }
}

static void prik_destroy_vector_capsule(PyObject * capsule) {
    void * address = PyCapsule_GetPointer(capsule, "prik.derived.vector");
    if (address != NULL) {
        bind_c_prik_destroy_vector(address);
    } else {
        PyErr_Clear();
    }
}

static void prik_destroy_holder_item_allocatable_holder_capsule(PyObject * capsule) {
    void * address = PyCapsule_GetPointer(capsule, "prik.derived.holder_item.allocatable_holder");
    if (address != NULL) {
        bind_c_prik_destroy_holder_item_allocatable_holder(address);
    } else {
        PyErr_Clear();
    }
}

static void prik_destroy_holder_item_pointer_holder_capsule(PyObject * capsule) {
    void * address = PyCapsule_GetPointer(capsule, "prik.derived.holder_item.pointer_holder");
    if (address != NULL) {
        bind_c_prik_destroy_holder_item_pointer_holder(address);
    } else {
        PyErr_Clear();
    }
}

static PyObject * _prik_create_holder_item(PyObject * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) {
        return NULL;
    }
    void * address = bind_c_prik_create_holder_item();
    if (address == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    PyObject * capsule = PyCapsule_New(address, "prik.derived.holder_item", prik_destroy_holder_item_capsule);
    if (capsule == NULL) {
        bind_c_prik_destroy_holder_item(address);
        return NULL;
    }
    PyObject * wrapper_helper = PyObject_GetAttrString(self, "_prik_wrap_holder_item");
    if (wrapper_helper == NULL) {
        Py_DECREF(capsule);
        return NULL;
    }
    PyObject * result = PyObject_CallFunctionObjArgs(wrapper_helper, capsule, NULL);
    Py_DECREF(wrapper_helper);
    Py_DECREF(capsule);
    return result;
}

static PyObject * _prik_create_vector(PyObject * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) {
        return NULL;
    }
    void * address = bind_c_prik_create_vector();
    if (address == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    PyObject * capsule = PyCapsule_New(address, "prik.derived.vector", prik_destroy_vector_capsule);
    if (capsule == NULL) {
        bind_c_prik_destroy_vector(address);
        return NULL;
    }
    PyObject * wrapper_helper = PyObject_GetAttrString(self, "_prik_wrap_vector");
    if (wrapper_helper == NULL) {
        Py_DECREF(capsule);
        return NULL;
    }
    PyObject * result = PyObject_CallFunctionObjArgs(wrapper_helper, capsule, NULL);
    Py_DECREF(wrapper_helper);
    Py_DECREF(capsule);
    return result;
}

static PyObject * _prik_field_holder_item_code_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value = bind_c_prik_field_holder_item_code_get(owner_address);
    return prik_int32_to_numpy(&value);
}

static PyObject * _prik_field_holder_item_code_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value;
    if (prik_int32_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.int32 for field code. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_field_holder_item_code_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_field_holder_item_weight_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value = bind_c_prik_field_holder_item_weight_get(owner_address);
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_field_holder_item_weight_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field weight. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_field_holder_item_weight_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_field_vector_x_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value = bind_c_prik_field_vector_x_get(owner_address);
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_field_vector_x_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field x. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_field_vector_x_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_field_vector_y_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value = bind_c_prik_field_vector_y_get(owner_address);
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_field_vector_y_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field y. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_field_vector_y_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_field_vector_samples_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * refactoring_goldens_vector_samples_ops = PyDict_New();
    PyObject * refactoring_goldens_vector_samples_operation = NULL;
    PyObject * refactoring_goldens_vector_samples_runtime = NULL;
    PyObject * refactoring_goldens_vector_samples_helper = NULL;
    PyObject * refactoring_goldens_vector_samples_handle = NULL;
    if (refactoring_goldens_vector_samples_ops == NULL) {
        return NULL;
    }
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_aligned_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "aligned", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_allocated_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "allocated", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_array_actual_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "array_actual", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_deallocate_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "deallocate", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_descriptor_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "descriptor", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_layout_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "layout", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_native_byte_order_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "native_byte_order", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_resize_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "resize", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_shape_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "shape", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_to_numpy_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "to_numpy", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_field_handle_vector_samples_writeable_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "writeable", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (refactoring_goldens_vector_samples_runtime == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_helper = PyObject_GetAttrString(refactoring_goldens_vector_samples_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(refactoring_goldens_vector_samples_runtime);
    if (refactoring_goldens_vector_samples_helper == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_handle = PyObject_CallFunction(refactoring_goldens_vector_samples_helper, "ssiOOssO", "allocatable", "float64", 1, refactoring_goldens_vector_samples_ops, owner_obj, "borrowed", "borrowed_view", Py_None);
    Py_DECREF(refactoring_goldens_vector_samples_helper);
    Py_DECREF(refactoring_goldens_vector_samples_ops);
    return refactoring_goldens_vector_samples_handle;
}

static PyObject * _prik_module_field_active_vector_x_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    double value = bind_c_prik_module_field_active_vector_x_get();
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_module_field_active_vector_x_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field x. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_module_field_active_vector_x_set(value);
    Py_RETURN_NONE;
}

static PyObject * _prik_module_field_active_vector_y_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    double value = bind_c_prik_module_field_active_vector_y_get();
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_module_field_active_vector_y_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field y. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_module_field_active_vector_y_set(value);
    Py_RETURN_NONE;
}

static PyObject * _prik_module_field_active_vector_samples_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * refactoring_goldens_vector_samples_ops = PyDict_New();
    PyObject * refactoring_goldens_vector_samples_operation = NULL;
    PyObject * refactoring_goldens_vector_samples_runtime = NULL;
    PyObject * refactoring_goldens_vector_samples_helper = NULL;
    PyObject * refactoring_goldens_vector_samples_handle = NULL;
    if (refactoring_goldens_vector_samples_ops == NULL) {
        return NULL;
    }
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_aligned_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "aligned", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_allocated_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "allocated", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_array_actual_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "array_actual", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_deallocate_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "deallocate", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_descriptor_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "descriptor", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_layout_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "layout", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_native_byte_order_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "native_byte_order", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_resize_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "resize", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_shape_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "shape", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_to_numpy_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "to_numpy", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_active_vector_samples_writeable_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "writeable", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (refactoring_goldens_vector_samples_runtime == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_helper = PyObject_GetAttrString(refactoring_goldens_vector_samples_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(refactoring_goldens_vector_samples_runtime);
    if (refactoring_goldens_vector_samples_helper == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_handle = PyObject_CallFunction(refactoring_goldens_vector_samples_helper, "ssiOOssO", "allocatable", "float64", 1, refactoring_goldens_vector_samples_ops, owner_obj, "borrowed", "borrowed_view", Py_None);
    Py_DECREF(refactoring_goldens_vector_samples_helper);
    Py_DECREF(refactoring_goldens_vector_samples_ops);
    return refactoring_goldens_vector_samples_handle;
}

static PyObject * _prik_module_field_selected_vector_x_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    double value = bind_c_prik_module_field_selected_vector_x_get();
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_module_field_selected_vector_x_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field x. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_module_field_selected_vector_x_set(value);
    Py_RETURN_NONE;
}

static PyObject * _prik_module_field_selected_vector_y_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    double value = bind_c_prik_module_field_selected_vector_y_get();
    return prik_float64_to_numpy(&value);
}

static PyObject * _prik_module_field_selected_vector_y_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field y. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_module_field_selected_vector_y_set(value);
    Py_RETURN_NONE;
}

static PyObject * _prik_module_field_selected_vector_samples_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * refactoring_goldens_vector_samples_ops = PyDict_New();
    PyObject * refactoring_goldens_vector_samples_operation = NULL;
    PyObject * refactoring_goldens_vector_samples_runtime = NULL;
    PyObject * refactoring_goldens_vector_samples_helper = NULL;
    PyObject * refactoring_goldens_vector_samples_handle = NULL;
    if (refactoring_goldens_vector_samples_ops == NULL) {
        return NULL;
    }
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_aligned_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "aligned", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_allocated_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "allocated", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_array_actual_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "array_actual", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_deallocate_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "deallocate", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_descriptor_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "descriptor", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_layout_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "layout", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_native_byte_order_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "native_byte_order", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_resize_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "resize", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_shape_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "shape", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_to_numpy_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "to_numpy", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_operation = PyCFunction_NewEx(&prik_module_field_handle_selected_vector_samples_writeable_def, owner_obj, NULL);
    if (refactoring_goldens_vector_samples_operation == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    if (PyDict_SetItemString(refactoring_goldens_vector_samples_ops, "writeable", refactoring_goldens_vector_samples_operation) < 0) {
        Py_DECREF(refactoring_goldens_vector_samples_operation);
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    Py_DECREF(refactoring_goldens_vector_samples_operation);
    refactoring_goldens_vector_samples_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (refactoring_goldens_vector_samples_runtime == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_helper = PyObject_GetAttrString(refactoring_goldens_vector_samples_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(refactoring_goldens_vector_samples_runtime);
    if (refactoring_goldens_vector_samples_helper == NULL) {
        Py_DECREF(refactoring_goldens_vector_samples_ops);
        return NULL;
    }
    refactoring_goldens_vector_samples_handle = PyObject_CallFunction(refactoring_goldens_vector_samples_helper, "ssiOOssO", "allocatable", "float64", 1, refactoring_goldens_vector_samples_ops, owner_obj, "borrowed", "borrowed_view", Py_None);
    Py_DECREF(refactoring_goldens_vector_samples_helper);
    Py_DECREF(refactoring_goldens_vector_samples_ops);
    return refactoring_goldens_vector_samples_handle;
}

static PyObject * _prik_holder_item_allocatable_holder_require_present(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.allocatable_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    if (!bind_c_prik_holder_item_allocatable_holder_present(owner_address)) {
        PyErr_SetString(PyExc_ReferenceError, "allocatable derived object is unallocated");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * _prik_allocatable_holder_field_holder_item_code_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.allocatable_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value = bind_c_prik_allocatable_holder_field_holder_item_code_get(owner_address);
    return prik_int32_to_python(&value);
}

static PyObject * _prik_allocatable_holder_field_holder_item_code_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.allocatable_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value;
    if (prik_int32_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.int32 for field code. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_allocatable_holder_field_holder_item_code_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_allocatable_holder_field_holder_item_weight_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.allocatable_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value = bind_c_prik_allocatable_holder_field_holder_item_weight_get(owner_address);
    return prik_float64_to_python(&value);
}

static PyObject * _prik_allocatable_holder_field_holder_item_weight_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.allocatable_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field weight. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_allocatable_holder_field_holder_item_weight_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_holder_item_pointer_holder_require_present(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.pointer_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    if (!bind_c_prik_holder_item_pointer_holder_present(owner_address)) {
        PyErr_SetString(PyExc_ReferenceError, "pointer derived object is disassociated");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * _prik_pointer_holder_field_holder_item_code_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.pointer_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value = bind_c_prik_pointer_holder_field_holder_item_code_get(owner_address);
    return prik_int32_to_python(&value);
}

static PyObject * _prik_pointer_holder_field_holder_item_code_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.pointer_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int32_t value;
    if (prik_int32_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.int32 for field code. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_pointer_holder_field_holder_item_code_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_pointer_holder_field_holder_item_weight_get(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.pointer_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value = bind_c_prik_pointer_holder_field_holder_item_weight_get(owner_address);
    return prik_float64_to_python(&value);
}

static PyObject * _prik_pointer_holder_field_holder_item_weight_set(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * value_obj;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &value_obj)) return NULL;
    PyObject * owner_capsule = PyObject_GetAttrString(owner_obj, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.holder_item.pointer_holder");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    double value;
    if (prik_float64_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected numpy.float64 for field weight. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return NULL; };
    bind_c_prik_pointer_holder_field_holder_item_weight_set(owner_address, value);
    Py_RETURN_NONE;
}

static PyObject * _prik_module_active_vector_require_present(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    if (!bind_c_prik_module_active_vector_present()) {
        PyErr_SetString(PyExc_ReferenceError, "module object active_vector is not currently present");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * _prik_module_selected_vector_require_present(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    if (!bind_c_prik_module_selected_vector_present()) {
        PyErr_SetString(PyExc_ReferenceError, "module object selected_vector is not currently present");
        return NULL;
    }
    Py_RETURN_NONE;
}

static void prik_field_handle_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context) {
    *(PyObject **)context = NULL;
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    *(PyObject **)context = descriptor_record;
    return;
}

static void prik_field_handle_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context) {
    *(void **)context = descriptor->base_addr;
    return;
}

static PyObject * prik_field_handle_vector_samples_aligned(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_field_handle_vector_samples_allocated(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    return PyBool_FromLong(bind_c_prik_field_handle_vector_samples_allocated(owner_address));
}

static PyObject * prik_field_handle_vector_samples_array_actual(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    void * base_addr = NULL;
    bind_c_prik_field_handle_vector_samples_descriptor(owner_address, prik_field_handle_vector_samples_actual_callback, &base_addr);
    return PyLong_FromVoidPtr(base_addr);
}

static PyObject * prik_field_handle_vector_samples_deallocate(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    bind_c_prik_field_handle_vector_samples_deallocate(owner_address);
    Py_RETURN_NONE;
}

static PyObject * prik_field_handle_vector_samples_descriptor(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    PyObject * descriptor_record = NULL;
    bind_c_prik_field_handle_vector_samples_descriptor(owner_address, prik_field_handle_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_field_handle_vector_samples_layout(PyObject * self, PyObject * args) {
    return PyUnicode_FromString("F");
}

static PyObject * prik_field_handle_vector_samples_native_byte_order(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_field_handle_vector_samples_resize(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    PyObject * extent_0_obj;
    int64_t extent_0 = 0;
    if (!PyArg_ParseTuple(args, "O", &extent_0_obj)) return NULL;
    extent_0 = (int64_t)PyLong_AsLongLong(extent_0_obj); if (PyErr_Occurred()) return NULL;
    bind_c_prik_field_handle_vector_samples_resize(owner_address, extent_0);
    Py_RETURN_NONE;
}

static PyObject * prik_field_handle_vector_samples_shape(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    int64_t extent_0 = 0;
    bind_c_prik_field_handle_vector_samples_shape(owner_address, &extent_0);
    PyObject * shape = PyTuple_New(1);
    if (shape == NULL) {
        return NULL;
    }
    PyTuple_SET_ITEM(shape, 0, PyLong_FromLongLong((long long)extent_0));
    if (PyErr_Occurred()) {
        Py_DECREF(shape);
        return NULL;
    }
    return shape;
}

static PyObject * prik_field_handle_vector_samples_to_numpy(PyObject * self, PyObject * args) {
    PyObject * owner_capsule = PyObject_GetAttrString(self, "_prik_capsule");
    if (owner_capsule == NULL) {
        return NULL;
    }
    if (owner_capsule == Py_None) {
        Py_DECREF(owner_capsule);
        PyErr_SetString(PyExc_ReferenceError, "module proxy has no whole-object address");
        return NULL;
    }
    void * owner_address = PyCapsule_GetPointer(owner_capsule, "prik.derived.vector");
    Py_DECREF(owner_capsule);
    if (owner_address == NULL) {
        return NULL;
    }
    PyObject * descriptor_record = NULL;
    bind_c_prik_field_handle_vector_samples_descriptor(owner_address, prik_field_handle_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_field_handle_vector_samples_writeable(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static void prik_module_field_handle_active_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context) {
    *(PyObject **)context = NULL;
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    *(PyObject **)context = descriptor_record;
    return;
}

static void prik_module_field_handle_active_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context) {
    *(void **)context = descriptor->base_addr;
    return;
}

static PyObject * prik_module_field_handle_active_vector_samples_aligned(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_field_handle_active_vector_samples_allocated(PyObject * self, PyObject * args) {
    return PyBool_FromLong(bind_c_prik_module_field_handle_active_vector_samples_allocated());
}

static PyObject * prik_module_field_handle_active_vector_samples_array_actual(PyObject * self, PyObject * args) {
    void * base_addr = NULL;
    bind_c_prik_module_field_handle_active_vector_samples_descriptor(prik_module_field_handle_active_vector_samples_actual_callback, &base_addr);
    return PyLong_FromVoidPtr(base_addr);
}

static PyObject * prik_module_field_handle_active_vector_samples_deallocate(PyObject * self, PyObject * args) {
    bind_c_prik_module_field_handle_active_vector_samples_deallocate();
    Py_RETURN_NONE;
}

static PyObject * prik_module_field_handle_active_vector_samples_descriptor(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_prik_module_field_handle_active_vector_samples_descriptor(prik_module_field_handle_active_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_field_handle_active_vector_samples_layout(PyObject * self, PyObject * args) {
    return PyUnicode_FromString("F");
}

static PyObject * prik_module_field_handle_active_vector_samples_native_byte_order(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_field_handle_active_vector_samples_resize(PyObject * self, PyObject * args) {
    PyObject * extent_0_obj;
    int64_t extent_0 = 0;
    if (!PyArg_ParseTuple(args, "O", &extent_0_obj)) return NULL;
    extent_0 = (int64_t)PyLong_AsLongLong(extent_0_obj); if (PyErr_Occurred()) return NULL;
    bind_c_prik_module_field_handle_active_vector_samples_resize(extent_0);
    Py_RETURN_NONE;
}

static PyObject * prik_module_field_handle_active_vector_samples_shape(PyObject * self, PyObject * args) {
    int64_t extent_0 = 0;
    bind_c_prik_module_field_handle_active_vector_samples_shape(&extent_0);
    PyObject * shape = PyTuple_New(1);
    if (shape == NULL) {
        return NULL;
    }
    PyTuple_SET_ITEM(shape, 0, PyLong_FromLongLong((long long)extent_0));
    if (PyErr_Occurred()) {
        Py_DECREF(shape);
        return NULL;
    }
    return shape;
}

static PyObject * prik_module_field_handle_active_vector_samples_to_numpy(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_prik_module_field_handle_active_vector_samples_descriptor(prik_module_field_handle_active_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_field_handle_active_vector_samples_writeable(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static void prik_module_field_handle_selected_vector_samples_descriptor_callback(CFI_cdesc_t * descriptor, void * context) {
    *(PyObject **)context = NULL;
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    *(PyObject **)context = descriptor_record;
    return;
}

static void prik_module_field_handle_selected_vector_samples_actual_callback(CFI_cdesc_t * descriptor, void * context) {
    *(void **)context = descriptor->base_addr;
    return;
}

static PyObject * prik_module_field_handle_selected_vector_samples_aligned(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_field_handle_selected_vector_samples_allocated(PyObject * self, PyObject * args) {
    return PyBool_FromLong(bind_c_prik_module_field_handle_selected_vector_samples_allocated());
}

static PyObject * prik_module_field_handle_selected_vector_samples_array_actual(PyObject * self, PyObject * args) {
    void * base_addr = NULL;
    bind_c_prik_module_field_handle_selected_vector_samples_descriptor(prik_module_field_handle_selected_vector_samples_actual_callback, &base_addr);
    return PyLong_FromVoidPtr(base_addr);
}

static PyObject * prik_module_field_handle_selected_vector_samples_deallocate(PyObject * self, PyObject * args) {
    bind_c_prik_module_field_handle_selected_vector_samples_deallocate();
    Py_RETURN_NONE;
}

static PyObject * prik_module_field_handle_selected_vector_samples_descriptor(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_prik_module_field_handle_selected_vector_samples_descriptor(prik_module_field_handle_selected_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_field_handle_selected_vector_samples_layout(PyObject * self, PyObject * args) {
    return PyUnicode_FromString("F");
}

static PyObject * prik_module_field_handle_selected_vector_samples_native_byte_order(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_field_handle_selected_vector_samples_resize(PyObject * self, PyObject * args) {
    PyObject * extent_0_obj;
    int64_t extent_0 = 0;
    if (!PyArg_ParseTuple(args, "O", &extent_0_obj)) return NULL;
    extent_0 = (int64_t)PyLong_AsLongLong(extent_0_obj); if (PyErr_Occurred()) return NULL;
    bind_c_prik_module_field_handle_selected_vector_samples_resize(extent_0);
    Py_RETURN_NONE;
}

static PyObject * prik_module_field_handle_selected_vector_samples_shape(PyObject * self, PyObject * args) {
    int64_t extent_0 = 0;
    bind_c_prik_module_field_handle_selected_vector_samples_shape(&extent_0);
    PyObject * shape = PyTuple_New(1);
    if (shape == NULL) {
        return NULL;
    }
    PyTuple_SET_ITEM(shape, 0, PyLong_FromLongLong((long long)extent_0));
    if (PyErr_Occurred()) {
        Py_DECREF(shape);
        return NULL;
    }
    return shape;
}

static PyObject * prik_module_field_handle_selected_vector_samples_to_numpy(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_prik_module_field_handle_selected_vector_samples_descriptor(prik_module_field_handle_selected_vector_samples_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_field_handle_selected_vector_samples_writeable(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static void prik_release_native_handle_refactoring_goldens_make_values_return(void * storage) {
    CFI_cdesc_t * owner_descriptor = (CFI_cdesc_t *)storage;
    if (owner_descriptor == NULL) {
        return;
    }
    bind_c_owned_result_5531b6b6_destroy(owner_descriptor);
}

static void prik_module_refactoring_goldens_workspace_descriptor_callback(CFI_cdesc_t * descriptor, void * context) {
    *(PyObject **)context = NULL;
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    *(PyObject **)context = descriptor_record;
    return;
}

static void prik_module_refactoring_goldens_workspace_array_actual_callback(CFI_cdesc_t * descriptor, void * context) {
    *(void **)context = descriptor->base_addr;
    return;
}

static PyObject * prik_module_refactoring_goldens_workspace_aligned(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_refactoring_goldens_workspace_allocated(PyObject * self, PyObject * args) {
    return PyBool_FromLong(bind_c_workspace_allocated());
}

static PyObject * prik_module_refactoring_goldens_workspace_array_actual(PyObject * self, PyObject * args) {
    void * base_addr = NULL;
    bind_c_workspace_array_actual(prik_module_refactoring_goldens_workspace_array_actual_callback, &base_addr);
    return PyLong_FromVoidPtr(base_addr);
}

static PyObject * prik_module_refactoring_goldens_workspace_deallocate(PyObject * self, PyObject * args) {
    bind_c_workspace_deallocate();
    Py_RETURN_NONE;
}

static PyObject * prik_module_refactoring_goldens_workspace_descriptor(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_workspace_descriptor(prik_module_refactoring_goldens_workspace_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_refactoring_goldens_workspace_layout(PyObject * self, PyObject * args) {
    return PyUnicode_FromString("F");
}

static PyObject * prik_module_refactoring_goldens_workspace_native_byte_order(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_refactoring_goldens_workspace_resize(PyObject * self, PyObject * args) {
    PyObject * extent_0_obj;
    int64_t extent_0 = 0;
    if (!PyArg_ParseTuple(args, "O", &extent_0_obj)) return NULL;
    extent_0 = (int64_t)PyLong_AsLongLong(extent_0_obj); if (PyErr_Occurred()) return NULL;
    bind_c_workspace_resize(extent_0);
    Py_RETURN_NONE;
}

static PyObject * prik_module_refactoring_goldens_workspace_shape(PyObject * self, PyObject * args) {
    int64_t extent_0 = 0;
    bind_c_workspace_shape(&extent_0);
    PyObject * shape = PyTuple_New(1);
    if (shape == NULL) {
        return NULL;
    }
    PyTuple_SET_ITEM(shape, 0, PyLong_FromLongLong((long long)extent_0));
    if (PyErr_Occurred()) { Py_DECREF(shape); return NULL; };
    return shape;
}

static PyObject * prik_module_refactoring_goldens_workspace_to_numpy(PyObject * self, PyObject * args) {
    PyObject * descriptor_record = NULL;
    bind_c_workspace_descriptor(prik_module_refactoring_goldens_workspace_descriptor_callback, &descriptor_record);
    return descriptor_record;
}

static PyObject * prik_module_refactoring_goldens_workspace_writeable(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_refactoring_goldens_selected_aligned(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_refactoring_goldens_selected_array_actual(PyObject * self, PyObject * args) {
    return PyLong_FromVoidPtr(bind_c_selected_array_actual());
}

static PyObject * prik_module_refactoring_goldens_selected_associate(PyObject * self, PyObject * args) {
    PyObject * source_packed;
    if (!PyArg_ParseTuple(args, "O", &source_packed)) return NULL;
    PyObject * source_item = NULL;
    CFI_CDESC_T(1) source_storage;
    CFI_cdesc_t * source_descriptor = NULL;
    void * source_base_addr = NULL;
    size_t source_elem_len = 0;
    CFI_rank_t source_descriptor_rank = 0;
    CFI_index_t source_extents[1];
    CFI_index_t source_lower_bound_0 = 0;
    CFI_index_t source_extent_0 = 0;
    CFI_index_t source_stride_multiplier_0 = 0;
    int source_establish_status = CFI_SUCCESS;
    if (!PyTuple_Check(source_packed) || PyTuple_GET_SIZE(source_packed) != 6) { PyErr_SetString(PyExc_TypeError, "pointer association requires 6 descriptor facts"); return NULL; };
    source_item = PyTuple_GET_ITEM(source_packed, 0);
    source_base_addr = (void *)PyLong_AsVoidPtr(source_item);
    if (source_base_addr == NULL && PyErr_Occurred()) return NULL;
    source_item = PyTuple_GET_ITEM(source_packed, 1);
    source_elem_len = (size_t)PyLong_AsUnsignedLongLong(source_item);
    if (PyErr_Occurred()) return NULL;
    source_item = PyTuple_GET_ITEM(source_packed, 2);
    source_descriptor_rank = PyLong_AsLongLong(source_item);
    if (PyErr_Occurred()) return NULL;
    source_item = PyTuple_GET_ITEM(source_packed, 3);
    source_lower_bound_0 = PyLong_AsLongLong(source_item);
    if (PyErr_Occurred()) return NULL;
    source_item = PyTuple_GET_ITEM(source_packed, 4);
    source_extent_0 = PyLong_AsLongLong(source_item);
    if (PyErr_Occurred()) return NULL;
    source_item = PyTuple_GET_ITEM(source_packed, 5);
    source_stride_multiplier_0 = PyLong_AsLongLong(source_item);
    if (PyErr_Occurred()) return NULL;
    source_extents[0] = source_extent_0;
    if (source_descriptor_rank != 1) { PyErr_Format(PyExc_ValueError, "pointer association source rank %d does not match destination rank 1", (int)source_descriptor_rank); return NULL; };
    source_establish_status = CFI_establish((CFI_cdesc_t *)&source_storage, source_base_addr, CFI_attribute_pointer, CFI_type_double, source_elem_len, 1, source_extents);
    if (source_establish_status != CFI_SUCCESS) { PyErr_SetString(PyExc_RuntimeError, "failed to establish pointer association source"); return NULL; };
    ((CFI_cdesc_t *)&source_storage)->dim[0].lower_bound = source_lower_bound_0;
    ((CFI_cdesc_t *)&source_storage)->dim[0].extent = source_extent_0;
    ((CFI_cdesc_t *)&source_storage)->dim[0].sm = source_stride_multiplier_0;
    source_descriptor = (CFI_cdesc_t *)&source_storage;
    bind_c_selected_associate(source_descriptor);
    Py_RETURN_NONE;
}

static PyObject * prik_module_refactoring_goldens_selected_associated(PyObject * self, PyObject * args) {
    return PyBool_FromLong(bind_c_selected_associated());
}

static PyObject * prik_module_refactoring_goldens_selected_contiguous(PyObject * self, PyObject * args) {
    return PyBool_FromLong(bind_c_selected_contiguous());
}

static PyObject * prik_module_refactoring_goldens_selected_descriptor(PyObject * self, PyObject * args) {
    CFI_CDESC_T(1) descriptor_storage;
    CFI_cdesc_t * descriptor = (CFI_cdesc_t *)&descriptor_storage;
    int status = CFI_SUCCESS;
    status = CFI_establish(descriptor, NULL, CFI_attribute_pointer, CFI_type_double, sizeof(double), 1, NULL);
    if (status != CFI_SUCCESS) {
        PyErr_SetString(PyExc_RuntimeError, "failed to establish pointer descriptor reader");
        return NULL;
    }
    bind_c_selected_descriptor(descriptor);
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return NULL;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return NULL;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    return descriptor_record;
}

static PyObject * prik_module_refactoring_goldens_selected_layout(PyObject * self, PyObject * args) {
    return PyUnicode_FromString("F");
}

static PyObject * prik_module_refactoring_goldens_selected_native_byte_order(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_module_refactoring_goldens_selected_nullify(PyObject * self, PyObject * args) {
    bind_c_selected_nullify();
    Py_RETURN_NONE;
}

static PyObject * prik_module_refactoring_goldens_selected_shape(PyObject * self, PyObject * args) {
    int64_t extent_0 = 0;
    bind_c_selected_shape(&extent_0);
    PyObject * shape = PyTuple_New(1);
    if (shape == NULL) {
        return NULL;
    }
    PyTuple_SET_ITEM(shape, 0, PyLong_FromLongLong((long long)extent_0));
    if (PyErr_Occurred()) { Py_DECREF(shape); return NULL; };
    return shape;
}

static PyObject * prik_module_refactoring_goldens_selected_to_numpy(PyObject * self, PyObject * args) {
    CFI_CDESC_T(1) descriptor_storage;
    CFI_cdesc_t * descriptor = (CFI_cdesc_t *)&descriptor_storage;
    int status = CFI_SUCCESS;
    status = CFI_establish(descriptor, NULL, CFI_attribute_pointer, CFI_type_double, sizeof(double), 1, NULL);
    if (status != CFI_SUCCESS) {
        PyErr_SetString(PyExc_RuntimeError, "failed to establish pointer descriptor reader");
        return NULL;
    }
    bind_c_selected_descriptor(descriptor);
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return NULL;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)descriptor->dim[0].lower_bound, "extent", (long long)descriptor->dim[0].extent, "sm", (long long)descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return NULL;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)descriptor->base_addr, "elem_len", (unsigned long long)descriptor->elem_len, "rank", (int)descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    return descriptor_record;
}

static PyObject * prik_module_refactoring_goldens_selected_writeable(PyObject * self, PyObject * args) {
    return PyBool_FromLong(1);
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_aligned(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    return PyBool_FromLong(1);
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_allocated(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    return PyBool_FromLong(bind_c_owned_result_5531b6b6_allocated(owner_descriptor));
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_array_actual(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    return PyLong_FromVoidPtr(owner_descriptor->base_addr);
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_deallocate(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    bind_c_owned_result_5531b6b6_deallocate(owner_descriptor);
    Py_RETURN_NONE;
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_descriptor(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    Py_INCREF(owner_obj);
    return owner_obj;
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_destroy(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    prik_native_array_handle_release(owner_handle);
    Py_RETURN_NONE;
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_layout(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    return PyUnicode_FromString("F");
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_native_byte_order(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    return PyBool_FromLong(1);
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_resize(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    PyObject * extent_0_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    CFI_index_t lower_bounds[1];
    CFI_index_t upper_bounds[1];
    int status = CFI_SUCCESS;
    if (!PyArg_ParseTuple(args, "OO", &owner_obj, &extent_0_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    upper_bounds[0] = (CFI_index_t)PyLong_AsLongLong(extent_0_obj) - 1;
    if (PyErr_Occurred()) return NULL;
    lower_bounds[0] = 0;
    bind_c_owned_result_5531b6b6_deallocate(owner_descriptor);
    status = CFI_allocate(owner_descriptor, lower_bounds, upper_bounds, owner_descriptor->elem_len);
    if (status != CFI_SUCCESS) { PyErr_SetString(PyExc_RuntimeError, "failed to resize owned native array"); return NULL; };
    Py_RETURN_NONE;
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_shape(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    int64_t extent_0 = 0;
    bind_c_owned_result_5531b6b6_shape(owner_descriptor, &extent_0);
    return Py_BuildValue("(L)", extent_0);
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_to_numpy(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    CFI_cdesc_t * owner_descriptor = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    owner_descriptor = (CFI_cdesc_t *)owner_handle->descriptor;
    PyObject * dimensions = PyList_New(1);
    if (dimensions == NULL) {
        return NULL;
    }
    PyObject * dimension_0 = Py_BuildValue("{sL,sL,sL}", "lower_bound", (long long)owner_descriptor->dim[0].lower_bound, "extent", (long long)owner_descriptor->dim[0].extent, "sm", (long long)owner_descriptor->dim[0].sm);
    if (dimension_0 == NULL) {
        Py_DECREF(dimensions);
        return NULL;
    }
    PyList_SET_ITEM(dimensions, 0, dimension_0);
    PyObject * descriptor_record = Py_BuildValue("{sK,sK,si,sO}", "base_addr", (unsigned long long)(uintptr_t)owner_descriptor->base_addr, "elem_len", (unsigned long long)owner_descriptor->elem_len, "rank", (int)owner_descriptor->rank, "dim", dimensions);
    Py_DECREF(dimensions);
    return descriptor_record;
}

static PyObject * prik_owned_refactoring_goldens_make_values_return_writeable(PyObject * self, PyObject * args) {
    PyObject * owner_obj;
    prik_native_array_handle * owner_handle = NULL;
    if (!PyArg_ParseTuple(args, "O", &owner_obj)) return NULL;
    owner_handle = prik_native_array_handle_from_capsule(owner_obj, PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)));
    if (owner_handle == NULL) return NULL;
    return PyBool_FromLong(1);
}

static PyObject * wrap_summarize(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"required", "scale", "values", "label", "item", NULL};
    PyObject * bound_required_obj;
    int32_t bound_required;
    PyObject * bound_scale_obj = Py_None;
    int32_t bound_scale;
    void * bound_scale_nullable = NULL;
    PyObject * bound_values_obj = Py_None;
    void * bound_values = NULL;
    int64_t bound_values_extent_0 = 0;
    int64_t bound_values_upper_bound_0 = 0;
    int64_t bound_values_stride_0 = 1;
    int bound_values_dense_actual = 0;
    PyObject * bound_label_obj = Py_None;
    Py_ssize_t bound_label_length = 0;
    const char * bound_label = NULL;
    PyObject * bound_item_obj = Py_None;
    void * bound_item = NULL;
    int bound_item_derived_access = 0;
    prik_derived_origin_ops * bound_item_derived_ops = NULL;
    void * bound_item_derived_identity = NULL;
    int bound_item_derived_status = 0;
    int32_t result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|OOOO", kwlist, &bound_required_obj, &bound_scale_obj, &bound_values_obj, &bound_label_obj, &bound_item_obj)) return NULL;
    if (prik_int32_unpack_exact(bound_required_obj, &bound_required) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.int32 for argument required. Received <class '%s'>", Py_TYPE(bound_required_obj)->tp_name); } return NULL; };
    if (bound_scale_obj != Py_None) {
        if (prik_int32_unpack_exact(bound_scale_obj, &bound_scale) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.int32 for argument scale. Received <class '%s'>", Py_TYPE(bound_scale_obj)->tp_name); } return NULL; };
        bound_scale_nullable = &bound_scale;
    }
    if (bound_values_obj != Py_None) {
        if (prik_array_validate(bound_values_obj, NPY_FLOAT64, 1, 1, PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F, 0, 0, "numpy.float64", "values") < 0) return NULL;
        bound_values = PyArray_DATA((PyArrayObject *)bound_values_obj);
        bound_values_dense_actual = PyArray_IS_F_CONTIGUOUS((PyArrayObject *)bound_values_obj);
        bound_values_extent_0 = (int64_t)PyArray_DIM((PyArrayObject *)bound_values_obj, 0);
        if (!bound_values_dense_actual) {
            bound_values_stride_0 = PyArray_SIZE((PyArrayObject *)bound_values_obj) == 0 ? 1 : (PyArray_STRIDE((PyArrayObject *)bound_values_obj, 0) / PyArray_ITEMSIZE((PyArrayObject *)bound_values_obj)) / (1);
            bound_values_upper_bound_0 = bound_values_extent_0 == 0 ? -1 : (bound_values_extent_0 - 1) * bound_values_stride_0;
            bound_values_extent_0 = bound_values_upper_bound_0 + 1;
        }
    }
    if (bound_label_obj != Py_None) {
        if (!PyUnicode_Check(bound_label_obj)) { PyErr_Format(PyExc_TypeError, "Expected an argument of type str for argument label. Received <class '%s'>", Py_TYPE(bound_label_obj)->tp_name); return NULL; };
        bound_label = PyUnicode_AsUTF8AndSize(bound_label_obj, &bound_label_length);
        if (bound_label == NULL) return NULL;
        if ((Py_ssize_t)strlen(bound_label) != bound_label_length) { PyErr_SetString(PyExc_TypeError, "Argument label cannot contain embedded NUL"); return NULL; };
    }
    if (bound_item_obj != Py_None) {
        int bound_item_extract_status = prik_extract_derived_argument(bound_item_obj, "vector", "vector", "prik.derived.vector", "item", prik_derived_cases_refactoring_goldens_summarize_item, sizeof(prik_derived_cases_refactoring_goldens_summarize_item) / sizeof(prik_derived_cases_refactoring_goldens_summarize_item[0]), &bound_item, &bound_item_derived_access, &bound_item_derived_ops);
        if (bound_item_extract_status < 0) {
            return NULL;
        }
    }
    bound_item_derived_identity = bound_item_derived_ops != NULL ? (void *)bound_item_derived_ops : bound_item;
    result = bind_c_summarize(bound_required, bound_scale_nullable, bound_values, bound_values_dense_actual, bound_values_extent_0, bound_values_upper_bound_0, bound_values_stride_0, bound_label, (int64_t)bound_label_length, bound_item, bound_item_derived_access, bound_item_derived_identity, bound_item_derived_ops != NULL ? bound_item_derived_ops->scoped : NULL, bound_item_derived_ops != NULL ? bound_item_derived_ops->checkout : NULL, bound_item_derived_ops != NULL ? bound_item_derived_ops->restore : NULL, &bound_item_derived_status);
    if (bound_item_derived_status != 0) {
        if (bound_item_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "item");
        } else {
            if (bound_item_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "item", bound_item_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    PyObject * result_obj = prik_int32_to_python(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap_make_values(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"count", "fill_value", NULL};
    PyObject * bound_count_obj;
    int32_t bound_count;
    PyObject * bound_fill_value_obj;
    double bound_fill_value;
    CFI_cdesc_t * result = NULL;
    int result_owner_status = CFI_SUCCESS;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_count_obj, &bound_fill_value_obj)) return NULL;
    if (prik_int32_unpack_exact(bound_count_obj, &bound_count) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.int32 for argument count. Received <class '%s'>", Py_TYPE(bound_count_obj)->tp_name); } return NULL; };
    if (prik_float64_unpack_exact(bound_fill_value_obj, &bound_fill_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument fill_value. Received <class '%s'>", Py_TYPE(bound_fill_value_obj)->tp_name); } return NULL; };
    result = (CFI_cdesc_t *)calloc(1, sizeof(CFI_CDESC_T(1)));
    if (result == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    result_owner_status = CFI_establish(result, NULL, CFI_attribute_allocatable, CFI_type_double, sizeof(double), 1, NULL);
    if (result_owner_status != CFI_SUCCESS) {
        free(result);
        result = NULL;
        PyErr_SetString(PyExc_RuntimeError, "failed to establish owned native array descriptor storage");
        return NULL;
    }
    bind_c_make_values(bound_count, bound_fill_value, result);
    PyObject * result_handle_runtime = NULL;
    PyObject * result_handle_helper = NULL;
    PyObject * result_handle_ops = NULL;
    PyObject * result_handle_owner = NULL;
    PyObject * result_handle_operation = NULL;
    PyObject * result_obj = NULL;
    result_handle_ops = PyDict_New();
    if (result_handle_ops == NULL) {
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_aligned_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "aligned", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_allocated_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "allocated", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_array_actual_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "array_actual", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_deallocate_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "deallocate", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_descriptor_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "descriptor", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_destroy_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "destroy", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_layout_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "layout", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_native_byte_order_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "native_byte_order", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_resize_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "resize", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_shape_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "shape", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_to_numpy_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "to_numpy", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_operation = PyCFunction_NewEx(&prik_owned_refactoring_goldens_make_values_return_writeable_def, NULL, NULL);
    if (result_handle_operation == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    if (PyDict_SetItemString(result_handle_ops, "writeable", result_handle_operation) < 0) {
        Py_DECREF(result_handle_operation);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    Py_DECREF(result_handle_operation);
    result_handle_owner = prik_native_array_handle_capsule_new(PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)), result, prik_release_native_handle_refactoring_goldens_make_values_return);
    if (result_handle_owner == NULL) {
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    result = NULL;
    result_handle_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (result_handle_runtime == NULL) {
        Py_DECREF(result_handle_owner);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    result_handle_helper = PyObject_GetAttrString(result_handle_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(result_handle_runtime);
    if (result_handle_helper == NULL) {
        Py_DECREF(result_handle_owner);
        Py_DECREF(result_handle_ops);
        if (result != NULL) { if (result->base_addr != NULL) (void)CFI_deallocate(result); free(result); result = NULL; };
        return NULL;
    }
    result_obj = PyObject_CallFunction(result_handle_helper, "ssiOOssO", "allocatable", "float64", 1, result_handle_ops, result_handle_owner, "owned", "borrowed_view", Py_None);
    Py_DECREF(result_handle_helper);
    Py_DECREF(result_handle_owner);
    Py_DECREF(result_handle_ops);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap_apply_callback(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"callback", "value", NULL};
    PyObject * bound_callback_obj;
    PyObject * bound_value_obj;
    double bound_value;
    prik_callback_context_callback_83b3d1d9 callback_callback_context;
    double result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_callback_obj, &bound_value_obj)) return NULL;
    if (!PyCallable_Check(bound_callback_obj)) {
        PyErr_SetString(PyExc_TypeError, "argument callback must be callable");
        return NULL;
    }
    if (prik_float64_unpack_exact(bound_value_obj, &bound_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument value. Received <class '%s'>", Py_TYPE(bound_value_obj)->tp_name); } return NULL; };
    callback_callback_context.callable = bound_callback_obj;
    callback_callback_context.module = self;
    callback_callback_context.thread_id = PyThread_get_thread_ident();
    callback_callback_context.previous = prik_callback_current_callback_83b3d1d9;
    callback_callback_context.last_result = NULL;
    Py_INCREF(bound_callback_obj);
    Py_INCREF(self);
    prik_callback_current_callback_83b3d1d9 = &callback_callback_context;
    result = bind_c_apply_callback(bound_value);
    prik_callback_current_callback_83b3d1d9 = callback_callback_context.previous;
    Py_XDECREF(callback_callback_context.last_result);
    Py_DECREF(callback_callback_context.module);
    Py_DECREF(callback_callback_context.callable);
    PyObject * result_obj = prik_float64_to_python(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap_split_value(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", NULL};
    PyObject * bound_value_obj;
    double bound_value;
    double doubled;
    int32_t status;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_value_obj)) return NULL;
    if (prik_float64_unpack_exact(bound_value_obj, &bound_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument value. Received <class '%s'>", Py_TYPE(bound_value_obj)->tp_name); } return NULL; };
    bind_c_split_value(bound_value, &doubled, &status);
    PyObject * result_0_obj = prik_float64_to_python(&doubled);
    if (result_0_obj == NULL) {
        return NULL;
    }
    PyObject * result_1_obj = prik_int32_to_python(&status);
    if (result_1_obj == NULL) {
        Py_DECREF(result_0_obj);
        return NULL;
    }
    PyObject * result_obj = PyTuple_New(2);
    if (result_obj == NULL) {
        Py_DECREF(result_0_obj);
        Py_DECREF(result_1_obj);
        return NULL;
    }
    PyTuple_SET_ITEM(result_obj, 0, result_0_obj);
    PyTuple_SET_ITEM(result_obj, 1, result_1_obj);
    return result_obj;
}

static PyObject * wrap_reset_allocatable_item(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", NULL};
    PyObject * bound_value_obj;
    void * bound_value = NULL;
    int bound_value_derived_access = 0;
    prik_derived_origin_ops * bound_value_derived_ops = NULL;
    void * bound_value_derived_identity = NULL;
    int bound_value_derived_status = 0;
    int bound_value_descriptor_output_present = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_value_obj)) return NULL;
    if (bound_value_obj != Py_None) {
        int bound_value_extract_status = prik_extract_derived_argument(bound_value_obj, "holder_item", "holder_item", "prik.derived.holder_item", "value", prik_derived_cases_refactoring_goldens_reset_allocatable_item_value, sizeof(prik_derived_cases_refactoring_goldens_reset_allocatable_item_value) / sizeof(prik_derived_cases_refactoring_goldens_reset_allocatable_item_value[0]), &bound_value, &bound_value_derived_access, &bound_value_derived_ops);
        if (bound_value_extract_status < 0) {
            return NULL;
        }
    } else {
        bound_value_derived_access = 3;
    }
    bound_value_derived_identity = bound_value_derived_ops != NULL ? (void *)bound_value_derived_ops : bound_value;
    bind_c_reset_allocatable_item(bound_value, bound_value_derived_access, bound_value_derived_identity, bound_value_derived_ops != NULL ? bound_value_derived_ops->scoped : NULL, bound_value_derived_ops != NULL ? bound_value_derived_ops->checkout : NULL, bound_value_derived_ops != NULL ? bound_value_derived_ops->restore : NULL, &bound_value_derived_status, &bound_value, &bound_value_descriptor_output_present);
    if (bound_value_derived_status != 0) {
        if (bound_value_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "value");
        } else {
            if (bound_value_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "value", bound_value_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    PyObject * result_obj = NULL;
    if (bound_value_obj != Py_None) {
        Py_INCREF(bound_value_obj);
        result_obj = bound_value_obj;
    } else {
        if (!bound_value_descriptor_output_present) {
            if (bound_value != NULL) {
                bind_c_prik_destroy_holder_item_allocatable_holder(bound_value);
            }
            Py_INCREF(Py_None);
            result_obj = Py_None;
        } else {
            PyObject * result_obj_capsule = PyCapsule_New(bound_value, "prik.derived.holder_item.allocatable_holder", prik_destroy_holder_item_allocatable_holder_capsule);
            if (result_obj_capsule == NULL) {
                bind_c_prik_destroy_holder_item_allocatable_holder(bound_value);
                return NULL;
            }
            PyObject * result_obj_helper = PyObject_GetAttrString(self, "_prik_wrap_holder_item");
            if (result_obj_helper == NULL) {
                Py_DECREF(result_obj_capsule);
                return NULL;
            }
            PyObject * result_obj_ops = PyObject_GetAttrString(self, "_prik_ops_holder_item_allocatable_holder");
            if (result_obj_ops == NULL) {
                Py_DECREF(result_obj_helper);
                Py_DECREF(result_obj_capsule);
                return NULL;
            }
            result_obj = PyObject_CallFunction(result_obj_helper, "OOOs", result_obj_capsule, Py_None, result_obj_ops, "allocatable_holder");
            Py_DECREF(result_obj_ops);
            Py_DECREF(result_obj_helper);
            Py_DECREF(result_obj_capsule);
            if (result_obj == NULL) {
                return NULL;
            }
        }
    }
    return result_obj;
}

static PyObject * wrap_shift_pointer_item(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", "amount", NULL};
    PyObject * bound_value_obj;
    void * bound_value = NULL;
    int bound_value_derived_access = 0;
    prik_derived_origin_ops * bound_value_derived_ops = NULL;
    void * bound_value_derived_identity = NULL;
    int bound_value_derived_status = 0;
    int bound_value_descriptor_output_present = 0;
    PyObject * bound_amount_obj;
    double bound_amount;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_value_obj, &bound_amount_obj)) return NULL;
    if (bound_value_obj != Py_None) {
        int bound_value_extract_status = prik_extract_derived_argument(bound_value_obj, "holder_item", "holder_item", "prik.derived.holder_item", "value", prik_derived_cases_refactoring_goldens_shift_pointer_item_value, sizeof(prik_derived_cases_refactoring_goldens_shift_pointer_item_value) / sizeof(prik_derived_cases_refactoring_goldens_shift_pointer_item_value[0]), &bound_value, &bound_value_derived_access, &bound_value_derived_ops);
        if (bound_value_extract_status < 0) {
            return NULL;
        }
    } else {
        bound_value_derived_access = 4;
    }
    bound_value_derived_identity = bound_value_derived_ops != NULL ? (void *)bound_value_derived_ops : bound_value;
    if (prik_float64_unpack_exact(bound_amount_obj, &bound_amount) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument amount. Received <class '%s'>", Py_TYPE(bound_amount_obj)->tp_name); } return NULL; };
    bind_c_shift_pointer_item(bound_value, bound_value_derived_access, bound_value_derived_identity, bound_value_derived_ops != NULL ? bound_value_derived_ops->scoped : NULL, bound_value_derived_ops != NULL ? bound_value_derived_ops->checkout : NULL, bound_value_derived_ops != NULL ? bound_value_derived_ops->restore : NULL, &bound_value_derived_status, &bound_value, &bound_value_descriptor_output_present, bound_amount);
    if (bound_value_derived_status != 0) {
        if (bound_value_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "value");
        } else {
            if (bound_value_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "value", bound_value_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    PyObject * result_obj = NULL;
    if (bound_value_obj != Py_None) {
        Py_INCREF(bound_value_obj);
        result_obj = bound_value_obj;
    } else {
        if (!bound_value_descriptor_output_present) {
            if (bound_value != NULL) {
                bind_c_prik_destroy_holder_item_pointer_holder(bound_value);
            }
            Py_INCREF(Py_None);
            result_obj = Py_None;
        } else {
            PyObject * result_obj_capsule = PyCapsule_New(bound_value, "prik.derived.holder_item.pointer_holder", prik_destroy_holder_item_pointer_holder_capsule);
            if (result_obj_capsule == NULL) {
                bind_c_prik_destroy_holder_item_pointer_holder(bound_value);
                return NULL;
            }
            PyObject * result_obj_helper = PyObject_GetAttrString(self, "_prik_wrap_holder_item");
            if (result_obj_helper == NULL) {
                Py_DECREF(result_obj_capsule);
                return NULL;
            }
            PyObject * result_obj_ops = PyObject_GetAttrString(self, "_prik_ops_holder_item_pointer_holder");
            if (result_obj_ops == NULL) {
                Py_DECREF(result_obj_helper);
                Py_DECREF(result_obj_capsule);
                return NULL;
            }
            result_obj = PyObject_CallFunction(result_obj_helper, "OOOs", result_obj_capsule, self, result_obj_ops, "pointer_holder");
            Py_DECREF(result_obj_ops);
            Py_DECREF(result_obj_helper);
            Py_DECREF(result_obj_capsule);
            if (result_obj == NULL) {
                return NULL;
            }
        }
    }
    return result_obj;
}

static PyObject * wrap__prik_class_vector_scale(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"self", "factor", NULL};
    PyObject * bound_self_obj;
    void * bound_self = NULL;
    int bound_self_derived_access = 0;
    prik_derived_origin_ops * bound_self_derived_ops = NULL;
    void * bound_self_derived_identity = NULL;
    int bound_self_derived_status = 0;
    int bound_self_polymorphic = 0;
    const char * bound_self_polymorphic_type_name = NULL;
    const char * bound_self_polymorphic_type_symbol = NULL;
    const char * bound_self_polymorphic_capsule_name = NULL;
    PyObject * bound_self_polymorphic_expected = NULL;
    PyObject * bound_factor_obj;
    double bound_factor;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_self_obj, &bound_factor_obj)) return NULL;
    if (bound_self_obj != Py_None) {
        bound_self_polymorphic_expected = PyObject_GetAttrString(self, "vector");
        if (bound_self_polymorphic_expected == NULL) {
            return NULL;
        }
        if (Py_TYPE(bound_self_obj) == (PyTypeObject *)bound_self_polymorphic_expected) {
            bound_self_polymorphic = 1;
            bound_self_polymorphic_type_name = "vector";
            bound_self_polymorphic_type_symbol = "vector";
            bound_self_polymorphic_capsule_name = "prik.derived.vector";
        }
        Py_DECREF(bound_self_polymorphic_expected);
        if (bound_self_polymorphic == 0) {
            PyErr_Format(PyExc_TypeError, "argument self requires exact polymorphic wrapper type: vector");
            return NULL;
        }
        int bound_self_extract_status = prik_extract_derived_argument(bound_self_obj, bound_self_polymorphic_type_name, bound_self_polymorphic_type_symbol, bound_self_polymorphic_capsule_name, "self", prik_derived_cases_refactoring_goldens_vector___method___scale_self, sizeof(prik_derived_cases_refactoring_goldens_vector___method___scale_self) / sizeof(prik_derived_cases_refactoring_goldens_vector___method___scale_self[0]), &bound_self, &bound_self_derived_access, &bound_self_derived_ops);
        if (bound_self_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument self requires a derived wrapper");
        return NULL;
    }
    bound_self_derived_identity = bound_self_derived_ops != NULL ? (void *)bound_self_derived_ops : bound_self;
    if (prik_float64_unpack_exact(bound_factor_obj, &bound_factor) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument factor. Received <class '%s'>", Py_TYPE(bound_factor_obj)->tp_name); } return NULL; };
    bind_c__prik_class_vector_scale(bound_self, bound_self_derived_access, bound_self_derived_identity, bound_self_polymorphic, bound_self_derived_ops != NULL ? bound_self_derived_ops->scoped : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->checkout : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->restore : NULL, &bound_self_derived_status, bound_factor);
    if (bound_self_derived_status != 0) {
        if (bound_self_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "self");
        } else {
            if (bound_self_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "self", bound_self_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * wrap__prik_class_vector_shift(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"dx", "owner", "dy", NULL};
    PyObject * bound_dx_obj;
    double bound_dx;
    PyObject * bound_owner_obj;
    void * bound_owner = NULL;
    int bound_owner_derived_access = 0;
    prik_derived_origin_ops * bound_owner_derived_ops = NULL;
    void * bound_owner_derived_identity = NULL;
    int bound_owner_derived_status = 0;
    int bound_owner_polymorphic = 0;
    const char * bound_owner_polymorphic_type_name = NULL;
    const char * bound_owner_polymorphic_type_symbol = NULL;
    const char * bound_owner_polymorphic_capsule_name = NULL;
    PyObject * bound_owner_polymorphic_expected = NULL;
    PyObject * bound_dy_obj;
    double bound_dy;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OOO", kwlist, &bound_dx_obj, &bound_owner_obj, &bound_dy_obj)) return NULL;
    if (prik_float64_unpack_exact(bound_dx_obj, &bound_dx) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument dx. Received <class '%s'>", Py_TYPE(bound_dx_obj)->tp_name); } return NULL; };
    if (bound_owner_obj != Py_None) {
        bound_owner_polymorphic_expected = PyObject_GetAttrString(self, "vector");
        if (bound_owner_polymorphic_expected == NULL) {
            return NULL;
        }
        if (Py_TYPE(bound_owner_obj) == (PyTypeObject *)bound_owner_polymorphic_expected) {
            bound_owner_polymorphic = 1;
            bound_owner_polymorphic_type_name = "vector";
            bound_owner_polymorphic_type_symbol = "vector";
            bound_owner_polymorphic_capsule_name = "prik.derived.vector";
        }
        Py_DECREF(bound_owner_polymorphic_expected);
        if (bound_owner_polymorphic == 0) {
            PyErr_Format(PyExc_TypeError, "argument owner requires exact polymorphic wrapper type: vector");
            return NULL;
        }
        int bound_owner_extract_status = prik_extract_derived_argument(bound_owner_obj, bound_owner_polymorphic_type_name, bound_owner_polymorphic_type_symbol, bound_owner_polymorphic_capsule_name, "owner", prik_derived_cases_refactoring_goldens_vector___method___shift_owner, sizeof(prik_derived_cases_refactoring_goldens_vector___method___shift_owner) / sizeof(prik_derived_cases_refactoring_goldens_vector___method___shift_owner[0]), &bound_owner, &bound_owner_derived_access, &bound_owner_derived_ops);
        if (bound_owner_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument owner requires a derived wrapper");
        return NULL;
    }
    bound_owner_derived_identity = bound_owner_derived_ops != NULL ? (void *)bound_owner_derived_ops : bound_owner;
    if (prik_float64_unpack_exact(bound_dy_obj, &bound_dy) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument dy. Received <class '%s'>", Py_TYPE(bound_dy_obj)->tp_name); } return NULL; };
    bind_c__prik_class_vector_shift(bound_dx, bound_owner, bound_owner_derived_access, bound_owner_derived_identity, bound_owner_polymorphic, bound_owner_derived_ops != NULL ? bound_owner_derived_ops->scoped : NULL, bound_owner_derived_ops != NULL ? bound_owner_derived_ops->checkout : NULL, bound_owner_derived_ops != NULL ? bound_owner_derived_ops->restore : NULL, &bound_owner_derived_status, bound_dy);
    if (bound_owner_derived_status != 0) {
        if (bound_owner_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "owner");
        } else {
            if (bound_owner_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "owner", bound_owner_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * wrap__prik_class_vector_magnitude(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"self", NULL};
    PyObject * bound_self_obj;
    void * bound_self = NULL;
    int bound_self_derived_access = 0;
    prik_derived_origin_ops * bound_self_derived_ops = NULL;
    void * bound_self_derived_identity = NULL;
    int bound_self_derived_status = 0;
    int bound_self_polymorphic = 0;
    const char * bound_self_polymorphic_type_name = NULL;
    const char * bound_self_polymorphic_type_symbol = NULL;
    const char * bound_self_polymorphic_capsule_name = NULL;
    PyObject * bound_self_polymorphic_expected = NULL;
    double result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_self_obj)) return NULL;
    if (bound_self_obj != Py_None) {
        bound_self_polymorphic_expected = PyObject_GetAttrString(self, "vector");
        if (bound_self_polymorphic_expected == NULL) {
            return NULL;
        }
        if (Py_TYPE(bound_self_obj) == (PyTypeObject *)bound_self_polymorphic_expected) {
            bound_self_polymorphic = 1;
            bound_self_polymorphic_type_name = "vector";
            bound_self_polymorphic_type_symbol = "vector";
            bound_self_polymorphic_capsule_name = "prik.derived.vector";
        }
        Py_DECREF(bound_self_polymorphic_expected);
        if (bound_self_polymorphic == 0) {
            PyErr_Format(PyExc_TypeError, "argument self requires exact polymorphic wrapper type: vector");
            return NULL;
        }
        int bound_self_extract_status = prik_extract_derived_argument(bound_self_obj, bound_self_polymorphic_type_name, bound_self_polymorphic_type_symbol, bound_self_polymorphic_capsule_name, "self", prik_derived_cases_refactoring_goldens_vector___method___magnitude_self, sizeof(prik_derived_cases_refactoring_goldens_vector___method___magnitude_self) / sizeof(prik_derived_cases_refactoring_goldens_vector___method___magnitude_self[0]), &bound_self, &bound_self_derived_access, &bound_self_derived_ops);
        if (bound_self_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument self requires a derived wrapper");
        return NULL;
    }
    bound_self_derived_identity = bound_self_derived_ops != NULL ? (void *)bound_self_derived_ops : bound_self;
    result = bind_c__prik_class_vector_magnitude(bound_self, bound_self_derived_access, bound_self_derived_identity, bound_self_polymorphic, bound_self_derived_ops != NULL ? bound_self_derived_ops->scoped : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->checkout : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->restore : NULL, &bound_self_derived_status);
    if (bound_self_derived_status != 0) {
        if (bound_self_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "self");
        } else {
            if (bound_self_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "self", bound_self_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    PyObject * result_obj = prik_float64_to_python(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap__prik_class_vector_replace_samples(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"self", "values", NULL};
    PyObject * bound_self_obj;
    void * bound_self = NULL;
    int bound_self_derived_access = 0;
    prik_derived_origin_ops * bound_self_derived_ops = NULL;
    void * bound_self_derived_identity = NULL;
    int bound_self_derived_status = 0;
    int bound_self_polymorphic = 0;
    const char * bound_self_polymorphic_type_name = NULL;
    const char * bound_self_polymorphic_type_symbol = NULL;
    const char * bound_self_polymorphic_capsule_name = NULL;
    PyObject * bound_self_polymorphic_expected = NULL;
    PyObject * bound_values_obj;
    void * bound_values = NULL;
    int64_t bound_values_extent_0 = 0;
    int64_t bound_values_upper_bound_0 = 0;
    int64_t bound_values_stride_0 = 1;
    int bound_values_dense_actual = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_self_obj, &bound_values_obj)) return NULL;
    if (bound_self_obj != Py_None) {
        bound_self_polymorphic_expected = PyObject_GetAttrString(self, "vector");
        if (bound_self_polymorphic_expected == NULL) {
            return NULL;
        }
        if (Py_TYPE(bound_self_obj) == (PyTypeObject *)bound_self_polymorphic_expected) {
            bound_self_polymorphic = 1;
            bound_self_polymorphic_type_name = "vector";
            bound_self_polymorphic_type_symbol = "vector";
            bound_self_polymorphic_capsule_name = "prik.derived.vector";
        }
        Py_DECREF(bound_self_polymorphic_expected);
        if (bound_self_polymorphic == 0) {
            PyErr_Format(PyExc_TypeError, "argument self requires exact polymorphic wrapper type: vector");
            return NULL;
        }
        int bound_self_extract_status = prik_extract_derived_argument(bound_self_obj, bound_self_polymorphic_type_name, bound_self_polymorphic_type_symbol, bound_self_polymorphic_capsule_name, "self", prik_derived_cases_refactoring_goldens_vector___method___replace_samples_self, sizeof(prik_derived_cases_refactoring_goldens_vector___method___replace_samples_self) / sizeof(prik_derived_cases_refactoring_goldens_vector___method___replace_samples_self[0]), &bound_self, &bound_self_derived_access, &bound_self_derived_ops);
        if (bound_self_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument self requires a derived wrapper");
        return NULL;
    }
    bound_self_derived_identity = bound_self_derived_ops != NULL ? (void *)bound_self_derived_ops : bound_self;
    if (PyArray_Check(bound_values_obj)) {
        if (prik_array_validate(bound_values_obj, NPY_FLOAT64, 1, 1, PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F, 0, 0, "numpy.float64", "values") < 0) return NULL;
        bound_values = PyArray_DATA((PyArrayObject *)bound_values_obj);
        bound_values_dense_actual = PyArray_IS_F_CONTIGUOUS((PyArrayObject *)bound_values_obj);
        bound_values_extent_0 = (int64_t)PyArray_DIM((PyArrayObject *)bound_values_obj, 0);
        if (!bound_values_dense_actual) {
            bound_values_stride_0 = PyArray_SIZE((PyArrayObject *)bound_values_obj) == 0 ? 1 : (PyArray_STRIDE((PyArrayObject *)bound_values_obj, 0) / PyArray_ITEMSIZE((PyArrayObject *)bound_values_obj)) / (1);
            bound_values_upper_bound_0 = bound_values_extent_0 == 0 ? -1 : (bound_values_extent_0 - 1) * bound_values_stride_0;
            bound_values_extent_0 = bound_values_upper_bound_0 + 1;
        }
    } else {
        PyObject * bound_values_shape = NULL;
        prik_array_actual bound_values_actual;
        bound_values_shape = PyTuple_New(1);
        if (bound_values_shape == NULL) return NULL;
        Py_INCREF(Py_None);
        PyTuple_SET_ITEM(bound_values_shape, 0, Py_None);
        if (PyTuple_GET_ITEM(bound_values_shape, 0) == NULL) { Py_DECREF(bound_values_shape); return NULL; };
        if (prik_array_actual_unpack(bound_values_obj, "float64", 1, bound_values_shape, NULL, 0, 1, 1, 0, 0, 1, 0, 0, -1, &bound_values_actual) < 0) { Py_DECREF(bound_values_shape); return NULL; };
        Py_DECREF(bound_values_shape);
        bound_values = bound_values_actual.data;
        bound_values_extent_0 = bound_values_actual.extents[0];
        bound_values_upper_bound_0 = bound_values_actual.upper_bounds[0];
        bound_values_stride_0 = bound_values_actual.strides[0];
    }
    bind_c__prik_class_vector_replace_samples(bound_self, bound_self_derived_access, bound_self_derived_identity, bound_self_polymorphic, bound_self_derived_ops != NULL ? bound_self_derived_ops->scoped : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->checkout : NULL, bound_self_derived_ops != NULL ? bound_self_derived_ops->restore : NULL, &bound_self_derived_status, bound_values, bound_values_dense_actual, bound_values_extent_0, bound_values_upper_bound_0, bound_values_stride_0);
    if (bound_self_derived_status != 0) {
        if (bound_self_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "self");
        } else {
            if (bound_self_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "self", bound_self_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * wrap__prik_class_vector___add___0(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"left", "right", NULL};
    PyObject * bound_left_obj;
    void * bound_left = NULL;
    int bound_left_derived_access = 0;
    prik_derived_origin_ops * bound_left_derived_ops = NULL;
    void * bound_left_derived_identity = NULL;
    int bound_left_derived_status = 0;
    int bound_left_polymorphic = 0;
    const char * bound_left_polymorphic_type_name = NULL;
    const char * bound_left_polymorphic_type_symbol = NULL;
    const char * bound_left_polymorphic_capsule_name = NULL;
    PyObject * bound_left_polymorphic_expected = NULL;
    PyObject * bound_right_obj;
    void * bound_right = NULL;
    int bound_right_derived_access = 0;
    prik_derived_origin_ops * bound_right_derived_ops = NULL;
    void * bound_right_derived_identity = NULL;
    int bound_right_derived_status = 0;
    prik_derived_alias_entry prik_derived_aliases[2];
    void * result = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_left_obj, &bound_right_obj)) return NULL;
    if (bound_left_obj != Py_None) {
        bound_left_polymorphic_expected = PyObject_GetAttrString(self, "vector");
        if (bound_left_polymorphic_expected == NULL) {
            return NULL;
        }
        if (Py_TYPE(bound_left_obj) == (PyTypeObject *)bound_left_polymorphic_expected) {
            bound_left_polymorphic = 1;
            bound_left_polymorphic_type_name = "vector";
            bound_left_polymorphic_type_symbol = "vector";
            bound_left_polymorphic_capsule_name = "prik.derived.vector";
        }
        Py_DECREF(bound_left_polymorphic_expected);
        if (bound_left_polymorphic == 0) {
            PyErr_Format(PyExc_TypeError, "argument left requires exact polymorphic wrapper type: vector");
            return NULL;
        }
        int bound_left_extract_status = prik_extract_derived_argument(bound_left_obj, bound_left_polymorphic_type_name, bound_left_polymorphic_type_symbol, bound_left_polymorphic_capsule_name, "left", prik_derived_cases_refactoring_goldens_vector___add___add_vectors_left, sizeof(prik_derived_cases_refactoring_goldens_vector___add___add_vectors_left) / sizeof(prik_derived_cases_refactoring_goldens_vector___add___add_vectors_left[0]), &bound_left, &bound_left_derived_access, &bound_left_derived_ops);
        if (bound_left_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument left requires a derived wrapper");
        return NULL;
    }
    bound_left_derived_identity = bound_left_derived_ops != NULL ? (void *)bound_left_derived_ops : bound_left;
    if (bound_right_obj != Py_None) {
        int bound_right_extract_status = prik_extract_derived_argument(bound_right_obj, "vector", "vector", "prik.derived.vector", "right", prik_derived_cases_refactoring_goldens_vector___add___add_vectors_right, sizeof(prik_derived_cases_refactoring_goldens_vector___add___add_vectors_right) / sizeof(prik_derived_cases_refactoring_goldens_vector___add___add_vectors_right[0]), &bound_right, &bound_right_derived_access, &bound_right_derived_ops);
        if (bound_right_extract_status < 0) {
            return NULL;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "argument right requires a derived wrapper");
        return NULL;
    }
    bound_right_derived_identity = bound_right_derived_ops != NULL ? (void *)bound_right_derived_ops : bound_right;
    prik_derived_aliases[0].identity = bound_left_derived_identity;
    prik_derived_aliases[0].writable = 0;
    prik_derived_aliases[0].argument_name = "left";
    prik_derived_aliases[1].identity = bound_right_derived_identity;
    prik_derived_aliases[1].writable = 0;
    prik_derived_aliases[1].argument_name = "right";
    if (prik_validate_derived_aliases(prik_derived_aliases, 2) < 0) {
        return NULL;
    }
    result = bind_c__prik_class_vector___add___0(bound_left, bound_left_derived_access, bound_left_derived_identity, bound_left_polymorphic, bound_left_derived_ops != NULL ? bound_left_derived_ops->scoped : NULL, bound_left_derived_ops != NULL ? bound_left_derived_ops->checkout : NULL, bound_left_derived_ops != NULL ? bound_left_derived_ops->restore : NULL, &bound_left_derived_status, bound_right, bound_right_derived_access, bound_right_derived_identity, bound_right_derived_ops != NULL ? bound_right_derived_ops->scoped : NULL, bound_right_derived_ops != NULL ? bound_right_derived_ops->checkout : NULL, bound_right_derived_ops != NULL ? bound_right_derived_ops->restore : NULL, &bound_right_derived_status);
    if (bound_left_derived_status != 0) {
        if (bound_left_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "left");
        } else {
            if (bound_left_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "left", bound_left_derived_status);
            }
        }
        return NULL;
    }
    if (bound_right_derived_status != 0) {
        if (bound_right_derived_status == 1) {
            PyErr_Format(PyExc_ValueError, "derived payload for argument %s is not present", "right");
        } else {
            if (bound_right_derived_status == 4) {
                PyErr_NoMemory();
            } else {
                PyErr_Format(PyExc_RuntimeError, "derived origin failure for argument %s (status %d)", "right", bound_right_derived_status);
            }
        }
        return NULL;
    }
    const char * prik_derived_after_native_fault = getenv("PRIK_WRAPPER_FAIL_DERIVED_AFTER_NATIVE");
    if (prik_derived_after_native_fault != NULL && prik_derived_after_native_fault[0] != '\0' && prik_derived_after_native_fault[0] != '0') {
        if (result != NULL) { bind_c_prik_destroy_vector(result); result = NULL; };
        PyErr_SetString(PyExc_RuntimeError, "injected derived failure after native return");
        return NULL;
    }
    if (result == NULL) {
        if (result != NULL) { bind_c_prik_destroy_vector(result); result = NULL; };
        PyErr_NoMemory();
        return NULL;
    }
    if (result == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    PyObject * result_obj_capsule = PyCapsule_New(result, "prik.derived.vector", prik_destroy_vector_capsule);
    if (result_obj_capsule == NULL) {
        bind_c_prik_destroy_vector(result);
        return NULL;
    }
    PyObject * result_obj_helper = PyObject_GetAttrString(self, "_prik_wrap_vector");
    if (result_obj_helper == NULL) {
        Py_DECREF(result_obj_capsule);
        return NULL;
    }
    PyObject * result_obj = PyObject_CallFunctionObjArgs(result_obj_helper, result_obj_capsule, NULL);
    Py_DECREF(result_obj_helper);
    Py_DECREF(result_obj_capsule);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap__prik_overload_convert_0(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", NULL};
    PyObject * bound_value_obj;
    int32_t bound_value;
    double result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_value_obj)) return NULL;
    if (prik_int32_unpack_exact(bound_value_obj, &bound_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.int32 for argument value. Received <class '%s'>", Py_TYPE(bound_value_obj)->tp_name); } return NULL; };
    result = bind_c__prik_overload_convert_0(bound_value);
    PyObject * result_obj = prik_float64_to_python(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * wrap__prik_overload_convert_1(PyObject * self, PyObject * args, PyObject * kwargs) {
    static char * kwlist[] = {"value", NULL};
    PyObject * bound_value_obj;
    double bound_value;
    int32_t result;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &bound_value_obj)) return NULL;
    if (prik_float64_unpack_exact(bound_value_obj, &bound_value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.float64 for argument value. Received <class '%s'>", Py_TYPE(bound_value_obj)->tp_name); } return NULL; };
    result = bind_c__prik_overload_convert_1(bound_value);
    PyObject * result_obj = prik_int32_to_python(&result);
    if (result_obj == NULL) {
        return NULL;
    }
    return result_obj;
}

static PyObject * module_get_counter(void) {
    int32_t value = bind_c_get_counter();
    PyObject * result = prik_int32_to_numpy(&value);
    return result;
}

static int module_set_counter(PyObject * value_obj) {
    int32_t value;
    if (prik_int32_unpack_exact(value_obj, &value) < 0) { if (!PyErr_Occurred()) { PyErr_Format(PyExc_TypeError, "Expected an argument of type numpy.int32 for module variable counter. Received <class '%s'>", Py_TYPE(value_obj)->tp_name); } return -1; };
    bind_c_set_counter(value);
    return 0;
}

static PyObject * module_get_workspace(void) {
    if (prik_module_refactoring_goldens_workspace_handle != NULL) {
        Py_INCREF(prik_module_refactoring_goldens_workspace_handle);
        return prik_module_refactoring_goldens_workspace_handle;
    }
    PyObject * prik_module_refactoring_goldens_workspace_handle_build_ops = PyDict_New();
    PyObject * prik_module_refactoring_goldens_workspace_handle_build_operation = NULL;
    PyObject * prik_module_refactoring_goldens_workspace_handle_build_runtime = NULL;
    PyObject * prik_module_refactoring_goldens_workspace_handle_build_helper = NULL;
    if (prik_module_refactoring_goldens_workspace_handle_build_ops == NULL) {
        return NULL;
    }
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_aligned_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "aligned", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_allocated_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "allocated", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_array_actual_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "array_actual", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_deallocate_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "deallocate", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_descriptor_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "descriptor", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_layout_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "layout", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_native_byte_order_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "native_byte_order", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_resize_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "resize", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_shape_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "shape", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_to_numpy_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "to_numpy", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_workspace_writeable_def, NULL, NULL);
    if (prik_module_refactoring_goldens_workspace_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_workspace_handle_build_ops, "writeable", prik_module_refactoring_goldens_workspace_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_operation);
    prik_module_refactoring_goldens_workspace_handle_build_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (prik_module_refactoring_goldens_workspace_handle_build_runtime == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    prik_module_refactoring_goldens_workspace_handle_build_helper = PyObject_GetAttrString(prik_module_refactoring_goldens_workspace_handle_build_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_runtime);
    if (prik_module_refactoring_goldens_workspace_handle_build_helper == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
        return NULL;
    }
    prik_module_refactoring_goldens_workspace_handle = PyObject_CallFunction(prik_module_refactoring_goldens_workspace_handle_build_helper, "ssiOOssO", "allocatable", "float64", 1, prik_module_refactoring_goldens_workspace_handle_build_ops, prik_module_refactoring_goldens_workspace_owner != NULL ? prik_module_refactoring_goldens_workspace_owner : Py_None, "borrowed", "descriptor_view", Py_None);
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_helper);
    Py_DECREF(prik_module_refactoring_goldens_workspace_handle_build_ops);
    if (prik_module_refactoring_goldens_workspace_handle == NULL) {
        return NULL;
    }
    Py_INCREF(prik_module_refactoring_goldens_workspace_handle);
    return prik_module_refactoring_goldens_workspace_handle;
}

static PyObject * module_get_selected(void) {
    if (prik_module_refactoring_goldens_selected_handle != NULL) {
        Py_INCREF(prik_module_refactoring_goldens_selected_handle);
        return prik_module_refactoring_goldens_selected_handle;
    }
    PyObject * prik_module_refactoring_goldens_selected_handle_build_ops = PyDict_New();
    PyObject * prik_module_refactoring_goldens_selected_handle_build_operation = NULL;
    PyObject * prik_module_refactoring_goldens_selected_handle_build_runtime = NULL;
    PyObject * prik_module_refactoring_goldens_selected_handle_build_helper = NULL;
    if (prik_module_refactoring_goldens_selected_handle_build_ops == NULL) {
        return NULL;
    }
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_aligned_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "aligned", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_array_actual_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "array_actual", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_associate_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "associate", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_associated_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "associated", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_contiguous_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "contiguous", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_descriptor_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "descriptor", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_layout_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "layout", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_native_byte_order_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "native_byte_order", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_nullify_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "nullify", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_shape_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "shape", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_to_numpy_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "to_numpy", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_operation = PyCFunction_NewEx(&prik_module_refactoring_goldens_selected_writeable_def, NULL, NULL);
    if (prik_module_refactoring_goldens_selected_handle_build_operation == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    if (PyDict_SetItemString(prik_module_refactoring_goldens_selected_handle_build_ops, "writeable", prik_module_refactoring_goldens_selected_handle_build_operation) < 0) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_operation);
    prik_module_refactoring_goldens_selected_handle_build_runtime = PyImport_ImportModule("prik.runtime.handles");
    if (prik_module_refactoring_goldens_selected_handle_build_runtime == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    prik_module_refactoring_goldens_selected_handle_build_helper = PyObject_GetAttrString(prik_module_refactoring_goldens_selected_handle_build_runtime, "_native_array_handle_from_generated_ops");
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_runtime);
    if (prik_module_refactoring_goldens_selected_handle_build_helper == NULL) {
        Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
        return NULL;
    }
    prik_module_refactoring_goldens_selected_handle = PyObject_CallFunction(prik_module_refactoring_goldens_selected_handle_build_helper, "ssiOOssO", "pointer", "float64", 1, prik_module_refactoring_goldens_selected_handle_build_ops, prik_module_refactoring_goldens_selected_owner != NULL ? prik_module_refactoring_goldens_selected_owner : Py_None, "borrowed", "unsupported", Py_None);
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_helper);
    Py_DECREF(prik_module_refactoring_goldens_selected_handle_build_ops);
    if (prik_module_refactoring_goldens_selected_handle == NULL) {
        return NULL;
    }
    Py_INCREF(prik_module_refactoring_goldens_selected_handle);
    return prik_module_refactoring_goldens_selected_handle;
}

static PyObject * module_get_active_vector(void) {
    PyObject * capsule = Py_None;
    PyObject * helper = PyObject_GetAttrString(prik_module_refactoring_goldens_active_vector_derived_owner, "_prik_wrap_vector");
    if (helper == NULL) {
        return NULL;
    }
    PyObject * ops = PyObject_GetAttrString(prik_module_refactoring_goldens_active_vector_derived_owner, "_prik_ops_active_vector");
    if (ops == NULL) {
        Py_DECREF(helper);
        return NULL;
    }
    PyObject * result = PyObject_CallFunction(helper, "OOOs", capsule, prik_module_refactoring_goldens_active_vector_derived_owner, ops, "module_allocatable");
    Py_DECREF(helper);
    Py_DECREF(ops);
    return result;
}

static PyObject * module_get_selected_vector(void) {
    PyObject * capsule = Py_None;
    PyObject * helper = PyObject_GetAttrString(prik_module_refactoring_goldens_selected_vector_derived_owner, "_prik_wrap_vector");
    if (helper == NULL) {
        return NULL;
    }
    PyObject * ops = PyObject_GetAttrString(prik_module_refactoring_goldens_selected_vector_derived_owner, "_prik_ops_selected_vector");
    if (ops == NULL) {
        Py_DECREF(helper);
        return NULL;
    }
    PyObject * result = PyObject_CallFunction(helper, "OOOs", capsule, prik_module_refactoring_goldens_selected_vector_derived_owner, ops, "module_pointer");
    Py_DECREF(helper);
    Py_DECREF(ops);
    return result;
}

static PyObject * wrap__prik_dispatch_convert_d27e6413(PyObject * self, PyObject * args, PyObject * kwargs) {
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    Py_ssize_t user_nargs = nargs;
    int candidate_id = -1;
    if (candidate_id < 0 && (user_nargs <= 1 && (kwargs == NULL || (PyDict_Size(kwargs) == ((PyDict_GetItemString(kwargs, "value") != NULL)) && (user_nargs <= 0 || PyDict_GetItemString(kwargs, "value") == NULL))) && ((user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL)) != NULL && (PyArray_IsScalar((user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL)), Int))))) {
        candidate_id = 0;
    }
    if (candidate_id < 0 && (user_nargs <= 1 && (kwargs == NULL || (PyDict_Size(kwargs) == ((PyDict_GetItemString(kwargs, "value") != NULL)) && (user_nargs <= 0 || PyDict_GetItemString(kwargs, "value") == NULL))) && ((user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL)) != NULL && (PyArray_IsScalar((user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL)), Double))))) {
        candidate_id = 1;
    }
    switch (candidate_id) {
        case 0: {
            PyObject * candidate_kwargs = PyDict_New();
            if (candidate_kwargs == NULL) {
                return NULL;
            }
            PyObject * candidate_value_0 = (user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL));
            if (PyDict_SetItemString(candidate_kwargs, "value", candidate_value_0) < 0) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_args = PyTuple_New(0);
            if (candidate_args == NULL) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_result = wrap__prik_overload_convert_0(self, candidate_args, candidate_kwargs);
            Py_DECREF(candidate_args);
            Py_DECREF(candidate_kwargs);
            return candidate_result;
        }
        case 1: {
            PyObject * candidate_kwargs = PyDict_New();
            if (candidate_kwargs == NULL) {
                return NULL;
            }
            PyObject * candidate_value_0 = (user_nargs > 0 ? PyTuple_GET_ITEM(args, 0) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "value") : NULL));
            if (PyDict_SetItemString(candidate_kwargs, "value", candidate_value_0) < 0) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_args = PyTuple_New(0);
            if (candidate_args == NULL) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_result = wrap__prik_overload_convert_1(self, candidate_args, candidate_kwargs);
            Py_DECREF(candidate_args);
            Py_DECREF(candidate_kwargs);
            return candidate_result;
        }
        default: {
            PyErr_SetString(PyExc_TypeError, "no matching overload for convert");
            return NULL;
        }
    }
}

static PyObject * wrap__prik_dispatch_add_eeb3bbc5(PyObject * self, PyObject * args, PyObject * kwargs) {
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs < 1) {
        PyErr_SetString(PyExc_TypeError, "no matching overload for __add__");
        return NULL;
    }
    PyObject * receiver = PyTuple_GET_ITEM(args, 0);
    Py_ssize_t user_nargs = nargs - 1;
    int candidate_id = -1;
    if (candidate_id < 0 && (user_nargs <= 1 && (kwargs == NULL || (PyDict_Size(kwargs) == ((PyDict_GetItemString(kwargs, "right") != NULL)) && (user_nargs <= 0 || PyDict_GetItemString(kwargs, "right") == NULL))) && ((user_nargs > 0 ? PyTuple_GET_ITEM(args, 1) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "right") : NULL)) != NULL && (PyDict_GetItemString(PyModule_GetDict(self), "vector") != NULL && (PyObject *)Py_TYPE((user_nargs > 0 ? PyTuple_GET_ITEM(args, 1) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "right") : NULL))) == PyDict_GetItemString(PyModule_GetDict(self), "vector"))))) {
        candidate_id = 0;
    }
    switch (candidate_id) {
        case 0: {
            PyObject * candidate_kwargs = PyDict_New();
            if (candidate_kwargs == NULL) {
                return NULL;
            }
            PyObject * candidate_value_0 = (user_nargs > 0 ? PyTuple_GET_ITEM(args, 1) : (kwargs != NULL ? PyDict_GetItemString(kwargs, "right") : NULL));
            if (PyDict_SetItemString(candidate_kwargs, "right", candidate_value_0) < 0) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            if (PyDict_SetItemString(candidate_kwargs, "left", receiver) < 0) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_args = PyTuple_New(0);
            if (candidate_args == NULL) {
                Py_DECREF(candidate_kwargs);
                return NULL;
            }
            PyObject * candidate_result = wrap__prik_class_vector___add___0(self, candidate_args, candidate_kwargs);
            Py_DECREF(candidate_args);
            Py_DECREF(candidate_kwargs);
            return candidate_result;
        }
        default: {
            PyErr_SetString(PyExc_TypeError, "no matching overload for __add__");
            return NULL;
        }
    }
}

PyMODINIT_FUNC PyInit_refactoring_goldens(void) {
    import_array();
    PyObject * mod = PyModule_Create(&refactoring_goldens_root_module);
    if (mod == NULL) return NULL;
    if (refactoring_goldens_root_module_property_setup(mod) < 0) { Py_DECREF(mod); return NULL; };
    PyObject * root_python_dict = PyModule_GetDict(mod);
    if (root_python_dict == NULL) {
        return NULL;
    }
    PyObject * root_python_setup = PyRun_String("_prik_unset = object()\n\n_prik_ops_holder_item = {'code_get': _prik_field_holder_item_code_get, 'code_set': _prik_field_holder_item_code_set, 'weight_get': _prik_field_holder_item_weight_get, 'weight_set': _prik_field_holder_item_weight_set}\nclass holder_item:\n    'holder_item\\n\\nOpaque wrapper for native type holder_item.\\n\\nConstructor\\n-----------\\nholder_item(*, code=0, weight=0) -> holder_item\\n\\nFields\\n------\\ncode : int32\\nweight : float64'\n    __slots__ = ('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')\n    def __new__(cls, *args, **kwargs):\n        return _prik_create_holder_item()\n    def __init__(self, *, code=_prik_unset, weight=_prik_unset):\n        'holder_item(*, code=0, weight=0) -> holder_item\\n\\nParameters\\n----------\\ncode : int32\\nweight : float64\\n\\nReturns\\n-------\\nholder_item\\n    New wrapper-owned native instance.\\n\\nRaises\\n------\\nTypeError\\n    If the supplied arguments do not satisfy the constructor contract.'\n        if code is not _prik_unset:\n            self.code = code\n        if weight is not _prik_unset:\n            self.weight = weight\n    @property\n    def code(self):\n        'code : int32\\n    Assignment writes through to native storage.'\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        return self._prik_ops['code_get'](self)\n    @code.setter\n    def code(self, value):\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        self._prik_ops['code_set'](self, value)\n    @property\n    def weight(self):\n        'weight : float64\\n    Assignment writes through to native storage.'\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        return self._prik_ops['weight_get'](self)\n    @weight.setter\n    def weight(self, value):\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        self._prik_ops['weight_set'](self, value)\ndef _prik_wrap_holder_item(capsule, owner=None, ops=None, origin='direct'):\n    value = object.__new__(holder_item)\n    value._prik_capsule = capsule\n    value._prik_owner = owner\n    value._prik_ops = _prik_ops_holder_item if ops is None else ops\n    value._prik_origin = origin\n    return value\n\n_prik_ops_vector = {'x_get': _prik_field_vector_x_get, 'x_set': _prik_field_vector_x_set, 'y_get': _prik_field_vector_y_get, 'y_set': _prik_field_vector_y_set, 'samples_get': _prik_field_vector_samples_get}\nclass vector:\n    'vector\\n\\nOpaque wrapper for native type vector.\\n\\nConstructor\\n-----------\\nvector(*, x=0, y=0) -> vector\\n\\nFields\\n------\\nx : float64\\ny : float64\\nsamples : AllocatableArray[float64]\\n\\nMethods\\n-------\\nscale(factor) -> None\\nshift(dx, dy) -> None\\nmagnitude() -> float64\\nreplace_samples(values) -> None\\n__add__(*args, **kwargs)'\n    __slots__ = ('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')\n    def __new__(cls, *args, **kwargs):\n        return _prik_create_vector()\n    def __init__(self, *, x=_prik_unset, y=_prik_unset):\n        'vector(*, x=0, y=0) -> vector\\n\\nParameters\\n----------\\nx : float64\\ny : float64\\n\\nReturns\\n-------\\nvector\\n    New wrapper-owned native instance.\\n\\nRaises\\n------\\nTypeError\\n    If the supplied arguments do not satisfy the constructor contract.'\n        if x is not _prik_unset:\n            self.x = x\n        if y is not _prik_unset:\n            self.y = y\n    @property\n    def x(self):\n        'x : float64\\n    Assignment writes through to native storage.'\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        return self._prik_ops['x_get'](self)\n    @x.setter\n    def x(self, value):\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        self._prik_ops['x_set'](self, value)\n    @property\n    def y(self):\n        'y : float64\\n    Assignment writes through to native storage.'\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        return self._prik_ops['y_get'](self)\n    @y.setter\n    def y(self, value):\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        self._prik_ops['y_set'](self, value)\n    @property\n    def samples(self):\n        'samples : AllocatableArray[float64]\\n    Rank: 1\\n    Live allocatable array descriptor handle.\\n    The parent wrapper retains the descriptor owner.\\n    Replacement assignment is not supported.'\n        present = self._prik_ops.get('_present')\n        if present is not None:\n            present(self)\n        return self._prik_ops['samples_get'](self)\n    @samples.setter\n    def samples(self, value):\n        raise AttributeError('field samples does not support replacement assignment')\n    def scale(self, factor):\n        'scale(factor) -> None\\n\\nParameters\\n----------\\nfactor : float64\\n\\nReturns\\n-------\\nNone\\n\\nRaises\\n------\\nTypeError\\n    If an argument has an incompatible Python type or dtype.\\n\\nNotes\\n-----\\nUpdates the wrapped native instance in place.'\n        return _prik_class_vector_scale(self, factor)\n    def shift(self, dx, dy):\n        'shift(dx, dy) -> None\\n\\nParameters\\n----------\\ndx : float64\\ndy : float64\\n\\nReturns\\n-------\\nNone\\n\\nRaises\\n------\\nTypeError\\n    If an argument has an incompatible Python type or dtype.\\n\\nNotes\\n-----\\nUpdates the wrapped native instance in place.'\n        return _prik_class_vector_shift(dx, self, dy)\n    def magnitude(self):\n        'magnitude() -> float64\\n\\nReturns\\n-------\\nresult : float64\\n\\nRaises\\n------\\nTypeError\\n    If an argument has an incompatible Python type or dtype.'\n        return _prik_class_vector_magnitude(self)\n    def replace_samples(self, values):\n        'replace_samples(values) -> None\\n\\nParameters\\n----------\\nvalues : ndarray[float64]\\n    Rank: 1\\n    Shape: (::Strided)\\n    Ownership: Caller-owned.\\n\\nReturns\\n-------\\nNone\\n\\nRaises\\n------\\nTypeError\\n    If an argument has an incompatible Python type or dtype.\\nValueError\\n    If rank, shape, layout, or descriptor state violates the contract.\\n\\nNotes\\n-----\\nUpdates the wrapped native instance in place.'\n        return _prik_class_vector_replace_samples(self, values)\n    def __add__(self, *args, **kwargs):\n        '__add__(*args, **kwargs)\\n\\nSupported Signatures\\n--------------------\\n__add__(right: vector) -> vector\\n\\nRaises\\n------\\nTypeError\\n    If no supported signature matches the supplied arguments.\\n\\nNotes\\n-----\\nDispatches to a native operation on the wrapped instance.'\n        return _prik_dispatch_add_eeb3bbc5(self, *args, **kwargs)\ndef _prik_wrap_vector(capsule, owner=None, ops=None, origin='direct'):\n    value = object.__new__(vector)\n    value._prik_capsule = capsule\n    value._prik_owner = owner\n    value._prik_ops = _prik_ops_vector if ops is None else ops\n    value._prik_origin = origin\n    return value\n\n_prik_ops_holder_item_allocatable_holder = {'_present': _prik_holder_item_allocatable_holder_require_present, 'code_get': _prik_allocatable_holder_field_holder_item_code_get, 'code_set': _prik_allocatable_holder_field_holder_item_code_set, 'weight_get': _prik_allocatable_holder_field_holder_item_weight_get, 'weight_set': _prik_allocatable_holder_field_holder_item_weight_set}\n\n_prik_ops_holder_item_pointer_holder = {'_present': _prik_holder_item_pointer_holder_require_present, 'code_get': _prik_pointer_holder_field_holder_item_code_get, 'code_set': _prik_pointer_holder_field_holder_item_code_set, 'weight_get': _prik_pointer_holder_field_holder_item_weight_get, 'weight_set': _prik_pointer_holder_field_holder_item_weight_set}\n\n_prik_ops_active_vector = {'_native_ops': _prik_origin_active_vector_26504a12_native_ops(), '_present': _prik_module_active_vector_require_present, 'x_get': _prik_module_field_active_vector_x_get, 'x_set': _prik_module_field_active_vector_x_set, 'y_get': _prik_module_field_active_vector_y_get, 'y_set': _prik_module_field_active_vector_y_set, 'samples_get': _prik_module_field_active_vector_samples_get}\n\n_prik_ops_selected_vector = {'_native_ops': _prik_origin_selected_vector_d2fd3c9d_native_ops(), '_present': _prik_module_selected_vector_require_present, 'x_get': _prik_module_field_selected_vector_x_get, 'x_set': _prik_module_field_selected_vector_x_set, 'y_get': _prik_module_field_selected_vector_y_get, 'y_set': _prik_module_field_selected_vector_y_set, 'samples_get': _prik_module_field_selected_vector_samples_get}", Py_file_input, root_python_dict, root_python_dict);
    if (root_python_setup == NULL) {
        return NULL;
    }
    Py_DECREF(root_python_setup);
    Py_INCREF(mod);
    prik_module_refactoring_goldens_workspace_owner = mod;
    Py_INCREF(mod);
    prik_module_refactoring_goldens_selected_owner = mod;
    Py_INCREF(mod);
    prik_module_refactoring_goldens_active_vector_derived_owner = mod;
    Py_INCREF(mod);
    prik_module_refactoring_goldens_selected_vector_derived_owner = mod;
    int32_t constant_default_count_value_0 = 3;
    PyObject * constant_default_count_object_0 = prik_int32_to_numpy(&constant_default_count_value_0);
    if (constant_default_count_object_0 == NULL) { Py_DECREF(mod); return NULL; };
    if (PyModule_AddObject(mod, "default_count", constant_default_count_object_0) < 0) { Py_DECREF(constant_default_count_object_0); Py_DECREF(mod); return NULL; };
    return mod;
}