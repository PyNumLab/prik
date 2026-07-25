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

x2py supports optional scalars, arrays, strings, derived types, and outputs while preserving native `present(...)` semantics.

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
from optional.adjustments import adjust

assert adjust(np.int32(5)) == np.int32(5)                    # omitted
assert adjust(np.int32(5), None) == np.int32(5)              # explicit None
assert adjust(np.int32(5), np.int32(3)) == np.int32(8)       # provided
assert adjust(np.int32(5), offset=np.int32(10)) == np.int32(15)  # keyword
```

---

## Key Rules

- For ordinary optional inputs, **omission** and `None` both mean the argument
  is **not present** to Fortran.
- Providing a concrete value makes the argument **present**.
- Use **keyword arguments** when skipping earlier optional parameters.
- Optional arrays and derived types also accept `None` to indicate absence.
- Optional `intent(out)` / `intent(inout)` arguments remain visible in Python so you can control `present(...)`.

Scalar allocatable and pointer descriptors are the three-state exception:
omission means absent, `None` means present but unallocated or unassociated,
and a concrete value means present storage.

---

## Optional Outputs

When an output argument is optional:

- Supplying writable storage uses the normal mutation and return behavior.
- Passing `None` or omitting it makes the native dummy absent.
- A result tuple uses `None` at that output position when other results are
  still returned; a routine with only that absent output returns `None`.

Always check the generated `.pyi` contract to see the exact return shape when mixing required and optional outputs.

---

## Limitations

- Optional procedure pointers and passed procedures are not yet supported.
- x2py does not invent default values — the Fortran procedure is responsible for handling missing arguments.

---

## Next

- Continue with [Generic Interfaces](generic-interfaces.md).
- For optional outputs and memory, see [Error Handling](error-handling.md) and [Memory Management](memory-management.md).
