# Wrap BSPLINE-FORTRAN with PRIK

Build the bundled
[BSPLINE-FORTRAN](https://github.com/jacobwilliams/bspline-fortran) source with
PRIK and validate its complete interpolation surface: 15 public procedural
routines, eight order constants, and seven public classes.

This is the example that exercises PRIK's modern-Fortran derived-type surface.
Unlike BLAS, FFTPACK, and MINPACK, it is a Fortran 2008 library. PRIK wraps the
vendored source **unmodified**:

- an **abstract** derived type (`bspline_class`) with two **deferred** bindings;
- six concrete extensions that inherit from it;
- **generic constructors** declared as `interface bspline_1d`;
- **private components and private bindings** kept off the Python surface;
- generic procedure interfaces (`db1ink`, `db1val`) with several specifics.

Analytic functions and `scipy.interpolate.make_interp_spline` provide
independent numerical oracles. The inventory has no unsupported or skipped
procedures.

## Requirements

Install GNU Fortran. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes gfortran
```

Install the pinned numerical tools:

```console
python3 -m pip install "numpy==2.5.1" "scipy==1.18.0" pytest
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

The build passes the three interpolation sources to PRIK in dependency order:
the kind definitions, procedural interface, and object-oriented interface.
Every source is compiled once and no alternative wrapper is created.

### Build the PRIK wrapper

<!-- prik-doc-source: examples/bspline/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export BSPLINE_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$BSPLINE_BUILD_ROOT/prik/generated"
cd "$BSPLINE_BUILD_ROOT/prik"

python3 -m prik \
  "$EXAMPLE_WORKSPACE/examples/bspline/native/bspline_kinds_module.F90" \
  "$EXAMPLE_WORKSPACE/examples/bspline/native/bspline_sub_module.f90" \
  "$EXAMPLE_WORKSPACE/examples/bspline/native/bspline_oo_module.f90" \
  --out prik_bspline \
  --out-dir "$BSPLINE_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

`-O0` keeps the example focused on correctness. The build writes its generated
contract beside the extension; it does not edit the upstream source.

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

## Run focused tests

After the quick-start build, run one interface family or routine:

```bash
python3 -m pytest -q examples/bspline/tests/test_object_oriented_api.py
python3 -m pytest -q examples/bspline/tests/test_procedural_api.py::test_db1ink
python3 -m pytest -q examples/bspline/tests -k db6
```

## What is validated

The suite builds every public procedural family from one to six dimensions,
then evaluates an affine function through every generated evaluator. It also
checks one-dimensional analytic values, derivatives, definite integrals, and
callback-driven integration, plus a SciPy interpolation comparison. The
object-oriented tests construct and evaluate every concrete spline class, and
check the abstract-base, inheritance, deferred-binding, and generic-constructor
contracts.

The routine-coverage test compares the reviewed inventory with the generated
exports and requires one named numerical test for every procedural routine.

## Scope

The upstream `bspline_defc_module` (least-squares fitting) and its
`bspline_blas_module` bridge are intentionally outside this interpolation
example. [`routine_inventory.py`](routine_inventory.py) records that boundary.

## Upstream

BSPLINE-FORTRAN is by Jacob Williams and is distributed under a BSD-3-Clause
licence, included at [`native/LICENSE`](native/LICENSE). The vendored sources
are version 7.4.0 (commit `047c7244`).
