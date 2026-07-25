---
title: Optional Arguments
description: How x2py handles Fortran `optional` arguments — inputs, outputs, arrays, and None behavior
audience: users
prerequisites: wrapping subroutines, data types
related: generic-interfaces.md, arrays.md, error-handling.md
status: maintained
publication: reviewed
---

# Optional Arguments

x2py supports optional scalars, arrays, strings, derived types, and outputs.
It preserves native `present(...)` semantics.

---

## Complete Example

Create `optional.f90`:

```fortran
module adjustments
  implicit none
contains

  integer(4) function adjust(value, offset) result(output)
    integer(4), intent(in) :: value
    integer(4), intent(in), optional :: offset

    output = value
    if (present(offset)) output = output + offset
  end function adjust

  subroutine make_values(size, count, values)
    integer(4), intent(in) :: size
    integer(4), intent(out) :: count
    real(8), intent(out), optional :: values(size)
    integer(4) :: index

    count = size
    if (present(values)) then
      do index = 1, size
        values(index) = real(index, 8)
      end do
    end if
  end subroutine make_values

end module adjustments
```

Build it:

```bash
python3 -m x2py optional.f90 --out-dir build/optional
```

---

## Usage in Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/optional")
from optional.adjustments import adjust, make_values

print(adjust(np.int32(5)))                         # 5 (omitted)
print(adjust(np.int32(5), None))                   # 5 (explicit None)
print(adjust(np.int32(5), np.int32(3)))            # 8 (provided)
print(adjust(np.int32(5), offset=np.int32(10)))    # 15 (keyword)
```

---

## Key Rules

- For ordinary optional inputs, **omission** and `None` both mean the argument
  is **not present** to Fortran.
- Providing a concrete value makes the argument **present**.
- Use **keyword arguments** when skipping earlier optional parameters.
- Optional arrays and derived types also accept `None` to indicate absence.
- Optional `intent(out)` / `intent(inout)` arguments remain visible in Python
  so you can control `present(...)`.

Scalar allocatable and pointer descriptors are the three-state exception:
omission means absent, `None` means present but unallocated or unassociated,
and a concrete value means present storage.

---

## Optional Outputs

An optional output remains visible in the Python call. This lets the caller
decide whether the native routine receives it.

Pass writable storage to make `values` present:

```python
values = np.empty(3, dtype=np.float64)
count = make_values(np.int32(3), values)

print(count)   # 3
print(values)  # [1. 2. 3.]
```

Omit the argument, or pass `None`, to make it absent:

```python
omitted_count = make_values(np.int32(3))
none_count = make_values(np.int32(3), None)

print(omitted_count)  # 3
print(none_count)     # 3
```

`count` is a required scalar output, so it is always returned. `values` is
caller-owned mutable storage, so it is never added to the result.

For optional ordinary array outputs:

- Supplying writable storage mutates that array in place.
- Passing `None` or omitting it makes the native dummy absent.
- Presence does not add an array-or-`None` position to the result.
- A routine with only optional ordinary array outputs returns `None`, whether
  those arrays are present or absent.

Optional scalar derived-type outputs follow the same in-place rule as arrays.
Primitive scalar outputs and native descriptor outputs have different storage
rules. Check the generated `.pyi` contract when mixing output kinds.

---

## Limitations

- Optional procedure pointers and passed procedures are not yet supported.
- x2py does not invent default values. The Fortran procedure handles missing
  arguments.

---

## Next

- Continue with [Generic Interfaces](generic-interfaces.md).
- For optional outputs and memory, see [Error Handling](error-handling.md) and [Memory Management](memory-management.md).
