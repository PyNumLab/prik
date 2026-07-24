---
title: x2py
description: Turn Fortran into importable Python extensions with zero boilerplate
audience: users
prerequisites: none
related: user/getting-started/index.md, user/getting-started/installation.md
status: maintained
publication: reviewed
---

# x2py

**x2py turns supported Fortran source into fast, importable Python extensions.**

It also generates a language-neutral semantic IR and editable `.pyi`
contracts, so unsupported boundaries are reported before wrapper compilation.

---

## Try it in 30 seconds {#try-x2py}

Create a file `scale.f90`:

<!-- x2py-doc-source: tests/data/fortran/wrapper/scale.f90 -->
```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

Build the Python extension:

```bash
python3 -m x2py scale.f90
```

Use it from Python:

```python
import numpy as np
import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)        # 7.5
```

Inspect the generated contract:

```python
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

Raises
------
TypeError
    If an argument has an incompatible Python type or dtype.
```

---

## How it works

1. You write standard Fortran
2. `x2py` parses the interface and generates a compact native wrapper
3. It produces a Python extension module and editable semantic `.pyi` contracts
4. You get full NumPy scalar dtype safety and clear error messages

No manual `f2py` signatures. No low-level boilerplate.

## Next steps

[Getting Started](user/getting-started/index.md){ .md-button .md-button--primary }

This guide walks you through installation, compiler setup, and a deeper look at the generated artifacts.

---

## Features

- Automatic generation of Python extensions from Fortran
- Language-neutral semantic IR
- Editable `.pyi` type stubs
- Strict NumPy dtype checking at call time
- Clean, readable `__doc__` strings
- Build artifacts isolated in `__x2py__/`

---

**Ready to wrap your Fortran code?**
Start with the [Getting Started](user/getting-started/index.md) guide.
