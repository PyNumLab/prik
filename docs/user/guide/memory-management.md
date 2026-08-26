---
title: Memory Management
description: Ownership, live views, copies, and safe cleanup in PRIK
audience: users, advanced users
prerequisites: arrays
related: allocatables.md, pointers.md, wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Memory Management

PRIK can give Python direct access to storage created by Fortran. This avoids
unnecessary copies, but Python must not use that storage after its owner
releases or replaces it.

Two questions keep these cases simple:

1. Who owns the Python object?
2. Who owns the storage behind it?

The answers are not always the same.

## The Python Object And Its Storage

An [allocatable](allocatables.md) or [pointer](pointers.md) handle is a Python
object that describes native array storage. The storage can belong to the
handle itself, a Fortran module, a parent object, or a separate pointer target:

```python
handle = api.values
view = handle.to_numpy()
```

Python owns the `handle` and `view` objects. The storage visible through
`view`, however, may belong to a Fortran module, a generated result handle, or
another native object.

Common cases are:

| Value seen by Python | Who owns the storage? |
| --- | --- |
| Ordinary Python value or independently created NumPy array | Python |
| `view.copy()` | Python |
| Fortran module variable | The Fortran module |
| Derived-type object constructed or returned by PRIK | Its generated Python wrapper |
| Derived-type field that exposes native storage | Usually its parent object |
| Allocatable or pointer handle | Depends on where the handle came from and how its current storage was created |

There must be one clear owner for every allocation. Other objects may view or
refer to that allocation, but they must not release it.

---

## Live Views And Copies

Calling `handle.to_numpy()` gives direct access to the handle's current native
storage:

```python
view = handle.to_numpy()
if view is not None:
    view[0] = 42.0  # changes the native storage
```

This is fast because no data is copied. It also means that the view is safe
only while the same native storage remains alive.

Copy the data when it must survive a later native change:

```python
view = handle.to_numpy()
saved = None if view is None else view.copy()

api.replace_values()

# Use saved here. Do not keep using view.
```

Reallocation, deallocation, pointer reassociation, resizing, or explicit
cleanup can make an older view invalid. Get a new view after such an operation.

---

## Allocatables And Pointers

Allocatable and pointer handles both describe native arrays, but they do not
have the same ownership rules:

| Operation | Allocatable handle | Pointer handle |
| --- | --- | --- |
| Check current state | `allocated` | `associated` |
| View current data | `to_numpy()` | `to_numpy()` |
| Remove current storage | `deallocate()` releases the allocation when the operation is available | `deallocate()` releases only a target allocated through this pointer |
| Stop referring to storage without releasing it | Not applicable | `nullify()` |
| End a returned or caller-created handle | `close()` releases the descriptor and any remaining allocation | `close()` releases the descriptor, not the target |

A pointer association does not by itself make the pointer responsible for the
target. If a target was allocated through a pointer, call `deallocate()` before
`nullify()`, reassociating that pointer, or closing it. Otherwise, the target
may be left without an owner.

See [Allocatables](allocatables.md) and [Pointers](pointers.md) for their full
APIs and examples.

---

## Closing Handles

Caller-created handles and function-result handles have their own descriptor
storage. Their `close()` method permanently ends the handle:

```python
result.close()
assert result.closed
```

Do not use the handle after calling `close()` on it. These handles close
automatically when Python no longer uses them, so call `close()` yourself only
when the resource must be released immediately.

Module and derived-field handles expose descriptors belonging to the Fortran
module or parent object. Calling `close()` on one does nothing: it does not
close the handle or release that storage.

The resource released by `close()` depends on the handle:

- Closing a returned or caller-created allocatable handle releases its descriptor and any
  allocation it still contains.
- Closing a returned or caller-created pointer handle releases only its descriptor. Its target has
  a separate lifetime.

---

## Sharing Handles Between Extensions

The same allocatable or pointer handle can be passed between separately built
PRIK extensions. Their matching arguments must have the same descriptor kind,
element type, and rank.

The handoff does not copy array data. Both extensions must use compatible PRIK
versions, the same Fortran compiler toolchain, and compatible Fortran
runtimes. An incompatible handle is rejected. Sharing a pointer handle does
not extend the lifetime of its target.

---

## Passing Objects To Functions

Passing an object to a wrapped function does not give the function ownership of
that object.

- A writable NumPy array remains the same Python array, although the function
  may change its elements.
- A writable allocatable handle remains the same handle, although the function
  may allocate, deallocate, or replace its current storage.
- A writable pointer handle remains the same handle, although the function may
  change its association.

If a call may change native storage, finish using or copy any existing views
before the call. Ask the handle for a new view afterward.

---

## Derived Objects And Fields

A generated wrapper for a derived-type object can own a native instance. The
wrapper releases that instance exactly once when it is finalized. Normal
Fortran deallocation and component finalization then apply, including an
applicable user-defined `FINAL` procedure.

Derived module variables remain live objects.
The Fortran module owns their storage. Python only accesses it.

Borrowed module objects and borrowed fields never destroy the native storage
they reference. They retain their Python owner when one exists, but native
reallocation or deallocation can still invalidate the borrowed storage.

A field returned from that object may refer to storage inside its parent. The
generated field object keeps its parent alive, but it cannot stop native code
from replacing or releasing the field's storage. Such a change can invalidate
existing views.

See [Wrapping Derived Types](wrapping-derived-types.md) for construction,
fields, and function arguments.

---

## Safety Checklist

- Check `allocated` on an allocatable handle or `associated` on a pointer handle
  before reading through it.
- Treat every result of `to_numpy()` as a live view.
- Copy a view before a call that may replace or release its storage.
- Call `deallocate()` on an allocatable handle only when it may release that
  allocation. Call it on a pointer handle only for a target allocated through
  that pointer.
- Call `nullify()` on a pointer handle to remove its association without
  destroying the target.
- Do not use a returned or caller-created handle after `close()`.
- Synchronize access when another thread may change the same native storage.

---

## Next

- Continue with [Callbacks](callbacks.md).
- Return to [Allocatables](allocatables.md), [Pointers](pointers.md), or
  [Wrapping Derived Types](wrapping-derived-types.md) for their full APIs.
