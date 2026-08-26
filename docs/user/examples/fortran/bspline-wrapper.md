---
title: Build and Validate BSPLINE-FORTRAN with PRIK
audience: users, advanced users
prerequisites: derived types, arrays, packaging
related: fftpack-wrapper.md, ../../guide/wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Build and Validate BSPLINE-FORTRAN with PRIK

This example takes the checked-in
[BSPLINE-FORTRAN](https://github.com/jacobwilliams/bspline-fortran) source and
builds an importable Python extension with the complete interpolation surface:
15 public procedural routines, eight order constants, and seven public classes.

It evaluates B-splines from one to six dimensions. The tests compare results
with analytic functions and SciPy rather than treating the wrapper as its own
reference.

### What this example shows

- Wrap a modern multi-file Fortran library as one Python extension.
- Construct and call derived types over an abstract Fortran base.
- Check procedural and object-oriented interpolation with NumPy arrays.

You should already be comfortable with NumPy arrays, Python classes, and
building a local Fortran extension.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| BSPLINE-FORTRAN | [version 7.4.0, commit `047c7244`](https://github.com/jacobwilliams/bspline-fortran/tree/047c7244) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy | 1.18.0 |
| Fortran compiler | GNU Fortran 13 in CI; a compatible `gfortran` works locally |

The repository owns the checked-in source snapshot under
`examples/fortran/bspline/native/`, so the example does not download code during its
build.

## Tested platforms

The Real Libraries Portability workflow builds and runs the complete numerical
suite with Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

---

## 1. Prepare the repository and toolchain

Clone PRIK, create a virtual environment, and install the Python tools used by
the dedicated CI job:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[qa]" "numpy==2.5.1" "scipy==1.18.0"
```

Install GNU Fortran separately. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install --yes gfortran
gfortran --version
```

All remaining commands run from the repository root with the virtual
environment active. The complete runnable project lives under
[`examples/fortran/bspline/`](../../../../examples/fortran/bspline/).

---

## 2. Build the PRIK wrapper

BSPLINE-FORTRAN separates its kind definitions, procedural routines, and
object-oriented types into ordered source files. The build command passes those
three public sources in dependency order:

<!-- prik-doc-source: examples/fortran/bspline/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export BSPLINE_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$BSPLINE_BUILD_ROOT/prik/generated"
cd "$BSPLINE_BUILD_ROOT/prik"

python3 -m prik \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_kinds_module.F90" \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_sub_module.f90" \
  "$EXAMPLE_WORKSPACE/examples/fortran/bspline/native/bspline_oo_module.f90" \
  --out prik_bspline \
  --out-dir "$BSPLINE_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

The example uses `-O0` so the tests focus on correct results. PRIK compiles the
native source and generated bridge into one extension.

For normal use, source the convenience entrypoint:

```bash
source examples/fortran/bspline/build_all.sh
```

It builds the extension and exports its directory on `PYTHONPATH` for the
current shell.

---

## 3. Use the generated Python API

The object-oriented module exposes an abstract `bspline_class` and six concrete
dimension-specific subclasses. The `bspline_1d` generic constructor accepts an
empty form and a data-driven form:

```python
import numpy as np
import prik_bspline.bspline_oo_module as bspline

x = np.linspace(0.0, 2.0 * np.pi, 25)
spline = bspline.bspline_1d(x, np.sin(x), np.int32(4))

value, iflag = spline.evaluate(np.float64(1.234), np.int32(0))
area, iflag = spline.integral(np.float64(0.0), np.float64(np.pi))
```

The abstract base is exported but cannot be constructed. Its concrete
extensions inherit the base bindings and answer its deferred operations:

```python
bspline.bspline_class()
# TypeError: bspline_class is an abstract native type and cannot be
#            instantiated; create one of its concrete extensions instead

issubclass(bspline.bspline_1d, bspline.bspline_class)   # True
```

The procedural module exposes the matching `db1ink` through `db6ink` setup
routines and `db1val` through `db6val` evaluators. Pass ordinary NumPy arrays;
PRIK performs the ABI conversion inside the generated wrapper.

---

## 4. Run the complete test suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/fortran/bspline/tests
```

The tests cover every exported routine and class:

| Family | Public surface |
| --- | ---: |
| Interpolation setup | 6 routines |
| Evaluation | 6 routines |
| Definite integrals | 2 routines |
| Status reporting | 1 routine |
| Order constants | 8 constants |
| Derived types | 1 abstract base + 6 concrete classes |

The inventory test fails if an expected export disappears, an extra public
export appears, or a procedural routine has no named numerical test.

---

## 5. See how results are validated

The suite checks interpolation against analytic values and SciPy, along with
constructor behavior, inheritance, abstract-base dispatch, generated status,
and Fortran-order array handling. This test comes directly from the runnable
suite and shows the procedural one-dimensional definite integral:

<!-- prik-doc-source: examples/fortran/bspline/tests/test_procedural_api.py::test_db1sqad -->
```python
def test_db1sqad(bspline_sub):
    x = np.linspace(0.0, np.pi, 60)
    knots, bcoef, nx = _interpolant(bspline_sub, x, np.sin(x))
    work = np.zeros(3 * int(CUBIC), dtype=np.float64)

    value, iflag = bspline_sub.db1sqad(knots, bcoef, nx, CUBIC, np.float64(0.0), np.float64(np.pi), work)
    assert iflag == np.int32(0)
    assert value == pytest.approx(2.0, abs=1.0e-6)
```

It builds a cubic spline for `sin(x)`, integrates it from zero to π, and checks
the known value of two.

---

## 6. Run focused examples

After building the extension, run a family or one routine:

```bash
python3 -m pytest -q examples/fortran/bspline/tests/test_object_oriented_api.py
python3 -m pytest -q \
  examples/fortran/bspline/tests/test_procedural_api.py::test_db1ink
python3 -m pytest -q examples/fortran/bspline/tests -k db6
```

- Derived-type examples →
  [`test_object_oriented_api.py`](../../../../examples/fortran/bspline/tests/test_object_oriented_api.py)
- Procedural numerical examples →
  [`test_procedural_api.py`](../../../../examples/fortran/bspline/tests/test_procedural_api.py)
- Public surface and coverage check →
  [`test_routine_coverage.py`](../../../../examples/fortran/bspline/tests/test_routine_coverage.py)
- Reviewed inventory →
  [`routine_inventory.py`](../../../../examples/fortran/bspline/routine_inventory.py)
- Copyable project instructions →
  [`examples/fortran/bspline/README.md`](../../../../examples/fortran/bspline/README.md)

---

## Troubleshooting

- Confirm that `gfortran` is available on `PATH`.
- Use `source examples/fortran/bspline/build_all.sh`; executing it in a child shell does
  not preserve the exported `PYTHONPATH`.
- Run one failing procedure with `-vv -s` to retain its compiler and wrapper
  diagnostics.

---

## Source provenance

The native files under
[`examples/fortran/bspline/native/`](../../../../examples/fortran/bspline/native/) are the
BSPLINE-FORTRAN 7.4.0 snapshot at
[commit `047c7244`](https://github.com/jacobwilliams/bspline-fortran/tree/047c7244).
The upstream `bspline_defc_module` least-squares fitter and its
`bspline_blas_module` bridge are intentionally outside this interpolation
example.

See the [upstream repository](https://github.com/jacobwilliams/bspline-fortran)
and its bundled BSD-3-Clause license before redistributing the vendored native
source.
