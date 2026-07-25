---
title: Generated Classes Reference
audience: users, advanced users
prerequisites: wrapping derived types
related: generated-functions.md, generated-modules.md, semantic-pyi-format.md, ../guide/wrapping-derived-types.md, ../guide/memory-management.md
status: maintained
publication: draft
---

# Generated Classes Reference

Supported Fortran derived types become generated Python extension classes.
Instances wrap native storage through x2py's completed ownership policy; Python
field access and methods use generated wrapper operations instead of exposing a
stable binary layout.

Use [Wrapping Derived Types](../guide/wrapping-derived-types.md) for the
source-first workflow and [Memory Management](../guide/memory-management.md)
for ownership vocabulary. This page is the generated class surface reference.

## Class Placement

A derived type declared in a Fortran module is exposed from the generated child
module for that native module:

```python
from geometry.points import point

item = point(x=np.float64(1.0), y=np.float64(2.0))
```

The semantic `.pyi` contract records the public class name, constructor shape,
fields, methods, overloads, native type metadata, and ownership metadata.
Private derived types are omitted unless an edited contract intentionally
changes visibility and remains supported.

## Constructors

x2py generates a keyword-only Python initializer for public rank-zero numeric,
logical, and complex fields that are safe constructor inputs:

```python
from x2py.contracts import Float64, Int32, native_type

@native_type(finalizers=('cleanup_initialized',))
class initialized:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
```

Omitted keywords preserve native default initialization. Private components,
arrays, allocatables, pointers, strings, and nested derived components are not
automatic constructor keywords.

An edited semantic `.pyi` may remove the generated constructor, bind one
concrete initializer, or replace it with an exact overload set. x2py does not
recreate a constructor intentionally removed from the contract. Overloaded
constructors select a concrete target from the completed scalar dtype, array
dtype/rank, or generated-class predicates before invoking native code. An
indistinguishable or incomplete set is rejected during generation.

## Fields And Methods

Supported public scalar fields become Python descriptors. Assigning to a
writable field uses the completed setter policy. Private fields are omitted.

Nested scalar derived components are borrowed child wrappers that retain their
owning parent. Allocatable fields expose `Allocatable[T[...]]` handles, and
pointer-array fields expose `Pointer[T[...]]` handles. Each field handle retains
its parent wrapper; `to_numpy()` performs explicit extraction when completed
policy supports it. Arrays of derived types are unsupported.

Whole-object snapshot classes are not part of the active generated contract.
Plain and `Aliased` derived module variables both expose this normal live field
surface. An `Aliased` declaration permits a direct-address borrowed wrapper;
a plain declaration uses typed module-specific getter and setter bridge
operations without fabricating a whole-object address.

Type-bound procedures become methods. The generated semantic contract uses
`Pass()` on the concrete native-specific method when the native passed-object
position is not the default, and `@overload(...)` when a generic method has
multiple specific procedures:

```python
from x2py.contracts import Addr, Arg, Float64, Int32, Pass, bind, native_call, overload, private

class accumulator:
    total: Float64 = 0.0

    @private
    @bind("accumulator_add_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def add_integer(
        self,
        value: Int32
    ) -> None: ...

    @overload("accumulator_add_integer")
    def add(
        self,
        value: Int32
    ) -> None: ...
```

Method and constructor dispatch is exact. Calls are normalized against each
candidate's declared positional and keyword parameters, then matched without
calling candidates speculatively. Indistinguishable overloads block generation;
a call with no match raises a stable `TypeError`. The overload declaration is
only a Python dispatch link; it cannot also carry `@native_call(...)`.

## Ownership And Finalization

Generated constructors and wrapper-owned function results allocate native
instances owned by the Python wrapper. The generated deallocator finalizes and
releases that native instance exactly once.

Borrowed child wrappers, borrowed module objects, and borrowed component views
do not destroy the storage they reference. They retain the owning wrapper or
module reference needed for Python lifetime, but explicit native deallocation
or reallocation can still invalidate borrowed storage. Plain and `Aliased`
derived module objects are both live native-owned objects. An `Aliased` object
may use a proved native address; a plain object uses module-specific bridge
operations and must not fabricate addressability.

Native finalizers do not provide a recoverable Python status channel during
object destruction. Use ordinary wrapped procedures for recoverable cleanup
steps that need status reporting.

## Unsupported Class Shapes

x2py blocks derived-type forms whose Python ownership or dispatch policy is not
complete:

- arrays of derived types;
- mutable polymorphic arguments and polymorphic results;
- `class(*)`, abstract instantiation, and deferred bindings;
- allocatable or pointer polymorphic scalars; and
- direct binary-layout access for ordinary generated classes.

When a type is unsupported, the wrapper-build error should explain the blocking
form instead of generating a partial class.

## Evidence And Maintenance

Generated class behavior is covered by
[`test_derived_type_boundaries.py`](../../../tests/wrapper/fortran/derived_types/test_derived_type_boundaries.py),
[`test_derived_type_methods.py`](../../../tests/wrapper/fortran/derived_types/test_derived_type_methods.py),
[`test_constructors_and_finalizers.py`](../../../tests/wrapper/fortran/derived_types/test_constructors_and_finalizers.py),
[`test_borrowed_finalizers.py`](../../../tests/wrapper/fortran/derived_types/test_borrowed_finalizers.py), and
[`test_inheritance.py`](../../../tests/wrapper/fortran/derived_types/test_inheritance.py).
Exact class-method and constructor overloads are covered by
[`test_phase9_class_overloads.py`](../../../tests/wrapper/fortran/naming/test_phase9_class_overloads.py),
and explicit bound construction by
[`test_phase9_bound_constructors.py`](../../../tests/wrapper/fortran/derived_types/test_phase9_bound_constructors.py).

When class behavior changes, update this page with the derived-type user guide,
semantic `.pyi` reference, generated contract fixtures, and ownership evidence.
