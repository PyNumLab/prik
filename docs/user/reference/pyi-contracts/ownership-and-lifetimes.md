---
title: .pyi Ownership and Lifetimes
audience: advanced users
prerequisites: editing .pyi contracts overview, allocatable and pointer handles
related: index.md, calls-and-results.md, ../semantic-pyi-format.md, ../../guide/memory-management.md, ../../guide/allocatables.md, ../../guide/pointers.md
status: maintained
publication: reviewed
---

# Ownership and Lifetimes

Generated contracts already contain the ownership rules needed by ordinary
wrappers. Edit these annotations only when deliberately changing how storage
crosses the Python boundary.

## The Complete Ownership Rule

An explicit rule has three parts:

```python
from x2py.contracts import Annotated, Destruction, Float64, Ownership, Transfer

values: Annotated[
    Float64[:],
    Ownership("native"),
    Transfer("borrowed_view"),
    Destruction("native_owner"),
]
```

| Annotation | Question it answers |
| --- | --- |
| `Ownership(...)` | Who owns the original storage? |
| `Transfer(...)` | Does Python receive a value, copy, view, existing object, or new handle? |
| `Destruction(...)` | Who releases persistent storage? |

The three values form one rule. x2py checks them together with the value's
kind, storage, mutability, nullability, position, and available release
operation. An annotation cannot change where an existing allocation came from.

Storage markers such as `Allocatable`, `Pointer`, `Aliased`, and
`PointerPolicy(...)` describe the native declaration. Keep them accurate; they
do not by themselves grant permission to copy, release, or reassociate
storage.

## Common Handle Cases

An allocatable or pointer array handle stores a native descriptor: the metadata
that records the current storage, shape, and strides.

The same allocatable-array idea needs different rules in different places:

| Where the allocatable lives | Ownership | Transfer | Destruction | What Python receives |
| --- | --- | --- | --- | --- |
| Module variable | `native` | `borrowed_view` | `native_owner` | A handle to storage controlled by the module |
| Field of a Python class instance | `wrapper` | `borrowed_view` | `wrapper_dealloc` | A field handle that keeps its class instance alive |
| Function result with persistent descriptor storage | `wrapper` | `wrapper_instance` | `wrapper_dealloc` | An owned result handle that can be closed |

For a module variable, Python must not claim the right to release module
storage. For a class field, the field handle keeps the containing object alive.
For an owned result, `close()` or finalization releases the handle and its
allocation.

`handle.to_numpy()` returns a view that keeps the handle alive; it is not a
detached copy. A later native deallocation or reallocation can still make an
older view stale. Use `.copy()` when the NumPy array needs an independent
lifetime. The [Memory Management](../../guide/memory-management.md) guide
explains these handle rules in everyday terms.

## Transfer Values

| Transfer | Supported use |
| --- | --- |
| `by_value` | A scalar value returned to Python |
| `call_local` | Temporary converted input, one-call pointer association, or intentionally discarded mutation |
| `in_place` | Caller-supplied writable storage or an existing wrapper object |
| `copy_return` | A string, ordinary array result, or explicit replacement copied to Python |
| `snapshot_copy` | A detached copy for a projection that explicitly supports it |
| `borrowed_view` | A view whose storage owner is known and kept alive |
| `wrapper_instance` | A derived object or descriptor result held by a Python extension object |
| `blocked` | An explicit statement that no safe implemented transfer is known |

Pointer-array handle results preserve their association in descriptor handles;
they are not implicit snapshots.

## Destruction Values

| Destruction | Who releases the storage |
| --- | --- |
| `python_refcount` | Python, NumPy, or a generated base object |
| `wrapper_dealloc` | The generated extension object's deallocator |
| `native_owner` | The module or another native owner |
| `caller` | The caller that supplied the object |
| `call_local` | Temporary cleanup before the wrapper call returns |
| `none` | No persistent storage was created for this boundary value |
| `blocked` | Release responsibility is unknown or unsupported |

`Ownership("unknown")`, `Transfer("blocked")`, and
`Destruction("blocked")` make an unresolved contract fail safely. They are not
working runtime ownership modes.

## Combinations That Are Rejected

x2py rejects rules such as:

- replacement-only writable storage with `Transfer("borrowed_view")`;
- `Transfer("copy_return")` without a projected replacement;
- a pointer-array result with no stable descriptor owner or target lifetime;
- pointer reassociation without complete owner, shape, lifetime, and release
  behavior;
- `Ownership("native")` with `Destruction("python_refcount")` for the same
  allocation; and
- `Ownership("python")` with `Destruction("native_owner")`.

The error identifies the declaration and rejected rule. x2py does not replace
it with a guessed default.

## Next

Use the [Semantic `.pyi` Format](../semantic-pyi-format.md#ownership-transfer-and-destruction-policies)
for the complete annotation grammar.
