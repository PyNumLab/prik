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

The concrete procedures are private because the source exports `convert`, not
`convert_integer` or `convert_real`. Each `@overload` links the candidate to
its concrete contract. Since those procedures are native-private,
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

## Extending an Overload Set

An edited contract can add an existing native procedure to a Python overload
set, even when it was not in the original Fortran interface.

Suppose the contract already declares `convert_logical`. Add a public overload
declaration that links to it:

```python
from x2py.contracts import Bool, Int32, overload

def convert_logical(value: Bool) -> Int32: ...

@overload("convert_logical")
def convert(value: Bool) -> Int32: ...
```

The decorator adds dispatch. It does not create a native implementation. The
target procedure must already exist in the contract and have a compatible call
shape.

Leave `convert_logical` public to expose both names. Mark it `@private` when it
should only be available through `convert`. This changes Python visibility,
not the native call. The overload still calls the public native specific
directly.

If that native specific is actually Fortran-private, the bridge cannot call it
directly. Keep `@bind("convert")` on the overload candidate. Source-based
generation adds this bind automatically.

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
- For current generic and operator support, refer to the [Language Feature Matrix](../language-support/feature-matrix.md).
