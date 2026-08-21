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
generated operation dictionary + dtype, rank, ownership, and view policy
  -> NativeArrayHandleBase validation and owner retention
  -> AllocatableArray or PointerArray
  -> state, lifecycle, association, and to_numpy() operations
```

The operation dictionary is the boundary between generated extension code and
the stable Python handle API. An operation exists only when the completed plan
allows the generator to expose it. Missing operations fail explicitly rather
than being inferred from `allocatable` or `pointer` alone.

## Local Structure

```text
prik/runtime/
├── handles.py
└── native_support/
    ├── prik_binding.h
    └── LICENSE
```

- [`handles.py`](../../../prik/runtime/handles.py) contains the Python runtime.
  `NativeArrayHandleBase` validates common metadata and operations.
  `AllocatableArray` adds allocation state, resize, and deallocation;
  `PointerArray` adds association, nullification, allocation, resize, and
  deallocation when supplied. Internal adapters translate generated call
  signatures and descriptor handoffs.
- `native_support/prik_binding.h` contains header-only CPython/NumPy
  conversion, descriptor, validation, capsule, and release support. Change it
  only with its generated C users and `prik/compiler/native_support.py`.
- `native_support/LICENSE` is distributed with the native payload.

`to_numpy()` returns `None` for an absent allocatable or pointer and otherwise
validates the completed view policy, dtype, rank, and any required contiguity.
Native argument handoff performs the additional expected shape, layout,
alignment, byte-order, and writeability checks. A returned NumPy array is a
view of native storage; a caller that needs independent storage must copy it.

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

The example supplies the same operation-dictionary shape as generated code.
It creates an allocatable handle, reads its live NumPy view, and routes a
resize through the adapter. The native header has no standalone Python route;
the compiler installs it into a generated `binding_support/` directory.

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
