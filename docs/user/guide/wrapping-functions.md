---
title: Wrapping Functions
description: How x2py wraps Fortran `function` procedures — return values, output arguments, arrays, and contracts
audience: users
prerequisites: data types, first wrapped function
related: wrapping-subroutines.md, arrays.md
status: maintained
publication: reviewed
---

# Wrapping Functions

A Fortran `function` becomes a Python callable. Its direct result is the first
Python return value. Other outputs follow only when their contract marks them
as Python results.

---

## Basic Scalar Function

The `scale` function built in
[First Wrapped Function](../getting-started/first-wrapped-function.md) returns
its direct result as one NumPy scalar:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

---

## Python And Native Names

A contract declaration normally uses one name for both Python and the native
procedure. Use `@bind("native_name")` only when those names differ.

For example, rename the generated declaration to `multiply` and add
`@bind("scale")`. The Python name changes, while the native target remains
`scale`:

```python
from x2py.contracts import Addr, Arg, Float64, bind, external, native_call

@bind("scale")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def multiply(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

```python
result = scale.multiply(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

`@bind` changes the native target name. It does not change the argument
contract or adapt an incompatible native interface. Matching names need no
`@bind`.

Also update the import in the contract package's `__init__.pyi` when it
re-exports the old Python name. Build the edited package using the
[editable-contract workflow](../getting-started/beginner-workflow.md#4-optionally-edit-the-contract).

The same rule applies to functions, subroutines, and methods.

---

## Array Return Values

Functions can return arrays. An ordinary array result becomes a new NumPy
array in Fortran order, as described in
the [`automatic_vector` example](arrays.md#complete-example):

```python
import numpy as np

result = automatic_vector(np.int32(4))
print(result)  # [ 1.  4.  9. 16.]
```

---

## Functions with Output Arguments

When a function has projected scalar or native-created outputs, Python returns
a **tuple**:

> `(function_result, out_arg1, out_arg2, ...)`

Caller-provided ordinary arrays are mutated in place and are not added to this
tuple.

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
total, count = sum_with_count(data_array)
```

---

## Important Rules

- Always pass **exact NumPy dtypes** (`np.float64`, `np.int32`, etc.).
- Array results are returned as new NumPy arrays (copies).
- Projected scalar outputs follow the direct function result in the return
  tuple.
- Caller-provided arrays and derived objects mutate in place. They are not
  repeated in the return tuple.
- Without `intent`, an argument uses conservative `intent(inout)` behavior.
  Primitive scalar replacements follow the direct function result in the
  Python return tuple.

## Next

- [Wrapping Subroutines](wrapping-subroutines.md) for the complete argument
  projection rules.
