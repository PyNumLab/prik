---
title: Wrapping Subroutines
description: How prik wraps Fortran `subroutine` procedures — output arguments, in-place mutation, and result projection
audience: users
prerequisites: data types, first wrapped function
related: wrapping-functions.md, arrays.md, optional-arguments.md
status: maintained
publication: reviewed
---

# Wrapping Subroutines

A Fortran `subroutine` has no direct return value. Scalar outputs and objects
created by Fortran form the Python result. Caller-provided mutable objects
change in place.

---

## How Arguments Become Python Results

| Native Argument              | Python Call                  | Python Result                     |
|-----------------------------|------------------------------|-----------------------------------|
| `intent(in)` scalar/array   | Visible argument             | Not returned                      |
| `intent(out)` scalar        | Hidden                       | Returned as value                 |
| `intent(inout)` scalar      | Visible argument             | Returned as replacement value     |
| `intent(out)` array         | Visible writable NumPy array | Filled in place; not returned     |
| `intent(inout)` array       | Visible writable NumPy array | Mutated in place; not returned    |
| Derived `intent(out/inout)` | Visible generated object     | Mutated in place; not returned    |
| `intent(out)` allocatable   | Hidden (or optional)         | `Allocatable[...]` handle         |
| No `intent`                 | Visible argument             | Conservative `intent(inout)` rule |

Without `intent`, prik uses the conservative `intent(inout)` behavior. A
primitive scalar stays visible and its replacement value is returned. If the
dummy is known to be input-only, remove that projected result from the
generated contract. This is common in legacy sources, but the rule applies to
any dummy declaration without `intent`.

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
python3 -m prik outputs.f90 --out-dir build/outputs
```

---

## Python Usage

```python
import sys

import numpy as np

sys.path.insert(0, "build/outputs")
from outputs.outputs import bounds, fill, scale_in_place, scale_scalar

# Hidden scalar outputs → returned as tuple
data = np.array([4.0, -2.0, 7.0], dtype=np.float64)
smallest, largest = bounds(data)
print(smallest, largest)   # -2.0  7.0

# Scalar inout replacement
updated = scale_scalar(np.float64(4.0), np.float64(2.5))
print(updated)              # 10.0

# In-place mutation
arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
scale_in_place(arr, np.float64(3.0))
print(arr)                 # [3. 6. 9.]

# Caller-provided output array
target = np.empty(4, dtype=np.float64)
fill(target)
print(target)              # [1. 1. 1. 1.]
```

---

## Key Rules

- Scalar `intent(out)` values are hidden in the call and returned.
- Scalar `intent(inout)` values are visible inputs and are also returned as
  replacement values; the original Python scalar object is unchanged.
- Array `intent(out/inout)` arguments must be pre-allocated by the caller and
  are mutated in place.
- Ordinary `intent(out/inout)` arrays are not added to the Python result.
- Scalar derived-type objects follow the same in-place rule as arrays.
- Array function results and hidden allocatable outputs still return new
  Python-visible objects because the caller did not supply their storage.
- The generated `.pyi` contract is the source of truth for what is returned.
- For functions with both a return value **and** outputs, the function result comes first in the tuple.

---

## Next

- Continue with [Wrapping Modules](wrapping-modules.md).
- Then read [Optional Arguments](optional-arguments.md) to control whether a
  native argument is present.
- For advanced memory management, see [Allocatables](allocatables.md) and [Pointers](pointers.md).
