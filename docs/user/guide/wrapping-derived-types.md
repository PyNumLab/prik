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
Constructor calls and ordinary function results own an opaque native instance.
Nested components and module-owned objects use borrowed or native-owned
instances of the same generated class. Field access and method calls go through
generated native operations; Python never depends on the native memory layout.

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
assert item.x == np.float64(4.0)
assert item.y == np.float64(6.0)

# Function returning derived type
made = points.make_point(np.float64(8.0), np.float64(9.0))

# Nested component
container = points.holder()
p.set_origin(container, made)
container.origin.x = np.float64(12.0)
assert container.origin.x == np.float64(12.0)
```

---

## Key Concepts

- **Ownership**: Wrapper-owned objects are finalized when the Python object is garbage-collected.
- **Mutation**: `intent(inout)` modifies the same native instance.
- **Fields**: Public scalar numeric/logical/complex fields become Python attributes.
- **Nested types**: Appear as borrowed child wrappers (they don’t own the memory).
- **Constructors**: Generated for public scalar fields (keyword-only).

---

## Scalar Actuals And Native Dummies

The generated class can represent several native origins. Compatibility depends
on both the object passed from Python and the native dummy declaration:

| Python object origin | Ordinary or `target` dummy | `allocatable` dummy | `pointer` dummy | `value` dummy |
| --- | --- | --- | --- | --- |
| Wrapper-owned ordinary object | Direct object reference | Incompatible | Input-only pointer adapter | Typed value copy |
| Native module object | Scoped live reference | Incompatible | Scoped input-only pointer adapter | Scoped typed value |
| Wrapper-owned allocatable holder | Current payload | Persistent holder | Payload input-only adapter | Payload value copy |
| Module allocatable | Scoped payload | Allocation transaction | Scoped payload input-only adapter | Scoped payload copy |
| Wrapper-owned pointer holder | Current target | Incompatible | Persistent pointer holder | Target value copy |
| Module pointer | Module target | Incompatible | Association transaction | Target value copy |

An unallocated allocatable or unassociated pointer cannot supply a payload to an
ordinary, `target`, or `value` dummy. Descriptor dummies accept empty state so
native code can establish it. A nonpointer actual can satisfy a pointer dummy
only when that dummy is known to be `intent(in)`.

Module allocation and association transactions are restored before the wrapped
call returns. Pointer holders own their association variable, not an unknown
target.

---

## Next

- Learn about [Memory Management](memory-management.md) before keeping borrowed objects or views.
- See [Allocatables](allocatables.md) and [Pointers](pointers.md) for advanced storage

---
