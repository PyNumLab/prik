---
title: Runtime Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed native handle policy
related: ../architecture.md, index.md, policy.md, compiler.md, pipeline.md
status: maintained
publication: reviewed
---

# Runtime Component

## Purpose And Boundaries

`prik/runtime/` provides Python objects used after a generated extension is
imported and the native support compiled into generated bindings. It validates
the operations and descriptor metadata supplied by the extension, retains
required owners, and exposes the NumPy views permitted by completed policy.

Runtime code enforces decisions already made by policy and represented in the
wrapper plan. It does not decide ownership, invent a missing operation, or
select a different view behavior from local descriptor facts.

## A Native Array Handle At Runtime

```text
generated dispatcher + completed capability set + native backend capsule
  + dtype, rank, ownership, and view policy
  -> NativeArrayHandleBase validation and owner retention
  -> AllocatableArray or PointerArray
  -> state, lifecycle, association, and to_numpy() operations
```

The dispatcher is the single Python call boundary between generated extension
code and the stable handle API. Its immutable capability set comes from the
completed plan and states which operation names the dispatcher accepts. The
runtime validates that set when it creates the handle and before dispatching an
operation.

### The Backend Capsule

Every generated handle publishes one versioned capsule,
`prik.native_array_backend.v1`, on `_native_backend`. It is the whole
cross-extension ABI for an array handle:

```c
typedef struct {
    uint32_t struct_size;
    uint32_t descriptor_kind;
    uint32_t rank;
    uint32_t descriptor_size;
    int32_t  cfi_type;
    size_t   element_size;
    void    *context;
    prik_native_array_with_descriptor_fn with_descriptor;
    prik_native_array_release_fn release;
} prik_native_array_backend;
```

`with_descriptor(context, consumer, consumer_context)` supplies a live
descriptor and runs the consumer on it:

- **Borrowed** — a module variable or a derived-type field. The entry point
  enters Fortran, which builds the descriptor for that call and copies back
  what the consumer wrote. The descriptor is gone when the consumer returns and
  must never be retained, copied, or serialized.
- **Owned** — a native result, or a contract handle that has been given
  storage. The binding allocated a descriptor and keeps it for the handle's
  life, so the entry point hands that storage straight to the consumer.

Consumers use the same contract for both forms. `context` is the parent's
address for a field, descriptor storage for an owned handle, and `NULL` for a
module variable. `release` is non-`NULL` when the extension owns `context`.
Clearing `context` after release makes `close()` and finalization idempotent.

The capsule name is `prik.native_array_backend.v1.<tag>`. The version identifies
the callback contract and field meanings. Change it when either changes without
changing the C record layout. The tag folds the record size and each field's
name, offset, and width, so a layout mismatch also changes the name.
`PyCapsule_GetPointer` compares that name before returning the record pointer;
an incompatible producer is therefore refused before its fields are read.

`descriptor_size` stays in the record because it attests the producer's
`CFI_CDESC_T(rank)` layout, which is the compiler's, not this header's, and so
is not folded into the tag. A reader still validates `descriptor_kind`, `rank`,
`cfi_type` and `element_size` against the dummy it is filling. `element_size`
is `0` for widths determined at run time, such as deferred-length character
arrays.

### Inquiries Read The Descriptor

`shape`, `allocated`, `associated`, `contiguous`, `element_length` and
`to_numpy` are all answered by small shared C consumers run through
`with_descriptor`, for borrowed and owned handles alike. Each consumer returns
the completed Python value. The bridge provides the descriptor entry point and
the mutations that act on the entity itself: `allocate`, `resize`,
`deallocate`, `nullify`, `associate`, and `destroy`.

A pointer additionally reports `descriptor` as a flat fact tuple: base address,
element width, rank, then a lower bound, extent, and byte stride per axis. A
pointer assignment uses this snapshot. A handle created from a `.pyi` contract
retains the snapshot until a call attaches native storage and replays the
association.

A call with more than one allocatable or pointer dummy enters each argument's
backend in turn. Each consumer records its descriptor and enters the next, and
the call runs inside the last consumer while every descriptor is live. Borrowed
and owned handles use the same placement; an owned backend hands the consumer
its persistent storage. An absent optional argument contributes an unallocated
placeholder to the chain. Each descriptor remains scoped to the consumer that
supplied it.

Ordinary numeric assumed-shape and assumed-rank arguments use the same C
descriptor entrypoint for both direct and adapted calls. The binding describes
a NumPy array with call-local descriptor storage, or enters a handle's live
descriptor through the consumer chain. A direct `bind(C)` procedure receives
that descriptor itself; a non-`bind(C)` procedure has an interoperable bridge
dummy that passes the array through unchanged. Explicit-shape, assumed-size,
raw C-pointer, and character-array entrypoints keep their planned address ABI.

### Views And Ownership

`to_numpy()` builds the view in C while the descriptor is live, over the
storage the descriptor names, with the descriptor's own byte strides — so
negative strides, non-contiguous pointer targets and zero-sized dimensions all
come through unchanged. The view's base is what keeps that storage valid: the
parent object for a derived-type field, the backend capsule for an owned
handle, and nothing for a module variable, whose storage outlives every view of
it. An owned handle's view additionally retains the handle, because closing the
handle is what releases the storage.

## Local Structure

```text
prik/runtime/
├── handles.py
└── native_support/
    ├── prik_binding.h
    └── LICENSE
```

- [`handles.py`](../../../prik/runtime/handles.py) contains the Python runtime.
  `NativeArrayHandleBase` validates common metadata, the dispatcher, and its
  completed capabilities.
  `AllocatableArray` adds allocation state, resize, and deallocation;
  `PointerArray` adds association, nullification, allocation, resize, and
  deallocation when supplied. A handle created from a `.pyi` contract answers
  from a fact tuple of its own until a call attaches generated storage; every
  other handle answers from its descriptor.
- `native_support/prik_binding.h` contains header-only CPython/NumPy
  conversion, descriptor, validation, capsule, and release support. Change it
  only with its generated C users and `prik/compiler/native_support.py`.
- `native_support/LICENSE` is distributed with the native payload.

`to_numpy()` returns `None` for an absent allocatable or pointer and otherwise
validates the completed view policy, dtype, rank, and any required contiguity.
Native argument handoff is performed in the binding, against the live
descriptor, and refuses a mismatched dtype, rank, fixed shape, character width,
layout, byte order, alignment, writeability, or contiguity there. A returned
NumPy array is a view of native storage; a caller that needs independent
storage must copy it.

## Run The Handle Demonstration

```bash
python3 prik/runtime/handles.py
```

```text
Runtime handle: AllocatableArray
Descriptor kind: allocatable
Initial view: [1.0, 2.0, 3.0]
Resized shape: (4,)
Generated resize received NumPy extents: True
```

The example supplies the same dispatcher and capability set as generated code.
It creates an allocatable handle, reads its live NumPy view, and routes a resize
through the dispatcher. The compiler installs the native header into the
generated `binding_support/` directory.

## Change Routes And Evidence

- Change handle protocol, validation, retention, views, or adapters in
  `handles.py`.
- Change the native payload together with its generated users and
  `prik/compiler/native_support.py`.
- Complete new ownership, lifecycle, operation, or view policy before planning
  rather than selecting it in runtime code.

| Evidence | What it establishes |
| --- | --- |
| [Allocatable runtime tests](../../../tests/fortran/allocatables/runtime/) | Allocation state, operations, descriptor handoffs, and NumPy views. |
| [Pointer runtime tests](../../../tests/fortran/pointers/runtime/) | Association, nullification, pointer descriptors, and views. |
| [Memory-management runtime tests](../../../tests/fortran/memory_management/runtime/) | Owner retention, release, and array handoffs. |
| [Native-support tests](../../../tests/fortran/infrastructure/runtime/) | Bundled payload discovery and installation inputs. |
| [Compiled runtime compatibility](../../../tests/fortran/infrastructure/building/end_to_end/test_runtime_compatibility.py) | The payload and Python runtime working through a real extension. |

An outstanding zero-copy NumPy view cannot be revoked after native
reallocation, deallocation, or pointer reassociation. Users must discard or
copy such views before changing the native storage.
