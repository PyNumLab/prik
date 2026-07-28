---
title: Wrapping Modules
description: How x2py exposes Fortran modules as Python namespaces with procedures, variables, and state
audience: users
prerequisites: data types, first wrapped module
related: wrapping-functions.md, memory-management.md, building-shared-library.md
status: maintained
publication: reviewed
---

# Wrapping Modules

A Fortran `module` becomes a **child Python module** (namespace) inside the generated extension.

---

## Basic Usage

After building `module_state.f90`:

```python
import sys
import numpy as np

sys.path.insert(0, "build/first-module")
import module_state

mod = module_state.module_state   # child namespace
```

See [First Wrapped Module](../getting-started/first-wrapped-module.md) for the complete source, build command, and usage examples.

---

## Procedures

Module functions and subroutines become attributes of the child module:

```python
print(mod.summarize())       # 15
print(mod.scaled_counter())  # 4.5
```

Standalone procedures (outside any module) remain at the extension root.

When compiling multiple source files, each Fortran module becomes its own child namespace, while standalone procedures stay on the extension root. The first source file usually determines the extension name (you can override with `--out`).

---

## Public Variables and Constants

Supported public scalar variables are exposed as direct Python attributes:

```python
mod.counter = np.int32(9)
print(mod.counter)      # 9
print(mod.summarize())  # 21

print(mod.nmax)         # 12 (read-only parameter)
```

- `parameter` declarations become `Final[...]` constants in the generated contract.
- Assigning to a constant in Python only creates a local shadow — it does **not** mutate the native value.

---

## Module Arrays & Saved State

- Allocatable module arrays use the `Allocatable[T[...]]` API.
- Allocation, lifetime, NumPy views, and mutation rules are covered in
  the storage and objects section.
- `save` attributes (including procedure-local `save` variables) persist across calls.
- Multiple Python imports of the same extension share the same native module state.

---

## Important Rules

- Private declarations are hidden from the Python API.
- Common blocks are **not** exposed as Python variables (only indirectly through procedures that access them).
- Module state is **shared** native storage — changes made through one reference are visible to all others.
- The extension name is derived from the source filename unless overridden.

---

## Next

- Learn about [Memory Management](memory-management.md) — especially important when working with module state
- See [Optional Arguments](optional-arguments.md)
- See [Building the Shared Library](building-shared-library.md)
- Check the [Language Feature Matrix](../language-support/feature-matrix.md)
  for supported module features and limitations
