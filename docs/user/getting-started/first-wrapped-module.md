---
title: First Wrapped Module
description: Wrap a Fortran module with public procedures and state variables
audience: users
prerequisites: first wrapped function
related: beginner-workflow.md, ../guide/wrapping-modules.md
status: maintained
publication: reviewed
---

# First Wrapped Module

A Fortran `module` becomes a **child namespace** inside the generated Python extension. Public procedures and supported public variables are exposed under that namespace.

---

## Source Code

Create a file named `module_state.f90`:

```fortran
module module_state
  implicit none
  private

  public :: nmax, counter, scale, saved_counter
  public :: summarize, scaled_counter, next_local

  integer(4), parameter :: nmax = 12
  integer(4) :: counter = 3
  real(8) :: scale = 1.5d0
  integer(4), save :: saved_counter = 6
  integer(4) :: hidden_counter = 17

contains

  integer(4) function summarize() result(value)
    value = counter + nmax
  end function summarize

  real(8) function scaled_counter() result(value)
    value = real(counter, 8) * scale
  end function scaled_counter

  integer(4) function next_local() result(value)
    integer(4), save :: local_counter = 0
    local_counter = local_counter + 1
    value = local_counter
  end function next_local

end module module_state
```

---

## Build the Extension

Run the following command:

```bash
python3 -m prik module_state.f90 --out-dir build/first-module
```

The extension will be named `module_state`, and the Fortran module will be available as `module_state.module_state`.

---

## Inspect the Generated Docstring

Import the built module and print its generated docstring:

```python
import sys

sys.path.insert(0, "build/first-module")
import module_state.module_state as mod

print(mod.__doc__)
```

```text
module_state

Module Attributes
-----------------
nmax : int32
    Read-only constant.
counter : int32
scale : float64
saved_counter : int32

Functions
---------
summarize() -> int32
scaled_counter() -> float64
next_local() -> int32
```

`help(mod)` shows the same index. Individual functions have their own detailed
docstrings.

---

## Usage Example

```python
import numpy as np

print(mod.nmax)           # 12
print(mod.counter)        # 3
print(mod.scale)          # 1.5

print(mod.summarize())           # 15
print(mod.scaled_counter())      # 4.5
```

---

## Mutating Module State

```python
mod.counter = np.int32(9)
print(mod.summarize())           # 21

mod.scale = np.float64(2.0)
print(mod.scaled_counter())      # 18.0
```

Procedure-local `save` variables also persist across calls:

```python
print(mod.next_local())   # 1
print(mod.next_local())   # 2
```

---

## Inspect the Contract

Preview the generated interface without building:

```bash
python3 -m prik generate --pyi module_state.f90
```

---

## Key Rules

- The extension name is derived from the source filename.
- Each Fortran `module` becomes a child Python namespace.
- Only **public** entities are exposed.
- Private variables (like `hidden_counter`) are hidden.
- Assign module variables with the matching NumPy scalar dtype.

---

## Next

- Continue with the [Beginner Workflow](beginner-workflow.md) to turn these
  steps into a repeatable development loop.
- For module details, see [Wrapping Modules](../guide/wrapping-modules.md).
