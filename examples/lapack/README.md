# Wrap Reference LAPACK with PRIK

Build the complete Reference LAPACK once, wrap it with PRIK and NumPy f2py, and
validate a reviewed double-precision surface against SciPy and independent
numerical checks.

PRIK wraps all 1,936 procedures in the Reference LAPACK default, non-XBLAS
source set. For focused validation, the suite selects the 127 `float64`
routines exposed by SciPy 1.18.0; raw f2py supports
125 of those source interfaces. All 127 selected routines have explicit
correctness tests, with no unsupported or skipped routines.

## Requirements

Install GNU Fortran, `ar`, the LAPACK and BLAS development libraries, and the
pinned Python tools. On Ubuntu:

```console
sudo apt-get install gfortran liblapack-dev libblas-dev
```

Then install the Python tools:

```console
python3 -m pip install \
  "numpy==2.5.1" "scipy==1.18.0" \
  "meson==1.11.2" "ninja==1.13.0" pytest
```

Run the remaining commands from the repository root.

## Quick start

Build both wrappers and run the 127-routine comparison:

```bash
source examples/lapack/build_all.sh
python3 -m pytest -q examples/lapack/tests
```

Use `source` so the build paths exported by `build_all.sh` remain available to
the test process.

## How the build works

The builder compiles the bundled LAPACK and BLAS sources once. It also links
the installed LAPACK and BLAS libraries for support routines outside the
bundled source set. PRIK and f2py then link the same shared library, so LAPACK
implementation code is not compiled twice.

The native build also retains its compiler-generated module files in
`LAPACK_MODULE_DIR`. Both generated wrappers use that directory when they
compile.

`build_all.sh` runs the following two scripts. The commands are shown so you
can reuse or adapt either build independently.

### Build the PRIK wrapper

<!-- prik-doc-source: examples/lapack/build_prik.sh -->
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

PRIK reads the same default, non-XBLAS source set compiled into the reusable
library. The complete upstream `SRC/` snapshot remains available under
`examples/lapack/native` for provenance and parser inspection.
`--no-compile-input-sources` makes it reuse `LAPACK_SHARED_LIBRARY` instead of
compiling those native sources again.

### Build the f2py comparison wrapper

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

The committed reviewed [`lapack.pyf`](lapack.pyf) defines the 125-routine f2py
comparison surface and exposes `la_constants`. f2py compiles only its generated
wrapper and reuses the native library and module directory.

## Run focused tests

After the quick-start build, run one family or routine:

```bash
python3 -m pytest -q examples/lapack/tests/test_linear_general.py
python3 -m pytest -q \
  examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
python3 -m pytest -q examples/lapack/tests -k dgesvd
```

## What is validated

PRIK preserves native argument order, storage, indexes, and scalar writebacks.
The 9 scalar-writeback routines omit Fortran `intent` for scalar outputs.
[`lapack.pyf`](lapack.pyf) records them as `intent(inout)`, so f2py receives
typed NumPy 0-D arrays. PRIK returns the same writebacks directly.

The tests cover linear solves, factorizations, eigenproblems, singular values,
banded and packed layouts, workspaces, pivots, untouched storage, and `INFO`.
Equivalent decompositions are checked with mathematical invariants rather than
byte equality.

The committed [`lapack.pyf`](lapack.pyf) excludes `dgees` and `dgges` because
f2py 2.5.1 generates incomplete declarations for their selection callbacks.
Their tests exercise PRIK and SciPy, then independently verify the resulting
Schur decompositions.

## Sources and license

[`native/`](native/) owns the complete 2,062-file LAPACK source snapshot: 2,061
files from Netlib LAPACK 3.12.1 plus the project-local `dlamch.f`. The official
default build excludes the 130 files listed in
[`xblas_sources.txt`](xblas_sources.txt), which require the separately
distributed XBLAS library. The reusable library and PRIK wrapper therefore use
the remaining 1,932 sources. Two required build helpers from upstream
`INSTALL/` live under [`support/`](support/), and BLAS dependencies come from
[`../blas/native/`](../blas/native/). Installed LAPACK and BLAS libraries
provide support routines outside the copied default source set. The
audited upstream archive has SHA-256
`37b00c90947488521f475b5a187fff4da4a5cfe61b525efcacf7a97f39a45ec6`.
See the [Reference LAPACK site](https://www.netlib.org/lapack/) and its
[three-clause BSD-style license](https://www.netlib.org/lapack/LICENSE.txt).
