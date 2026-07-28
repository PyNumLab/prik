---
title: .pyi Functions and Classes
audience: users, advanced users
prerequisites: editing .pyi contracts overview
related: index.md, exports-and-modules.md, calls-and-results.md, ../semantic-pyi-format.md, ../../guide/wrapping-derived-types.md, ../../guide/generic-interfaces.md
status: maintained
publication: reviewed
---

# Functions and Classes

Declarations may be moved into a more useful Python shape while still calling
the same native procedures.

## Expose a Module Procedure as a Method

Keep the module procedure declaration and add a method that calls it. `Pass()`
places `self` in the native argument list:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, native_call, private

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move(self, dx: Float64) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def move(item: point, dx: Float64) -> None: ...
```

Python exposes `item.move(dx)`. The private module declaration keeps the native
procedure information but is not callable from Python. Remove `@private` when
both `move(item, dx)` and `item.move(dx)` should be public.

The method name normally selects the native procedure. Add `@bind("move")` to
the method when its Python name differs from that procedure.

## Edit an Overload Set

Each `@overload(...)` declaration is one runtime candidate:

```python
from x2py.contracts import Addr, Arg, Float64, Int32, bind, native_call, overload, private

@private
@native_call([Addr(Arg(0))])
def scale_integer(value: Int32) -> Int32: ...

@private
@native_call([Addr(Arg(0))])
def scale_real(value: Float64) -> Float64: ...

@overload("scale_integer")
def scale(value: Int32) -> Int32: ...

@overload("scale_real")
def scale(value: Float64) -> Float64: ...
```

- Delete one overload declaration to remove only that accepted signature.
- Add a candidate only when its linked concrete procedure exists.
- Keep candidates distinguishable by supported runtime dtype and rank.
- `@private` changes Python visibility; it does not make a native-private
  procedure callable.

Without `@bind`, a candidate calls the concrete procedure named by
`@overload`. When the callable native target must instead be a public generic,
bind it explicitly:

```python
@bind("convert")
@overload("convert_integer")
def convert_number(value: Int32) -> Int32: ...
```

The overload string still links the concrete contract; `@bind("convert")`
selects the native call target.

## Replace the Constructor

Generated classes have either a field-keyword constructor or a no-argument
native constructor. Replace it with one concrete native initializer by editing
`__init__`:

```python
from x2py.contracts import Addr, Arg, Int32, Pass, bind, native_call

class state:
    @bind("init_state")
    @native_call([Pass(), Addr(Arg(0))])
    def __init__(self, size: Int32) -> None: ...
```

`Pass()` places the newly created `state` object in the native call. Its
position must match the initializer's native argument order, and the selected
native argument must accept `state`.

Remove the old generated `__init__` when replacing it. Deleting `__init__`
without adding another one makes public construction unavailable.

## Type-Bound and Magic Methods

Type-bound and magic methods follow the same rules:

- keep a concrete native procedure declaration;
- place `self` with `Pass()` when the native call needs it;
- use `@bind(...)` when the Python and native names differ; and
- use `@overload(...)` when one Python method accepts several native
  signatures.

See [Wrapping Derived Types](../../guide/wrapping-derived-types.md#type-bound-methods)
for ordinary methods and
[Defined Operators](../../guide/wrapping-derived-types.md#defined-operators)
for magic methods. Each public declaration must retain a concrete, callable
native target with an exact argument mapping.

## Next

Use [Calls and Results](calls-and-results.md) to change how native arguments
appear at the Python boundary.
