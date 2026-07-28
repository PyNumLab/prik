---
title: Memory Management
description: Ownership, live views, copies, and safe cleanup in x2py
audience: users, advanced users
prerequisites: arrays
related: allocatables.md, pointers.md, wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Memory Management

x2py can give Python direct access to storage created by Fortran. This avoids
unnecessary copies, but Python must not use that storage after its owner
releases or replaces it.

Two questions keep these cases simple:

1. Who owns the Python object?
2. Who owns the storage behind it?

The answers are not always the same.

## Key Concepts

- Ordinary Python values and independently created NumPy arrays have
  Python-managed storage.
- An [allocatable](allocatables.md) or [pointer](pointers.md) handle is a Python
  object that describes native array storage. Owning the handle does not always
  mean owning the storage it refers to.
- Calling `to_numpy()` on an allocatable or pointer handle returns a live NumPy
  view, not a copy.
- A live view can become invalid if native code reallocates, deallocates, or
  changes the storage it refers to.
- Passing an object to a wrapped function does not transfer its ownership.
- Release storage only through the object or native API that owns it.

---

## The Python Object And Its Storage

For example, an allocatable or pointer handle can refer to storage owned
somewhere else:

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
| Derived-type object constructed or returned by x2py | Its generated Python wrapper |
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
| End an owned handle | `close()` releases the descriptor and any remaining allocation | `close()` releases the descriptor, not the target |

A pointer association does not by itself make the pointer responsible for the
target. If a target was allocated through a pointer, call `deallocate()` before
`nullify()`, reassociating that pointer, or closing it. Otherwise, the target
may be left without an owner.

See [Allocatables](allocatables.md) and [Pointers](pointers.md) for their full
APIs and examples.

---

## Owned And Borrowed Handles

Allocatable and pointer handles can be owned or borrowed. Caller-created
handles and function-result handles own their descriptor storage. Their
`close()` method permanently ends the handle:

```python
result.close()
assert result.closed
```

Do not use an owned allocatable or pointer handle after calling `close()` on
it. Owned handles close automatically when Python finalizes them, so call
`close()` yourself only when the resource must be released immediately.

Module and derived-field handles are borrowed from their native owner. Calling
`close()` on a borrowed handle does nothing: it does not close the handle or
release the owner's storage.

The resource released by `close()` depends on the handle:

- Closing an owned allocatable handle releases its descriptor and any
  allocation it still contains.
- Closing an owned pointer handle releases only its descriptor. Its target has
  a separate lifetime.

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
wrapper releases that instance automatically when it is finalized.

Both plain and `Aliased` derived module variables remain live objects. The
Fortran module owns their storage, and Python only accesses it.

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
- Do not use an owned allocatable or pointer handle after `close()`.
- Synchronize access when another thread may change the same native storage.

---

## Next

- Read [Allocatables](allocatables.md) for allocation and resizing.
- Read [Pointers](pointers.md) for association and target lifetime.
- Read [Wrapping Derived Types](wrapping-derived-types.md) for object and field
  lifetimes.
