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
`prik.native_array_backend.v1.<tag>`, on `_native_backend`. It is the whole
cross-extension ABI for an array handle:

```c
typedef struct {
    uint32_t descriptor_kind;
    uint32_t descriptor_attribute;
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
  enters Fortran and supplies the plan-selected descriptor for that call. The
  descriptor is gone when the consumer returns and must never be retained,
  copied, or serialized.
- **Owned** — a native result, or a contract handle that has been given
  storage. The binding allocated a descriptor and keeps it for the handle's
  life, so the entry point hands that storage straight to the consumer.

Consumers use the same contract for both forms. `context` is the parent's
address for a field, descriptor storage for an owned handle, and `NULL` for a
module variable. `release` is non-`NULL` when the extension owns `context`.
Clearing `context` after release makes `close()` and finalization idempotent.

The capsule name combines a semantic version with a tag for the record layout,
so incompatible extensions are rejected before reading the record. Readers
validate the descriptor metadata against the planned argument. The kind names
the native entity; the attribute names the descriptor supplied to a consumer.

### Inquiries Read The Descriptor

State inquiries and `to_numpy()` use shared C consumers through
`with_descriptor` for both borrowed and owned handles. Mutations that act on
the native entity remain generated bridge operations.

A call with more than one allocatable or pointer dummy nests the consumers, one
per argument, and runs the call inside the innermost one so every descriptor is
live; an absent optional argument contributes an unallocated placeholder. Each
descriptor stays scoped to the consumer that supplied it.

### Views And Ownership

`to_numpy()` builds a view over the storage described by the live descriptor.
The view retains the parent object for a field or the backend capsule for owned
storage; module storage needs no additional owner. An owned view also retains
its handle because closing the handle releases the storage.

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
  deallocation when supplied.
- `native_support/prik_binding.h` contains header-only CPython/NumPy
  conversion, descriptor, validation, capsule, and release support. Change it
  only with its generated C users and `prik/compiler/native_support.py`.
- `native_support/LICENSE` is distributed with the native payload.

`to_numpy()` returns `None` for absent storage and otherwise applies the
completed view policy. Native argument handoff is performed in the binding
against the planned array contract. A returned NumPy array is a view of native
storage; a caller that needs independent storage must copy it.

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
- Change the capsule version when the callback contract or a field's meaning
  changes without changing the C record layout; a layout change is already
  caught by the name's tag.
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
