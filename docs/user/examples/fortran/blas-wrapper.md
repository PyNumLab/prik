---
title: Build and Validate the Reference BLAS with PRIK
audience: users, advanced users
prerequisites: arrays, packaging
related: lapack-wrapper.md, ../../guide/arrays.md
status: maintained
publication: reviewed
---

# Build and Validate the Reference BLAS with PRIK

This example wraps all 155 routines of the Reference BLAS twice, once with
PRIK and once with NumPy's f2py, and checks both against independent
mathematical results. BLAS is compiled once into a shared library that both
wrappers link, so a difference between them comes from the wrapper, never
from the numerics.

### What you get

- Two extension modules, `prik_reference_blas` and `f2py_reference_blas`, each
  exposing the same 155 routines: Level 1 vector, Level 2 matrix-vector, and
  Level 3 matrix-matrix operations, in real and complex precisions, including
  packed, banded, symmetric, Hermitian, and triangular storage.
- A named test for every routine that checks PRIK and f2py against an
  independent formula and against each other.

---

## Quick start

From a PRIK checkout with PRIK installed, GNU Fortran on `PATH`, and the pinned
NumPy, Meson, and Ninja (see [Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/blas/build_all.sh
python3 -m pytest -q examples/fortran/blas/tests
```

The first command builds both wrappers and puts them on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
complete comparison.

After this, both modules import in the same shell:

```python
import numpy as np
import f2py_reference_blas
import prik_reference_blas

x = np.array([2.0, -4.0, 1.0])
y = np.array([3.0, 5.0, -2.0])
prik_reference_blas.daxpy(np.int32(3), np.float64(-1.5), x, np.int32(1), y, np.int32(1))
print(y)  # [ 0.  11.  -3.5]
```

---

## Key files

Everything lives under
[`examples/fortran/blas/`](../../../../examples/fortran/blas/):

| File | What it does |
| --- | --- |
| [`native/`](../../../../examples/fortran/blas/native/) | The 155 Reference BLAS sources from Netlib LAPACK 3.12.1; the build downloads nothing. |
| [`build_prik.sh`](../../../../examples/fortran/blas/build_prik.sh) | Compiles BLAS into one shared library and builds the PRIK wrapper against it. |
| [`blas.pyf`](../../../../examples/fortran/blas/blas.pyf) | The reviewed f2py signature file for all 155 routines. |
| [`build_f2py.sh`](../../../../examples/fortran/blas/build_f2py.sh) | Builds the f2py wrapper from `blas.pyf`, linked to the same library. |
| [`build_all.sh`](../../../../examples/fortran/blas/build_all.sh) | Runs both build scripts and adds both modules to `PYTHONPATH`. |
| [`routine_inventory.py`](../../../../examples/fortran/blas/routine_inventory.py) | The authoritative list of routines, grouped by BLAS level and kind. |
| [`tests/`](../../../../examples/fortran/blas/tests/) | One test file per routine family, plus [`test_routine_coverage.py`](../../../../examples/fortran/blas/tests/test_routine_coverage.py), which fails if a routine is missing from the sources, inventory, exports, or tests. |
| [`tests/helpers.py`](../../../../examples/fortran/blas/tests/helpers.py) | The small comparison helpers used by every test. |

---

## How the build works

BLAS is compiled once. Both wrappers link that one shared library:

```text
155 BLAS sources ──compile once──> libprik_full_blas
                                           │
  PRIK API, read from the sources ─────────┼──> prik_reference_blas
  f2py API, from blas.pyf ─────────────────┴──> f2py_reference_blas
```

1. `examples.native_library` compiles the 155 sources into
   `libprik_full_blas` and prints its path.
2. PRIK reads the same sources to generate its Python API, compiles no BLAS
   source itself (`--no-compile-input-sources`), and links the library.
3. f2py builds its wrapper from the reviewed `blas.pyf` and links the same
   library.

Both wrappers are built with `-O0`, so the comparison checks correctness
rather than optimization-dependent results. This example is not a performance
benchmark. `build_all.sh` runs these two scripts; each can also be reused on
its own.

**The PRIK build**, from `build_prik.sh`:

<!-- prik-doc-source: examples/fortran/blas/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export BLAS_BUILD_ROOT="$(mktemp -d)"
export BLAS_SHARED_LIBRARY="$(
  python -m examples.native_library blas \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"

mkdir -p "$BLAS_BUILD_ROOT/prik/generated"
cd "$BLAS_BUILD_ROOT/prik"

python -m prik "$EXAMPLE_WORKSPACE/examples/fortran/blas/native" \
  --out prik_reference_blas \
  --out-dir "$BLAS_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --no-compile-input-sources \
  --native-objects "$BLAS_SHARED_LIBRARY" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

**The f2py build**, from `build_f2py.sh`:

<!-- prik-doc-source: examples/fortran/blas/build_f2py.sh -->
```bash
cd "$EXAMPLE_WORKSPACE"
export BLAS_F2PY_ROOT="$BLAS_BUILD_ROOT/f2py"
mkdir -p "$BLAS_F2PY_ROOT/generated"
cd "$BLAS_F2PY_ROOT"

export FC="$(command -v gfortran)"
export F77="$FC"
export F90="$FC"
export FFLAGS="-O0"
export F90FLAGS="-O0"
export LDFLAGS="${LDFLAGS:+$LDFLAGS }-Wl,-rpath,$(dirname "$BLAS_SHARED_LIBRARY")"

python -m numpy.f2py -c \
  "$EXAMPLE_WORKSPACE/examples/fortran/blas/blas.pyf" \
  "-L$(dirname "$BLAS_SHARED_LIBRARY")" \
  -lprik_full_blas \
  --build-dir "$BLAS_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags=-O0 \
  --opt=-O0
```

Everything is written to the temporary `BLAS_BUILD_ROOT` directory, not to the
repository.

---

## PRIK and f2py differences

Both wrappers mutate output arrays in place and compute identical results.
They differ in what a call returns:

| Routine | PRIK returns | f2py returns |
| --- | --- | --- |
| A subroutine such as `daxpy` | The visible scalar arguments, which it treats as in-out: `(n, alpha, incx, incy)` | `None` |
| A function such as `ddot` | The result and the visible scalars: `(result, n, incx, incy)` | The result alone |
| The 6 rotation routines, whose scalars have no Fortran `intent` | The scalar writebacks directly | Typed NumPy 0-D arrays, because `blas.pyf` records those scalars as `intent(inout)` |

PRIK follows the native argument list and scalar contract; the f2py signature
file is the reviewed comparison interface.

---

## How results are validated

Each comparison checks three relationships:

```text
PRIK result      == independent mathematical result
f2py result      == independent mathematical result
PRIK result      == f2py result
```

The suite also checks mutation, input preservation, dtype, shape, increments,
leading dimensions, and unused storage where they are part of a routine's
contract. The independent formula or residual remains the primary numerical
reference.

The two examples below come directly from the runnable suite and use its
helpers:

- `assert_allclose_for_dtype` compares floating-point results with a tolerance
  matched to their NumPy dtype. Its optional `operation_size` is a
  rounding-error scale: use the number of terms in the calculation, such as
  `3` for the three products in the displayed dot product.
- `assert_storage_unchanged` requires an input array to remain exactly equal
  to its saved value, including its dtype and any `NaN` sentinels.

### DAXPY – in-place vector update

<!-- prik-doc-source: examples/fortran/blas/tests/test_level1_real.py::test_daxpy -->
```python
def test_daxpy(prik_blas, f2py_blas):
    alpha = np.float64(-1.5)
    x = np.array([2.0, -4.0, 1.0], dtype=np.float64)
    original_y = np.array([3.0, 5.0, -2.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = original_y.copy(), original_y.copy()

    prik_scalars = prik_blas.daxpy(np.int32(3), alpha, prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_result = f2py_blas.daxpy(np.int32(3), alpha, f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected_y = alpha * x + original_y
    assert_allclose_for_dtype(prik_y, expected_y)
    assert_allclose_for_dtype(f2py_y, expected_y)
    assert_allclose_for_dtype(prik_y, f2py_y)
    assert prik_scalars == (np.int32(3), alpha, np.int32(1), np.int32(1))
    assert f2py_result is None
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
```

Both wrappers must mutate `y` to the expected value. The input-only array `x`
must remain unchanged.

### DDOT – scalar function result

<!-- prik-doc-source: examples/fortran/blas/tests/test_level1_real.py::test_ddot -->
```python
def test_ddot(prik_blas, f2py_blas):
    x = np.array([1.0, -2.0, 4.0], dtype=np.float64)
    y = np.array([3.0, 5.0, -1.0], dtype=np.float64)
    prik_x, f2py_x = x.copy(), x.copy()
    prik_y, f2py_y = y.copy(), y.copy()

    prik_value, n, incx, incy = prik_blas.ddot(np.int32(3), prik_x, np.int32(1), prik_y, np.int32(1))
    f2py_value = f2py_blas.ddot(np.int32(3), f2py_x, np.int32(1), f2py_y, np.int32(1))

    expected = np.float64(1.0 * 3.0 + (-2.0) * 5.0 + 4.0 * (-1.0))
    assert_allclose_for_dtype(prik_value, expected, operation_size=3)
    assert_allclose_for_dtype(f2py_value, expected, operation_size=3)
    assert_allclose_for_dtype(prik_value, f2py_value, operation_size=3)
    assert (n, incx, incy) == (np.int32(3), np.int32(1), np.int32(1))
    assert_storage_unchanged(prik_x, x)
    assert_storage_unchanged(f2py_x, x)
    assert_storage_unchanged(prik_y, y)
    assert_storage_unchanged(f2py_y, y)
```

---

## Run the tests

Run the complete suite, one family, one routine, or every test that mentions a
routine name:

```bash
python3 -m pytest -q examples/fortran/blas/tests
python3 -m pytest -q examples/fortran/blas/tests/test_level1_real.py
python3 -m pytest -q examples/fortran/blas/tests/test_level1_real.py::test_daxpy
python3 -m pytest -q examples/fortran/blas/tests -k dgemm
```

The tests cover vector, matrix, packed, banded, symmetric, Hermitian, and
triangular operations, each called with representative inputs and checked
against an independent result.

---

## Set up a clean environment

Clone PRIK, create a virtual environment, and install the same Python build
tools used by the dedicated CI job:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[qa]" \
  "numpy==2.5.1" "meson==1.11.2" "ninja==1.13.0"
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
| Reference BLAS | snapshot shipped in Netlib LAPACK 3.12.1 |
| Python | 3.12 in the dedicated CI job |
| NumPy / f2py | NumPy 2.5.1 |
| Meson | 1.11.2 |
| Ninja | 1.13.0 |
| Fortran compiler | GNU Fortran 13 in CI; a compatible `gfortran` works locally |

f2py is part of NumPy. On Python 3.12 it uses the Meson backend, which is why
Meson and Ninja are required.

## Tested platforms

The Real Libraries Portability workflow builds and runs this example with
Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

The numerical suite runs on all four targets. A maintainer full-surface audit
also runs on Linux x86-64.

## Troubleshooting

- Confirm that `gfortran`, `meson`, and `ninja` are on your `PATH`.
- On Python 3.12 or later, do not force f2py's old distutils backend. Use the
  pinned Meson and Ninja shown above.
- Use `source examples/fortran/blas/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- Run a single failing test with more detail and keep the build directory:

  ```bash
  python3 -m pytest -vv -s --basetemp=/tmp/prik-blas-debug \
    examples/fortran/blas/tests/test_level1_real.py::test_daxpy
  ```

- Read the compiler output from `build_all.sh`.

---

## Source provenance

The files under [`examples/fortran/blas/native/`](../../../../examples/fortran/blas/native/) are byte-for-byte copies of the 155 files in `BLAS/SRC/` from the official [LAPACK 3.12.1 archive](https://www.netlib.org/lapack/lapack-3.12.1.tar.gz).

If you want to reconstruct the upstream sources yourself:

```bash
curl --location --output lapack-3.12.1.tar.gz \
  https://www.netlib.org/lapack/lapack-3.12.1.tar.gz

printf '%s  %s\n' \
  37b00c90947488521f475b5a187fff4da4a5cfe61b525efcacf7a97f39a45ec6 \
  lapack-3.12.1.tar.gz | sha256sum --check -

tar -xzf lapack-3.12.1.tar.gz
```

Official license and provenance:
[Netlib LAPACK site](https://www.netlib.org/lapack/) · [LAPACK license](https://www.netlib.org/lapack/LICENSE.txt)
