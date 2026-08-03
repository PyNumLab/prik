# Wrap Reference LAPACK with PRIK

This copyable example builds the complete Reference LAPACK once and links PRIK
and NumPy f2py wrappers to the same native library. It validates 127 reviewed
double-precision routines with SciPy and independent residuals,
reconstructions, and storage checks.

PRIK wraps all 2,064 discovered procedures. The comparison suite selects
the 127 `float64` routines exposed by SciPy 1.18.0; raw f2py supports 125 of
those source interfaces. All 127 selected routines have explicit correctness
tests, with no unsupported or skipped routines.

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

Run every command from the directory that contains `examples/`.

## Build both wrappers

The native builder compiles the bundled LAPACK and BLAS sources once and links
the development libraries for companion support symbols. Internal support
objects are included once in the shared library, while their compiler-specific
`.mod` files are retained for generated wrappers.

`build_all.sh` runs these two scripts:

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

PRIK keeps the module namespaces discovered from the complete sources. The
committed reviewed [`lapack.pyf`](lapack.pyf) exposes `la_constants`, and f2py
compiles its generated wrapper with the retained module directory.

No LAPACK implementation or support object is compiled twice.

Build and validate the example:

```bash
source examples/lapack/build_all.sh
python3 -m pytest -q examples/lapack/tests
```

You can also run one family or routine:

```bash
python3 -m pytest -q examples/lapack/tests/test_linear_general.py
python3 -m pytest -q \
  examples/lapack/tests/test_linear_general.py::test_dgesv_solves_general_system
python3 -m pytest -q examples/lapack/tests -k dgesvd
```

## What the comparison shows

PRIK preserves native argument order, storage, indexes, and scalar writebacks.
The 9 scalar-writeback routines omit Fortran `intent` for scalar outputs.
Their reviewed signature declarations use `intent(inout)` and typed NumPy 0-D
arrays, while PRIK returns those values directly.

The tests cover linear solves, factorizations, eigenproblems, singular values,
banded and packed layouts, workspaces, pivots, untouched storage, and `INFO`.
Equivalent decompositions are checked with mathematical invariants rather than
byte equality.

`dgees` and `dgges` use unannotated selection callbacks that raw f2py 2.5.1
cannot generate safely. They remain covered through PRIK, SciPy, and independent
Schur reconstruction.

## Sources and license

[`native/`](native/) owns 2,062 LAPACK implementation sources: 2,061 from
Netlib LAPACK 3.12.1 plus the project-local `dlamch.f`. BLAS dependencies come
from [`../blas/native/`](../blas/native/) and are not duplicated here. The
audited upstream archive has SHA-256
`37b00c90947488521f475b5a187fff4da4a5cfe61b525efcacf7a97f39a45ec6`.
See the [Reference LAPACK site](https://www.netlib.org/lapack/) and its
[three-clause BSD-style license](https://www.netlib.org/lapack/LICENSE.txt).
