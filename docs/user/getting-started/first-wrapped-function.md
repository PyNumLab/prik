---
title: First Wrapped Function
description: Build and call your first Fortran function as a Python extension
audience: users
prerequisites: installation, verification
related: first-wrapped-module.md, ../guide/wrapping-functions.md, ../reference/semantic-pyi-format.md
status: maintained
publication: reviewed
---

# First Wrapped Function

This example shows how to build a simple scalar Fortran function and call it from Python using the exact NumPy dtypes required by its contract.

---

## Source Code

Use the same `scale.f90` from the homepage:

```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

---

## Build the Extension

From the directory containing `scale.f90`, run:

```bash
python3 -m x2py scale.f90 --out-dir build/first-function
```

This creates an importable `scale` extension module in the `build/first-function` directory.

---

## Import and Call

```python
import sys
import numpy as np

sys.path.insert(0, "build/first-function")
import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)          # 7.5

# The generated Float64 result becomes a Python float.
assert isinstance(result, float)
```

---

## Inspect the Generated Contract

You can preview the semantic interface without building:

```bash
python3 -m x2py generate --pyi scale.f90
```

The generated contract has this shape:

```python
from x2py.contracts import Addr, Arg, Float64, external, native_call

@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

This contract is the source of truth for the generated wrapper.

---

## Common Pitfall: Wrong Scalar Type

You **must** pass the exact NumPy scalar types:

```python
# This will raise TypeError
scale.scale(3.0, 2.5)

# Correct way
scale.scale(np.float64(3.0), np.float64(2.5))
```

Always convert at the call site for scalar arguments.

---

## Next

- Learn how to wrap [Fortran modules](first-wrapped-module.md)
- Read more about [wrapping functions](../guide/wrapping-functions.md)
- Understand the [semantic .pyi format](../reference/semantic-pyi-format.md)

---

**Troubleshooting**
If the build fails, rerun with `--verbose`.
If the call fails, compare your arguments with the generated contract.
