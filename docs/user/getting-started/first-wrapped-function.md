---
title: First Wrapped Function
description: Build and call your first Fortran function as a Python extension
audience: users
prerequisites: installation, verification
related: first-wrapped-module.md, ../guide/wrapping-functions.md
status: maintained
publication: reviewed
---

# First Wrapped Function

This example shows how to build a simple scalar Fortran function and call it from Python using the exact NumPy dtypes required by its contract.

---

## Source Code

Create `scale.f90`:

```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

---

## Inspect the Generated Contract

Preview the Python interface before building:

```bash
python3 -m prik generate --pyi scale.f90
```

The generated semantic `.pyi` contains:

```python
from prik.contracts import Addr, Arg, Float64, native_call, standalone

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

`Float64` means the function requires `numpy.float64` scalar arguments and
returns the same scalar type. `@standalone` identifies a procedure outside a
Fortran module. `@native_call(...)` maps the two Python arguments to the native
call and passes each scalar by address.

This file is both the wrapper contract and an editable description of the
Python interface. You can leave it unchanged for this example; later pages
show useful edits in context.

---

## Build the Extension

From the directory containing `scale.f90`, run:

```bash
python3 -m prik scale.f90 --out-dir build/first-function
```

This creates an importable `scale` extension module in the `build/first-function` directory.

---

## Inspect the Generated Docstring

prik creates NumPy-style docstrings from the same contract. Import the built
extension and inspect the function:

```python
import sys

sys.path.insert(0, "build/first-function")
import scale

print(scale.scale.__doc__)
```

```text
scale(value, factor) -> float64

Parameters
----------
value : float64
factor : float64

Returns
-------
result : float64
```

`help(scale.scale)` shows the same signature, parameter types, result, and
documented exceptions. Generated modules, classes, methods, and properties
also provide docstrings.

---

## Call the Function

```python
import numpy as np

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)          # 7.5
assert result == 7.5
```

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

If the build fails, rerun it with `--verbose`.

---

## Next

- Continue with [Your First Wrapped Module](first-wrapped-module.md).
- For more function behavior, see [Wrapping Functions](../guide/wrapping-functions.md).
