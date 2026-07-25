---
title: Memory Management
description: Clear ownership rules, views vs copies, lifetimes, and destruction responsibility in x2py
audience: users, advanced users
prerequisites: arrays, wrapping derived types
related: allocatables.md, pointers.md, editing-semantic-pyi-contracts.md
status: maintained
publication: reviewed
---

# Memory Management

x2py lets Python work directly with native Fortran storage when that is safe.
That gives you fast wrappers without surprise copies, but it also means
ownership has to be explicit.

The guiding question is:

> Who is allowed to release this storage, and how long is the Python object allowed to use it?

x2py answers that question **before** wrapper code is generated. The generated
Python extension then follows the completed policy exactly, so ownership is a
documented contract rather than a runtime guess.

---

## The Short Version

Most memory-management questions in x2py reduce to three cases:

| Situation | What to expect |
| --- | --- |
| Python receives a normal value or NumPy array result | Python owns an independent value. |
| Python passes an object into a wrapped call | The same object remains with the caller; native code may mutate through it only when the contract allows it. |
| Python receives a handle, wrapper object, component, or view into native state | The Python object may be live, borrowed, or wrapper-owned; check the ownership kind before keeping views across native calls. |

!!! tip "A reliable habit"
    Before keeping a view or passing an object back into native code, ask two
    separate questions: who owns the Python object, and who owns the storage
    behind it?

---

## Two Ownership Layers

Ownership can describe two different things:

| Layer | Question | Example |
| --- | --- | --- |
| **Boundary object** | Who supplied and keeps the Python object used in this call? | A NumPy array, handle, or wrapper instance passed as an argument |
| **Target storage** | Who owns the native allocation that object exposes or points at? | Python array data, Fortran module storage, or a wrapper-owned native instance |

Those layers can have different owners. A caller-owned handle can point at a
native-owned module allocation. A caller-owned child wrapper can borrow storage
owned by its parent wrapper. There is still exactly one owner for each real
allocation.

---

## Ownership Terms

| Term | Plain meaning | Typical example |
| --- | --- | --- |
| **Python-owned** | Python owns an independent value or array. | Function array result, `view.copy()` |
| **Caller-owned** | Your Python code supplied the boundary object and keeps it after the call. | Writable NumPy array, native-backed handle, wrapper instance |
| **Wrapper-owned** | A generated x2py Python object owns native storage. | Derived-type result, owned allocatable result handle |
| **Native-owned** | Fortran module state or another native owner controls release. | Module variable, module allocatable |
| **Borrowed view** | Python sees storage owned by someone else. | `handle.to_numpy()`, nested component |
| **Call-local** | x2py creates temporary storage for one native call only. | Scalar address slot, fixed string buffer |

### Python-owned

Python-owned values are ordinary Python or NumPy objects with independent
lifetime. If native storage changes later, a Python-owned copy does not change.

```python
view = handle.to_numpy()
copy = None if view is None else view.copy()
```

Use this when the data must survive native reallocation, deallocation, or
reassociation.

### Caller-owned

"Caller" means your Python code: the code that calls the wrapped function. This
label says x2py must preserve the Python object you supplied. It does not always
say who owns every allocation reachable through that object.

For an ordinary NumPy array, the boundary object and the target storage are both
Python-owned:

```python
values = np.ones(4, dtype=np.float64)
api.scale(values)

# Same array object, possibly mutated in place.
print(values[0])  # 2.0
```

The wrapper may mutate through a caller-owned object when the contract allows
it, but it must not free, reallocate, or secretly replace that object.

For a native-backed handle or borrowed wrapper, the caller owns the Python
object it passes, but native code or a parent wrapper may still own the target
storage behind it:

```python
handle = api.values          # Python holds the handle object.
view = handle.to_numpy()     # Native module storage may be behind the view.
api.update_values(handle)    # The call keeps using the same handle object.
```

!!! note "Ownership is not transferred"
    Passing an object to native code does not transfer the owner of that object
    or its target storage. Mutation is allowed only when the completed contract
    says that specific object can be written through.

### Wrapper-owned

A generated Python class is an extension class produced by x2py and imported
from the generated module. You construct and pass it like a normal Python
object, but internally it controls one native instance.

For Fortran users, wrapper-owned is mostly visible with supported
`type :: ...` derived types:

```python
point = geometry.points.point(x=np.float64(1.0), y=np.float64(2.0))
made = geometry.points.make_point(np.float64(3.0), np.float64(4.0))
```

Here `point` and `made` are Python objects whose generated x2py deallocator is
responsible for finalizing and releasing their native instances exactly once.

Owned allocatable array results are another wrapper-owned case: their generated
handle owns persistent descriptor storage and releases it on `close()` or
finalization. Module allocatable handles are different because the Fortran
module still owns their target allocation.

Ordinary NumPy arrays, module variables, and borrowed components are not
wrapper-owned.

Nested derived-type components are different: `container.origin` may be a
borrowed child wrapper. It gives Python a convenient object for the component,
but the parent object still owns the native storage.

### Native-owned

Native-owned storage belongs to Fortran module state or another native owner.
Python can read it, write it through supported setters, or view it through a
handle, but Python is not responsible for releasing it.

In short, plain and `Aliased` derived module variables remain live native-owned objects.
An `Aliased` module object may use an address-backed borrow; a plain module
object uses generated module-specific access. In both cases, the owning module
state decides when the native storage is valid.

### Borrowed views

A borrowed view is a Python object that points at storage owned somewhere else.
The view itself may keep the parent wrapper or module object alive when x2py can
do so, but it cannot stop native code from reallocating or deallocating the
target storage.

```python
view = api.values.to_numpy()
snapshot = None if view is None else view.copy()

api.resize_values()

# view may now be stale; snapshot remains independent Python-owned data.
```

### Call-local

Call-local storage is temporary workspace created only for one wrapped call.
x2py may create a native scalar slot, a fixed-width string buffer, or a
descriptor adapter, pass it to native code, and release it before returning to
Python.

If the contract says native changes should be returned to Python, policy
completion must also say how that value is projected back. Otherwise, mutation
of call-local storage is intentionally not a persistent Python-visible update.

---

## Handles And Target Storage

`Allocatable[T[...]]` and `Pointer[T[...]]` handles are control objects. They
tell Python whether native storage is allocated or associated, and they provide
`.to_numpy()` when a live view is available.

Owning a handle is not the same thing as owning the target array. A module
allocatable handle can be a stable Python object while the Fortran module still
owns the allocation behind it. A pointer handle can describe an association
without owning the target at all.

!!! warning "Views are live, not snapshots"
    `handle.to_numpy()` returns a view of current native storage. It never
    creates an automatic detached snapshot. If native code may reallocate or
    deallocate that storage, copy the view first.

---

## Core Rules

1. **Exactly one owner** is responsible for destroying each allocation.
2. Passing an object to native code does not automatically transfer ownership of
   the object or its target storage.
3. **Borrowed views** can become stale if the owner reallocates or deallocates.
4. **Copies** are safe but more expensive.
5. Pointers **do not** imply ownership of their target.
6. A view from `.to_numpy()` is live: changes affect the native storage.

---

## Views vs Copies

```python
view = handle.to_numpy()        # borrowed live view
copy = view.copy()              # independent Python-owned copy
```

Use a **view** when performance matters and you know the owner will keep the
storage valid. Use a **copy** when the data must survive later native
reallocation, deallocation, or reassociation.

| Need | Use |
| --- | --- |
| Fast access to current native storage | `view = handle.to_numpy()` |
| Data that survives native changes | `copy = view.copy()` |
| In-place mutation of Python input | Caller-owned boundary object; target owner depends on that object |
| Native object lifetime managed by Python wrapper | Wrapper-owned generated class |

---

## Common Situations

| Situation | Ownership shape |
| --- | --- |
| Ordinary NumPy array passed to a writable argument | Caller-owned boundary object with Python-owned array storage. |
| Native-backed handle passed into a call | Caller-owned boundary object; target storage can remain native-owned. |
| Function returning an ordinary array | Usually a Python-owned NumPy array. |
| Derived-type constructor or derived-type function result | Wrapper-owned generated class instance. |
| Nested derived-type component | Borrowed child wrapper retained through the parent. |
| Module variable | Native-owned state exposed through a getter, setter, handle, or proxy. |
| `Allocatable[T[...]]` handle | Control object for allocation state and live views; target ownership depends on origin. |
| `Pointer[T[...]]` handle | Control object for association state; the pointer does not own the target. |
| Call-local adapter | Internal temporary storage used only during one wrapped call. |

---

## Practical Guidelines

- Always call `.copy()` on a view before a native operation that might reallocate storage.
- Do not use `del` as a native deallocation API.
- Check `.allocated` / `.associated` before using handles.
- Review the generated `.pyi` contract to understand ownership.
- When a value crosses a boundary, identify both the boundary object owner and
  the target storage owner.

---

## Next

- Use the [Semantic `.pyi` Format](../reference/semantic-pyi-format.md) for policy metadata details.
- Review [Callbacks](callbacks.md) and [Error Handling](error-handling.md) when ownership affects callable lifetimes or cleanup after failures.
