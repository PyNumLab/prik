---
title: Wrapping Modules
description: How x2py exposes Fortran modules as Python namespaces with procedures, variables, and state
audience: users
prerequisites: data types, first wrapped module
related: wrapping-functions.md, memory-management.md, packaging.md
status: maintained
publication: reviewed
---

# Wrapping Modules

A Fortran `module` becomes a **child Python module** (namespace) inside the generated extension. This preserves the original structure instead of flattening everything to the extension root.

---

## Basic Usage

After building `module_state.f90`:

```python
import sys

sys.path.insert(0, "build/first-module")
import module_state

mod = module_state.module_state   # ← child module
```

See [First Wrapped Module](../getting-started/first-wrapped-module.md) for the full example.

---

## Procedures

Module procedures become methods on the child module:

```python
print(mod.summarize())        # 15
print(mod.scaled_counter())   # 4.5
```

Standalone procedures (not inside any module) remain at the extension root.

---

## Public Variables & Constants

Supported public scalar variables are exposed as direct attributes:

```python
mod.counter = np.int32(9)
assert mod.counter == np.int32(9)

assert mod.nmax == np.int32(12)   # parameters are read-only
```

- `parameter` declarations become `Final[...]` constants.
- Writing to a constant in Python only shadows the attribute locally — it does **not** change native storage.

---

## Module Arrays & State

- Allocatable module arrays appear as `Allocatable[T[...]]` handles.
- You can read the current state with `.to_numpy()` and mutate through the view.
- `save` variables (including procedure-local `save`) persist across calls.
- Multiple Python imports of the same extension share the same native module state.

---

## Important Notes

- Private declarations are hidden.
- Common blocks are **not** exposed as Python variables (only through procedures that access them).
- Module state is **shared** — changes are visible across all references to the same extension.

---

## Next

- Learn about [Memory Management](memory-management.md)
- See [Optional Arguments](optional-arguments.md)
- Explore [Packaging](packaging.md) for distribution
- For supported module features, check the [Language Feature Matrix](../language-support/feature-matrix.md).
