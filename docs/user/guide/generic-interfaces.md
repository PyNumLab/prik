---
title: Generic Interfaces
description: How x2py supports Fortran named generics, type-bound generics, operators, and defined assignment
audience: users, advanced users
prerequisites: wrapping functions, wrapping subroutines, data types
related: optional-arguments.md, wrapping-derived-types.md, error-handling.md
status: maintained
publication: reviewed
---

# Generic Interfaces

x2py turns Fortran named generic interfaces (and type-bound generics) into a single Python callable backed by an overload set. Dispatch is based on **exact** dtype, rank, and generated class — no implicit numeric coercion is performed.

---

## Complete Example

Create `generic.f90`:

```fortran
module conversions
  implicit none
  private
  public :: convert

  interface convert
    module procedure convert_integer
    module procedure convert_real
  end interface convert

contains

  integer(4) function convert_integer(value) result(output)
    integer(4), intent(in) :: value
    output = value + 10
  end function convert_integer

  real(8) function convert_real(value) result(output)
    real(8), intent(in) :: value
    output = value + 0.5_8
  end function convert_real

end module conversions
```

Build it:

```bash
python3 -m x2py generic.f90 --out-dir build/generic
```

---

## Usage in Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/generic")
from generic.conversions import convert

assert convert(np.int32(4)) == np.int32(14)
assert convert(np.float64(4.0)) == np.float64(4.5)
```

The correct specific procedure is chosen automatically based on the argument type.

---

## Key Rules

- Dispatch uses **exact** match on dtype, rank, and generated class.
- If no overload matches, a `TypeError` is raised.
- If two specifics collapse to the same Python signature, wrapper generation fails (ambiguity is rejected).
- Type-bound generics also work and dispatch after accounting for the passed object.

---

## Defined Operators and Assignment

- Supported operators (`+`, `-`, `*`, `==`, etc.) can be used with normal Python syntax when the native generic defines them.
- Defined assignment (`=`) is exposed as an explicit `.assign(...)` method because Python `=` only rebinds names.

---

## Limitations

- Generic constructors and initialization overloads are not yet supported.
- Polymorphic (`class(*)`) arguments and results are blocked.
- Arrays of derived types and complex polymorphic cases are not supported yet.

---

## Next

- Continue with [Wrapping Derived Types](wrapping-derived-types.md)
- See [Error Handling](error-handling.md) for dispatch errors
- For current generic and operator support, refer to the [Language Feature Matrix](../language-support/feature-matrix.md).
