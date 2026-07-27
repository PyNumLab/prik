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

A Fortran allocatable descriptor records whether storage is allocated and, for
arrays, its address, shape, and strides. The descriptor controls the allocation,
while the owner of the Python handle depends on where that handle came from.

## Key Concepts

- Scalar allocatables appear as `T | None`; array allocatables use
  `Allocatable[T[...]]` handles.
- An array handle exposes allocation state and descriptor operations; it is not
  itself a NumPy array.
- `allocated` reports whether storage exists; `to_numpy()` returns a borrowed
  live view of that storage.
- Reallocation or deallocation invalidates existing views.
- Module and derived-field handles borrow their native owner. Function results
  and caller-created handles own persistent descriptor storage.
- `deallocate()` releases the current allocation but keeps the handle open;
  `close()` permanently ends an owned handle.

---

## When To Use An Allocatable Handle

Use `Allocatable[T[...]]` when the native callable needs the allocatable
descriptor and may inspect or change its allocation state:

```python
from x2py.contracts import Allocatable, Float64, Int32

values: Allocatable[Float64[:]]

def resize(values: Allocatable[Float64[:]], n: Int32) -> None: ...
```

Use ordinary `T[...]` when the callable needs only array data:

```python
def sum_values(values: Float64[:]) -> Float64: ...
```

A plain NumPy array cannot satisfy an `Allocatable[T[...]]` parameter because
it does not carry native allocation state. Use `to_numpy()` when Python needs
the current array data held by an allocatable handle.

---

## Allocatable Array Handle API

`Allocatable[T[...]]` is the semantic contract spelling. Generated Python APIs
return an `AllocatableArray`. You can also create an unallocated handle when a
routine needs a present descriptor that it will allocate:

```python
import x2py.contracts as xc

values = xc.Allocatable[xc.Float64[:]]()
assert values.allocated is False

api.fill_values(values)
assert values.allocated is True
```

The annotation supplies the element dtype and rank. The handle acquires
compiler-compatible descriptor storage when first passed to a writable
matching wrapper argument. It stays the same Python object after the call.
`Allocatable[Float64]()` is not supported because scalar allocatables cross the
Python boundary as values rather than array handles.

The same handle may be used by separately built x2py modules when their native
handle and Fortran compiler/runtime ABIs are compatible. See
[Sharing Descriptor Handles Between Modules](data-types.md#sharing-descriptor-handles-between-modules).

A returned or attribute array handle remains present even when its descriptor
is unallocated. Reading the Python attribute
returns an `Allocatable[T[...]]` handle, not `ndarray | None`.

A NumPy view reflects current native storage. Access it only while the
allocation is present:

```python
h = api.some_allocatable
if h.allocated:
    view = h.to_numpy()  # borrowed live view
    view[0] = 42.0
else:
    print("Not allocated")
```

| Member | Type | Behavior |
| --- | --- | --- |
| `allocated` | `bool` | Whether native storage is currently allocated. |
| `shape` | `tuple[int, ...] \| None` | Current dimensions, or `None` when unallocated. |
| `dtype` | `numpy.dtype` | Declared array element type. |
| `rank` | `int` | Declared number of dimensions. |
| `to_numpy()` | `numpy.ndarray \| None` | A live view of current storage, or `None` when unallocated. It never creates an automatic detached snapshot. |
| `deallocate()` | `() -> None` | Deallocates current storage when the generated contract permits this operation. |
| `resize(shape)` | `(int \| Sequence[int]) -> None` | Allocates or resizes storage to `shape` when the generated contract permits this operation. |
| `close()` | `() -> None` | Permanently releases an owned descriptor and any remaining allocation. It does nothing on a borrowed handle. |
| `closed` | `bool` | Whether an owned handle has been closed. |

Calling `deallocate()` or `resize(shape)` when the operation is unavailable
raises `NotImplementedError`.

---

## Deallocate Versus Close

| Operation | What it releases | Handle afterward |
| --- | --- | --- |
| `deallocate()` | The current array allocation. | Open and usable, with `allocated == False`. |
| `close()` | An owned descriptor and any allocation it still contains. | Permanently closed and unusable. |

Finalization closes owned handles automatically. Call `close()` explicitly only
when deterministic release matters, such as after using a large allocation.

Module and field handles are borrowed. Calling `close()` on one is a no-op: it
leaves the handle and its owner's storage unchanged. `deallocate()` changes the
owner's allocation when the generated contract permits it.

---

## Where Handles Come From

### Module Variables And Derived Fields

A module handle observes the live module allocatable descriptor. A derived-field
handle retains its parent wrapper and observes the live allocatable component
inside it. Native allocation changes are visible through the same Python
handle:

```python
h = api.values
assert not h.allocated

api.allocate_values(3)
assert h.allocated
assert h.shape == (3,)

api.resize_values(5)
assert h.shape == (5,)
```

### Function Results

An allocatable-array function result becomes an owned `AllocatableArray`. The
handle owns persistent descriptor storage that x2py finalizes automatically:

```python
values = api.make_values(3)
print(values.to_numpy())
```

A direct allocatable-array function result is expected to be allocated. Use a
zero-sized allocation to represent an empty result. If the native function may
instead return an unallocated result, declare that possibility explicitly:

```python
from x2py.contracts import Allocatable, Annotated, Float64, Int32, MaybeUnallocated

def make_values(n: Int32) -> Allocatable[Float64[:]]: ...

def maybe_values(
    n: Int32,
) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...
```

The second function still returns a present handle. That handle may have
`allocated == False`, in which case `to_numpy()` returns `None`. Returning an
unallocated direct result without `MaybeUnallocated` violates the generated
contract and may crash the wrapper.

### Output And Inout Arguments

A nonoptional allocatable-array `intent(out)` does not consume incoming
allocation state, so it is hidden and returned as a new owned handle. A hidden
output may remain unallocated.

An optional `intent(out)` remains visible so omission preserves native
`present(...)` behavior. An `intent(inout)` descriptor also remains visible
because native code reads and changes its current allocation. When the semantic
contract projects that argument as a result, Python receives the same handle
object:

```python
values = api.make_values(2)
returned = api.replace_values(values)

assert returned is values
print(values.to_numpy())
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
    allocate(arr(max(n, 0)))
    if (n > 0) then
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
from storage.storage import make_values, replace_values

values = make_values(np.int32(3))
print(values.to_numpy())                    # [2. 4. 6.]

returned = replace_values(values)
assert returned is values                   # same handle
print(values.to_numpy())                    # [10. 20.]
```

---

## Safety Checklist

Keep these rules in mind when allocation state can change.

### Check Allocation Before Use

```python
view = h.to_numpy()
view[0] = 1.0  # NOT OK: view may be None
```

```python
if h.allocated:
    view = h.to_numpy()
    if view is not None:
        view[0] = 1.0
```

This check is required whenever an allocatable may be unallocated, including a
result declared with `MaybeUnallocated`.

### Copy Or Discard Views Before Storage Changes

```python
view = h.to_numpy()
saved = None if view is None else view.copy()
h.resize(8)
```

After `resize()`, `deallocate()`, or a native call that may reallocate the
descriptor, discard `view` and call `to_numpy()` again. The independent
Python-owned `saved` copy remains safe.

### Do Not Keep Using A Closed Result

```python
view = result.to_numpy()
result.close()
result.shape  # NOT OK: the owned descriptor has been released
view[0]       # NOT OK: close() released the owned allocation
```

A view normally retains its handle, but an explicit `close()` releases an owned
allocatable result immediately. Finish using or copy all views before closing
the handle.

### Respect Ownership And Operation Permissions

```python
h.deallocate()  # NOT OK when the generated contract does not permit it
```

Allocation, deallocation, and resizing are available only when completed
policy permits them. A module or field handle can borrow storage controlled by
its native owner; the presence of an allocation does not by itself grant
Python permission to release it. Only a permitted descriptor operation or the
native owner's API may deallocate that storage.

---

## Scalar Allocatables

Scalar allocatables appear as `T | None` values at the Python boundary rather
than `AllocatableArray` handles. An unallocated projected scalar result becomes
`None`. Scalar values do not expose persistent allocation state, `to_numpy()`,
or descriptor operations.

---

## Next

- Continue with [Memory Management](memory-management.md) for ownership,
  lifetime, and cleanup rules.
