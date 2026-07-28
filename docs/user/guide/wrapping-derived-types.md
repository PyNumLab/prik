---
title: Wrapping Derived Types
description: How x2py wraps Fortran derived types as Python classes with methods, fields, constructors, and ownership rules
audience: users, advanced users
prerequisites: wrapping modules, data types
related: memory-management.md, generic-interfaces.md
status: maintained
publication: reviewed
---

# Wrapping Derived Types

A supported Fortran `type` becomes a **generated Python extension class**.
Constructors and ordinary function results create independent Fortran
instances that are released with their Python objects. A nested component
belongs to its parent, and a module object belongs to the Fortran module.
Python accesses fields through generated getters and setters. Methods call
wrapped Fortran procedures. Python never reads the native memory layout
directly.

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

## Inspect the Class

The class docstring gives a short index:

```python
print(points.point.__doc__)
```

```text
point

Opaque wrapper for native type point.

Constructor
-----------
point(*, x=0.0, y=0.0) -> point

Fields
------
x : float64
y : float64
```

The constructor has its own detailed docstring:

```python
print(points.point.__init__.__doc__)
```

---

## Key Concepts

- **Lifetime**: A constructed or returned object is released when its Python
  object is no longer used. A nested component stays tied to its parent.
- **Mutation**: `intent(out)` and `intent(inout)` modify a caller-provided
  instance and do not return it again.
- **Missing intent**: A dummy without `intent` follows the same conservative
  in-place rule as `intent(inout)`.
- **Fields**: Public scalar numeric/logical/complex fields become Python attributes.
- **Nested types**: Appear as generated objects tied to their parent.
- **Results**: Derived-type function results create new independent objects.
- **Default constructor**: Automatically generated from public, writable
  primitive scalar fields.
- **Constructor fields**: Passed by keyword (`logical`, `integer`, `real`, and
  `complex`).

---

## Custom Constructor

The default constructor assigns public fields directly. If the native module
already provides `initialize_point(item, x, y)`, an edited contract can use it
as the constructor.

In this mapping, `@bind` selects the native initializer,
`@native_call(...)` gives its argument order, `Pass()` inserts the new
`point`, and `Addr(Arg(i))` passes Python argument `i` by address:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, bind, native_call

class point:
    x: Float64
    y: Float64

    @bind("initialize_point")
    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def __init__(self, x: Float64, y: Float64) -> None: ...
```

Replace the generated field-keyword `__init__` declaration with this one.
The edit changes construction only; it does not create
`initialize_point` in the native module.

After rebuilding, `points.point.__init__.__doc__` starts with
`point(x, y) -> point` and lists both parameters.

For the complete replacement rules, see
[Replace the Constructor](../reference/pyi-contracts/functions-and-classes.md#replace-the-constructor).

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

### Expose a Module Procedure as a Method

The `move(item, dx, dy)` procedure from this page's example can remain a
module-level function and also become `point.move(dx, dy)`.

`Pass()` supplies `self` to the native call. `Arg(i)` refers to a visible
Python argument. Add the method to the existing `point` class while keeping
the module declaration:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, native_call

class point:
    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def move(self, dx: Float64, dy: Float64) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move(item: point, dx: Float64, dy: Float64) -> None: ...
```

Both declarations call the existing native `move` procedure:

```python
points.move(item, np.float64(2.0), np.float64(3.0))
item.move(np.float64(2.0), np.float64(3.0))
```

To expose only the method, import `private` and add `@private` to the
module-level declaration.

The class docstring now lists `move(dx, dy) -> None` under `Methods`.
`points.point.move.__doc__` contains its complete parameter and return details.

For the complete mapping rules, see
[Expose a Module Procedure as a Method](../reference/pyi-contracts/functions-and-classes.md#expose-a-module-procedure-as-a-method).

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

The magic method docstring shows the accepted operator signatures:

```python
print(points.point.__add__.__doc__)
```

The relevant part is:

```text
__add__(*args, **kwargs)

Supported Signatures
--------------------
__add__(right: point) -> point
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

For the overload rules shared by type-bound generics and operators, see
[Edit an Overload Set](../reference/pyi-contracts/functions-and-classes.md#edit-an-overload-set).

---

## Next

- Continue with [Allocatables](allocatables.md).
- Read [Memory Management](memory-management.md) for the lifetime of native
  storage and NumPy views.
