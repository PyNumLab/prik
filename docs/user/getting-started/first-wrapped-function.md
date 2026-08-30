---
title: First Wrapped Function
description: Build and call the same scalar function from Fortran or C
audience: users
prerequisites: installation, verification
related: beginner-workflow.md, ../guide/wrapping-functions.md, ../guide/c/functions-and-scalars.md
status: maintained
publication: reviewed
---

# First Wrapped Function

Choose the [Fortran](#fortran-path) or [C](#c-path) path below. Both define the
same operation, build an extension named `scale`, and expose `scale.scale` to
Python. After building, continue with [Call the Function](#call-the-function).

---

## Fortran Path

Create `scale.f90`:

```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

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

Build the extension:

```bash
python3 -m prik scale.f90 \
  --out scale \
  --out-dir build/first-function
```

`@standalone` records that the procedure is outside a Fortran module, and
`@native_call(...)` records Fortran's by-address scalar arguments.

Continue with [Call the Function](#call-the-function), or read the C path to
compare the native source and generated contract.

## C Path

Create `scale.c`:

```c
double scale(double value, double factor) {
    return value * factor;
}
```

Preview the Python interface:

```bash
python3 -m prik generate --pyi --language c scale.c
```

The generated semantic `.pyi` contains:

```python
from prik.contracts import Float64

def scale(value: Float64, factor: Float64) -> Float64: ...
```

Build the extension:

```bash
python3 -m prik --language c scale.c \
  --compiler cc \
  --out scale \
  --out-dir build/first-function
```

## Call the Function

Whichever source path you chose, import and call the extension in the same way:

```python
import sys

import numpy as np

sys.path.insert(0, "build/first-function")
import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)          # 7.5
assert result == 7.5
```

---

## Common Pitfall: Wrong Scalar Type

`Float64` requires `numpy.float64` scalar arguments and returns a
`numpy.float64` result. Pass the exact NumPy scalar types:

```python
# This will raise TypeError
scale.scale(3.0, 2.5)

# Correct way
scale.scale(np.float64(3.0), np.float64(2.5))
```

Always convert at the call site for scalar arguments. If the build fails,
rerun the command for your selected path with `--verbose`.

The semantic `.pyi` is an editable description of the Python interface. The
[Common Beginner Workflow](beginner-workflow.md) shows how to save and edit it.

---

## Next

- Continue with the [Common Beginner Workflow](beginner-workflow.md).
- For Fortran procedures and modules, see [Wrapping
  Functions](../guide/wrapping-functions.md) and [Wrapping
  Modules](../guide/wrapping-modules.md).
- For C functions and pointer contracts, see the [C User
  Guide](../guide/c/index.md).
