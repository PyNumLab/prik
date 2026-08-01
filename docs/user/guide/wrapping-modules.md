---
title: Wrapping Modules
description: How prik exposes Fortran modules as Python namespaces with procedures, variables, and state
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

- `parameter` declarations become read-only constants in the generated
  contract.
- Assigning to a constant in Python only creates a local shadow — it does **not** mutate the native value.

---

## Module Arrays & Saved State

- Allocatable module arrays use the `Allocatable[T[...]]` API.
- Allocation, lifetime, NumPy views, and mutation rules are covered in
  the storage and objects section.
- `save` attributes (including procedure-local `save` variables) persist across calls.
- Multiple Python imports of the same extension share the same native module state.

---

## Shape the Module API With the Contract

Small contract edits can set initial values or hide names from Python:

```python
from prik.contracts import Final, Float64, Int32, private

nmax: Final[Int32] = 12
counter: Int32 = 9
scale: Float64 = 2.0
saved_counter: private[Int32]

@private
def scaled_counter() -> Float64: ...
```

- `counter` and `scale` are set in the Fortran module when the extension is
  imported. They remain writable.
- `private[T]` hides a module variable; `@private` hides a procedure. Both
  still exist in Fortran.
- `Final[T] = value` is only for a true constant, such as a Fortran
  `parameter`. It does not turn a writable Fortran variable into a read-only
  view.

Deleting a declaration removes that name from the generated Python API. These
edits do not create or rename native variables and procedures; those still
need to exist in the compiled module.

For the complete rules, see
[Remove or Hide a Declaration](../reference/pyi-contracts/exports-and-modules.md#remove-or-hide-a-declaration)
and
[Set Module Values at Import](../reference/pyi-contracts/exports-and-modules.md#set-module-values-at-import).

---

## Flatten Module Namespaces

The package entry `__init__.pyi` controls the Python import layout. Suppose an
extension named `library` contains two Fortran modules. prik generates:

```python
# __init__.pyi
from . import module1
from . import module2
```

The modules remain child namespaces:

```python
from library.module1 import func1
from library.module2 import func2
```

To place every public name directly on `library`, replace those imports with
wildcard imports:

```python
# __init__.pyi
from .module1 import *
from .module2 import *
```

Python then uses the flattened API:

```python
import library

library.func1()
library.func2()

# This is also valid:
from library import func1, func2
```

Public functions, variables, constants, and generated classes are exported at
the extension root. If the original module imports were replaced,
`library.module1` and `library.module2` are no longer exported. The native
Fortran modules and their storage do not move; only the Python API changes.

Wildcard imports never use import order to resolve a collision. If both
modules export the same name, the wrapper build fails and asks for an explicit
choice. Export aliases instead:

```python
from .module1 import update as update_module1
from .module2 import update as update_module2
```

This produces `library.update_module1` and `library.update_module2`. You can
also import only selected names instead of flattening every public declaration.
Build the edited entry using the
[editable-contract workflow](../getting-started/beginner-workflow.md#4-optionally-edit-the-contract).

For all supported imports, aliases, and namespace layouts, see
[Choose the Package Shape](../reference/pyi-contracts/exports-and-modules.md#choose-the-package-shape).

---

## Important Rules

- Private declarations are hidden from the Python API.
- Common blocks are **not** exposed as Python variables (only indirectly through procedures that access them).
- Module state is **shared** native storage — changes made through one reference are visible to all others.
- The extension name is derived from the source filename unless overridden.

---

## Next

- Continue with [Optional Arguments](optional-arguments.md).
- Read [Memory Management](memory-management.md) before keeping live views of
  module storage.
