---
title: PRIK — Python Runtime Interop Kit
description: PRIK generates native Python bindings from Fortran projects, producing importable extensions and editable .pyi contracts for Pythonic APIs.
audience: users
prerequisites: none
related: user/getting-started/index.md, user/getting-started/installation.md, user/performance.md
status: maintained
publication: reviewed
---

# PRIK — Python Runtime Interop Kit

**Generate native Python bindings for Fortran, with editable `.pyi` contracts
and Pythonic APIs.**

PRIK generates native Python bindings from Fortran projects, producing
importable extensions and editable `.pyi` contracts for Pythonic APIs.

**Project status: Alpha (`0.1.x`).** Core Fortran wrapper workflows are
implemented and tested across supported compilers, but public APIs may still
change before `1.0`.

**PRIK starts with Fortran-to-Python.** Its semantic contract model is designed
to support more native languages over time.

---

## From Fortran to Python in one command

Install the package in a virtual environment:

```bash
python3 -m pip install prik
```

Create `scale.f90`:

<!-- prik-doc-source: tests/fortran/building_shared_library/end_to_end/fixtures/native/scale.f90 -->
```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

Build an importable extension:

```bash
python3 -m prik scale.f90
```

Call the generated Python API:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

No manual binding code is required. PRIK derives the native wrapper and a
readable Python signature from the Fortran source.

## Why PRIK

- **Natural Python APIs:** Fortran modules become namespaces and derived types
  become classes.
- **Editable contracts:** generated `.pyi` files let you rename, hide, flatten,
  or reorganize the public API.
- **Explicit native behavior:** NumPy dtypes, array layouts, ownership, and
  lifetimes are checked at the boundary.
- **Clear limits:** unsupported contracts fail before wrapper generation with
  actionable diagnostics.

## Proven on real Fortran libraries

The maintained examples wrap and numerically validate
[BLAS](user/examples/blas-wrapper.md),
[LAPACK](user/examples/lapack-wrapper.md),
[FFTPACK](user/examples/fftpack-wrapper.md), and
[MINPACK](user/examples/minpack-wrapper.md). The reproducible
[performance comparison](user/performance.md) measures PRIK and NumPy's f2py
against the same Fortran kernels.

**Ready to wrap your Fortran project?**

[Install PRIK →](user/getting-started/installation.md){ .prik-primary-cta }
[Read Getting Started →](user/getting-started/index.md){ .prik-primary-cta }
