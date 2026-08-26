---
title: Wrapping Derived Types
description: How PRIK wraps Fortran derived types as Python classes with methods, fields, constructors, and ownership rules
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

The source, generated contract, and Python call describe the same generated
class surface. The result stays visible below the three views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Derived types example">
<button class="prik-example-tab" id="derived-types-source-tab" type="button" role="tab" aria-controls="derived-types-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="derived-types-contract-tab" type="button" role="tab" aria-controls="derived-types-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="derived-types-python-tab" type="button" role="tab" aria-controls="derived-types-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="derived-types-source" role="tabpanel" aria-labelledby="derived-types-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `points.f90`:

```fortran
module points
  implicit none

  type :: point
    real(8) :: x = 0.0d0
    real(8) :: y = 0.0d0
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
python3 -m prik points.f90 --out geometry --out-dir build/geometry
```

</div>

<div class="prik-example-panel" id="derived-types-contract" role="tabpanel" aria-labelledby="derived-types-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `points.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, native_call

class point:
    def __init__(
        self,
        *,
        x: Float64 = 0.0,
        y: Float64 = 0.0
    ) -> None: ...

    x: Float64 = 0.0
    y: Float64 = 0.0

class holder:
    def __init__(self) -> None: ...

    origin: point

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move(
    item: point,
    dx: Float64,
    dy: Float64
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_point(
    x: Float64,
    y: Float64
) -> point: ...

def set_origin(
    container: holder,
    item: point
) -> None: ...
```

Generate it:

```bash
python3 -m prik generate --pyi points.f90
```

</div>

<div class="prik-example-panel" id="derived-types-python" role="tabpanel" aria-labelledby="derived-types-python-tab" tabindex="0" markdown="1">

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

</div>
</div>

Result:

```text
4.0 6.0
12.0
```

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

## Native Representation

All wrapped Fortran derived types use opaque native-instance storage, including
`bind(C)` and `sequence` types. Fields are read and written through generated
Fortran operations. The generated C binding does not mirror a struct, calculate
component offsets, or assume padding and alignment. Supported value-shaped
objects cross calls through Fortran's typed value semantics.

---

## Which Constructor You Get

The Fortran source decides which constructor the generated class publishes:

| Source | Generated Python constructor |
| --- | --- |
| No user constructor | Keyword-field `__init__` over the public components |
| `interface <typename>` present | Overloaded `__init__` from its specific functions |
| Edited `.pyi` | Exactly what the contract declares |

An interface named for a derived type is that type's constructor, so its
specifics become the accepted signatures:

```fortran
type, public :: box
  integer(4) :: count = 0
  real(8) :: value = 0.0d0
end type box

interface box
  module procedure box_empty, box_from_count, box_from_value
end interface box
```

```python
box()                      # box_empty
box(np.int32(7))           # box_from_count
box(np.float64(2.5))       # box_from_value
box("unsupported")         # TypeError: no matching overload for __init__
```

Each specific may be `private` in its module — the type name is public and
resolves to the same procedure, so the generated wrapper calls through it.

When a constructor interface exists it replaces the keyword-field form, and the
generated contract states only the signatures the class actually accepts.

---

## Custom Constructor

The default constructor assigns public fields directly. If the native module
already provides `initialize_point(item, x, y)`, an edited contract can use it
as the constructor.

In this mapping, `@bind` selects the native initializer,
`@native_call(...)` gives its argument order, `Pass()` inserts the new
`point`, and `Addr(Arg(i))` passes Python argument `i` by address:

```python
from prik.contracts import Addr, Arg, Float64, Pass, bind, native_call

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
from prik.contracts import Addr, Arg, Float64, Pass, native_call

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

## What The Source Already Hides

PRIK reads the accessibility a type declares and does not publish what the type
keeps to itself, so a contract is not needed to hide internals:

```fortran
module solver
  implicit none
  private                      ! module default

  type,public :: state         ! exported despite the module default
    private                    ! components default to private
    real(8) :: work(8) = 0.0d0 ! internal, not a Python attribute
    integer(4),public :: steps = 0
  contains
    private                    ! bindings default to private
    procedure :: advance_once  ! internal, not a Python method
    procedure,public :: run => advance_once
  end type state
end module solver
```

The generated `state` class exposes `steps` and `run` only. Each rule is the
Fortran one:

| Declaration | Effect on the Python class |
| --- | --- |
| `type, public ::` | Exported, even when the module defaults to `private` |
| `type, private ::` | Not exported, even when the module defaults to `public` |
| `private` before `contains` | Components default to hidden |
| `private` after `contains` | Type-bound procedures default to hidden |
| `integer, public ::` on a component | Published regardless of the type default |
| `procedure, public ::` on a binding | Published regardless of the type default |

The class docstring now lists `move(dx, dy) -> None` under `Methods`.
`points.point.move.__doc__` contains its complete parameter and return details.

For the complete mapping rules, see
[Expose a Module Procedure as a Method](../reference/pyi-contracts/functions-and-classes.md#expose-a-module-procedure-as-a-method).

---

## Inheritance And Polymorphic Input Dispatch

Fortran extension types generate a matching Python inheritance hierarchy.
Inherited fields and methods remain available on the derived class, and an
overridden type-bound method uses the derived implementation.

```fortran
type :: base_shape
  real(8) :: size
contains
  procedure :: area => base_area
  procedure :: set_size => base_set_size
end type base_shape

type, extends(base_shape) :: circle
  real(8) :: radius
contains
  procedure :: area => circle_area
end type circle

contains

real(8) function base_area(self) result(value)
  class(base_shape), intent(in) :: self
  value = self%size
end function base_area

subroutine base_set_size(self, value)
  class(base_shape), intent(inout) :: self
  real(8), intent(in) :: value
  self%size = value
end subroutine base_set_size

real(8) function circle_area(self) result(value)
  class(circle), intent(in) :: self
  value = acos(-1.0_8) * self%radius * self%radius
end function circle_area
```

For a wrapped module imported as `shapes`, the generated classes preserve that
relationship:

```python
shape = shapes.circle()
assert isinstance(shape, shapes.base_shape)

shape.set_size(np.float64(5.0))
shape.radius = np.float64(2.0)
print(shape.size)    # inherited field: 5.0
print(shape.area())  # overridden method: about 12.5664
```

A required scalar `class(base), intent(in)` argument accepts wrapped instances
from the known base and descendant classes:

```fortran
real(8) function describe_shape(item) result(value)
  class(base_shape), intent(in) :: item
  value = item%area()
end function describe_shape
```

```python
print(shapes.describe_shape(shape))  # about 12.5664
```

This polymorphic boundary is intentionally limited to required scalar inputs.
Polymorphic outputs, mutable arguments, arrays, allocatable or pointer scalars,
and unlimited polymorphism (`class(*)`) are not supported.

---

## Abstract Types And Deferred Bindings

A `type, abstract ::` declaration has no instances, so its Python class has no
constructor. Its extensions are ordinary Python subclasses, and a deferred
binding resolves through the object you actually hold.

```fortran
type, public, abstract :: shape_base
  private
  integer(4) :: sides = 0
contains
  private
  procedure(area_interface), deferred, public :: area
  procedure, public, non_overridable :: side_count => shape_side_count
end type shape_base

type, extends(shape_base), public :: circle
  real(8) :: radius = 1.0d0
contains
  procedure, public :: area => circle_area
end type circle
```

```python
import numpy as np
import shapes.abstract_hierarchy as shapes

shapes.shape_base()
# TypeError: shape_base is an abstract native type and cannot be instantiated;
#            create one of its concrete extensions instead

circle = shapes.circle(radius=np.float64(2.0))
print(circle.area())                       # 12.566370614
print(circle.side_count())                 # 0, from the abstract base
print(isinstance(circle, shapes.shape_base))  # True
```

The rules follow the Fortran declaration:

| Fortran | Python |
| --- | --- |
| `type, abstract ::` | Class with no constructor; instantiating it raises `TypeError` |
| `type, extends(base) ::` | Subclass of the base's generated class |
| `procedure(iface), deferred ::` | Declared on the base, resolved by the object's own type |
| `procedure, non_overridable ::` | Ordinary inherited method |
| Component of an abstract type | Reached through the extension that inherits it |

A deferred binding needs no Python-side dispatch: the generated adapter converts
the object's address to its own concrete type and lets Fortran resolve the
override. The same applies when a procedure takes `class(base)` — the boundary
is still limited to required scalar inputs, as above.

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
from prik.contracts import Float64, Int32, bind, overload, private

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
from prik.contracts import overload, private

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
