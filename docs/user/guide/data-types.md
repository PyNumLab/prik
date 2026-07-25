---
title: Data Types
description: How x2py maps Fortran types to Python, NumPy dtypes, and semantic contracts
audience: users
prerequisites: common beginner workflow
related: arrays.md, wrapping-derived-types.md, ../reference/semantic-pyi-format.md
status: maintained
publication: reviewed
---

# Data Types

x2py resolves Fortran types using the selected compiler, then generates an
explicit semantic contract (`.pyi`). Inspect that contract before calling the
wrapper because kind numbers are compiler-dependent.

---

## Example

Create `numeric_types.f90`:

```fortran
module numeric_types
  use iso_fortran_env, only: int32, real64
  implicit none
contains

  integer(int32) function add_one(value) result(output)
    integer(int32), intent(in) :: value
    output = value + 1
  end function add_one

  real(real64) function double(value) result(output)
    real(real64), intent(in) :: value
    output = 2.0_real64 * value
  end function double

  complex(real64) function conjugate_value(value) result(output)
    complex(real64), intent(in) :: value
    output = conjg(value)
  end function conjugate_value

  logical(kind=1) function invert(flag) result(output)
    logical(kind=1), intent(in) :: flag
    output = .not. flag
  end function invert

end module numeric_types
```

Generate the contract:

```bash
python3 -m x2py generate --pyi numeric_types.f90
```

Build it:

```bash
python3 -m x2py numeric_types.f90 --out-dir build/numeric-types
```

---

## Calling from Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/numeric-types")
import numeric_types

api = numeric_types.numeric_types

assert api.add_one(np.int32(4)) == np.int32(5)
assert api.double(np.float64(1.5)) == np.float64(3.0)
assert api.conjugate_value(np.complex128(1.0 + 2.0j)) == np.complex128(1.0 - 2.0j)
assert bool(api.invert(True)) is False
```

---

## Scalar Type Mapping

| Fortran Type                  | Semantic Type   | Preferred Python / NumPy Type      |
|-------------------------------|-----------------|------------------------------------|
| `integer(1)`                  | `Int8`          | `np.int8`                          |
| `integer(2)`                  | `Int16`         | `np.int16`                         |
| `integer(4)` / `int32`        | `Int32`         | `np.int32`                         |
| `integer(8)` / `int64`        | `Int64`         | `np.int64`                         |
| `real(4)`                     | `Float32`       | `np.float32`                       |
| `real(8)` / `real64`          | `Float64`       | `np.float64`                       |
| `complex(4)`                  | `Complex64`     | `np.complex64`                     |
| `complex(8)`                  | `Complex128`    | `np.complex128`                    |
| `logical`                     | `Bool`          | `bool` or `np.bool_`               |
| `character`                   | `String` / `String[n]` | `str` or fixed `np.bytes_`     |
| Derived Type                  | Generated Class | Instance of that class             |

---

## Important Rules

- Always use **exact NumPy scalar dtypes** (`np.float64`, `np.int32`, etc.).
- Plain Python `float` / `int` will raise `TypeError` for scalar arguments.
- x2py resolves kinds using the selected compiler (`gfortran` by default).
- Inspect the contract with `generate --pyi` whenever you change compiler flags or architecture.

---

## Values And Native Storage

A bare primitive type is a Python-visible value:

```python
def double(value: Float64) -> Float64: ...
```

If the native routine expects that scalar by reference, the generated
`@native_call` records the address handoff while the Python call stays simple:

```python
@native_call([Addr(Arg(0))])
def double(value: Float64) -> Float64: ...
```

Use `T[()]` when the Python boundary is rank-zero NumPy storage. Arguments
accept a 0-D NumPy array, and results return a 0-D NumPy array.
Use type-level `Addr(T)` only for an API whose caller supplies a raw integer
address. Arrays and strings already carry storage and do not need an address
override.

The semantic format can represent wider types such as `Float128` and
`Complex256`, but the current Fortran wrapper blocks real storage wider than 64
bits and complex storage wider than 128 total bits instead of narrowing it.

---

## Next

- **[Arrays](arrays.md)** - Rank, shape, strides, and contiguity rules
- [Wrapping Derived Types](wrapping-derived-types.md)
- [Semantic `.pyi` Format](../reference/semantic-pyi-format.md)
- Check the [Language Feature Matrix](../language-support/feature-matrix.md) for current type support status.
