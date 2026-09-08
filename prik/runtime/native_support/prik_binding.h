/* Native mechanics shared by prik-generated CPython bindings. */

#ifndef PRIK_BINDING_H
#define PRIK_BINDING_H

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <complex.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "numpy_version.h"

#ifndef PY_ARRAY_UNIQUE_SYMBOL
#define PY_ARRAY_UNIQUE_SYMBOL PRIK_BINDING_ARRAY_API
#endif
#ifndef PRIK_BINDING_IMPORT_ARRAY
#define NO_IMPORT_ARRAY
#endif
#include <numpy/arrayobject.h>
#include <numpy/arrayscalars.h>

/*
 * One capsule publishes everything a generated binding needs from another
 * extension's array handle, and its name is derived from the record's own
 * layout rather than from a version anyone maintains by hand.
 *
 * The problem it solves: a capsule carries an address, and C has no runtime
 * types, so a reader has to decide what is at that address using offsets its
 * own compiler baked in. Two extensions built from different snapshots of this
 * header disagree about those offsets while agreeing about everything they can
 * name. Comparing a version *field* cannot settle it -- reading the field
 * already assumes the layout in question -- and it goes wrong worst on
 * `context`, `with_descriptor` and `release`, which are opaque addresses no
 * reader can sanity-check before calling one.
 *
 * The capsule name carries both a semantic ABI version and a layout tag.
 * PyCapsule_GetPointer compares names before it returns the pointer, so a
 * producer with a different callback contract or record layout is refused
 * before any field is read. Bump the version when field meanings or callback
 * behavior change without changing the record layout.
 *
 * `owner_abi` and `owner_signature` identify a Fortran-owned context and are
 * zero for every other kind. A generated owner type is an ordinary Fortran
 * derived type: its layout is its compiler's, not this header's, so a reader
 * that dereferences one built by a different compiler reinterprets memory.
 * Two extensions built by the same compiler from the same owner signature
 * agree; gfortran and ifx do not, and the mismatch surfaces as a fault inside
 * the callee with nothing to attribute it to. The capsule name settles that
 * both sides share this record; it cannot settle a type this header does not
 * define, so these two values carry that and are compared before any
 * dereference.
 */
#define PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_PREFIX "prik.native_array_backend.v2"
#define PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE 1u
#define PRIK_NATIVE_ARRAY_KIND_POINTER 2u
#define PRIK_NATIVE_ARRAY_ATTRIBUTE_ALLOCATABLE 1u
#define PRIK_NATIVE_ARRAY_ATTRIBUTE_POINTER 2u
#define PRIK_NATIVE_ARRAY_ATTRIBUTE_OTHER 3u

/*
 * What `context` points at.
 *
 * NONE is a borrowed backend: a module variable's, whose entity needs no
 * address at all.
 */
#define PRIK_NATIVE_ARRAY_CONTEXT_NONE 0u
#define PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR 1u
#define PRIK_NATIVE_ARRAY_CONTEXT_PARENT 2u
#define PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER 3u

/*
 * A generated owner may cross between extensions only when their paired C
 * drivers identify the same Fortran compiler ABI family and release. Build
 * integration always pairs these drivers; the value is intentionally
 * conservative so an uncertain pair is refused rather than dereferenced.
 */
#ifndef PRIK_FORTRAN_OWNER_ABI
#if defined(__INTEL_LLVM_COMPILER)
#define PRIK_FORTRAN_OWNER_ABI \
    (UINT64_C(0x4946580000000000) | (uint64_t)(__INTEL_LLVM_COMPILER))
#elif defined(__GNUC__)
#define PRIK_FORTRAN_OWNER_ABI \
    (UINT64_C(0x474E550000000000) | ((uint64_t)(__GNUC__) << 16) \
     | ((uint64_t)(__GNUC_MINOR__) << 8) | (uint64_t)(__GNUC_PATCHLEVEL__))
#else
#define PRIK_FORTRAN_OWNER_ABI UINT64_C(0)
#endif
#endif

/*
 * GNU Fortran releases before 14 lose the length when a deferred-length
 * character array pointer is reassociated (GCC PR 89352/106317).  Letting an
 * owner through on those releases would expose a corrupt element width.
 */
#ifndef PRIK_FORTRAN_DEFERRED_CHARACTER_POINTER_OWNER_SUPPORTED
#if defined(__INTEL_LLVM_COMPILER)
#define PRIK_FORTRAN_DEFERRED_CHARACTER_POINTER_OWNER_SUPPORTED 1
#elif defined(__GNUC__) && __GNUC__ >= 14
#define PRIK_FORTRAN_DEFERRED_CHARACTER_POINTER_OWNER_SUPPORTED 1
#else
#define PRIK_FORTRAN_DEFERRED_CHARACTER_POINTER_OWNER_SUPPORTED 0
#endif
#endif

#if defined(_MSC_VER)
#define PRIK_NO_INLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define PRIK_NO_INLINE __attribute__((noinline))
#else
#define PRIK_NO_INLINE
#endif

#ifdef PRIK_BINDING_CAPTURE_ADDRESS
/*
 * Report the address a caller already passed by reference.
 *
 * Fortran's `c_loc` can only name a variable that is a target or a pointer, so
 * an ordinary declaration -- a module array without `target`, say -- has no way
 * to state its own address. Handing the whole object to a `bind(C)` procedure
 * does: an assumed-type assumed-size dummy is passed as the bare base address,
 * so the parameter below already is where that object lives and only has to be
 * handed back. It does the job of `c_loc` exactly where `c_loc` is not
 * available, for any type and any rank, because it never inspects what it is
 * given. Nothing on the Fortran side forms a pointer or claims a target.
 *
 * This needs external linkage for the generated bridge to call it, so it is
 * defined only in the translation unit that opts in with this macro.
 */
void *prik_capture_address(void *base)
{
    return base;
}
#endif

/*
 * Consumer for one descriptor that is valid only while it runs.
 * The descriptor stays a compiler-owned representation here, as everywhere
 * else in this header, so this signature does not depend on the Fortran
 * interop header and stays usable from a C-only extension.
 */
typedef void (*prik_native_array_descriptor_fn)(void *descriptor, void *context);

/*
 * Enter the native entity and run `consumer` while its descriptor is live.
 * An ordinary projection may return without calling `consumer` when its
 * allocatable or pointer entity has no storage. `context` is whatever that
 * entity needs to be reached; see the backend record below.
 */
typedef void (*prik_native_array_with_descriptor_fn)(
    void *context,
    prik_native_array_descriptor_fn consumer,
    void *consumer_context);

/* Release the storage a backend owns. NULL when the backend borrows it. */
typedef void (*prik_native_array_release_fn)(void *context);

/*
 * Bridges a generated descriptor bridge, whose consumer takes the compiler's
 * descriptor type, to a backend consumer that takes it as void *. Forwarding
 * through this record avoids casting between function pointer types.
 */
typedef struct {
    prik_native_array_descriptor_fn consumer;
    void *context;
    int invoked;
} prik_native_array_descriptor_forward;

/*
 * Versioned cross-extension backend for one array handle.
 *
 * `with_descriptor(context, ...)` is the single entry point: it produces a
 * live descriptor and runs the consumer on it. `context` is the address that
 * entity needs -- the parent object for a derived-type field, the wrapper's
 * own descriptor storage for an owned handle, NULL for a module variable --
 * and is resolved once when the handle is built, so reaching the entity costs
 * one indirect call instead of a Python attribute lookup per operation.
 *
 * A borrowed backend enters Fortran, which supplies the plan-selected
 * descriptor for the call; the descriptor is gone when the consumer returns
 * and must never be retained. An owned backend hands over the persistent
 * storage it allocated, which stays valid for the handle's life. Consumers
 * cannot tell the two ownership forms apart, and must not try to.
 *
 * The metadata refuses an incompatible producer before any descriptor is
 * interpreted. The record's own layout is attested by the capsule name, so
 * nothing here restates it; what remains is what the name cannot know:
 *  - descriptor_size attests the producer's CFI_CDESC_T(rank) layout, which
 *    neither this record nor the descriptor itself can be read to establish;
 *  - descriptor_kind identifies the native entity while descriptor_attribute
 *    identifies what `with_descriptor` supplies. Together with rank, cfi_type
 *    and element_size, they let a reader refuse a mismatch without entering
 *    Fortran at all.
 * element_size is 0 when the element width is only known at run time, as for
 * a deferred-length character array; such a reader takes it from the live
 * descriptor's elem_len instead.
 */
typedef struct {
    uint32_t descriptor_kind;
    uint32_t descriptor_attribute;
    uint32_t rank;
    uint32_t descriptor_size;
    int32_t cfi_type;
    size_t element_size;
    uint32_t context_kind;
    uint64_t owner_abi;
    uint64_t owner_signature;
    void *context;
    prik_native_array_with_descriptor_fn with_descriptor;
    prik_native_array_release_fn release;
    uint32_t active_calls;
    uint32_t release_pending;
    uint32_t capsule_released;
} prik_native_array_backend;

/*
 * Describe one field for the layout tag: its name, where it starts, how wide
 * it is. All three come from the same token, so they cannot disagree.
 */
#define PRIK_NATIVE_ARRAY_BACKEND_FIELD(member)                                \
    {#member, offsetof(prik_native_array_backend, member), sizeof(((prik_native_array_backend *)0)->member)}

/*
 * Fold this record into one tag.
 *
 * Every field contributes its name, its offset and its width, in declaration
 * order, and the total size goes in first. A reorder, a widening, an
 * insertion, a removal and a rename all change the result. FNV-1a is used
 * because the mixing has to be order-dependent -- XOR-ing the offsets would
 * give the same tag for two fields exchanged.
 *
 * Field names are folded too, so renaming a field changes the tag even when its
 * offset and width stay the same. The semantic version covers contract changes
 * that do not alter or rename a field.
 */
static inline uint64_t prik_native_array_backend_layout_tag(void)
{
    static const struct {
        const char *name;
        size_t offset;
        size_t width;
    } layout[] = {
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(descriptor_kind),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(descriptor_attribute),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(rank),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(descriptor_size),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(cfi_type),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(element_size),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(context_kind),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(owner_abi),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(owner_signature),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(context),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(with_descriptor),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(release),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(active_calls),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(release_pending),
        PRIK_NATIVE_ARRAY_BACKEND_FIELD(capsule_released),
    };
    uint64_t tag = UINT64_C(14695981039346656037);
    size_t index;
    const char *character;

    tag = (tag ^ (uint64_t)sizeof(prik_native_array_backend)) * UINT64_C(1099511628211);
    for (index = 0; index < sizeof(layout) / sizeof(layout[0]); ++index) {
        for (character = layout[index].name; *character != '\0'; ++character) {
            tag = (tag ^ (uint64_t)(unsigned char)*character) * UINT64_C(1099511628211);
        }
        tag = (tag ^ (uint64_t)layout[index].offset) * UINT64_C(1099511628211);
        tag = (tag ^ (uint64_t)layout[index].width) * UINT64_C(1099511628211);
    }
    return tag;
}

/*
 * Name the capsule this extension publishes and accepts.
 *
 * Both sides build this string from their own header, so two extensions agree
 * on it exactly when they agree on the record. The name is what
 * PyCapsule_GetPointer compares, which is why a disagreement is reported
 * before the pointer is handed over rather than after something has been read
 * through it.
 */
static inline const char *prik_native_array_backend_capsule_name(void)
{
    static char name[80];

    if (name[0] == '\0') {
        /* Every caller computes the same bytes, so a race writes them twice. */
        snprintf(
            name,
            sizeof(name),
            PRIK_NATIVE_ARRAY_BACKEND_CAPSULE_PREFIX ".%016llx",
            (unsigned long long)prik_native_array_backend_layout_tag());
    }
    return name;
}

/*
 * Hand over a descriptor the wrapper itself owns.
 *
 * A handle the caller created has no native entity behind it: the binding
 * allocated its descriptor when the handle was first bound and keeps it for
 * the handle's lifetime. There is no call-scoped window to stay inside, so
 * the consumer runs on that storage directly. Publishing it through the same
 * backend lets such a handle reach a call the way a module array does.
 */
static inline void prik_native_array_owned_with_descriptor(
    void *context,
    prik_native_array_descriptor_fn consumer,
    void *consumer_context)
{
    consumer(context, consumer_context);
}

/*
 * Release owned storage exactly once.
 *
 * `release` is non-NULL only when `context` is storage this extension
 * allocated, so a borrowed backend -- a module variable's, a field's -- never
 * reaches the free below and Python never releases native storage it does not
 * own. Clearing `context` makes the release idempotent, so an explicit
 * close() and finalization can both run.
 */
static inline void prik_native_array_backend_release_now(prik_native_array_backend *backend)
{
    void *context;
    uint32_t context_kind;

    if (backend == NULL || backend->release == NULL || backend->context == NULL) {
        return;
    }
    context = backend->context;
    context_kind = backend->context_kind;
    backend->context = NULL;
    backend->release(context);
    /*
     * Only C storage is freed here. A Fortran owner was allocated by the
     * Fortran runtime, so its `release` is the generated destruction entry
     * point and freeing it here as well would be undefined.
     */
    if (context_kind == PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR) {
        free(context);
    }
}

/* Request idempotent release, deferring it while a native call holds a lease. */
static inline void prik_native_array_backend_release(prik_native_array_backend *backend)
{
    if (backend == NULL || backend->release == NULL || backend->context == NULL) {
        return;
    }
    if (backend->active_calls != 0) {
        backend->release_pending = 1u;
        return;
    }
    prik_native_array_backend_release_now(backend);
}

/* Hold a backend across a native call that may run without the GIL. */
static inline int prik_native_array_backend_acquire_call(prik_native_array_backend *backend)
{
    if (backend == NULL) {
        return 0;
    }
    if (backend->release_pending || (backend->release != NULL && backend->context == NULL)) {
        PyErr_SetString(PyExc_ReferenceError, "prik native array handle is closed");
        return -1;
    }
    backend->active_calls += 1u;
    return 0;
}

/* End a call lease and complete any release requested while it was active. */
static inline void prik_native_array_backend_release_call(prik_native_array_backend *backend)
{
    if (backend == NULL || backend->active_calls == 0) {
        return;
    }
    backend->active_calls -= 1u;
    if (backend->active_calls == 0 && backend->release_pending) {
        backend->release_pending = 0u;
        prik_native_array_backend_release_now(backend);
    }
    if (backend->active_calls == 0 && backend->capsule_released) {
        free(backend);
    }
}

/* Finalize one backend record owned by a Python capsule. */
static inline void prik_native_array_backend_capsule_destructor(PyObject *capsule)
{
    PyObject *error_type = NULL;
    PyObject *error_value = NULL;
    PyObject *error_traceback = NULL;
    prik_native_array_backend *backend;

    PyErr_Fetch(&error_type, &error_value, &error_traceback);
    backend = (prik_native_array_backend *)PyCapsule_GetPointer(
        capsule, prik_native_array_backend_capsule_name());
    if (backend == NULL) {
        PyErr_Clear();
    } else {
        backend->capsule_released = 1u;
        prik_native_array_backend_release(backend);
        if (backend->active_calls == 0) {
            free(backend);
        }
    }
    PyErr_Restore(error_type, error_value, error_traceback);
}

/*
 * Publish a per-handle backend.
 *
 * A handle whose entity needs a context address, or whose storage this
 * extension owns, cannot share one file-scope record, so its backend is built
 * when the handle is and released with the capsule that carries it. A module
 * variable needs neither, and publishes a file-scope record directly.
 *
 * Ownership of `context` transfers only on success: when this returns NULL the
 * caller is still responsible for releasing it.
 */
static inline PyObject *prik_native_array_backend_capsule_new(
    uint32_t descriptor_kind,
    uint32_t descriptor_attribute,
    uint32_t rank,
    uint32_t descriptor_size,
    int cfi_type,
    size_t element_size,
    uint32_t context_kind,
    uint64_t owner_abi,
    uint64_t owner_signature,
    void *context,
    prik_native_array_with_descriptor_fn with_descriptor,
    prik_native_array_release_fn release)
{
    prik_native_array_backend *backend;
    PyObject *capsule;

    if (descriptor_kind != PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE
        && descriptor_kind != PRIK_NATIVE_ARRAY_KIND_POINTER) {
        PyErr_SetString(PyExc_ValueError, "invalid prik native array descriptor kind");
        return NULL;
    }
    if (descriptor_attribute != PRIK_NATIVE_ARRAY_ATTRIBUTE_ALLOCATABLE
        && descriptor_attribute != PRIK_NATIVE_ARRAY_ATTRIBUTE_POINTER
        && descriptor_attribute != PRIK_NATIVE_ARRAY_ATTRIBUTE_OTHER) {
        PyErr_SetString(PyExc_ValueError, "invalid prik native array descriptor attribute");
        return NULL;
    }
    if (with_descriptor == NULL && context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER) {
        PyErr_SetString(PyExc_ValueError, "prik native array backend needs a descriptor entry point");
        return NULL;
    }
    if (release != NULL && context == NULL) {
        PyErr_SetString(PyExc_ValueError, "prik native array backend has no storage to release");
        return NULL;
    }
    if (context_kind > PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER) {
        PyErr_SetString(PyExc_ValueError, "invalid prik native array context kind");
        return NULL;
    }
    if (context != NULL && context_kind == PRIK_NATIVE_ARRAY_CONTEXT_NONE) {
        PyErr_SetString(PyExc_ValueError, "prik native array backend context has no declared kind");
        return NULL;
    }
    if (context == NULL && context_kind != PRIK_NATIVE_ARRAY_CONTEXT_NONE) {
        PyErr_SetString(PyExc_ValueError, "prik native array backend context kind requires storage");
        return NULL;
    }
    if (release != NULL
        && context_kind != PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR
        && context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER) {
        PyErr_SetString(PyExc_ValueError, "prik native array backend cannot release borrowed context storage");
        return NULL;
    }
    if (release == NULL
        && (context_kind == PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR
            || context_kind == PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER)) {
        PyErr_SetString(PyExc_ValueError, "prik native array owned context needs a release entry point");
        return NULL;
    }
    /*
     * An owner is the one context a reader cannot sanity-check by looking at
     * it, so it may not be published without the identity that decides whether
     * dereferencing it is safe.
     */
    if (context_kind == PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER && (owner_abi == 0 || owner_signature == 0)) {
        PyErr_SetString(PyExc_ValueError, "prik native array Fortran owner needs an owner ABI identity");
        return NULL;
    }
    if (context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER && (owner_abi != 0 || owner_signature != 0)) {
        PyErr_SetString(PyExc_ValueError, "prik native array owner identity is only carried by a Fortran owner");
        return NULL;
    }
    backend = (prik_native_array_backend *)calloc(1, sizeof(*backend));
    if (backend == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    backend->descriptor_kind = descriptor_kind;
    backend->descriptor_attribute = descriptor_attribute;
    backend->rank = rank;
    backend->descriptor_size = descriptor_size;
    backend->cfi_type = (int32_t)cfi_type;
    backend->element_size = element_size;
    backend->context_kind = context_kind;
    backend->owner_abi = owner_abi;
    backend->owner_signature = owner_signature;
    backend->context = context;
    backend->with_descriptor = with_descriptor;
    backend->release = release;
    capsule = PyCapsule_New(
        backend, prik_native_array_backend_capsule_name(), prik_native_array_backend_capsule_destructor);
    if (capsule == NULL) {
        backend->context = NULL;
        free(backend);
    }
    return capsule;
}

/*
 * Unwrap a backend capsule and check what makes its record usable at all.
 *
 * A backend that owns its storage and has released it is closed; a borrowed
 * one has no storage of its own and its NULL context means only that its
 * entity needs no address.
 */
static inline prik_native_array_backend *prik_native_array_backend_from_capsule(PyObject *capsule)
{
    prik_native_array_backend *backend;

    backend = (prik_native_array_backend *)PyCapsule_GetPointer(
        capsule, prik_native_array_backend_capsule_name());
    if (backend == NULL) {
        return NULL;
    }
    if (backend->with_descriptor == NULL
        && backend->context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER) {
        PyErr_SetString(PyExc_TypeError, "incompatible prik native array backend record");
        return NULL;
    }
    if (backend->release != NULL && backend->context == NULL) {
        PyErr_SetString(PyExc_ReferenceError, "prik native array handle is closed");
        return NULL;
    }
    if (backend->context_kind == PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER
        && backend->owner_abi != PRIK_FORTRAN_OWNER_ABI) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle was produced by a different Fortran compiler ABI and cannot be used here");
        return NULL;
    }
    return backend;
}

/*
 * Read a backend whose context is a Fortran owner this reader may dereference.
 *
 * This is the one gate before `c_f_pointer`. An owner is an ordinary Fortran
 * derived type, so nothing about the address says whether the bytes behind it
 * were laid out by this reader's compiler from this reader's owner signature.
 * Same compiler and same signature agree; anything else reinterprets memory,
 * which shows up as a fault inside the callee with nothing to attribute it to.
 *
 * The capsule name has already settled that both sides share this record. What
 * it cannot settle is the owner type, which this header does not define -- so
 * the comparison happens here, on values the producer wrote and the consumer
 * computes for itself.
 */
static inline prik_native_array_backend *prik_native_array_backend_for_owner(
    PyObject *capsule,
    uint64_t expected_owner_abi,
    uint64_t expected_owner_signature)
{
    prik_native_array_backend *backend;

    backend = prik_native_array_backend_from_capsule(capsule);
    if (backend == NULL) {
        return NULL;
    }
    if (backend->context_kind != PRIK_NATIVE_ARRAY_CONTEXT_FORTRAN_OWNER) {
        PyErr_SetString(PyExc_TypeError, "native array handle does not carry a Fortran owner");
        return NULL;
    }
    if (backend->owner_abi != expected_owner_abi) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle was produced by a different Fortran compiler ABI and cannot be used here");
        return NULL;
    }
    if (backend->owner_signature != expected_owner_signature) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle owner does not match the entity this argument declares");
        return NULL;
    }
    return backend;
}

/*
 * Read a backend for a descriptor dummy.
 *
 * Such a dummy is declared allocatable or pointer, so the handle's own kind
 * has to be the declared one; everything else about the storage must match the
 * declaration too. `expected_element_size` is 0 for a dummy that takes its
 * width from the actual.
 */
static inline prik_native_array_backend *prik_native_array_backend_for_descriptor(
    PyObject *capsule,
    uint32_t expected_descriptor_kind,
    uint32_t expected_rank,
    uint32_t expected_descriptor_size,
    int expected_cfi_type,
    size_t expected_element_size)
{
    prik_native_array_backend *backend;
    uint32_t expected_descriptor_attribute;

    backend = prik_native_array_backend_from_capsule(capsule);
    if (backend == NULL) {
        return NULL;
    }
    if (backend->descriptor_size != expected_descriptor_size) {
        PyErr_SetString(PyExc_TypeError, "incompatible Fortran descriptor storage size");
        return NULL;
    }
    if (backend->with_descriptor == NULL) {
        PyErr_SetString(PyExc_TypeError, "native array handle does not expose a usable descriptor");
        return NULL;
    }
    expected_descriptor_attribute = expected_descriptor_kind == PRIK_NATIVE_ARRAY_KIND_POINTER
        ? PRIK_NATIVE_ARRAY_ATTRIBUTE_POINTER
        : PRIK_NATIVE_ARRAY_ATTRIBUTE_ALLOCATABLE;
    if (backend->descriptor_attribute != expected_descriptor_attribute) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle does not expose the descriptor attribute required by the dummy argument");
        return NULL;
    }
    if (backend->descriptor_kind != expected_descriptor_kind || backend->rank != expected_rank
        || backend->cfi_type != expected_cfi_type
        || (expected_element_size != 0 && backend->element_size != expected_element_size)) {
        PyErr_SetString(PyExc_TypeError, "native array handle does not match the declared dummy argument");
        return NULL;
    }
    return backend;
}

/*
 * Take the descriptor a backend owns.
 *
 * `prik_native_array_owned_with_descriptor` hands its consumer the context
 * itself, so this accessor accepts only persistent descriptor storage. Only
 * the operations published on an owned handle -- allocate, resize, deallocate,
 * destroy -- ask for it,
 * and only ever about their own handle's storage; a borrowed backend has
 * nothing of the kind, and saying so here keeps a mis-wired one an error
 * instead of a null descriptor handed to CFI_allocate.
 */
static inline void *prik_native_array_backend_owned_descriptor(prik_native_array_backend *backend)
{
    if (backend->release == NULL) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle operation needs storage the handle owns; this one borrows its descriptor");
        return NULL;
    }
    /*
     * Owning storage is no longer the same fact as owning a descriptor: a
     * Fortran-owned handle owns an entity, which is not a CFI descriptor and
     * must never be handed to one of the operations that reads through this.
     */
    if (backend->context_kind != PRIK_NATIVE_ARRAY_CONTEXT_DESCRIPTOR) {
        PyErr_SetString(
            PyExc_TypeError,
            "native array handle operation needs descriptor storage; this handle owns a Fortran entity");
        return NULL;
    }
    return backend->context;
}

/*
 * Read a backend for an ordinary array actual.
 *
 * An ordinary array dummy takes the storage behind a handle, not the handle's
 * descriptor kind: an allocatable and a pointer are equally acceptable there,
 * so the kind is not compared. Everything that decides whether the storage
 * matches the dummy -- rank, element type and element size -- still is, and a
 * character dummy that takes its width from the actual passes 0 for the size.
 */
static inline prik_native_array_backend *prik_native_array_backend_for_actual(
    PyObject *capsule,
    uint32_t minimum_rank,
    uint32_t maximum_rank,
    int expected_cfi_type,
    size_t expected_element_size,
    const char *dtype_name,
    const char *argument_name)
{
    prik_native_array_backend *backend;

    backend = prik_native_array_backend_from_capsule(capsule);
    if (backend == NULL) {
        return NULL;
    }
    if (backend->with_descriptor == NULL) {
        PyErr_SetString(PyExc_TypeError, "native array handle does not expose a usable descriptor");
        return NULL;
    }
    if (backend->rank < minimum_rank || backend->rank > maximum_rank
        || backend->cfi_type != expected_cfi_type
        || (expected_element_size != 0 && backend->element_size != expected_element_size)) {
        PyErr_Format(
            PyExc_TypeError,
            "%s handle of rank %u with %zu-byte elements does not match expected dtype %s for argument %s",
            backend->descriptor_kind == PRIK_NATIVE_ARRAY_KIND_POINTER ? "pointer" : "allocatable",
            (unsigned)backend->rank,
            backend->element_size,
            dtype_name,
            argument_name);
        return NULL;
    }
    return backend;
}

#define PRIK_MAX_ARRAY_RANK 15

#ifdef PRIK_BINDING_NATIVE_ARRAY_ACTUAL

/* Mechanical result of reading a live handle descriptor for an ordinary array. */
typedef struct {
    void *data;
    int64_t rank;
    int64_t itemsize;
    int64_t extents[PRIK_MAX_ARRAY_RANK];
    int64_t upper_bounds[PRIK_MAX_ARRAY_RANK];
    int64_t strides[PRIK_MAX_ARRAY_RANK];
} prik_array_actual;
#endif

/* Build a Python string from caller-supplied status-message storage.

   The read never passes ``capacity`` because a native writer is not obliged to
   terminate. When it did terminate, the bytes are taken exactly as written;
   when it did not, the storage is fixed-length padded (Fortran blank-pads
   ``character(len=n)``), so trailing blanks and NULs are dropped. */
static inline PyObject *prik_status_message_text(const char *bytes, Py_ssize_t capacity)
{
    const char *terminator = (const char *)memchr(bytes, 0, (size_t)capacity);
    Py_ssize_t length = capacity;
    if (terminator != NULL) {
        return PyUnicode_FromStringAndSize(bytes, (Py_ssize_t)(terminator - bytes));
    }
    while (length > 0 && (bytes[length - 1] == ' ' || bytes[length - 1] == '\0')) {
        length -= 1;
    }
    return PyUnicode_FromStringAndSize(bytes, length);
}


/* Completed selectors for compact ordinary NumPy-array validation. */
#define PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS 0
#define PRIK_ARRAY_LAYOUT_C_CONTIGUOUS 1
#define PRIK_ARRAY_LAYOUT_F_CONTIGUOUS 2
#define PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F 3
#define PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F 4
#define PRIK_ARRAY_LAYOUT_ANY_STRIDED 5

/*
 * Report why one strided array cannot be described to Fortran.
 *
 * A Fortran array section runs over a contiguous parent: each axis advances by
 * a whole number of elements, the axes are ordered by how far they step, and no
 * axis steps back into another's span. A view that breaks those rules -- one
 * NumPy made by broadcasting, or by overlapping itself -- has no parent to be a
 * section of, whatever its strides say, so it cannot be handed over without
 * copying. An axis that merely runs backwards breaks none of them, and is
 * refused only where the entrypoint takes an address and so has nowhere to say
 * so.
 */
static inline int prik_array_refuse_section(
    const char *argument_name,
    int axis,
    int signed_strides)
{
    PyErr_Format(
        PyExc_TypeError,
        "Argument %s has a layout at axis %d that is not a Fortran array section: "
        "each axis must step a whole number of elements%s, in increasing order of step, without overlapping",
        argument_name,
        axis,
        signed_strides ? "" : " forward");
    return -1;
}

/*
 * Validate one axis of an F-ordered strided array.
 *
 * ``signed_strides`` says whether an axis may run backwards, which is exactly
 * whether the entrypoint carries a descriptor to record it in. Everything else
 * is required either way, because it is what makes the view a section at all.
 */
static inline int prik_array_validate_strided_axis(
    PyArrayObject *array,
    int axis,
    int signed_strides,
    const char *argument_name)
{
    int previous_axis;
    npy_intp stride = PyArray_STRIDE(array, axis);
    npy_intp itemsize = PyArray_ITEMSIZE(array);
    npy_intp previous_extent;
    npy_intp previous;

    if (itemsize <= 0 || (stride % itemsize) != 0) {
        /* A step that is not a whole element has no Fortran spelling at all. */
        return prik_array_refuse_section(argument_name, axis, signed_strides);
    }
    if (PyArray_SIZE(array) == 0 || PyArray_DIM(array, axis) <= 1) {
        /* One element cannot step anywhere, and no element cannot either. */
        return 0;
    }
    if (stride == 0) {
        /* A repeated element: NumPy broadcasting, which Fortran has no form for. */
        return prik_array_refuse_section(argument_name, axis, signed_strides);
    }
    if (stride == NPY_MIN_INTP) {
        /* Its magnitude is not representable by the signed descriptor index type. */
        return prik_array_refuse_section(argument_name, axis, signed_strides);
    }
    if (!signed_strides && stride < 0) {
        PyErr_Format(
            PyExc_TypeError,
            "Argument %s runs backwards along axis %d, and this entrypoint receives only an address, "
            "which cannot record a direction",
            argument_name,
            axis);
        return -1;
    }
    previous_axis = axis - 1;
    while (previous_axis >= 0 && PyArray_DIM(array, previous_axis) <= 1) {
        previous_axis -= 1;
    }
    if (previous_axis >= 0) {
        npy_intp current = stride < 0 ? -stride : stride;
        previous = PyArray_STRIDE(array, previous_axis);
        if (previous == NPY_MIN_INTP) {
            return prik_array_refuse_section(argument_name, previous_axis, signed_strides);
        }
        previous = previous < 0 ? -previous : previous;
        previous_extent = PyArray_DIM(array, previous_axis);
        if (previous != 0 && previous > current / previous_extent) {
            /*
             * This axis steps less far than the one before it covers, so the
             * axes are either in the wrong order for Fortran or they overlap.
             * Both are the same measurement, and ordering is what a caller can
             * actually act on.
             */
            PyErr_Format(
                PyExc_TypeError,
                "Argument %s has incompatible layout; expected ordering (F)",
                argument_name);
            return -1;
        }
        if (previous == 0 || (current % previous) != 0) {
            /* CFI_section needs an integral step relative to its contiguous parent. */
            return prik_array_refuse_section(argument_name, axis, signed_strides);
        }
    }
    return 0;
}

/*
 * Validate mechanics shared by every ordinary NumPy-array argument. The
 * generated wrapper supplies completed policy selectors and retains its
 * call-local shape and ABI-field lowering.
 */
static inline int prik_array_validate_ndarray(
    PyArrayObject *array,
    int numpy_type,
    int minimum_rank,
    int maximum_rank,
    int layout,
    int require_contiguous,
    int require_writeable,
    const char *python_type,
    const char *argument_name)
{
    int axis;
    int rank;
    const char *expected_order;
    const char *contiguous_suffix;

    if (minimum_rank < 0 || maximum_rank < minimum_rank || maximum_rank > PRIK_MAX_ARRAY_RANK
        || layout < PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS
        || layout > PRIK_ARRAY_LAYOUT_ANY_STRIDED
        || python_type == NULL || argument_name == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "prik generated invalid NumPy-array validation selectors");
        return -1;
    }
    rank = PyArray_NDIM(array);
    if (PyArray_TYPE(array) != numpy_type || rank < minimum_rank || rank > maximum_rank) {
        PyErr_Format(
            PyExc_TypeError,
            "Expected a compatible numpy.ndarray of dtype %s for argument %s. Received <class '%s'>",
            python_type,
            argument_name,
            Py_TYPE((PyObject *)array)->tp_name);
        return -1;
    }
    if (layout == PRIK_ARRAY_LAYOUT_ANY_STRIDED) {
        /* The plan accepts whatever strides the caller's array already has. */
    } else if (layout == PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F || layout == PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F) {
        int signed_strides = layout == PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F;
        for (axis = 0; axis < rank; axis++) {
            if (prik_array_validate_strided_axis(array, axis, signed_strides, argument_name) < 0) {
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

/* Validate an arbitrary Python argument before entering the shared ndarray core. */
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
    if (!PyArray_Check(value)) {
        PyErr_Format(
            PyExc_TypeError,
            "Expected a compatible numpy.ndarray of dtype %s for argument %s. Received <class '%s'>",
            python_type,
            argument_name,
            Py_TYPE(value)->tp_name);
        return -1;
    }
    return prik_array_validate_ndarray(
        (PyArrayObject *)value,
        numpy_type,
        minimum_rank,
        maximum_rank,
        layout,
        require_contiguous,
        require_writeable,
        python_type,
        argument_name);
}

/*
 * Bind one ordinary array argument, replacing the sequence a generated wrapper
 * used to emit inline at every array argument of every wrapper.
 *
 * A wrapper needs two things from an array argument: the raw pointer handed to
 * the native entrypoint, and one extent per contract axis. Obtaining them takes
 * two routes. This helper validates and reads NumPy arrays. Generated wrappers
 * read native handles through their versioned backend capsule before falling
 * back here for the NumPy route and the common wrong-type diagnostic.
 *
 *   object              the Python argument to bind
 *   numpy_type          NPY_* element selector the plan chose for this array
 *   expected_itemsize   required byte width for fixed character elements, or
 *                       zero when the NumPy type selector is sufficient
 *   rank                number of contract axes, and the length of `fixed`
 *                       and `extents`
 *   minimum_rank        smallest accepted runtime rank; equals `rank` unless
 *                       the plan flattens Python storage
 *   maximum_rank        largest accepted runtime rank
 *   layout              PRIK_ARRAY_LAYOUT_* ordering the plan requires;
 *                       PRIK_ARRAY_LAYOUT_ANY_STRIDED requires none
 *   require_contiguous  non-zero when the plan requires contiguous storage
 *   require_writeable   non-zero when the plan may write through this argument
 *   python_type         public dtype name used in diagnostics, "numpy.float64"
 *   argument_name       public argument name used in diagnostics
 *   flatten_axis        contract axis that absorbs every trailing runtime axis;
 *                       `rank - 1` when the plan does not flatten
 *   fixed               one entry per contract axis: the required extent, or
 *                       -1 when the axis is free
 *   data                receives the pointer passed to the native entrypoint
 *   extents             receives one extent per contract axis
 *   itemsize            optionally receives the element width in bytes
 *
 * Returns 0 on success, or -1 with a Python exception set.
 */
#ifdef PRIK_BINDING_NATIVE_ARRAY_ACTUAL
PRIK_NO_INLINE static int prik_bind_array(
    PyObject *object,
    int numpy_type,
    size_t expected_itemsize,
    int rank,
    int minimum_rank,
    int maximum_rank,
    int layout,
    int require_contiguous,
    int require_writeable,
    const char *python_type,
    const char *argument_name,
    int flatten_axis,
    const long long *fixed,
    void **data,
    int64_t *extents,
    int64_t *itemsize)
{
    int axis;
    if (PyArray_Check(object)) {
        PyArrayObject *array = (PyArrayObject *)object;
        if (prik_array_validate_ndarray(
                array, numpy_type, minimum_rank, maximum_rank, layout,
                require_contiguous, require_writeable, python_type, argument_name) < 0) {
            return -1;
        }
        if (expected_itemsize != 0 && (size_t)PyArray_ITEMSIZE(array) != expected_itemsize) {
            PyErr_Format(
                PyExc_TypeError,
                "Argument %s must have NumPy bytes dtype itemsize %zu",
                argument_name,
                expected_itemsize);
            return -1;
        }
        for (axis = 0; axis < rank; ++axis) {
            if (fixed[axis] >= 0 && PyArray_DIM(array, axis) != (npy_intp)fixed[axis]) {
                PyErr_Format(
                    PyExc_TypeError,
                    "Argument %s has incompatible shape at axis %d",
                    argument_name,
                    axis);
                return -1;
            }
        }
        *data = PyArray_DATA(array);
        if (itemsize != NULL) {
            *itemsize = (int64_t)PyArray_ITEMSIZE(array);
        }
        for (axis = 0; axis < flatten_axis; ++axis) {
            extents[axis] = (int64_t)PyArray_DIM(array, axis);
        }
        extents[flatten_axis] = 1;
        for (axis = flatten_axis; axis < PyArray_NDIM(array); ++axis) {
            extents[flatten_axis] *= (int64_t)PyArray_DIM(array, axis);
        }
        return 0;
    }
    /* A generated wrapper takes an accepted handle route before calling this
       ndarray-only helper. */
    PyErr_Format(
        PyExc_TypeError,
        "Expected a compatible numpy.ndarray of dtype %s for argument %s. Received <class '%s'>",
        python_type,
        argument_name,
        Py_TYPE(object)->tp_name);
    return -1;
}
#endif

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
    *destination = (int8_t)PyArrayScalar_VAL(value, Int8);
    return 0;
}

static inline int prik_int16_unpack_exact(PyObject *value, int16_t *destination)
{
    if (!PyArray_IsScalar(value, Int16)) {
        return -1;
    }
    *destination = (int16_t)PyArrayScalar_VAL(value, Int16);
    return 0;
}

static inline int prik_int32_unpack_exact(PyObject *value, int32_t *destination)
{
    if (!PyArray_IsScalar(value, Int)) {
        return -1;
    }
    *destination = (int32_t)PyArrayScalar_VAL(value, Int);
    return 0;
}

/*
 * C long and long long are distinct NumPy scalar types even where both are
 * 64 bits wide, and which one a target calls int64_t varies. A scalar crosses
 * by value, so either spelling is accepted here and converted to the exact
 * native storage. An array buffer cannot be converted element by element, so
 * array validation stays exact.
 */
static inline int prik_int64_unpack_exact(PyObject *value, int64_t *destination)
{
#if NPY_SIZEOF_LONG == 8
    if (PyArray_IsScalar(value, Long)) {
        *destination = (int64_t)PyArrayScalar_VAL(value, Long);
        return 0;
    }
#endif
#if NPY_SIZEOF_LONGLONG == 8
    if (PyArray_IsScalar(value, LongLong)) {
        *destination = (int64_t)PyArrayScalar_VAL(value, LongLong);
        return 0;
    }
#endif
    return -1;
}

static inline int prik_float32_unpack_exact(PyObject *value, float *destination)
{
    if (!PyArray_IsScalar(value, Float)) {
        return -1;
    }
    *destination = (float)PyArrayScalar_VAL(value, Float);
    return 0;
}

static inline int prik_float64_unpack_exact(PyObject *value, double *destination)
{
    if (!PyArray_IsScalar(value, Double)) {
        return -1;
    }
    *destination = (double)PyArrayScalar_VAL(value, Double);
    return 0;
}

static inline int prik_complex64_unpack_exact(PyObject *value, float complex *destination)
{
    if (!PyArray_IsScalar(value, CFloat)) {
        return -1;
    }
    *destination = (float complex)PyArrayScalar_VAL(value, CFloat);
    return 0;
}

static inline int prik_complex128_unpack_exact(PyObject *value, double complex *destination)
{
    if (!PyArray_IsScalar(value, CDouble)) {
        return -1;
    }
    *destination = (double complex)PyArrayScalar_VAL(value, CDouble);
    return 0;
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

static inline int prik_signed_integer_unpack(
    PyObject *value,
    int64_t minimum,
    int64_t maximum,
    int64_t *destination)
{
    long long parsed = PyLong_AsLongLong(value);
    if (PyErr_Occurred() != NULL) {
        return -1;
    }
    if (parsed < (long long)minimum || parsed > (long long)maximum) {
        PyErr_SetString(PyExc_OverflowError, "Python integer is outside the native signed-integer range");
        return -1;
    }
    *destination = (int64_t)parsed;
    return 0;
}

static inline int prik_unsigned_integer_unpack(
    PyObject *value,
    uint64_t maximum,
    uint64_t *destination)
{
    unsigned long long parsed = PyLong_AsUnsignedLongLong(value);
    if (PyErr_Occurred() != NULL) {
        return -1;
    }
    if (parsed > (unsigned long long)maximum) {
        PyErr_SetString(PyExc_OverflowError, "Python integer is outside the native unsigned-integer range");
        return -1;
    }
    *destination = (uint64_t)parsed;
    return 0;
}

static inline int prik_int8_unpack(PyObject *value, int8_t *destination)
{
    int64_t parsed;
    if (PyArray_IsScalar(value, Int8)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_signed_integer_unpack(value, INT8_MIN, INT8_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (int8_t)parsed;
    return 0;
}

static inline int prik_int16_unpack(PyObject *value, int16_t *destination)
{
    int64_t parsed;
    if (PyArray_IsScalar(value, Int16)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_signed_integer_unpack(value, INT16_MIN, INT16_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (int16_t)parsed;
    return 0;
}

static inline int prik_int32_unpack(PyObject *value, int32_t *destination)
{
    int64_t parsed;
    if (PyArray_IsScalar(value, Int)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_signed_integer_unpack(value, INT32_MIN, INT32_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (int32_t)parsed;
    return 0;
}

static inline int prik_int64_unpack(PyObject *value, int64_t *destination)
{
    if (PyArray_IsScalar(value, Int64)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    return prik_signed_integer_unpack(value, INT64_MIN, INT64_MAX, destination);
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
    PyObject *result = PyArrayScalar_New(Bool);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Bool, (npy_bool)*value);
    }
    return result;
}

static inline PyObject *prik_int8_to_numpy(const int8_t *value)
{
    PyObject *result = PyArrayScalar_New(Int8);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Int8, (npy_int8)*value);
    }
    return result;
}

static inline PyObject *prik_int16_to_numpy(const int16_t *value)
{
    PyObject *result = PyArrayScalar_New(Int16);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Int16, (npy_int16)*value);
    }
    return result;
}

static inline PyObject *prik_int32_to_numpy(const int32_t *value)
{
    PyObject *result = PyArrayScalar_New(Int);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Int, (npy_int32)*value);
    }
    return result;
}

static inline PyObject *prik_int64_to_numpy(const int64_t *value)
{
    PyObject *result = PyArrayScalar_New(Int64);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Int64, (npy_int64)*value);
    }
    return result;
}

static inline PyObject *prik_float32_to_numpy(const float *value)
{
    PyObject *result = PyArrayScalar_New(Float);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Float, (npy_float32)*value);
    }
    return result;
}

static inline PyObject *prik_float64_to_numpy(const double *value)
{
    PyObject *result = PyArrayScalar_New(Double);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, Double, (npy_float64)*value);
    }
    return result;
}

static inline PyObject *prik_complex64_to_numpy(const float complex *value)
{
    PyObject *result = PyArrayScalar_New(CFloat);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, CFloat, (npy_cfloat)*value);
    }
    return result;
}

static inline PyObject *prik_complex128_to_numpy(const double complex *value)
{
    PyObject *result = PyArrayScalar_New(CDouble);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, CDouble, (npy_cdouble)*value);
    }
    return result;
}

/* Unsigned-integer and extended-precision scalar conversions.

   NumPy dropped the ``Intp`` scalar tag, so ``size_t`` selects the fixed-width
   tag that matches the target's pointer width instead. */

static inline int prik_uint8_unpack_exact(PyObject *value, uint8_t *destination)
{
    if (!PyArray_IsScalar(value, UByte)) {
        return -1;
    }
    *destination = (uint8_t)PyArrayScalar_VAL(value, UByte);
    return 0;
}

static inline int prik_uint8_unpack(PyObject *value, uint8_t *destination)
{
    uint64_t parsed;
    if (PyArray_IsScalar(value, UByte)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_unsigned_integer_unpack(value, UINT8_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (uint8_t)parsed;
    return 0;
}

static inline PyObject *prik_uint8_to_python(const uint8_t *value)
{
    return PyLong_FromUnsignedLong(*value);
}

static inline PyObject *prik_uint8_to_numpy(const uint8_t *value)
{
    PyObject *result = PyArrayScalar_New(UByte);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, UByte, (npy_uint8)*value);
    }
    return result;
}

static inline int prik_uint16_unpack_exact(PyObject *value, uint16_t *destination)
{
    if (!PyArray_IsScalar(value, UShort)) {
        return -1;
    }
    *destination = (uint16_t)PyArrayScalar_VAL(value, UShort);
    return 0;
}

static inline int prik_uint16_unpack(PyObject *value, uint16_t *destination)
{
    uint64_t parsed;
    if (PyArray_IsScalar(value, UShort)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_unsigned_integer_unpack(value, UINT16_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (uint16_t)parsed;
    return 0;
}

static inline PyObject *prik_uint16_to_python(const uint16_t *value)
{
    return PyLong_FromUnsignedLong(*value);
}

static inline PyObject *prik_uint16_to_numpy(const uint16_t *value)
{
    PyObject *result = PyArrayScalar_New(UShort);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, UShort, (npy_uint16)*value);
    }
    return result;
}

static inline int prik_uint32_unpack_exact(PyObject *value, uint32_t *destination)
{
    if (!PyArray_IsScalar(value, UInt)) {
        return -1;
    }
    *destination = (uint32_t)PyArrayScalar_VAL(value, UInt);
    return 0;
}

static inline int prik_uint32_unpack(PyObject *value, uint32_t *destination)
{
    uint64_t parsed;
    if (PyArray_IsScalar(value, UInt)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_unsigned_integer_unpack(value, UINT32_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (uint32_t)parsed;
    return 0;
}

static inline PyObject *prik_uint32_to_python(const uint32_t *value)
{
    return PyLong_FromUnsignedLong(*value);
}

static inline PyObject *prik_uint32_to_numpy(const uint32_t *value)
{
    PyObject *result = PyArrayScalar_New(UInt);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, UInt, (npy_uint32)*value);
    }
    return result;
}

/* Accepts either 64-bit spelling; see prik_int64_unpack_exact. */
static inline int prik_uint64_unpack_exact(PyObject *value, uint64_t *destination)
{
#if NPY_SIZEOF_LONG == 8
    if (PyArray_IsScalar(value, ULong)) {
        *destination = (uint64_t)PyArrayScalar_VAL(value, ULong);
        return 0;
    }
#endif
#if NPY_SIZEOF_LONGLONG == 8
    if (PyArray_IsScalar(value, ULongLong)) {
        *destination = (uint64_t)PyArrayScalar_VAL(value, ULongLong);
        return 0;
    }
#endif
    return -1;
}

static inline int prik_uint64_unpack(PyObject *value, uint64_t *destination)
{
    if (PyArray_IsScalar(value, ULongLong)) {
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    return prik_unsigned_integer_unpack(value, UINT64_MAX, destination);
}

static inline PyObject *prik_uint64_to_python(const uint64_t *value)
{
    return PyLong_FromUnsignedLongLong(*value);
}

static inline PyObject *prik_uint64_to_numpy(const uint64_t *value)
{
#if NPY_SIZEOF_LONG == 8
    PyObject *result = PyArrayScalar_New(ULong);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, ULong, (npy_uint64)*value);
    }
#else
    PyObject *result = PyArrayScalar_New(ULongLong);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, ULongLong, (npy_uint64)*value);
    }
#endif
    return result;
}

/* Accepts every unsigned spelling of the target's pointer width. */
static inline int prik_uintp_unpack_exact(PyObject *value, size_t *destination)
{
#if NPY_SIZEOF_LONG == NPY_SIZEOF_INTP
    if (PyArray_IsScalar(value, ULong)) {
        *destination = (size_t)PyArrayScalar_VAL(value, ULong);
        return 0;
    }
#endif
#if NPY_SIZEOF_LONGLONG == NPY_SIZEOF_INTP
    if (PyArray_IsScalar(value, ULongLong)) {
        *destination = (size_t)PyArrayScalar_VAL(value, ULongLong);
        return 0;
    }
#endif
#if NPY_SIZEOF_INT == NPY_SIZEOF_INTP
    if (PyArray_IsScalar(value, UInt)) {
        *destination = (size_t)PyArrayScalar_VAL(value, UInt);
        return 0;
    }
#endif
    return -1;
}

static inline int prik_uintp_unpack(PyObject *value, size_t *destination)
{
    uint64_t parsed;
#if NPY_SIZEOF_LONG == NPY_SIZEOF_INTP
    if (PyArray_IsScalar(value, ULong)) {
#elif NPY_SIZEOF_INTP == 8
    if (PyArray_IsScalar(value, ULongLong)) {
#else
    if (PyArray_IsScalar(value, UInt)) {
#endif
        PyArray_ScalarAsCtype(value, destination);
        return 0;
    }
    if (prik_unsigned_integer_unpack(value, SIZE_MAX, &parsed) < 0) {
        return -1;
    }
    *destination = (size_t)parsed;
    return 0;
}

static inline PyObject *prik_uintp_to_python(const size_t *value)
{
    return PyLong_FromUnsignedLongLong((unsigned long long)*value);
}

static inline PyObject *prik_uintp_to_numpy(const size_t *value)
{
#if NPY_SIZEOF_LONG == NPY_SIZEOF_INTP
    PyObject *result = PyArrayScalar_New(ULong);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, ULong, (npy_ulong)*value);
    }
#elif NPY_SIZEOF_INTP == 8
    PyObject *result = PyArrayScalar_New(ULongLong);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, ULongLong, (npy_uint64)*value);
    }
#else
    PyObject *result = PyArrayScalar_New(UInt);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, UInt, (npy_uint32)*value);
    }
#endif
    return result;
}

static inline int prik_longdouble_unpack_exact(PyObject *value, long double *destination)
{
    if (!PyArray_IsScalar(value, LongDouble)) {
        return -1;
    }
    *destination = (long double)PyArrayScalar_VAL(value, LongDouble);
    return 0;
}

static inline int prik_longdouble_unpack(PyObject *value, long double *destination)
{
    if (PyArray_IsScalar(value, LongDouble)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        *destination = (long double)PyFloat_AsDouble(value);
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline PyObject *prik_longdouble_to_python(const long double *value)
{
    return PyFloat_FromDouble((double)*value);
}

static inline PyObject *prik_longdouble_to_numpy(const long double *value)
{
    PyObject *result = PyArrayScalar_New(LongDouble);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, LongDouble, (npy_longdouble)*value);
    }
    return result;
}

static inline int prik_clongdouble_unpack_exact(PyObject *value, long double complex *destination)
{
    if (!PyArray_IsScalar(value, CLongDouble)) {
        return -1;
    }
    *destination = (long double complex)PyArrayScalar_VAL(value, CLongDouble);
    return 0;
}

static inline int prik_clongdouble_unpack(PyObject *value, long double complex *destination)
{
    if (PyArray_IsScalar(value, CLongDouble)) {
        PyArray_ScalarAsCtype(value, destination);
    } else {
        Py_complex parsed = PyComplex_AsCComplex(value);
        *destination = (long double)parsed.real + (long double)parsed.imag * _Complex_I;
    }
    return PyErr_Occurred() == NULL ? 0 : -1;
}

static inline PyObject *prik_clongdouble_to_python(const long double complex *value)
{
    return PyComplex_FromDoubles((double)creall(*value), (double)cimagl(*value));
}

static inline PyObject *prik_clongdouble_to_numpy(const long double complex *value)
{
    PyObject *result = PyArrayScalar_New(CLongDouble);
    if (result != NULL) {
        PyArrayScalar_ASSIGN(result, CLongDouble, (npy_clongdouble)*value);
    }
    return result;
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
