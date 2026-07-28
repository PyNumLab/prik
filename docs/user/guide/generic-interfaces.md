---
title: Generic Interfaces (Overloading)
description: How x2py supports Fortran named generic interfaces and exact overload dispatch
audience: users, advanced users
prerequisites: wrapping functions, wrapping subroutines, data types
related: optional-arguments.md, wrapping-derived-types.md, error-handling.md
status: maintained
publication: reviewed
---

# Generic Interfaces (Overloading)

x2py turns a Fortran generic interface into one Python callable. The callable
dispatches to a concrete native procedure by exact dtype, rank, and generated
class. It does not apply implicit numeric coercion.

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
python3 -m x2py generate --pyi generic.f90
python3 -m x2py generic.f90 --out-dir build/generic
```

---

## Generated Contract

The semantic `.pyi` keeps the concrete procedures as private link targets.
Each public declaration adds one candidate to `convert`:

`@private` hides a concrete procedure from Python. `@overload` links a public
candidate to that procedure, and `@bind` selects the public native generic when
the concrete procedure is private in Fortran.

```python
from x2py.contracts import Float64, Int32, bind, overload, private

@private
def convert_integer(value: Int32) -> Int32: ...

@private
def convert_real(value: Float64) -> Float64: ...

@bind("convert")
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_real")
def convert(value: Float64) -> Float64: ...
```

The source exports `convert`, not `convert_integer` or `convert_real`. Since
those concrete procedures are native-private,
[`@bind("convert")`](wrapping-functions.md#python-and-native-names) routes both
candidates through the public generic.

---

## Usage in Python

```python
import sys

import numpy as np

sys.path.insert(0, "build/generic")
from generic.conversions import convert

print(convert(np.int32(4)))      # 14
print(convert(np.float64(4.0)))  # 4.5
```

The argument type selects the concrete procedure. `np.int32` calls
`convert_integer`; `np.float64` calls `convert_real`.

---

## Inspect the Overloads

The module docstring lists one public callable:

```python
import generic.conversions as conversions

print(conversions.__doc__)  # includes convert(*args, **kwargs)
```

The callable docstring lists every accepted signature:

```python
print(conversions.convert.__doc__)
```

The relevant part is:

```text
convert(*args, **kwargs)

Supported Signatures
--------------------
convert(value: int32) -> int32
convert(value: float64) -> float64
```

Private procedures such as `convert_integer` do not appear.

---

## Extend an Overload Set

An edited contract can add another existing native procedure to the same
Python callable. Suppose the native module and contract also contain a public
`convert_logical`:

```python
from x2py.contracts import Bool, Int32, overload, private

@private
def convert_logical(value: Bool) -> Int32: ...

@overload("convert_logical")
def convert(value: Bool) -> Int32: ...
```

The new declaration makes `convert(np.bool_(...))` select
`convert_logical`. It does not create the native procedure; that procedure
must already exist and match the declaration. `@private` means users reach the
procedure only through `convert`.

If the concrete procedure is private in Fortran, keep
`@bind("convert")` on the overload so the native call goes through the public
generic.

---

## Key Rules

- Dispatch uses **exact** match on dtype, rank, and generated class.
- If no overload matches, a `TypeError` is raised.
- If two candidates have the same runtime signature, wrapper generation fails.
- Each `@overload` declaration links to exactly one concrete procedure.
- `@bind` changes the final native target, not the linked candidate contract.
- `@private` controls Python visibility only.

Type-bound generics, defined operators, and defined assignment become methods
on generated derived-type classes. They are introduced after ordinary methods
in Wrapping Derived Types.

---

## Limitations

- Source generic interfaces are not inferred as constructors automatically.
  Edited exact constructor overload sets are supported.
- Polymorphic (`class(*)`) arguments and results are blocked.
- Arrays of derived types and complex polymorphic cases are not supported yet.

---

## Next

- Continue with [Wrapping Derived Types](wrapping-derived-types.md) for
  type-bound generics and operators
- See [Error Handling](error-handling.md) for dispatch errors
