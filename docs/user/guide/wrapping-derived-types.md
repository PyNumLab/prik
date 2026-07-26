---
title: Wrapping Derived Types
description: How x2py wraps Fortran derived types as Python classes with methods, fields, constructors, and ownership rules
audience: users, advanced users
prerequisites: wrapping modules, data types
related: memory-management.md, generic-interfaces.md, fortran-wrapper.md
status: maintained
publication: reviewed
---

# Wrapping Derived Types

A supported Fortran `type` becomes a **generated Python extension class**.
Constructors and ordinary function results create wrapper-owned Fortran
instances.
Nested components and module-owned objects use borrowed or native-owned
instances of the same generated class. Python accesses fields through generated
getters and setters. Methods call wrapped Fortran procedures. Python never reads
the native memory layout directly.

---

## Complete Example

Create `points.f90`:

```fortran
module points
  implicit none

  type :: point
    real(8) :: x = 0.0_8
    real(8) :: y = 0.0_8
  end type point

  type :: holder
    type(point) :: origin
  end type holder

contains

  subroutine move(item, dx, dy)
    type(point), intent(inout) :: item
    real(8), intent(in) :: dx, dy
    item%x = item%x + dx
    item%y = item%y + dy
  end subroutine move

  function make_point(x, y) result(item)
    real(8), intent(in) :: x, y
    type(point) :: item
    item%x = x
    item%y = y
  end function make_point

  subroutine set_origin(container, item)
    type(holder), intent(inout) :: container
    type(point), intent(in) :: item
    container%origin = item
  end subroutine set_origin

end module points
```

Build it:

```bash
python3 -m x2py points.f90 --out geometry --out-dir build/geometry
```

---

## Usage in Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/geometry")
import geometry.points as points

# Create new object
item = points.point(x=np.float64(1.0), y=np.float64(2.0))

# Call method (inout mutation)
points.move(item, np.float64(3.0), np.float64(4.0))
print(item.x, item.y)  # 4.0 6.0

# Function returning derived type
made = points.make_point(np.float64(8.0), np.float64(9.0))

# Nested component
container = points.holder()
points.set_origin(container, made)
container.origin.x = np.float64(12.0)
print(container.origin.x)  # 12.0
```

---

## Key Concepts

- **Ownership**: Wrapper-owned objects are finalized when the Python object is garbage-collected.
- **Mutation**: `intent(out)` and `intent(inout)` modify a caller-provided
  instance and do not return it again.
- **Missing intent**: A dummy without `intent` follows the same conservative
  in-place rule as `intent(inout)`.
- **Fields**: Public scalar numeric/logical/complex fields become Python attributes.
- **Nested types**: Appear as borrowed child wrappers (they don’t own the memory).
- **Results**: Derived-type function results create new wrapper-owned objects.
- **Default constructor**: Automatically generated from public, writable
  primitive scalar fields.
- **Default arguments**: Keyword-only (`logical`, `integer`, `real`, and
  `complex`).
- **Custom constructor**: Define `__init__` in the edited `.pyi` to call one
  native initializer.

---

## Custom Constructor

The default constructor assigns fields directly. An edited `.pyi` can replace
it with a native initializer:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, bind, native_call

class point:
    x: Float64
    y: Float64

    @bind("initialize_point")
    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])
    def __init__(self, x: Float64, y: Float64) -> None: ...
```

`__init__` and `initialize_point` have different names, so
`@bind("initialize_point")` selects the initializer. `Pass()` marks the new
`point` at zero-based native position 1. That dummy must accept `point`.
Exactly one `Pass()` is required. Other `point` arguments use `Arg(...)` like
ordinary constructor inputs.

The generated module-level function can remain public or be marked `@private`.
The custom declaration replaces only the default field constructor.

---

## Type-Bound Methods

A public type-bound procedure becomes a method on the generated class. The
passed object becomes `self` and is not repeated in the Python call.

```fortran
type :: counter
  integer(4) :: value = 0
contains
  procedure :: increment
end type counter

contains

subroutine increment(self, amount)
  class(counter), intent(inout) :: self
  integer(4), intent(in) :: amount
  self%value = self%value + amount
end subroutine increment
```

```python
item = counters.counter(value=np.int32(4))
item.increment(np.int32(3))
print(item.value)  # 7
```

The method mutates the existing `counter`; it does not replace the Python
object.

### Project A Module Procedure As A Method

An edited `.pyi` can expose one native procedure in both Python scopes:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, native_call

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move_point(self, dx: Float64) -> None: ...

@native_call([Arg(0), Addr(Arg(1))])
def move_point(item: point, dx: Float64) -> None: ...
```

Both calls reach native `move_point`:

```python
move_point(item, np.float64(2.0))
item.move_point(np.float64(2.0))
```

`Pass()` inserts `item` for the method call. Both declarations already match
native `move_point`, so no `@bind` is needed.

Mark the module declaration `@private` to expose only the method.

---

## Type-Bound Generics

A type-bound generic groups several concrete methods under one Python method.
For example, `add` can accept exact integer or real amounts:

```fortran
type :: counter
  integer(4) :: value = 0
contains
  procedure :: add_integer
  procedure :: add_real
  generic :: add => add_integer, add_real
end type counter
```

The generated contract uses the same explicit overload links as a module-level
generic:

```python
from x2py.contracts import Float64, Int32, bind, overload, private

class counter:
    @private
    def add_integer(self, amount: Int32) -> Int32: ...

    @private
    def add_real(self, amount: Float64) -> Float64: ...

    @bind("add")
    @overload("add_integer")
    def add(self, amount: Int32) -> Int32: ...

    @bind("add")
    @overload("add_real")
    def add(self, amount: Float64) -> Float64: ...
```

```python
print(item.add(np.int32(2)))       # exact Int32 candidate
print(item.add(np.float64(0.5)))   # exact Float64 candidate
```

The passed object participates in native dispatch but is already fixed by the
generated class. The remaining arguments must still match one candidate
exactly. Each `@overload` retains a concrete contract. `@bind("add")` routes
the native call through the public type-bound generic because its specifics
are private.

---

## Defined Operators

A defined operator with a wrapped derived-type operand becomes a Python magic
method. Its overload candidates are attached to the generated class.

```fortran
interface operator(+)
  module procedure add_points
end interface operator(+)

contains

function add_points(left, right) result(output)
  type(point), intent(in) :: left, right
  type(point) :: output
  output%x = left%x + right%x
  output%y = left%y + right%y
end function add_points
```

The generated contract exposes `operator(+)` as `__add__`:

```python
from x2py.contracts import overload, private

class point:
    @overload("add_points")
    def __add__(self, right: point) -> point: ...

@private
def add_points(left: point, right: point) -> point: ...
```

Python uses the normal operator:

```python
left = points.point(x=np.float64(1.0), y=np.float64(2.0))
right = points.point(x=np.float64(3.0), y=np.float64(4.0))
total = left + right
print(total.x, total.y)  # 4.0 6.0
```

| Fortran generic | Python method | Python syntax |
|-----------------|---------------|---------------|
| Binary `+`, `-`, `*`, `/`, `**` | Direct and reflected magic methods | `left + right` |
| Unary `+`, `-` | `__pos__`, `__neg__` | `+value`, `-value` |
| Relational operators | `__eq__`, `__lt__`, and related methods | `left == right` |
| `.and.`, `.or.`, `.not.` | `__and__`, `__or__`, `__invert__` | `left & right`, `~value` |
| Named operator `.name.` | `operator_name` or `r_operator_name` | Explicit method call |
| `assignment(=)` | `assign` | `target.assign(value)` |

Python `and`, `or`, and `not` cannot be overloaded, so logical operator
generics use `&`, `|`, and `~`. Python assignment only rebinds a name, so
defined assignment uses `.assign(...)`.

At least one operand must be a wrapped derived type. Other operands can be
supported primitive scalars, arrays, or generated classes. Their dispatch is
exact.

---

## Next

- Continue with [Allocatables](allocatables.md) and [Pointers](pointers.md) for
  advanced storage.
- Review [Memory Management](memory-management.md) before keeping borrowed
  objects or views.

---
