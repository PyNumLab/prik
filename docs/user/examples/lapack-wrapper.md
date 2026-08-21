---
title: Build and Validate LAPACK with PRIK
audience: users, advanced users
prerequisites: arrays, BLAS wrapper example
related: blas-wrapper.md, ../guide/error-handling.md
status: maintained
publication: reviewed
---

# Build and Validate LAPACK with PRIK

This example builds the complete Reference LAPACK library and wraps it with
PRIK. It validates the 127 double-precision real routines also available
through `scipy.linalg.lapack` in SciPy 1.18.0.

### What this example shows

- Build PRIK and f2py wrappers against the same compiled LAPACK library.
- Call linear-system, factorization, eigenvalue, and singular-value routines
  with NumPy arrays.
- Compare results with SciPy and check solutions, residuals, reconstructions,
  and other mathematical properties.

You should already be comfortable with the BLAS wrapper example, NumPy arrays, and basic packaging.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| Reference LAPACK | Netlib LAPACK 3.12.1 |
| Reference BLAS | BLAS snapshot shipped in LAPACK 3.12.1 |
| Python | 3.12 or newer |
| NumPy / f2py | NumPy 2.5.1 |
| SciPy | exactly 1.18.0 |
| Meson | 1.11.2 |
| Ninja | 1.13.0 |
| Fortran compiler | compatible `gfortran` |

---

## 1. Prepare the repository and toolchain

Clone PRIK, create a virtual environment, and install the pinned comparison and
build tools:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[qa]" \
  "numpy==2.5.1" "scipy==1.18.0" \
  "meson==1.11.2" "ninja==1.13.0"
```

Install GNU Fortran and the LAPACK and BLAS development packages. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install --yes gfortran liblapack-dev libblas-dev
gfortran --version
```

All remaining commands run from the repository root with the virtual
environment active.

The runnable material is self-contained in the repository's
[`examples/` directory](../../../examples/). After PRIK and the listed tools
are installed, you can copy that directory alone.

---

## 2. Compile LAPACK once and build the PRIK wrapper

Compile the native files once into a shared `.so` file so both wrappers can
reuse it. The native builder links the installed LAPACK and BLAS development
libraries for companion support symbols:

<!-- prik-doc-source: examples/lapack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export LAPACK_BUILD_ROOT="$(mktemp -d)"
export LAPACK_SHARED_LIBRARY="$(
  python -m examples.native_library lapack \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"
export LAPACK_MODULE_DIR="$(dirname "$LAPACK_SHARED_LIBRARY")/modules"

mkdir -p "$LAPACK_BUILD_ROOT/prik/generated"
cd "$LAPACK_BUILD_ROOT/prik"
python -m prik "$EXAMPLE_WORKSPACE/examples/lapack/native" \
  --out prik_reference_lapack_example \
  --out-dir "$LAPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --no-compile-input-sources \
  --native-objects "$LAPACK_SHARED_LIBRARY" \
  -I "$LAPACK_MODULE_DIR" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

PRIK reads the sources to build the Python API, skips native implementation
compilation, and links the shared library. The include path supplies the module
metadata needed by the generated wrapper.

---

## 3. Build the f2py comparison wrapper

The committed [`lapack.pyf`](../../../examples/lapack/lapack.pyf) contains the
125 selected routines and the `la_constants` module signature. f2py compiles
only this wrapper and links `LAPACK_SHARED_LIBRARY`.

Run the same direct f2py command exercised by the test suite:

<!-- prik-doc-source: examples/lapack/build_f2py.sh -->
```bash
cd "$EXAMPLE_WORKSPACE"
export LAPACK_F2PY_ROOT="$LAPACK_BUILD_ROOT/f2py"
mkdir -p "$LAPACK_F2PY_ROOT/generated"
cd "$LAPACK_F2PY_ROOT"

export FC="$(command -v gfortran)"
export F77="$FC"
export F90="$FC"
export FFLAGS="-O0"
export F90FLAGS="-O0"
export LDFLAGS="${LDFLAGS:+$LDFLAGS }-Wl,-rpath,$(dirname "$LAPACK_SHARED_LIBRARY")"

python -m numpy.f2py -c \
  "$EXAMPLE_WORKSPACE/examples/lapack/lapack.pyf" \
  "-L$(dirname "$LAPACK_SHARED_LIBRARY")" \
  -lprik_full_lapack \
  --f2cmap "$EXAMPLE_WORKSPACE/examples/lapack/lapack.f2cmap" \
  --build-dir "$LAPACK_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags="-O0 -I$LAPACK_MODULE_DIR" \
  --opt=-O0
```

`LAPACK_MODULE_DIR` provides the compiler-generated module files needed to
compile each wrapper. Both wrappers link the existing shared library instead of
recompiling LAPACK.

The comparison excludes `dgees` and `dgges` because f2py 2.5.1 cannot generate
their callback declarations correctly. Those two routines are still checked
through PRIK, SciPy, and their Schur decompositions.

Import the two built modules and SciPy's LAPACK module from the repository
root:

```python
import os
import sys

sys.path.insert(0, f"{os.environ['LAPACK_BUILD_ROOT']}/prik")
sys.path.insert(0, os.environ["LAPACK_F2PY_ROOT"])

import f2py_reference_lapack_example
import prik_reference_lapack_example
from scipy.linalg import lapack as scipy_lapack
```

### SciPy comparison

The tests use the 127 double-precision real LAPACK routines available in SciPy
1.18.0 for `np.float64` arrays. Pinning that version keeps the comparison API
and expected results reproducible.

---

## 4. Run the complete test suite

Build both wrappers and run all 127 routine tests:

```bash
source examples/lapack/build_all.sh
python3 -m pytest -q examples/lapack/tests
```

The suite covers linear systems, least squares, factorizations, eigenvalue
problems, singular values, and related matrix operations.

---

## 5. See how results are validated

LAPACK outputs are not always unique. Eigenvectors and singular vectors may
change sign, repeated eigenspaces may use a different orthonormal basis, and
pivot ties may choose another valid permutation.
Therefore byte-for-byte agreement is not the only oracle.

Tests use explicit solutions, residuals, factor reconstructions, orthogonality,
eigen equations, and storage checks. The two reusable checks shown below live
in [`tests/helpers.py`](../../../examples/lapack/tests/helpers.py).

#### Test helper conventions

The snippets use standard NumPy operations whenever the check is local. The
two helpers in the displayed DPOTRF test keep its repeated checks consistent:

- `assert_allclose_float64` compares values using a tolerance appropriate for
  float64 arithmetic. Its `operation_size` argument is a rounding-error scale:
  use the relevant matrix dimension, such as `2` for these 2-by-2 examples,
  so the tolerance allows for accumulated arithmetic.
- `assert_storage_unchanged` compares storage exactly, including `NaN`
  sentinels in parts of an array LAPACK must not read or overwrite.

The examples below show the PRIK, f2py, and SciPy calls together with a direct
mathematical check. They come from the runnable suite.

### DGESV – solve a general linear system

<!-- prik-doc-source: examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system -->
```python
def test_dgesv_solves_general_system(prik_lapack, scipy_lapack, f2py_lapack):
    original_a = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    original_b = np.array([[5.0], [5.0]], dtype=np.float64)
    expected_x = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_a, f2py_a = original_a.copy(order="F"), original_a.copy(order="F")
    prik_b, f2py_b = original_b.copy(order="F"), original_b.copy(order="F")
    prik_piv = np.empty(2, dtype=np.int32)
    f2py_piv = np.empty(2, dtype=np.int32)

    prik_scalars = prik_lapack.dgesv(
        np.int32(2), np.int32(1), prik_a, np.int32(2), prik_piv, prik_b, np.int32(2), np.int32(0)
    )
    f2py_result = f2py_lapack.dgesv(2, 1, f2py_a, f2py_piv, f2py_b, 0)
    scipy_lu, scipy_piv, scipy_x, scipy_info = scipy_lapack.dgesv(
        original_a.copy(order="F"), original_b.copy(order="F")
    )

    assert prik_scalars == (2, 1, 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    np.testing.assert_allclose(prik_b, expected_x)
    np.testing.assert_allclose(f2py_b, expected_x)
    np.testing.assert_allclose(scipy_x, expected_x)
    np.testing.assert_allclose(prik_a, scipy_lu)
    np.testing.assert_allclose(f2py_a, scipy_lu)
    lapack_pivots = np.asarray(scipy_piv, dtype=np.int32) + 1
    np.testing.assert_array_equal(prik_piv, lapack_pivots)
    np.testing.assert_array_equal(f2py_piv, lapack_pivots)
    np.testing.assert_allclose(original_a @ prik_b, original_b)
```

`copy(order="F")` creates separate Fortran-contiguous inputs because DGESV
overwrites `A` with its LU factors and `B` with the solution. The test checks
the known solution, `A @ X == B`, the LU output, and `INFO == 0`. SciPy reports
zero-based pivots, so adding one gives the one-based pivot values returned by
LAPACK. Both PRIK and the f2py comparison module update the output arrays in
place.

### DPOTRF – reconstruct a Cholesky factorization

<!-- prik-doc-source: examples/lapack/tests/test_linear_positive_definite.py::test_dpotrf_reconstructs_spd_matrix -->
```python
def test_dpotrf_reconstructs_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    logical = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    stored = np.array([[4.0, np.nan], [1.0, 3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = stored.copy(order="F"), stored.copy(order="F")

    prik_scalars = prik_lapack.dpotrf("L", np.int32(2), prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpotrf(b"L", 2, f2py_a, 0)
    scipy_factor, scipy_info = scipy_lapack.dpotrf(stored.copy(order="F"), lower=1, clean=0)

    # LAPACK declares no intent on its dummies, so the conservative
    # intent(inout) default returns every scalar, character selectors included.
    assert prik_scalars == ("L", 2, 2, 0)
    assert f2py_result is None
    assert scipy_info == 0
    prik_lower = np.tril(prik_a)
    f2py_lower = np.tril(f2py_a)
    scipy_lower = np.tril(scipy_factor)
    assert_allclose_float64(prik_lower @ prik_lower.T, logical, operation_size=2)
    assert_allclose_float64(f2py_lower @ f2py_lower.T, logical, operation_size=2)
    assert_allclose_float64(scipy_lower @ scipy_lower.T, logical, operation_size=2)
    assert_allclose_float64(prik_lower, scipy_lower, operation_size=2)
    assert_allclose_float64(f2py_lower, scipy_lower, operation_size=2)
    assert_storage_unchanged(np.triu(prik_a, 1), np.triu(stored, 1))
    assert_storage_unchanged(np.triu(f2py_a, 1), np.triu(stored, 1))
```

The NaN in the unused upper triangle detects accidental access.
The reconstruction `A = L @ L.T` confirms that the factor is correct.

---

## 6. Run focused examples

After building the wrappers, run a family or one routine:

```bash
python3 -m pytest -q examples/lapack/tests/test_linear_general.py
python3 -m pytest -q \
  examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
python3 -m pytest -q examples/lapack/tests -k dgesvd
```

- Full DGESV and related general-system tests → [`test_linear_general.py`](../../../examples/lapack/tests/test_linear_general.py)
- Cholesky and other positive-definite examples → [`test_linear_positive_definite.py`](../../../examples/lapack/tests/test_linear_positive_definite.py)
- Other families live under [`examples/lapack/tests/`](../../../examples/lapack/tests/)
- Public routine list → [`routine_inventory.py`](../../../examples/lapack/routine_inventory.py)
- Routine coverage check → [`test_routine_coverage.py`](../../../examples/lapack/tests/test_routine_coverage.py)

For the copyable build scripts, test commands, and source provenance, see the
[`examples/lapack` project README](../../../examples/lapack/README.md).

---

## Troubleshooting

- Confirm that `gfortran`, `ar`, `meson` and `ninja` are on `PATH`.
- Keep SciPy at **exactly 1.18.0** so its low-level comparison API matches this
  example.
- On Python 3.12 or newer, let f2py use Meson; do not force the removed
  distutils backend.
- Rerun one named test with more detail and keep the build directory:

  ```bash
  python3 -m pytest -vv -s --basetemp=/tmp/prik-lapack-debug \
    examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
  ```

- Compare residuals and reconstructions before comparing raw factor bytes;
  several valid LAPACK decompositions are not unique.

---

## Source provenance

The official versioned archive is
[`lapack-3.12.1.tar.gz`](https://www.netlib.org/lapack/lapack-3.12.1.tar.gz)

The repository boundary is precise:

- [`examples/lapack/native/`](../../../examples/lapack/native/) owns 2,062 implementation sources.
  Of those, 2,061 are byte-for-byte the upstream `SRC/` directory; the repository adds its project-local `dlamch.f` machine-parameter implementation.
- Upstream test programs, timing programs, examples and matrix generators are **not** part of the library source set.
- [`examples/blas/native/`](../../../examples/blas/native/) separately owns the 155 Reference BLAS sources.
  They are consumed as dependencies and are not copied into the LAPACK directory.

To independently audit the official archive:

```bash
curl --location --output lapack-3.12.1.tar.gz \
  https://www.netlib.org/lapack/lapack-3.12.1.tar.gz
printf '%s  %s\n' \
  37b00c90947488521f475b5a187fff4da4a5cfe61b525efcacf7a97f39a45ec6 \
  lapack-3.12.1.tar.gz | sha256sum --check -
tar -xzf lapack-3.12.1.tar.gz
```

See the [Netlib LAPACK release](https://www.netlib.org/lapack/lapack-3.12.1.html)
and the [three-clause BSD-style license](https://www.netlib.org/lapack/LICENSE.txt)
for upstream provenance and redistribution terms.
