# Wrap Reference BLAS with PRIK

This copyable example builds the complete Reference BLAS once, then links both
PRIK and NumPy f2py wrappers to the same native library. Its 155 named tests
compare both wrappers with small independent formulas, storage checks, and each
other.

All 155 routines are exported and validated through both wrappers, with no
unsupported or skipped routines.

## Requirements

Install GNU Fortran and the Python build tools:

```console
python3 -m pip install "numpy==2.5.1" "meson==1.11.2" "ninja==1.13.0" pytest
```

Run every command from the directory that contains `examples/`.

## Build both wrappers

`build_all.sh` runs these two scripts:

<!-- prik-doc-source: examples/blas/build_prik.sh -->
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

python -m prik "$EXAMPLE_WORKSPACE/examples/blas/native" \
  --out prik_reference_blas \
  --out-dir "$BLAS_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --no-compile-input-sources \
  --native-objects "$BLAS_SHARED_LIBRARY" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

<!-- prik-doc-source: examples/blas/build_f2py.sh -->
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
  "$EXAMPLE_WORKSPACE/examples/blas/blas.pyf" \
  "-L$(dirname "$BLAS_SHARED_LIBRARY")" \
  -lprik_full_blas \
  --build-dir "$BLAS_F2PY_ROOT/generated" \
  --f77flags=-O0 \
  --f90flags=-O0 \
  --opt=-O0
```

Build and validate the example:

```bash
source examples/blas/build_all.sh
python3 -m pytest -q examples/blas/tests
```

You can also run one family or routine:

```bash
python3 -m pytest -q examples/blas/tests/test_level1_real.py
python3 -m pytest -q \
  examples/blas/tests/test_level1_real.py::test_daxpy
python3 -m pytest -q examples/blas/tests -k dgemm
```

## What the comparison shows

PRIK preserves the native BLAS argument order and returns visible scalar
writebacks. f2py compiles the committed reviewed [`blas.pyf`](blas.pyf) and
links the existing shared library.

The 6 rotation routines do not declare Fortran `intent` for scalar writebacks.
The reviewed signature records their `intent(inout)` declarations and the
comparison passes typed NumPy 0-D arrays. PRIK needs neither: it returns those
scalar writebacks directly.

The tests cover positive and negative increments, leading-dimension padding,
packed and banded layouts, triangular and Hermitian storage, native one-based
indexes, input preservation, and dtype-aware numerical tolerances. The
independent oracle remains visible beside every wrapper call.

## Sources and license

[`native/`](native/) contains the 155 files from `BLAS/SRC/` in Netlib LAPACK
3.12.1. The audited archive has SHA-256
`37b00c90947488521f475b5a187fff4da4a5cfe61b525efcacf7a97f39a45ec6`.
See the [Netlib BLAS FAQ](https://www.netlib.org/blas/faq.html#1_5) and the
[LAPACK license](https://www.netlib.org/lapack/LICENSE.txt) before
redistributing the native sources.
