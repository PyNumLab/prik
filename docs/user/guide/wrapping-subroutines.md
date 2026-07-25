---
title: Wrapping Subroutines
description: How x2py wraps Fortran `subroutine` procedures — output arguments, in-place mutation, and result projection
audience: users
prerequisites: data types, first wrapped function
related: wrapping-functions.md, arrays.md, optional-arguments.md
status: maintained
publication: reviewed
---

# Wrapping Subroutines

A Fortran `subroutine` has no direct return value. Instead, its `intent(out)` and `intent(inout)` arguments are projected into the Python result.

---

## Argument Projection Rules

| Native Argument              | Python Call                  | Python Result                     |
|-----------------------------|------------------------------|-----------------------------------|
| `intent(in)` scalar/array   | Visible argument             | Not returned                      |
| `intent(out)` scalar        | Hidden                       | Returned as value                 |
| `intent(inout)` scalar      | Visible argument             | Returned as replacement value     |
| `intent(out)` array         | Visible writable NumPy array | Same array, filled and returned   |
| `intent(inout)` array       | Visible writable NumPy array | Mutated in place; normally no extra result |
| `intent(out)` allocatable   | Hidden (or optional)         | `Allocatable[...]` handle         |

---

## Complete Example

Create `outputs.f90`:

```fortran
module outputs
  implicit none
contains

  subroutine bounds(values, smallest, largest)
    real(8), intent(in) :: values(:)
    real(8), intent(out) :: smallest, largest
    smallest = minval(values)
    largest = maxval(values)
  end subroutine bounds

  subroutine scale_in_place(values, factor)
    real(8), intent(inout) :: values(:)
    real(8), intent(in) :: factor
    values = factor * values
  end subroutine scale_in_place

  subroutine scale_scalar(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
  end subroutine scale_scalar

  subroutine fill(values)
    real(8), intent(out) :: values(:)
    values = 1.0_8
  end subroutine fill

end module outputs
```

Build it:

```bash
python3 -m x2py outputs.f90 --out-dir build/outputs
```

---

## Python Usage

```python
import sys
import numpy as np

sys.path.insert(0, "build/outputs")
import outputs

api = outputs.outputs

# Hidden scalar outputs → returned as tuple
data = np.array([4.0, -2.0, 7.0], dtype=np.float64)
smallest, largest = api.bounds(data)
print(smallest, largest)   # -2.0  7.0

# Scalar inout replacement
updated = api.scale_scalar(np.float64(4.0), np.float64(2.5))
print(updated)              # 10.0

# In-place mutation
arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
api.scale_in_place(arr, np.float64(3.0))
print(arr)                 # [3. 6. 9.]

# Caller-provided output array
target = np.empty(4, dtype=np.float64)
returned = api.fill(target)
assert returned is target
print(target)              # [1. 1. 1. 1.]
```

---

## Key Rules

- Scalar `intent(out)` values are hidden in the call and returned.
- Scalar `intent(inout)` values are visible inputs and are also returned as
  replacement values; the original Python scalar object is unchanged.
- Array `intent(out/inout)` arguments must be pre-allocated by the caller and
  are mutated in place.
- Source-generated `intent(out)` arrays return the same supplied array;
  `intent(inout)` arrays normally communicate through in-place mutation only.
- The generated `.pyi` contract is the source of truth for what is returned.
- For functions with both a return value **and** outputs, the function result comes first in the tuple.

---

## Next

- Continue with [Optional Arguments](optional-arguments.md) or [Wrapping Modules](wrapping-modules.md).
- For advanced memory management, see [Allocatables](allocatables.md) and [Pointers](pointers.md).
