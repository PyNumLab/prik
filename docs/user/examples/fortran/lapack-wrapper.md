---
title: Build and Validate LAPACK with PRIK
audience: users, advanced users
prerequisites: arrays, BLAS wrapper example
related: blas-wrapper.md, ../../guide/error-handling.md
status: maintained
publication: reviewed
---

# Build and Validate LAPACK with PRIK

This example wraps the complete Reference LAPACK with PRIK, and a comparison
surface with NumPy's f2py, then checks both against SciPy and independent
mathematical results. LAPACK is compiled once into a shared library that both
wrappers link, so a difference between them comes from the wrapper, never from
the numerics.

### What you get

- `prik_reference_lapack_example`: PRIK's wrapper of all 1,936 procedures in
  Reference LAPACK's default, non-XBLAS source set.
- `f2py_reference_lapack_example`: the f2py comparison wrapper.
- A named test for each of the 127 double-precision real routines that SciPy
  1.18.0 also exposes: linear systems, least squares, factorizations,
  eigenvalue problems, and singular values. Each test checks PRIK, f2py, and
  SciPy against an independent mathematical result.

This example builds on the [Reference BLAS example](blas-wrapper.md), which
explains the same shared-library pattern in a smaller setting.

---

## Quick start

From a PRIK checkout with PRIK installed, GNU Fortran and the LAPACK and BLAS
development libraries on the system, and the pinned NumPy, SciPy, Meson, and
Ninja (see [Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/lapack/build_all.sh
python3 -m pytest -q examples/fortran/lapack/tests
```

The first command builds both wrappers and puts them on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
127-routine comparison.

After this, `prik_reference_lapack_example` and
`f2py_reference_lapack_example` import in the same shell. The
[DGESV example](#dgesv-solve-a-general-linear-system) below shows a complete
call through each wrapper.

---

## Key files

Everything lives under
[`examples/fortran/lapack/`](../../../../examples/fortran/lapack/):

| File | What it does |
| --- | --- |
| [`native/`](../../../../examples/fortran/lapack/native/) | The Reference LAPACK 3.12.1 source snapshot; the build downloads nothing. |
| [`xblas_sources.txt`](../../../../examples/fortran/lapack/xblas_sources.txt) | The sources left out of the default build because they need the separate XBLAS library. |
| [`support/`](../../../../examples/fortran/lapack/support/) | Two workspace-rounding helpers from upstream `INSTALL/` that the default build needs. |
| [`build_prik.sh`](../../../../examples/fortran/lapack/build_prik.sh) | Compiles LAPACK into one shared library and builds the PRIK wrapper against it. |
| [`lapack.pyf`](../../../../examples/fortran/lapack/lapack.pyf) | The reviewed f2py signature file for the comparison routines and `la_constants`. |
| [`lapack.f2cmap`](../../../../examples/fortran/lapack/lapack.f2cmap) | Tells f2py that `real(wp)` is a C `double`. |
| [`build_f2py.sh`](../../../../examples/fortran/lapack/build_f2py.sh) | Builds the f2py wrapper from `lapack.pyf`, linked to the same library. |
| [`build_all.sh`](../../../../examples/fortran/lapack/build_all.sh) | Runs both build scripts and adds both modules to `PYTHONPATH`. |
| [`routine_inventory.py`](../../../../examples/fortran/lapack/routine_inventory.py) | The reviewed list of the 127 validated routines, grouped by LAPACK family. |
| [`tests/`](../../../../examples/fortran/lapack/tests/) | One test file per routine family, plus [`test_routine_coverage.py`](../../../../examples/fortran/lapack/tests/test_routine_coverage.py), which checks the inventory against the tests. |
| [`tests/helpers.py`](../../../../examples/fortran/lapack/tests/helpers.py) | The comparison helpers used by the tests. |

---

## How the build works

LAPACK is compiled once. Both wrappers link that one shared library:

```text
LAPACK and BLAS sources ──compile once──> libprik_full_lapack
                                                   │
  PRIK API, read from the sources ─────────────────┼──> prik_reference_lapack_example
  f2py API, from lapack.pyf ───────────────────────┴──> f2py_reference_lapack_example
```

1. `examples.native_library` compiles the bundled LAPACK and BLAS sources into
   `libprik_full_lapack`, links the installed LAPACK and BLAS libraries for
   support routines outside the bundled set, and keeps the compiler's module
   files in `LAPACK_MODULE_DIR`.
2. PRIK reads the same default, non-XBLAS sources to generate its Python API,
   compiles no LAPACK source itself (`--no-compile-input-sources`), and links
   the library.
3. f2py builds its wrapper from the reviewed `lapack.pyf` and links the same
   library.

Both wrappers are built with `-O0` and use `LAPACK_MODULE_DIR` when they
compile. `build_all.sh` runs these two scripts; each can also be reused on its
own.

**The PRIK build**, from `build_prik.sh`:

<!-- prik-doc-source: examples/fortran/lapack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export LAPACK_BUILD_ROOT="$(mktemp -d)"
LAPACK_SHARED_LIBRARY="$(
  python -m examples.native_library lapack \
    --compiler "$(command -v gfortran)" \
    --jobs 8
)"
export LAPACK_SHARED_LIBRARY
export LAPACK_MODULE_DIR="$(dirname "$LAPACK_SHARED_LIBRARY")/modules"
export LAPACK_SOURCE_ROOT="$(dirname "$LAPACK_SHARED_LIBRARY")/wrapper_sources"

mkdir -p "$LAPACK_BUILD_ROOT/prik/generated"
cd "$LAPACK_BUILD_ROOT/prik"
python -m prik "$LAPACK_SOURCE_ROOT" \
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

**The f2py build**, from `build_f2py.sh`:

<!-- prik-doc-source: examples/fortran/lapack/build_f2py.sh -->
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
  "$EXAMPLE_WORKSPACE/examples/fortran/lapack/lapack.pyf" \
  "-L$(dirname "$LAPACK_SHARED_LIBRARY")" \
  -lprik_full_lapack \
  --f2cmap "$EXAMPLE_WORKSPACE/examples/fortran/lapack/lapack.f2cmap" \
  --build-dir "$LAPACK_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags="-O0 -I$LAPACK_MODULE_DIR" \
  --opt=-O0
```

Everything is written to the temporary `LAPACK_BUILD_ROOT` directory, not to
the repository.

---

## PRIK, f2py, and SciPy differences

All three compute the same results. They differ in how a call looks:

| Case | PRIK | f2py comparison wrapper | SciPy |
| --- | --- | --- | --- |
| A routine such as `dgesv` | Native argument order; updates arrays in place and returns the visible scalars, for example `(2, 1, 2, 2, 0)` | Updates arrays in place and returns `None` | Returns new arrays and `info` |
| Character selectors such as `"L"` in `dpotrf` | Returned with the other scalars, because LAPACK declares no `intent` | Passed as `b"L"` | A keyword such as `lower=1` |
| The 9 routines whose scalar outputs have no Fortran `intent` | Returns the writebacks directly | Typed NumPy 0-D arrays, because `lapack.pyf` records them as `intent(inout)` | — |
| `dgees` and `dgges` | Wrapped and tested | Not in the comparison: f2py 2.5.1 cannot generate their selection callbacks | Used to verify the Schur decompositions |

SciPy reports zero-based pivots, while LAPACK and both wrappers use one-based
pivots.

---

## How results are validated

LAPACK outputs are not always unique. Eigenvectors and singular vectors may
change sign, repeated eigenspaces may use a different orthonormal basis, and
pivot ties may choose another valid permutation, so byte-for-byte agreement is
not the only oracle.

Tests use explicit solutions, residuals, factor reconstructions, orthogonality,
eigen equations, and storage checks. The two helpers used below live in
[`tests/helpers.py`](../../../../examples/fortran/lapack/tests/helpers.py):

- `assert_allclose_float64` compares values using a tolerance appropriate for
  float64 arithmetic. Its `operation_size` argument is a rounding-error scale:
  use the relevant matrix dimension, such as `2` for these 2-by-2 examples,
  so the tolerance allows for accumulated arithmetic.
- `assert_storage_unchanged` compares storage exactly, including `NaN`
  sentinels in parts of an array LAPACK must not read or overwrite.

The examples below come from the runnable suite and show the PRIK, f2py, and
SciPy calls together with a direct mathematical check.

### DGESV – solve a general linear system

<!-- prik-doc-source: examples/fortran/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system -->
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

<!-- prik-doc-source: examples/fortran/lapack/tests/test_linear_positive_definite.py::test_dpotrf_reconstructs_spd_matrix -->
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

## Run the tests

Run the complete suite, one family, one routine, or every test that mentions a
routine name:

```bash
python3 -m pytest -q examples/fortran/lapack/tests
python3 -m pytest -q examples/fortran/lapack/tests/test_linear_general.py
python3 -m pytest -q \
  examples/fortran/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
python3 -m pytest -q examples/fortran/lapack/tests -k dgesvd
```

---

## Set up a clean environment

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

Run the example's commands from the repository root with the virtual
environment active.

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

SciPy is pinned to exactly 1.18.0 so its low-level comparison API and expected
results stay reproducible.

## Tested platforms

The Real Libraries Portability workflow builds and runs this example with
Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

The 127-routine validation suite runs on all four targets. A maintainer
full-surface audit also runs on Linux x86-64.

## Troubleshooting

- Confirm that `gfortran`, `ar`, `meson`, and `ninja` are on `PATH`.
- Keep SciPy at **exactly 1.18.0** so its low-level comparison API matches this
  example.
- On Python 3.12 or newer, let f2py use Meson; do not force the removed
  distutils backend.
- Use `source examples/fortran/lapack/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- Rerun one named test with more detail and keep the build directory:

  ```bash
  python3 -m pytest -vv -s --basetemp=/tmp/prik-lapack-debug \
    examples/fortran/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
  ```

- Compare residuals and reconstructions before comparing raw factor bytes;
  several valid LAPACK decompositions are not unique.

---

## Source provenance

The official versioned archive is
[`lapack-3.12.1.tar.gz`](https://www.netlib.org/lapack/lapack-3.12.1.tar.gz)

The repository boundary is precise:

- [`examples/fortran/lapack/native/`](../../../../examples/fortran/lapack/native/) owns the complete 2,062-file source snapshot.
  Of those, 2,061 are byte-for-byte the upstream `SRC/` directory; the repository adds its project-local `dlamch.f` machine-parameter implementation.
- The official default build excludes the 130 sources in [`examples/fortran/lapack/xblas_sources.txt`](../../../../examples/fortran/lapack/xblas_sources.txt), which require the separately distributed XBLAS library.
  PRIK and the reusable native library use the remaining 1,932 sources and expose 1,936 procedures.
- [`examples/fortran/lapack/support/`](../../../../examples/fortran/lapack/support/) owns the two `INSTALL/` workspace-rounding helpers required by that default source set.
- Upstream test programs, timing programs, examples and matrix generators are **not** part of the library source set.
- [`examples/fortran/blas/native/`](../../../../examples/fortran/blas/native/) separately owns the 155 Reference BLAS sources.
  They are consumed as dependencies and are not copied into the LAPACK directory.
- Installed LAPACK and BLAS libraries provide support routines outside the copied default source set.

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
