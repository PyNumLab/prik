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

`with_descriptor(context, consumer, consumer_context)` is the only route to a
descriptor. It produces a live one and runs the consumer on it:

- **Borrowed** — a module variable or a derived-type field. The entry point
  enters Fortran, which builds the descriptor for that call and copies back
  what the consumer wrote. The descriptor is gone when the consumer returns and
  must never be retained, copied, or serialized.
- **Owned** — a native result, or a contract handle that has been given
  storage. The binding allocated a descriptor and keeps it for the handle's
  life, so the entry point hands that storage straight to the consumer.

Consumers cannot tell the two apart and must not try to. `context` is whatever
the entity needs to be reached: the parent's address for a field, the
descriptor storage for an owned handle, `NULL` for a module variable.
`release` is non-`NULL` exactly when `context` is storage this extension
allocated, so a borrowed backend can never free anything, and clearing
`context` after one release makes `close()` and finalization both safe.

The version lives in the capsule name: `PyCapsule_GetPointer` refuses a
capsule created under any other name, so no magic word or second version field
is carried. `struct_size` catches a layout change made without renaming;
`descriptor_size` is `sizeof(CFI_CDESC_T(rank))` and is the only way one
extension can attest another's CFI layout, which nothing inside a descriptor
can establish. `descriptor_kind`, `rank`, `cfi_type` and `element_size` are
what a reader compares against the dummy it is filling, so a mismatched actual
is refused before any Fortran is entered. `element_size` is `0` when the width
is only known at run time, as for a deferred-length character array.

### Inquiries Read The Descriptor

`shape`, `allocated`, `associated`, `contiguous`, `element_length` and
`to_numpy` are all answered by small shared C consumers run through
`with_descriptor`, for borrowed and owned handles alike. Nothing crosses into
Python except the finished object, so no descriptor is serialized into Python
fields and no field is decoded back into C. There is correspondingly no Fortran
procedure per variable for any of them; the bridge emits only the descriptor
entry point and the mutations that must reach the entity itself — `allocate`,
`resize`, `deallocate`, `nullify`, `associate` and `destroy`.

A pointer additionally reports `descriptor` as a flat fact tuple — base
address, element width, rank, then a lower bound, extent and byte stride per
axis. That is how a pointer assignment snapshots what another pointer is
associated with, which matters because a handle created from a `.pyi` contract
has no native storage until a call gives it some and so has nowhere else to
record it.

A call with more than one allocatable or pointer dummy enters each argument's
backend in turn. Each consumer records its descriptor and enters the next, and
the call runs inside the last consumer while every descriptor is live. Borrowed
and owned handles use the same placement; an owned backend hands the consumer
its persistent storage. An absent optional argument contributes an unallocated
placeholder to the chain. Each descriptor remains scoped to the consumer that
supplied it.

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
through the dispatcher. The native header has no standalone Python route; the
compiler installs it into a generated `binding_support/` directory.

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
