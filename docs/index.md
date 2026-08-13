---
title: PRIK — Python Runtime Interop Kit
description: PRIK generates native Python bindings from Fortran projects, producing importable extensions and editable .pyi contracts for Pythonic APIs.
audience: users
prerequisites: none
related: user/getting-started/index.md, user/getting-started/installation.md, user/performance.md, developer/architecture.md
status: maintained
publication: reviewed
---

# PRIK — Python Runtime Interop Kit

**Generate native Python bindings for Fortran, with editable `.pyi` contracts
and Pythonic APIs.**

PRIK generates native Python bindings from Fortran projects, producing
importable extensions and editable `.pyi` contracts for Pythonic APIs.

**Project status: Alpha.** Core Fortran wrapper workflows are
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

## Measured against NumPy's f2py

The published benchmark compares both tools on the same Fortran sources and
the same machine. The charts show the current published snapshot. Results are
specific to its machine and toolchain, which are documented with the full results.

**Runtime-call performance** — values above `1.0×` favor PRIK.

[![Relative runtime performance of PRIK and f2py across call, vector, and matrix workloads. Values above 1.0 mean PRIK is faster.](user/assets/performance-comparison.svg)](user/performance.md)
{ .prik-performance-chart }

The chart shows `f2py time ÷ PRIK time`: values above `1.0×` favor PRIK and
values below `1.0×` favor f2py.

**Clean end-to-end build time** — lower times are better.

[![Clean end-to-end build time for PRIK and f2py under development and optimized compiler profiles. Lower times are better.](user/assets/build-time-comparison.svg)](user/performance.md#clean-build-time)
{ .prik-performance-chart }

[See the benchmark machine, full results, and methodology →](user/performance.md)

**Ready to wrap your Fortran project?**

[Install PRIK →](user/getting-started/installation.md){ .prik-primary-cta }
[Read Getting Started →](user/getting-started/index.md){ .prik-primary-cta }

**Working on PRIK itself?**

[Read Developer Documentation →](developer/index.md){ .prik-primary-cta }
