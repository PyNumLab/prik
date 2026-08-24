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
Instances wrap native storage through PRIK's completed ownership policy; Python
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

PRIK generates a keyword-only Python initializer for public rank-zero numeric,
logical, and complex fields that are safe constructor inputs:

```python
from prik.contracts import Float64, Int32

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

When the Fortran source declares a generic interface named for the derived
type, its specific functions generate an overloaded `__init__` surface instead
of the field-keyword form. Each candidate must have a complete, distinguishable
runtime signature. [Which Constructor You
Get](../guide/wrapping-derived-types.md#which-constructor-you-get) shows the
source-to-Python mapping.

An edited semantic `.pyi` may remove the generated constructor, bind one
concrete initializer, or replace it with an exact overload set. To reuse one
existing native initializer, replace the generated field-keyword declaration:

```python
from prik.contracts import Addr, Arg, Int32, Pass, bind, native_call

def init_state(owner: state, size: Int32) -> None: ...

class state:
    @bind("init_state")
    @native_call([Pass(), Addr(Arg(0))])
    def __init__(self, size: Int32) -> None: ...
```

Exactly one `Pass()` places the newly allocated `state` object in the native
call. The edited declaration replaces the generated `__init__`; keeping both
forms is contradictory. Removing `__init__` without adding a replacement makes
the class non-constructible from Python.

An edited contract can instead declare an exact constructor overload set. PRIK
selects a concrete target from the completed scalar dtype, array dtype/rank, or
generated-class predicates before invoking native code. An indistinguishable or
incomplete set is rejected during generation.

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
from prik.contracts import Addr, Arg, Float64, Int32, Pass, bind, native_call, overload, private

class accumulator:
    def __init__(self, *, total: Float64 = 0.0) -> None: ...

    total: Float64 = 0.0

    @private
    @bind("accumulator_add_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def add_integer(self, value: Int32) -> None: ...

    @private
    @bind("accumulator_add_real")
    @native_call([Pass(), Addr(Arg(0))])
    def add_real(self, value: Float64) -> None: ...

    @bind("add")
    @overload("accumulator_add_integer")
    def add(self, value: Int32) -> None: ...

    @bind("add")
    @overload("accumulator_add_real")
    def add(self, value: Float64) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_integer(
    self: accumulator,
    value: Int32
) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def accumulator_add_real(
    self: accumulator,
    value: Float64
) -> None: ...
```

The two `add` declarations are the public Python overload set. Each
`@overload(...)` links one concrete contract, while `@bind("add")` routes the
native call through the accessible type-bound generic when its specifics are
private.

Method and constructor dispatch is exact. Calls are normalized against each
candidate's declared positional and keyword parameters, then matched without
calling candidates speculatively. Indistinguishable overloads block generation;
a call with no match raises a stable `TypeError`. The overload declaration is
only a Python dispatch link; it cannot also carry `@native_call(...)`.

## Ownership And Finalization

Generated constructors and wrapper-owned function results allocate native
instances owned by the Python wrapper. The generated deallocator finalizes and
releases that native instance exactly once.

Every wrapper-owned instance has this destruction path, whether or not its
Fortran type declares a `FINAL` procedure. The Python object owns a native
capsule. When the last owning Python reference is released, the capsule
destructor calls PRIK's generated Fortran destroy helper, which deallocates the
typed native object. Normal Fortran deallocation and component-finalization
rules then apply; if the type declares an applicable `FINAL` procedure, Fortran
invokes it as part of that deallocation.

`del item` only releases that Python reference. Destruction waits until no
owning reference remains, including references retained by borrowed child
wrappers.

Borrowed child wrappers, borrowed module objects, and borrowed component views
do not destroy the storage they reference. They retain the owning wrapper or
module reference needed for Python lifetime, but explicit native deallocation
or reallocation can still invalidate borrowed storage. Plain and `Aliased`
derived module objects are both live native-owned objects. An `Aliased` object
may use a proved native address; a plain object uses module-specific bridge
operations and must not fabricate addressability.

### When Native Resources Need Custom Destruction

A user-defined Fortran `FINAL` procedure is optional. Define one when the type
owns a resource that normal Fortran deallocation does not release, such as an
owned pointer target or an external library handle. Allocatable components
already follow Fortran's automatic deallocation rules, and a finalizer must not
release a pointer target that the type only borrows. PRIK does not infer that
native resource ownership.

For example, this type uniquely owns its pointer target. The `final`
declaration is how the native source identifies the cleanup procedure:

```fortran
module owned_buffers
  implicit none

  type :: owned_buffer
    private
    real(8), pointer :: values(:) => null()
  contains
    final :: finalize_owned_buffer
  end type owned_buffer

contains

  subroutine finalize_owned_buffer(self)
    type(owned_buffer), intent(inout) :: self

    if (associated(self%values)) deallocate(self%values)
  end subroutine finalize_owned_buffer
end module owned_buffers
```

PRIK discovers `final :: finalize_owned_buffer` while reading the source and
records that native fact in the generated semantic contract:

```python
from prik.contracts import destroy

class owned_buffer:
    def __init__(self) -> None: ...

    @destroy
    def finalize_owned_buffer(self) -> None: ...
```

`@destroy` is a language-neutral native lifecycle role. It does not publish
`finalize_owned_buffer` as a Python method, and it does not tell Python to call
that procedure directly. For this Fortran type, deallocating the native object
causes Fortran to invoke the applicable `FINAL` procedure. A type with several
rank-specific final procedures receives one `@destroy` declaration for each
procedure.

When wrapping source, users write the native language's declaration and PRIK
emits this semantic role. In a manually maintained contract for a precompiled
native module, retain an `@destroy` declaration only when the native type really
has that teardown operation.

Native finalizers do not provide a recoverable Python status channel during
object destruction. Use ordinary wrapped procedures for recoverable cleanup
steps that need status reporting.

Destroy declarations describe the native type. They are not constructor
options, Python methods, or cleanup functions that Python calls directly.

## Unsupported Class Shapes

PRIK blocks derived-type forms whose Python ownership or dispatch policy is not
complete:

- arrays of derived types;
- mutable polymorphic arguments and polymorphic results;
- `class(*)` and instantiating an abstract base;
- allocatable or pointer polymorphic scalars; and
- direct binary-layout access for ordinary generated classes.

Refusing to instantiate an abstract base is deliberate; the abstract hierarchy
itself is supported. The base wraps as a Python class with no constructor, its
extensions are ordinary subclasses, and deferred bindings resolve through the
caller's concrete type. See [Abstract Types And Deferred
Bindings](../guide/wrapping-derived-types.md#abstract-types-and-deferred-bindings).

When a type is unsupported, the wrapper-build error should explain the blocking
form instead of generating a partial class.

## Evidence

Generated class behavior is covered by
[`test_derived_boundaries.py`](../../../tests/fortran/derived_types/end_to_end/test_derived_boundaries.py),
[`test_type_bound_methods.py`](../../../tests/fortran/derived_types/end_to_end/test_type_bound_methods.py),
[`test_default_constructors_and_finalizers.py`](../../../tests/fortran/derived_types/end_to_end/test_default_constructors_and_finalizers.py),
[`test_borrowed_components.py`](../../../tests/fortran/derived_types/end_to_end/test_borrowed_components.py),
[`test_inheritance_and_polymorphism.py`](../../../tests/fortran/derived_types/end_to_end/test_inheritance_and_polymorphism.py), and
[`test_abstract_hierarchy.py`](../../../tests/fortran/derived_types/end_to_end/test_abstract_hierarchy.py).
Source type-named generic constructors are covered by
[`test_generic_constructor.py`](../../../tests/fortran/derived_types/end_to_end/test_generic_constructor.py).
Exact class-method and constructor overloads, including explicit bound
construction, are covered by
[`test_edited_class_surfaces.py`](../../../tests/fortran/infrastructure/semantic_pyi/contracts/functions_and_classes/end_to_end/test_edited_class_surfaces.py).
