---
title: Allocatables
description: How x2py handles Fortran `allocatable` variables, arrays, and descriptors
audience: users, advanced users
prerequisites: arrays
related: arrays.md, pointers.md, memory-management.md
status: maintained
publication: reviewed
---

# Allocatables

x2py treats `allocatable` entities differently depending on context:

- **Scalar allocatables** appear as `T | None` values.
- **Array allocatables** appear as `Allocatable[T[...]]` handles.

---

## Allocatable Array Handles

Use `Allocatable[T[...]]` for array allocatables in the semantic contract:

```python
from x2py.contracts import Allocatable, Float64, Int32

values: Allocatable[Float64[:]]

def resize(values: Allocatable[Float64[:]], n: Int32) -> None: ...
```

### Important Properties

- A handle is **always present**, even when unallocated.
- Reading the Python attribute returns an `Allocatable[T[...]]` handle, not `ndarray | None`.
- `handle.allocated` tells you the current state.
- `handle.to_numpy()` returns a live NumPy view **or** `None` if unallocated; it never creates an automatic detached snapshot.
- The view is **borrowed**. Do not keep it after the native storage may change.
- A borrowed view is a NumPy array that points at storage Python does not own.

```python
h = api.some_allocatable
if h.allocated:
    view = h.to_numpy()        # live mutable view
    view[0] = 42.0
else:
    print("Not allocated")
```

---

## Complete Example

Create `storage.f90`:

```fortran
module storage
  implicit none
  real(8), allocatable :: values(:)
contains

  function make_values(n) result(arr)
    integer(4), intent(in) :: n
    integer(4) :: i
    real(8), allocatable :: arr(:)
    if (n > 0) then
      allocate(arr(n))
      arr = [(real(i, 8)*2, i = 1, n)]
    end if
  end function make_values

  subroutine replace_values(arr)
    real(8), allocatable, intent(inout) :: arr(:)
    if (allocated(arr)) deallocate(arr)
    allocate(arr(2))
    arr = [10.0_8, 20.0_8]
  end subroutine replace_values

end module storage
```

Build it:

```bash
python3 -m x2py storage.f90 --out-dir build/storage
```

Use the generated module:

```python
import sys

import numpy as np

sys.path.insert(0, "build/storage")
import storage

api = storage.storage

values = api.make_values(np.int32(3))
print(values.to_numpy())                    # [2. 4. 6.]

returned = api.replace_values(values)
assert returned is values                   # same handle
print(values.to_numpy())                    # [10. 20.]
```

---

## Key Rules

- Use `Allocatable[T[...]]` when the Python API needs a native descriptor.
- Use normal `T[...]` when you just want to pass array **data**.
- Call `.to_numpy()` to get a view; the handle itself is not an array.
- Copy data (`view.copy()`) if you need it to survive possible reallocation/deallocation.
- Direct allocatable array function results preserve allocated, zero-sized, and
  unallocated handle state. This includes matrices and higher-rank arrays.

---
