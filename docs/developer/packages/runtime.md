---
title: Runtime Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed native handle policy
related: ../architecture.md, index.md, policy.md, compiler.md, pipeline.md
status: maintained
publication: draft
---

# Runtime Component

## Purpose And Boundaries

`prik/runtime/` owns Python objects that remain active after importing a
generated extension and the bundled native header payload used by generated
bindings. Runtime objects validate descriptor metadata, retain owners, adapt
generated operations, and expose policy-selected NumPy views. They enforce
completed behavior; they do not decide ownership or invent missing operations.

## Local Structure

```text
prik/runtime/
├── __init__.py
├── handles.py
└── native_support/
    ├── __init__.py
    ├── prik_binding.h
    └── LICENSE
```

## What This Stage Receives And Produces

```text
generated extension operation dictionary
  -> descriptor metadata validation
  -> AllocatableArray or PointerArray adapter
  -> policy-permitted allocate/deallocate/resize/nullify/to_numpy operations
```

The native-support initializer only makes the payload locatable. The compiler
installs it into a generated `binding_support/` include directory.

## Directory Tour

| Path | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/runtime/__init__.py`](../../../prik/runtime/__init__.py) | Package boundary for Python runtime support. | A small supported runtime import surface is deliberately introduced. |
| [`prik/runtime/handles.py`](../../../prik/runtime/handles.py) | `NativeArrayHandleBase`, `AllocatableArray`, and `PointerArray` validate generated operations, retain owners, and produce policy-permitted live NumPy views. | Handle protocol, validation, retention, descriptor conversion, or Python operation behavior changes. |
| [`prik/runtime/native_support/__init__.py`](../../../prik/runtime/native_support/__init__.py) | Locates the bundled native-support payload without creating another Python runtime API. | Payload discovery changes. |
| `runtime/native_support/prik_binding.h` | Bundled native capsule, descriptor, validation, conversion, and release support compiled into generated bindings. | A generated binding requires changed native support; also inspect `compiler/native_support.py` installation. |
| `runtime/native_support/LICENSE` | License text distributed with the native payload. | The payload licensing changes. |

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

## Tests And What They Prove

- [Allocatable runtime tests](../../../tests/fortran/allocatables/runtime/) cover allocatable operations and NumPy views.
- [Pointer runtime tests](../../../tests/fortran/pointers/runtime/) cover pointer association and views.
- [Memory-management runtime tests](../../../tests/fortran/memory_management/runtime/) cover release and ownership enforcement.
- [Runtime infrastructure](../../../tests/fortran/infrastructure/runtime/) covers generated-operation protocols.
- [Compiled runtime compatibility](../../../tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py) covers the payload in a real extension.

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
