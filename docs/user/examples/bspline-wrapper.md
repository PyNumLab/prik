---
title: Build and Validate BSPLINE-FORTRAN with PRIK
audience: users, advanced users
prerequisites: derived types, arrays
related: minpack-wrapper.md, ../guide/wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Build and Validate BSPLINE-FORTRAN with PRIK

This example wraps [BSPLINE-FORTRAN](https://github.com/jacobwilliams/bspline-fortran)
and validates both of its public interfaces from Python.

It is the modern-Fortran example. The BLAS, LAPACK, FFTPACK, and MINPACK
projects are FORTRAN 77; this library is Fortran 2008, and PRIK wraps it
**unmodified**:

- an **abstract** derived type, `bspline_class`, with two **deferred** bindings;
- six concrete extensions that inherit from it;
- **generic constructors** declared as `interface bspline_1d`;
- **private components and bindings** kept off the Python surface;
- generic procedure interfaces with several specifics each.

## Build and test

```bash
source examples/bspline/build_all.sh
python3 -m pytest -q examples/bspline/tests -m real_library
```

The build passes the three interpolation sources to PRIK in dependency order.
No `.pyi` contract is written and no source is edited.

## The generated API

```python
import numpy as np
import prik_bspline.bspline_oo_module as bspline

x = np.linspace(0.0, 2.0 * np.pi, 25)
spline = bspline.bspline_1d(x, np.sin(x), np.int32(4))

value, iflag = spline.evaluate(np.float64(1.234), np.int32(0))
area, iflag = spline.integral(np.float64(0.0), np.float64(np.pi))
```

`bspline_1d(x, fcn, kx)` is the Fortran `interface bspline_1d` constructor;
`bspline_1d()` is its empty overload. The abstract base is exported but cannot
be constructed:

```python
bspline.bspline_class()
# TypeError: bspline_class is an abstract native type and cannot be
#            instantiated; create one of its concrete extensions instead

issubclass(bspline.bspline_1d, bspline.bspline_class)   # True
```

## What is validated

| Test file | Covers |
| --- | --- |
| `test_object_oriented_api.py` | Abstract base, inheritance, deferred bindings, generic constructors, 1D and 2D interpolation, derivatives, definite integrals |
| `test_procedural_api.py` | Public procedures, order constants, generic interfaces, exactness on a cubic, derivatives, integrals, SciPy comparison |

Numerical checks use analytic values and `scipy.interpolate.make_interp_spline`
as independent oracles rather than trusting the wrapper as its own reference.

## Scope and licence

The upstream least-squares module and its BLAS bridge are outside this example;
the interpolation surface does not need them.
[`routine_inventory.py`](../../../examples/bspline/routine_inventory.py) records
the reviewed surface and that exclusion.

BSPLINE-FORTRAN is by Jacob Williams under a BSD-3-Clause licence, included with
the vendored sources at version 7.4.0.
