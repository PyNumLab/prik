# Wrap BSPLINE-FORTRAN with PRIK

Build [BSPLINE-FORTRAN](https://github.com/jacobwilliams/bspline-fortran) with
PRIK and validate both of its public interfaces from Python: the
object-oriented classes and the procedural routines.

This is the example that exercises PRIK's modern-Fortran surface. Unlike the
BLAS, LAPACK, FFTPACK, and MINPACK projects — which are FORTRAN 77 — this
library is written in Fortran 2008 and wraps **unmodified**:

- an **abstract** derived type (`bspline_class`) with two **deferred** bindings;
- six concrete extensions that inherit from it;
- **generic constructors** declared as `interface bspline_1d`;
- **private components and private bindings** kept off the Python surface;
- generic procedure interfaces (`db1ink`, `db1val`) with several specifics.

## Requirements

Install GNU Fortran. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes gfortran
```

Install the Python test tools. SciPy is optional; the comparison test skips
without it:

```console
python3 -m pip install numpy pytest scipy
```

Run the remaining commands from the repository root.

## Quick start

```bash
source examples/bspline/build_all.sh
python3 -m pytest -q examples/bspline/tests -m real_library
```

Use `source` so the build paths exported by `build_all.sh` stay available to
the test process.

## How the build works

`build_prik.sh` passes the three interpolation sources to PRIK in dependency
order and builds one extension:

```bash
python3 -m prik \
  examples/bspline/native/bspline_kinds_module.F90 \
  examples/bspline/native/bspline_sub_module.f90 \
  examples/bspline/native/bspline_oo_module.f90 \
  --out prik_bspline
```

No `.pyi` contract is written and no source is edited. The upstream files are
vendored byte-for-byte under `native/`.

## The Python API

```python
import numpy as np
import prik_bspline.bspline_oo_module as bspline

x = np.linspace(0.0, 2.0 * np.pi, 25)
spline = bspline.bspline_1d(x, np.sin(x), np.int32(4))   # generic constructor

value, iflag = spline.evaluate(np.float64(1.234), np.int32(0))
print(value)                                             # about 0.943811

area, iflag = spline.integral(np.float64(0.0), np.float64(np.pi))
print(area)                                              # about 2.0
```

The abstract base is present but cannot be constructed:

```python
bspline.bspline_class()
# TypeError: bspline_class is an abstract native type and cannot be
#            instantiated; create one of its concrete extensions instead

issubclass(bspline.bspline_1d, bspline.bspline_class)    # True
```

## What is validated

| Test file | Covers |
| --- | --- |
| `tests/test_object_oriented_api.py` | Abstract base, inheritance, deferred bindings, generic constructors, 1D/2D interpolation, derivatives, definite integrals |
| `tests/test_procedural_api.py` | Public procedures, order constants, generic interfaces, interpolation exactness on a cubic, derivatives, integrals, SciPy comparison |

Numerical checks use independent oracles — analytic values, and
`scipy.interpolate.make_interp_spline` — rather than trusting the wrapper as
its own reference.

## Scope

The upstream `bspline_defc_module` (least-squares fitting) and its
`bspline_blas_module` bridge are not part of this example; the interpolation
surface does not need them. `routine_inventory.py` records the reviewed
surface and this exclusion.

## Upstream

BSPLINE-FORTRAN is by Jacob Williams and is distributed under a BSD-3-Clause
licence, included at `native/LICENSE`. The vendored sources are version 7.4.0
(commit `047c7244`).
