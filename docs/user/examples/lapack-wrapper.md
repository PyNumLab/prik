---
title: Build and Validate LAPACK with PRIK
audience: users, advanced users
prerequisites: arrays, BLAS wrapper example
related: blas-wrapper.md, ../guide/error-handling.md
status: maintained
publication: reviewed
---

# Build and Validate LAPACK with PRIK

This example wraps the complete Reference LAPACK implementation corpus once with PRIK, then validates a reviewed, reproducible correctness surface.
The surface contains the 127 double-precision real routines exposed by `scipy.linalg.lapack` in SciPy 1.18.0 for `dtype=np.float64`.

### Why this example exists

- PRIK wraps the **complete** LAPACK library (including its BLAS dependencies).
  All source-level wrapper and compilation coverage stays intact.
- Raw f2py generates wrappers for the 125 selected routines it can expose
  safely and links them to the same complete native artifact as PRIK.
- SciPy supplies the 127 reviewed low-level comparison functions.
- Independent residuals, reconstructions and invariants remain the primary correctness oracle.

This separation keeps a large real library manageable without weakening the claim:
every LAPACK source compiles once for the complete PRIK wrapper, while every selected float64 routine has one visible, named correctness test.

You should already be comfortable with the BLAS wrapper example, NumPy arrays, and basic packaging.

---

## Versions and source boundary

| Component          | Version / source                                      |
|--------------------|-------------------------------------------------------|
| PRIK               | current repository checkout (`0.1.0`)                 |
| Reference LAPACK   | Netlib LAPACK 3.12.1                                  |
| Reference BLAS     | BLAS snapshot shipped in LAPACK 3.12.1                |
| Python             | 3.12 or newer                                          |
| NumPy / f2py       | NumPy 2.5.1                                           |
| SciPy              | exactly 1.18.0 (reviewed inventory)                   |
| Meson              | 1.11.2                                                |
| Ninja              | 1.13.0                                                |
| Fortran compiler   | compatible `gfortran`                                  |

---

## 1. Prepare the repository and toolchain

Clone PRIK, create a virtual environment, and install the pinned comparison and
build tools:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[qa]" \
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

## 3. Build the reviewed f2py comparison surface

The committed [`lapack.pyf`](../../../examples/lapack/lapack.pyf) contains the
reviewed selected routines and `la_constants` module signature. f2py compiles
only its wrapper and links `LAPACK_SHARED_LIBRARY`.

Nine routines document scalar writebacks without declaring Fortran `intent`.
Their reviewed `intent(inout)` declarations live directly in `lapack.pyf`, and
the tests pass typed 0-D arrays. PRIK needs neither: it returns unannotated
scalar writebacks directly, with ordinary scalar arguments.

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

The committed `lapack.pyf` excludes `dgees` and `dgges` because f2py 2.5.1
generates incomplete declarations for their selection callbacks. Their tests
exercise PRIK and SciPy, then independently verify the resulting Schur
decompositions.

Import the two built modules and SciPy's comparison surface from the repository
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

---

## 4. Resolve the SciPy float64 comparison API

SciPy determines eligibility, not the organisation of the test files.
The reviewed inventory was discovered with representative `np.float64` arrays and then frozen for SciPy 1.18.0.

A typical low-level lookup looks like this:

```python
import numpy as np
import scipy
from scipy.linalg import lapack

assert scipy.__version__ == "1.18.0"
matrix = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64, order="F")
dgesv = lapack.get_lapack_funcs("gesv", (matrix,))
assert dgesv.typecode == "d"
```

The runtime suite does **not** silently select “whatever SciPy exports today”.
It fails clearly if the SciPy version or the expected routine inventory drifts.

---

## 5. Run the correctness tests

The arguments `prik_lapack`, `f2py_lapack`, and `scipy_lapack` are
session-scoped pytest fixtures from
[`conftest.py`](../../../examples/lapack/conftest.py). After the build scripts
finish, they provide the complete PRIK module, selected f2py comparison module,
and SciPy's pinned low-level LAPACK module to the tests under
[`examples/lapack/tests/`](../../../examples/lapack/tests/).

The displayed tests use small helpers from
[`tests/helpers.py`](../../../examples/lapack/tests/helpers.py):

| Helper | Exact responsibility |
| --- | --- |
| `column_major(a)` | Copies a matrix as `np.float64` in Fortran-contiguous column-major order. |
| `active(a, rows, columns)` | Selects the logical matrix and excludes leading-dimension padding. |
| `native_pivots(p)` | Converts SciPy's zero-based general-LU pivots to LAPACK's native one-based values. |
| `assert_allclose_float64(a, b)` | Uses a float64-epsilon tolerance scaled by operation length and expected magnitude. |
| `assert_small_residual(r, ...)` | Checks an infinity-norm backward residual scaled by matrix and solution norms. |
| `assert_storage_unchanged(a, b)` | Requires exact preservation, including NaN sentinels. |

The numerical and preservation checks are intentionally small and visible:

```python
import numpy as np
```

<!-- prik-doc-source: examples/lapack/tests/helpers.py::assert_allclose_float64 -->
```python
def assert_allclose_float64(actual, expected, *, operation_size: int = 1) -> None:
    """Compare float64 LAPACK results with an accumulation-aware tolerance."""
    scale = max(1, operation_size)
    expected_array = np.asarray(expected)
    magnitude = max(1.0, float(np.max(np.abs(expected_array), initial=0.0)))
    np.testing.assert_allclose(
        actual,
        expected,
        rtol=np.finfo(np.float64).eps * 32 * scale,
        atol=np.finfo(np.float64).eps * 32 * scale * magnitude,
    )
```

<!-- prik-doc-source: examples/lapack/tests/helpers.py::assert_small_residual -->
```python
def assert_small_residual(
    residual,
    *,
    matrix_norm: float,
    solution_norm: float,
    operation_size: int,
) -> None:
    """Check a backward residual scaled by the represented operation."""
    denominator = max(1.0, matrix_norm * solution_norm)
    scaled = np.linalg.norm(np.asarray(residual, dtype=np.float64), ord=np.inf) / denominator
    tolerance = np.finfo(np.float64).eps * 128 * max(1, operation_size)
    assert scaled <= tolerance, f"scaled residual {scaled} exceeded {tolerance}"
```

<!-- prik-doc-source: examples/lapack/tests/helpers.py::assert_storage_unchanged -->
```python
def assert_storage_unchanged(actual: np.ndarray, expected: np.ndarray) -> None:
    """Compare storage exactly, including NaN sentinels."""
    np.testing.assert_array_equal(actual, expected)
```

These helpers do not call LAPACK and do not hide any wrapper invocation. The
routine call and the essential residual or reconstruction remain in each test.

---

## 6. Validate mathematical behaviour

LAPACK outputs are not always unique.
Eigenvectors and singular vectors may change sign, repeated eigenspaces may use a different orthonormal basis, and pivot ties may choose another valid permutation.
Therefore byte-for-byte agreement is not the only oracle.

Tests use explicit solutions, residuals, factor reconstructions, orthogonality, eigen equations and storage invariants.

The two real tests below keep all three wrapper calls and the independent oracle visible.
The displayed blocks are copied directly from their source functions.

### DGESV – solve a general linear system

<!-- prik-doc-source: examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system -->
```python
def test_dgesv_solves_general_system(prik_lapack, scipy_lapack, f2py_lapack):
    original_a = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    original_b = np.array([[5.0], [5.0]], dtype=np.float64)
    expected_x = np.array([[1.0], [2.0]], dtype=np.float64)
    prik_a, f2py_a = column_major(original_a), column_major(original_a)
    prik_b, f2py_b = column_major(original_b), column_major(original_b)
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
    assert_allclose_float64(active(prik_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(active(f2py_b, 2, 1), expected_x, operation_size=2)
    assert_allclose_float64(scipy_x, expected_x, operation_size=2)
    assert_allclose_float64(prik_a, scipy_lu, operation_size=2)
    assert_allclose_float64(f2py_a, scipy_lu, operation_size=2)
    np.testing.assert_array_equal(prik_piv, native_pivots(scipy_piv))
    np.testing.assert_array_equal(f2py_piv, native_pivots(scipy_piv))
    assert_small_residual(
        original_a @ prik_b - original_b,
        matrix_norm=np.linalg.norm(original_a, ord=np.inf),
        solution_norm=np.linalg.norm(prik_b, ord=np.inf),
        operation_size=2,
    )
```

This test checks the known solution, the independently scaled residual `A @ X - B`, the LU output, native one-based pivots versus SciPy’s convention, and `INFO == 0`.
PRIK preserves the native argument order and returns visible scalar arguments; both PRIK and the f2py comparison module mutate the native output arrays.

### DPOTRF – reconstruct a Cholesky factorization

<!-- prik-doc-source: examples/lapack/tests/test_linear_positive_definite.py::test_dpotrf_reconstructs_spd_matrix -->
```python
def test_dpotrf_reconstructs_spd_matrix(prik_lapack, scipy_lapack, f2py_lapack):
    logical = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    stored = np.array([[4.0, np.nan], [1.0, 3.0]], dtype=np.float64, order="F")
    prik_a, f2py_a = column_major(stored), column_major(stored)

    prik_scalars = prik_lapack.dpotrf("L", np.int32(2), prik_a, np.int32(2), np.int32(0))
    f2py_result = f2py_lapack.dpotrf(b"L", 2, f2py_a, 0)
    scipy_factor, scipy_info = scipy_lapack.dpotrf(stored.copy(order="F"), lower=1, clean=0)

    assert prik_scalars == (2, 2, 0)
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
Correctness is established by reconstructing `A = L @ L.T`, not merely by comparing the factor’s bytes.

---

## 7. Run the maintained example

Build both wrappers once, then run all 127 named tests:

```bash
cd "$REPOSITORY_ROOT"
source examples/lapack/build_all.sh
python -m pytest -q examples/lapack/tests
```

Use a family or a single routine while diagnosing a failure:

```bash
python -m pytest -q examples/lapack/tests/test_linear_general.py
python -m pytest -q \
  examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
python -m pytest -q examples/lapack/tests -k dgesvd
```

- Full DGESV and related general-system tests → [`test_linear_general.py`](../../../examples/lapack/tests/test_linear_general.py)
- Cholesky and other positive-definite examples → [`test_linear_positive_definite.py`](../../../examples/lapack/tests/test_linear_positive_definite.py)
- Other families live under [`examples/lapack/tests/`](../../../examples/lapack/tests/)
- Authoritative mapping of all 127 routines → [`routine_inventory.py`](../../../examples/lapack/routine_inventory.py)
- Coverage audit → [`test_routine_coverage.py`](../../../examples/lapack/tests/test_routine_coverage.py)

The command is complete and reproducible with the listed native toolchain.

For the copyable build scripts, test commands, and source provenance, see the
[`examples/lapack` project README](../../../examples/lapack/README.md).

---

## Troubleshooting

- Confirm that `gfortran`, `ar`, `meson` and `ninja` are on `PATH`.
- Keep SciPy at **exactly 1.18.0** for this reviewed inventory. A different version is treated as inventory drift, not silently accepted.
- On Python 3.12 or newer, let f2py use Meson; do not force the removed distutils backend.
- Rerun one named test with more detail and keep the build directory:

  ```bash
  python -m pytest -vv -s --basetemp=/tmp/prik-lapack-debug \
    examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
  ```

- Compare residuals and reconstructions **before** comparing raw factor bytes; several valid LAPACK decompositions are not unique.
- This is a deterministic correctness suite. It collects no timings and makes no performance claims.

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
