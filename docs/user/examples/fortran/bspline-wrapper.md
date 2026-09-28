---
title: Build and Validate BSPLINE-FORTRAN with PRIK
audience: users, advanced users
prerequisites: derived types, arrays, packaging
related: fftpack-wrapper.md, ../../guide/wrapping-derived-types.md
status: maintained
publication: reviewed
---

# Build and Validate BSPLINE-FORTRAN with PRIK

This example turns [BSPLINE-FORTRAN](https://github.com/jacobwilliams/bspline-fortran),
a modern Fortran 2008 B-spline interpolation library, into one Python
extension. It wraps the upstream source unmodified, including an abstract
derived type, six concrete subclasses, and generic constructors. The suite
checks interpolation from one to six dimensions against analytic functions and
SciPy.

### What you get

One extension, `prik_bspline`, with two namespaces:

| Namespace | Public surface |
| --- | --- |
| `bspline_oo_module` | The abstract `Bspline_Class` and six concrete classes, `Bspline_1d` through `Bspline_6d` |
| `bspline_sub_module` | 15 procedural routines: `db1ink`-`db6ink` (setup), `db1val`-`db6val` (evaluation), `db1sqad` and `db1fqad` (definite integrals), and `get_status_message`; plus eight order constants such as `bspline_order_cubic` |

---

## Quick start

From a PRIK checkout with PRIK installed, GNU Fortran on `PATH`, and the pinned
NumPy and SciPy (see [Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/bspline/build_all.sh
python3 -m pytest -q examples/fortran/bspline/tests
```

The first command builds the extension and puts it on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
tests.

After this, the classes import in the same shell:

```python
import prik_bspline.bspline_oo_module as bspline
```

[Use the generated API](#use-the-generated-api) shows complete calls.

---

## Key files

Everything lives under [`examples/fortran/bspline/`](../../../../examples/fortran/bspline/):

| File | What it does |
| --- | --- |
| [`native/bspline_kinds_module.F90`](../../../../examples/fortran/bspline/native/bspline_kinds_module.F90) | Defines the kind parameters used by the other modules. |
| [`native/bspline_sub_module.f90`](../../../../examples/fortran/bspline/native/bspline_sub_module.f90) | The procedural interface: setup, evaluation, and integral routines. |
| [`native/bspline_oo_module.f90`](../../../../examples/fortran/bspline/native/bspline_oo_module.f90) | The object-oriented interface: the abstract base and its six extensions. |
| [`build_prik.sh`](../../../../examples/fortran/bspline/build_prik.sh) | Builds the extension with one PRIK command. |
| [`build_all.sh`](../../../../examples/fortran/bspline/build_all.sh) | Runs `build_prik.sh` and adds the extension to `PYTHONPATH`. |
| [`routine_inventory.py`](../../../../examples/fortran/bspline/routine_inventory.py) | The reviewed public surface: classes, bindings, routines, and constants. |
| [`tests/test_object_oriented_api.py`](../../../../examples/fortran/bspline/tests/test_object_oriented_api.py) | Constructs and evaluates every class, and checks the abstract-base and inheritance behavior. |
| [`tests/test_procedural_api.py`](../../../../examples/fortran/bspline/tests/test_procedural_api.py) | One named numerical test per procedural routine. |
| [`tests/test_routine_coverage.py`](../../../../examples/fortran/bspline/tests/test_routine_coverage.py) | Fails if an expected export disappears, an extra one appears, or a routine has no test. |

---

## How the build works

One PRIK command reads the three sources in dependency order and compiles them,
with the generated wrapper, into one extension. The upstream source is not
edited:

```text
bspline_kinds_module.F90 ─┐
bspline_sub_module.f90 ───┼──prik──> prik_bspline ┬─ bspline_sub_module  (procedural)
bspline_oo_module.f90 ────┘                       └─ bspline_oo_module   (classes)
```

`build_prik.sh` runs that command:

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

The example uses `-O0` so the tests focus on correct results. Everything is
written to the temporary `BSPLINE_BUILD_ROOT` directory, not to the repository.

---

## What PRIK maps from modern Fortran

| Fortran construct | In Python |
| --- | --- |
| Abstract type `bspline_class` with deferred bindings | `Bspline_Class`, which raises `TypeError` if constructed directly |
| Six extensions of that type | Subclasses: `issubclass(bspline.Bspline_1d, bspline.Bspline_Class)` is `True` |
| Bindings the base implements once | Inherited methods: `clear_flag`, `status_message`, `status_ok` |
| Deferred bindings | Methods each class answers itself: `destroy`, `size_of` |
| Generic constructor `interface bspline_1d` | `Bspline_1d(...)`, which accepts both the empty and the data-driven form |
| Generic interfaces such as `db1ink` and `db1val` | One Python name for their specific procedures |
| Private components and private bindings | Not exposed |
| Module constants such as `bspline_order_cubic` | Module attributes (`bspline_order_cubic == 4`) |

---

## Use the generated API

**A one-dimensional spline.** The data-driven constructor builds the spline;
`evaluate` takes the derivative order as its second argument:

```python
import numpy as np
import prik_bspline.bspline_oo_module as bspline

x = np.linspace(0.0, 2.0 * np.pi, 25)
spline = bspline.Bspline_1d(x, np.sin(x), np.int32(4))  # cubic: order 4

value, iflag = spline.evaluate(np.float64(1.234), np.int32(0))
print(value)  # 0.943811 (sin(1.234) = 0.943818)

slope, iflag = spline.evaluate(np.float64(1.234), np.int32(1))
print(slope)  # 0.330588 (cos(1.234) = 0.330465)

area, iflag = spline.integral(np.float64(0.0), np.float64(np.pi))
print(area)   # 1.999991 (exact: 2)
```

`iflag == 0` means success. `spline.status_ok()` reports whether the last call
succeeded, and `spline.status_message(iflag)` turns a code into text: evaluating
at `x = 99`, outside the data, gives `iflag == 601`, "Error in db*val: x value
out of bounds".

**A two-dimensional surface.** Sample on a grid in Fortran order and pass one
order per dimension:

```python
x = np.linspace(0.0, np.pi, 20)
y = np.linspace(0.0, np.pi, 20)
samples = np.asfortranarray(np.sin(x)[:, None] * np.cos(y)[None, :])

surface = bspline.Bspline_2d(x, y, samples, np.int32(4), np.int32(4))
value, iflag = surface.evaluate(np.float64(1.0), np.float64(0.5), np.int32(0), np.int32(0))
print(value)  # 0.738460 (sin(1) * cos(0.5) = 0.738460)
```

`Bspline_3d` through `Bspline_6d` follow the same pattern.

**The abstract base** is exported but cannot be constructed:

```python
bspline.Bspline_Class()
# TypeError: bspline_class is an abstract native type and cannot be
#            instantiated; create one of its concrete extensions instead
```

**The procedural interface** in `bspline_sub_module` mirrors the Fortran
routines: `db1ink` builds the knots and coefficients, and `db1val` evaluates
them, with the arrays passed explicitly. The `db1sqad` test below shows it.

---

## How results are validated

The suite builds every procedural family from one to six dimensions and
evaluates an affine function through every evaluator. It checks
one-dimensional analytic values, derivatives, definite integrals, and
callback-driven integration, plus a comparison with SciPy's
`make_interp_spline`. The object-oriented tests construct and evaluate every
concrete class and check the abstract-base, inheritance, deferred-binding, and
generic-constructor behavior.

This test builds a cubic spline for `sin(x)` through the procedural interface,
integrates it from zero to π, and checks the known value of two:

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

---

## Run the tests

Run the complete suite, one interface family, one routine, or every test that
mentions a name:

```bash
python3 -m pytest -q examples/fortran/bspline/tests
python3 -m pytest -q examples/fortran/bspline/tests/test_object_oriented_api.py
python3 -m pytest -q \
  examples/fortran/bspline/tests/test_procedural_api.py::test_db1ink
python3 -m pytest -q examples/fortran/bspline/tests -k db6
```

---

## Set up a clean environment

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

Run the example's commands from the repository root with the virtual
environment active.

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| BSPLINE-FORTRAN | [version 7.4.0, commit `047c7244`](https://github.com/jacobwilliams/bspline-fortran/tree/047c7244) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy | 1.18.0 |
| Fortran compiler | GNU Fortran 13 in CI; a compatible `gfortran` works locally |

## Tested platforms

The Real Libraries Portability workflow builds and runs the complete numerical
suite with Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

## Troubleshooting

- Confirm that `gfortran` is available on `PATH`.
- Use `source examples/fortran/bspline/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- A nonzero `iflag`: `status_message(iflag)` on the spline, or
  `get_status_message(iflag)` in the procedural interface, explains it.
- Run one failing procedure with `-vv -s` to see its compiler and wrapper
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
