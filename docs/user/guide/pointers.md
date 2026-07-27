---
title: Pointers
description: How x2py handles Fortran `pointer` variables, results, fields, and descriptors
audience: advanced users
prerequisites: arrays, memory management
related: allocatables.md, memory-management.md
status: maintained
publication: reviewed
---

# Pointers

A Fortran pointer describes an association with target storage. The pointer
descriptor records whether a target is present and, for arrays, its address,
shape, and strides. It does not by itself say who owns that target.

## Key Concepts

- A pointer descriptor refers to target storage; it does not own that storage
  by default.
- Scalar pointers appear as `T | None`; array pointers use live
  `Pointer[T[...]]` handles.
- `associated` describes association, not ownership or target lifetime.
- NumPy arrays returned by `to_numpy()` are borrowed live views, not copies.
- Reassociation, resizing, or deallocation can invalidate existing views.
- `associate(other)` makes two pointer handles refer to the same target without
  copying it.
- Use `deallocate()` only if this pointer was used to create its current target
  with `allocate()`. Otherwise, use `nullify()`.
- `close()` releases an owned handle descriptor, not its target.

---

## When To Use A Pointer Handle

Use `Pointer[T[...]]` when the native callable needs the pointer descriptor:

```python
from x2py.contracts import Float64, Pointer

module_values: Pointer[Float64[:]]

def inspect_pointer(values: Pointer[Float64[:]]) -> Float64: ...
```

Use ordinary `T[...]` when the callable needs only array data:

```python
def sum_values(values: Float64[:]) -> Float64: ...
```

An associated pointer handle may satisfy an ordinary array parameter when its
dtype, rank, shape, layout, and contiguity meet that parameter's contract. A
plain NumPy array cannot satisfy a `Pointer[T[...]]` parameter because it does
not carry a native pointer descriptor.

---

## Pointer Array Handle API

`Pointer[T[...]]` is the semantic contract spelling. Generated Python APIs
return a `PointerArray`. You can also create an unassociated handle when a
routine needs a present pointer descriptor that it will associate:

```python
import x2py.contracts as xc

target = xc.Pointer[xc.Float64[:]]()
assert target.associated is False

api.choose_target(target)
assert target.associated is True
```

The annotation supplies the element dtype and rank. The handle acquires
compiler-compatible descriptor storage when first passed to a writable
matching wrapper argument. It stays the same Python object after the call.
`Pointer[Float64]()` is not supported because scalar pointers cross the Python
boundary as values rather than array handles.

| Member | Type | Behavior |
| --- | --- | --- |
| `associated` | `bool` | Whether the descriptor currently has a target. |
| `shape` | `tuple[int, ...] \| None` | Current target dimensions, or `None` when unassociated. |
| `dtype` | `numpy.dtype` | Declared target element type. |
| `rank` | `int` | Declared number of dimensions. |
| `to_numpy()` | `numpy.ndarray \| None` | A borrowed live target view, or `None` when unassociated. |
| `associate(other)` | `(PointerArray) -> None` | Makes this pointer's association match `other` without copying data. |
| `nullify()` | `() -> None` | Removes the association without destroying the target. |
| `allocate(shape)` | `(int \| Sequence[int]) -> None` | Creates and associates a target for an unassociated pointer. |
| `deallocate()` | `() -> None` | Destroys the current target if this pointer was used to allocate it. |
| `resize(shape)` | `(int \| Sequence[int]) -> None` | Replaces the current target when `deallocate()` is valid. |
| `close()` | `() -> None` | Permanently releases owned descriptor storage; it does not deallocate the target. It does nothing on a borrowed handle. |
| `closed` | `bool` | Whether an owned handle has been closed. |

`associate()` and `nullify()` are available by default. A handle may also
support allocation, target deallocation, resizing, and NumPy extraction.
Calling one of these operations when it is unavailable raises
`NotImplementedError`.

---

## Associate Two Pointers

```python
p1 = xc.Pointer[xc.Float64[:]]()
p1.associate(p2)
```

Both pointers must have the same dtype and rank. If `p2` is associated, both
pointers refer to the same target. If `p2` is unassociated, `p1` becomes
unassociated. No data is copied.

Any previous association of `p1` is removed without destroying its old target.
If `p1` was the only pointer to a target it allocated, call `p1.deallocate()`
before reassociating it to avoid leaking that memory.

---

## Nullify, Deallocate, And Close

| Operation | What it releases | Handle afterward |
| --- | --- | --- |
| `nullify()` | This descriptor's association. It does not destroy the target. | Open and usable, with `associated == False`. |
| `deallocate()` | A target this pointer was used to allocate. | Open and usable, with `associated == False`. |
| `close()` | Owned descriptor storage. It does not destroy the target. | Permanently closed and unusable. |

Finalization closes owned descriptors automatically. Call `close()`
explicitly only when deterministic descriptor release matters. It never
destroys the pointer target because descriptor and target ownership are
separate.

Module and field pointer handles are borrowed. Calling `close()` on one is a
no-op that leaves the descriptor, target, and handle unchanged.

---

## Where Handles Come From

### Module Variables And Derived Fields

A module handle observes the live module pointer descriptor. A field handle
retains its parent wrapper and observes the live pointer component inside it.
Native reassociation is visible through the same Python handle:

```python
p = api.values
assert not p.associated

api.associate_values()
assert p.associated

api.choose_different_values()
print(p.shape)  # reflects the new target
```

### Function Results

A pointer-array function result becomes a returned `PointerArray`. The handle
owns persistent descriptor storage, not necessarily the target:

```python
p = api.selected_values(True)
if p.associated:
    print(p.shape)
```

An unassociated native result is a present handle with `associated == False`.
It is not returned as `None`.

### Output And Inout Arguments

A nonoptional pointer-array `intent(out)` does not consume an incoming
association, so it is hidden and returned as a new handle:

```python
p = api.select_values()
```

An optional `intent(out)` remains visible so omission can preserve native
`present(...)` behavior. Pointer-array `intent(inout)` also remains visible
because its incoming association is part of the call:

```python
p = api.values
api.reassociate_values(p)
assert p.associated  # the same descriptor was updated in place
```

For an optional pointer descriptor, omission or `None` makes the native dummy
absent. Passing an unassociated handle makes it present but unassociated.

---

## Complete Module Example

Create `pointers.f90`:

```fortran
module pointers_api
  implicit none
  real(8), target :: storage(6) = [1, 2, 3, 4, 5, 6]
  real(8), pointer :: values(:) => null()
contains

  subroutine associate_values()
    values => storage(1:6:2)
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

Build and use it:

```bash
python3 -m x2py pointers.f90 --out-dir build/pointers
```

```python
import sys

sys.path.insert(0, "build/pointers")
import pointers.pointers_api as pointers_api

handle = pointers_api.values
assert not handle.associated
assert pointers_api.sum_pointer(handle) == -1.0

pointers_api.associate_values()
assert handle.associated
assert pointers_api.sum_pointer(handle) == 9.0

handle.nullify()
assert not handle.associated
```

---

## Contiguous And Strided Targets

A pointer may describe a whole array, a contiguous section, or a strided
section:

```fortran
real(8), target :: storage(6) = [10, 20, 30, 40, 50, 60]
real(8), pointer :: selected(:)

selected => storage(1:6:2)
```

With descriptor-view extraction enabled, Python preserves that layout:

```python
view = api.selected.to_numpy()
print(view)          # [10. 30. 50.]
print(view.shape)    # (3,)
print(view.strides)  # (16,) for eight-byte elements

view[1] = 99.0       # updates storage(3)
```

A strided pointer can be passed to a pointer-descriptor parameter. Passing the
same handle to an ordinary array parameter that requires contiguous data is
rejected.

---

## Safety Checklist

Pointer safety depends on the target owner and lifetime, not only on descriptor
state.

### Check Association And Lifetime

```python
view = p.to_numpy()
view[0] = 1.0  # NOT OK: view may be None
```

```python
if p.associated:
    view = p.to_numpy()
    if view is not None:
        view[0] = 1.0
```

Association is necessary but cannot prove that an externally managed target is
still alive. Native code must not leave a pointer associated with expired
storage.

### Do Not Return A Pointer To Expired Local Storage

```fortran
function invalid_result() result(values)
  real(8), target :: local_values(3)
  real(8), pointer :: values(:)
  values => local_values  ! NOT OK: local_values expires on return
end function invalid_result
```

Putting the pointer inside a returned derived object does not repair this
native lifetime error.

### Copy Or Discard Views Before Target Changes

```python
view = p.to_numpy()
saved = None if view is None else view.copy()
api.point_at_different_storage()
current = p.to_numpy()
```

Do not use `view` after target deallocation, reassociation, resizing, or
reallocation behind the pointer. Extract `current` for the new target. The
independent Python-owned `saved` copy remains safe.

### Deallocate Only What This Pointer Allocated

```python
p.allocate(10)
p.deallocate()
```

The `allocate()` may be called from Python or from a native routine using the
same pointer. If the pointer was only associated with existing storage, use
`nullify()` instead:

```python
p.nullify()  # does not destroy the target
```

Do not use `nullify()` for a target created with `p.allocate()`. The memory
remains allocated and leaks if no other pointer refers to it. Use
`p.deallocate()` instead.

Use `resize()` only in the same cases where `deallocate()` is valid.

### Nullifying One Pointer Does Not Change Other Aliases

```python
first = api.first_pointer
second = api.second_pointer
assert first.associated and second.associated

first.nullify()
assert second.associated
```

`nullify()` removes only `first`'s association. It does not destroy the target
or change `second`. Deallocating their shared target makes every pointer to
that target invalid.

### Do Not Keep Using A Closed Handle

```python
view = returned_pointer.to_numpy()
returned_pointer.close()
returned_pointer.shape  # NOT OK: the descriptor has been released
```

`close()` releases an owned result descriptor but never deallocates its target.
An existing NumPy view may still refer to the target, but its safety now depends
entirely on that target's separate owner and lifetime. Do not use the closed
handle to reason about the view.

### Respect Contiguity Requirements

```python
strided = api.selected_slice
api.requires_contiguous_array(strided)  # NOT OK: rejected before the call
```

Pass the descriptor to a pointer parameter, or make an explicit contiguous
copy when ordinary array data is required:

```python
view = strided.to_numpy()
copy = None if view is None else view.copy(order="F")
```

### Synchronize Target Changes

```python
view = p.to_numpy()
# Another thread reassociates or deallocates p here.
value = view[0]  # NOT OK without native synchronization
```

x2py does not lock native pointer association or track outstanding NumPy views.
The application must synchronize concurrent native changes.

---

## Scalar Pointers

Scalar pointers appear as `T | None` values at the Python boundary rather than
`PointerArray` handles. An unassociated projected scalar result becomes `None`.
Scalar values do not expose persistent association, `to_numpy()`, or pointer
descriptor operations.

---

## Next

- Continue with [Memory Management](memory-management.md) for owner and lifetime
  rules shared by arrays, pointers, allocatables, and derived objects.
