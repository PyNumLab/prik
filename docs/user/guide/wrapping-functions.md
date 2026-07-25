---
title: Wrapping Functions
description: How x2py wraps Fortran `function` procedures — return values, output arguments, arrays, and contracts
audience: users
prerequisites: data types, first wrapped function
related: wrapping-subroutines.md, arrays.md, fortran-wrapper.md
status: maintained
publication: reviewed
---

# Wrapping Functions

A Fortran `function` becomes a Python callable. The function’s return value becomes the first item in Python, followed by any `intent(out)` or `intent(inout)` arguments (if present).

---

## Basic Scalar Function

Using the `scale.f90` example:

```bash
python3 -m x2py generate --pyi scale.f90
python3 -m x2py scale.f90 --out-dir build/scale
```

**Generated contract:**

```python
from x2py.contracts import Addr, Arg, Float64, external, native_call

@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

**Python call:**

```python
import sys
import numpy as np

sys.path.insert(0, "build/scale")
import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
assert result == 7.5
```

---

## Array Return Values

Functions can return arrays. These are returned as new NumPy arrays (Fortran-ordered by default).

**Example** (`function_results.f90`):

```fortran
module results
  implicit none
contains

  function squares(count) result(values)
    integer(4), intent(in) :: count
    real(8) :: values(count)
    integer(4) :: i

    values = [(real(i, 8)**2, i = 1, count)]
  end function squares

end module results
```

Build and import this example:

```bash
python3 -m x2py function_results.f90 --out-dir build/function-results
```

```python
import sys

import numpy as np

sys.path.insert(0, "build/function-results")
from function_results.results import squares

result = squares(np.int32(4))
np.testing.assert_array_equal(result, np.array([1.0, 4.0, 9.0, 16.0], dtype=np.float64))
```

---

## Functions with Output Arguments

When a function has `intent(out)` or `intent(inout)` arguments, Python returns a **tuple**:

> `(function_result, out_arg1, out_arg2, ...)`

**Example:**

```fortran
function sum_with_count(values, count) result(total)
  real(8), intent(in) :: values(:)
  integer(4), intent(out) :: count
  real(8) :: total
  total = sum(values)
  count = size(values)
end function
```

**Python call:**

```python
total, count = api.sum_with_count(data_array)
```

---

## Important Rules

- Always pass **exact NumPy dtypes** (`np.float64`, `np.int32`, etc.).
- Array results are returned as new NumPy arrays (copies).
- `intent(out)` and `intent(inout)` values are handled by the generated contract.
