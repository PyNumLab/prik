---
title: Runtime Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed native handle policy
related: ../architecture.md, index.md, policy.md, compiler.md, pipeline.md
status: maintained
publication: draft
---

# Runtime Package

## Purpose And Boundaries

`prik/runtime/` owns Python objects that remain active after importing a
generated extension and the bundled native header payload used by generated
bindings. Runtime objects validate descriptor metadata, retain owners, adapt
generated operations, and expose policy-selected NumPy views. They enforce
completed behavior; they do not decide ownership or invent missing operations.

## Local Structure

```text
prik/runtime/
├── handles.py
└── native_support/
    ├── __init__.py
    ├── prik_binding.h
    └── LICENSE
```

## Internal Workflow

```text
generated extension operation dictionary
  -> descriptor metadata validation
  -> AllocatableArray or PointerArray adapter
  -> policy-permitted allocate/deallocate/resize/nullify/to_numpy operations
```

The native-support initializer only makes the payload locatable. The compiler
installs it into a generated `binding_support/` include directory.

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `handles.py` | `NativeArrayHandleBase`, `AllocatableArray`, `PointerArray` | Adapts generated descriptor operations into stable Python APIs and live NumPy views. |
| `native_support/prik_binding.h` | capsule, descriptor, validation, conversion, and release helpers | Supplies the header-only native runtime used by generated bindings. |
| `native_support/__init__.py` | package marker | Makes the payload discoverable without creating another runtime API. |

## Execution Example

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

The example supplies the same operation dictionary shape exported by a
generated extension. It proves descriptor selection, validation, operation
adaptation, and the generated NumPy extent convention. The returned NumPy
storage is live, not a detached snapshot.

The native payload intentionally has no standalone Python example: it is
compiled only as part of a generated binding.

## Tests

- [Allocatable runtime tests](../../../tests/fortran/allocatables/runtime/)
- [Pointer runtime tests](../../../tests/fortran/pointers/runtime/)
- [Memory-management runtime tests](../../../tests/fortran/memory_management/runtime/)
- [Runtime infrastructure](../../../tests/fortran/infrastructure/runtime/)
- [Compiled runtime compatibility](../../../tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change handle protocol, validation, retention, or adapters in `handles.py`.
- Change header implementation in `native_support/` and installation in
  `prik/compiler/native_support.py`.
- Complete any new ownership, operation permission, or view policy upstream
  before runtime enforcement.

## Invariants And Common Mistakes

- Outstanding zero-copy NumPy views cannot be revoked after native
  reallocation or pointer reassociation. Callers must discard or copy them.
- Runtime must reject operations absent from completed policy rather than
  guessing permission from descriptor kind.
- The native support directory is a payload, not a second pipeline stage.
