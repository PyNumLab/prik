---
title: Pointers
description: How x2py handles Fortran `pointer` variables and descriptors
audience: advanced users
prerequisites: arrays, memory management
related: allocatables.md, memory-management.md, ../reference/semantic-pyi-format.md
status: maintained
publication: reviewed
---

# Pointers

Fortran pointers are handled differently from allocatables. An allocatable
describes owned allocation state; a pointer describes an association to storage
whose owner may be elsewhere.

- **Scalar pointers** appear as `T | None` values.
- **Array pointers** appear as `Pointer[T[...]]` handles.

---

## Pointer Array Handles

Use `Pointer[T[...]]` for pointer arrays in the semantic contract:

```python
from x2py.contracts import Pointer, Float64

values: Pointer[Float64[:]]
```

### Key Properties

- A handle is always present, even when unassociated.
- `handle.associated` tells you the state.
- `handle.to_numpy()` returns a live view or `None`.
- The view is **borrowed** and can become stale if the target changes.
- Any NumPy view returned by `p.to_numpy()` is tied to the pointer target.
- Pointer-array handle results remain blocked until ownership and target
  lifetime are explicit.

---

## Complete Example

Create `pointers.f90`:

```fortran
module pointers_api
  implicit none
  real(8), target :: storage(3) = [1.0_8, 2.0_8, 3.0_8]
  real(8), pointer :: values(:) => null()
contains

  subroutine associate_values()
    values => storage
  end subroutine associate_values

  real(8) function sum_pointer(p) result(total)
    real(8), pointer, intent(in) :: p(:)
    if (associated(p)) then
      total = sum(p)
    else
      total = -1.0_8
    end if
  end function sum_pointer

end module pointers_api
```

Build it:

```bash
python3 -m x2py pointers.f90 --out-dir build/pointers
```

Use the generated module:

```python
import sys

sys.path.insert(0, "build/pointers")
import pointers.pointers_api as pointers_api

handle = pointers_api.values
print(handle.associated)                 # False
print(pointers_api.sum_pointer(handle))  # -1.0

pointers_api.associate_values()
print(handle.associated)                 # True
print(pointers_api.sum_pointer(handle))  # 6.0

handle.nullify()
print(handle.associated)                 # False
```

---

## Important Rules

- Use `Pointer[T[...]]` when a callable argument needs a pointer descriptor.
- Use normal `T[...]` when passing the **target data**.
- `to_numpy()` gives a live view. Copy explicitly if you need independent storage.
- Discard old views after nullification, reassociation, or target deallocation.
- `handle.nullify()` is available by default. Other operations (`allocate`, `deallocate`, etc.) require explicit policy.

---

## Scalar Pointers

Scalar pointers are handled as `T | None` values at the Python boundary. The
wrapper manages the call-local native pointer descriptor. An unassociated
projected result becomes `None`.

---

## Next

- Continue with **[Memory Management](memory-management.md)** after allocatables and pointers.
- See the [Language Feature Matrix](../language-support/feature-matrix.md) for current pointer support status

---
