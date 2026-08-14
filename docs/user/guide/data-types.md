---
title: Data Types
description: How prik maps Fortran types to Python, NumPy dtypes, and semantic contracts
audience: users
prerequisites: common beginner workflow
related: arrays.md, strings.md, wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Data Types

prik resolves Fortran types using the selected compiler, then generates an
explicit semantic contract (`.pyi`). Inspect that contract before calling the
wrapper because kind numbers are compiler-dependent.

---

## Example

The source, generated contract, and Python call describe the same API. The
observable values remain below the three views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Data types example">
<button class="prik-example-tab" id="data-types-source-tab" type="button" role="tab" aria-controls="data-types-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="data-types-contract-tab" type="button" role="tab" aria-controls="data-types-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="data-types-python-tab" type="button" role="tab" aria-controls="data-types-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="data-types-source" role="tabpanel" aria-labelledby="data-types-source-tab" tabindex="0" markdown="1">

### Fortran source

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

Build it:

```bash
python3 -m prik numeric_types.f90 --out-dir build/numeric-types
```

</div>

<div class="prik-example-panel" id="data-types-contract" role="tabpanel" aria-labelledby="data-types-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `numeric_types.pyi` is:

```python
from prik.contracts import Addr, Arg, Bool8, Complex128, Float64, Int32, native_call

@native_call([Addr(Arg(0))])
def add_one(
    value: Int32
) -> Int32: ...

@native_call([Addr(Arg(0))])
def double(
    value: Float64
) -> Float64: ...

@native_call([Addr(Arg(0))])
def conjugate_value(
    value: Complex128
) -> Complex128: ...

@native_call([Addr(Arg(0))])
def invert(
    flag: Bool8
) -> Bool8: ...
```

Generate it:

```bash
python3 -m prik generate --pyi numeric_types.f90
```

`Bool8` is the result of probing `logical(kind=1)` with the selected compiler.

</div>

<div class="prik-example-panel" id="data-types-python" role="tabpanel" aria-labelledby="data-types-python-tab" tabindex="0" markdown="1">

## Calling from Python

```python
import sys

import numpy as np

sys.path.insert(0, "build/numeric-types")
from numeric_types.numeric_types import add_one, conjugate_value, double, invert

print(add_one(np.int32(4)))                        # 5
print(double(np.float64(1.5)))                     # 3.0
print(conjugate_value(np.complex128(1.0 + 2.0j)))  # (1-2j)
print(invert(True))                                # False
```

</div>
</div>

Result:

```text
5
3.0
(1-2j)
False
```

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
| `logical`                     | `Bool8`-`Bool64` | `bool` or `np.bool_`              |
| `character`                   | `String` / `String[n]` | `str` or fixed `np.bytes_`     |
| Derived Type                  | Generated Class | Instance of that class             |

Boolean contract names describe native storage, not different Python dtypes:

| Semantic Contract | Native Logical Storage Represented | Scalar Input / Result | Array Input / Output Storage |
|-------------------|------------------------------------|-----------------------|------------------------------|
| `Bool`            | 8 bits; portable default, equivalent to `Bool8` | `bool` or `np.bool_` | NumPy array with `dtype=np.bool_` |
| `Bool8`           | 8 bits                             | `bool` or `np.bool_` | NumPy array with `dtype=np.bool_` |
| `Bool16`          | 16 bits                            | `bool` or `np.bool_` | NumPy array with `dtype=np.bool_` |
| `Bool32`          | 32 bits                            | `bool` or `np.bool_` | NumPy array with `dtype=np.bool_` |
| `Bool64`          | 64 bits                            | `bool` or `np.bool_` | NumPy array with `dtype=np.bool_` |

Generated contracts select a numbered name after probing the chosen compiler.
Callers never pass integer arrays for wider logical storage: the wrapper adapts
the one-byte NumPy Boolean representation at the native boundary.

---

## Runtime Default Constructors

Concrete primitive contracts can create their matching NumPy scalar with its
zero value:

```python
import prik.contracts as xc

count = xc.Int32()      # np.int32(0)
weight = xc.Float64()   # np.float64(0.0)
flag = xc.Bool()        # np.bool_(False)
```

This applies to Boolean, fixed-width numeric, and `SizeT` contracts. It does
not apply to target-resolved `Int`, `UInt`, or `CEnum`, or to `Byte`, `Char`,
`String`, and `Void`, because those names do not define one portable NumPy
scalar representation by themselves. A scalar being constructible does not
mean every wrapper backend supports that native type; the generated contract
and feature matrix remain authoritative.

Array annotations are not array factories: `Float64[:]()` is invalid. Create
ordinary arrays with NumPy. Allocatable and pointer descriptor handles have
their own default constructors, described in their later user-guide pages.

## Important Rules

- Always use **exact NumPy scalar dtypes** (`np.float64`, `np.int32`, etc.).
- Plain Python `float` / `int` will raise `TypeError` for scalar arguments.
- prik resolves kinds using the selected compiler (`gfortran` by default).
- Inspect the contract with `generate --pyi` whenever you change compiler flags or architecture.

---

## Values And Native Storage

A bare primitive type represents a Python-visible scalar:

```python
def double(value: Float64) -> Float64: ...
```

The wrapper handles the native call details. Python still passes and receives
`numpy.float64` values.

`T[()]` represents rank-zero NumPy storage: arguments accept a 0-D NumPy
array, and results return a 0-D NumPy array. Raw integer addresses are an
advanced boundary covered later in the guide. A `T[()]` result is a 0-D NumPy
array, while a bare `T` result is a NumPy scalar.

## Unsupported Widths And Forms

The semantic format can represent wider types such as `Float128` and
`Complex256`, but the current Fortran wrapper blocks real storage wider than 64
bits and complex storage wider than 128 total bits instead of narrowing it.

---

## Next

- Continue with [Arrays](arrays.md) for rank, shape, strides, and contiguity.
- Then read [Strings](strings.md) for immutable values and mutable character
  storage.
- [Wrapping Derived Types](wrapping-derived-types.md)
