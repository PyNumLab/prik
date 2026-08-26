# Wrap FFTPACK with PRIK

Build the bundled modern
[fortran-lang/fftpack](https://github.com/fortran-lang/fftpack) source with
PRIK and validate all 31 public procedures in its `fftpack` module against
NumPy, SciPy, or explicit transform invariants.

No f2py comparison wrapper is used: independent mathematical results are the
primary oracle. The inventory has no unsupported or skipped procedures.

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

Run the remaining commands from the PRIK repository root.

## Quick start

Build the extension and run the complete test suite:

```bash
source examples/fortran/fftpack/build_all.sh
python3 -m pytest -q examples/fortran/fftpack/tests
```

Use `source` so the build directory exported by `build_all.sh` remains on
`PYTHONPATH` for pytest.

## How the build works

`fftpack.f90` is the authoritative API. `rk.f90` supplies its kind parameter,
and `fftpack_*.f90` supplies its submodule implementations. The remaining
legacy kernels are compiled through `--native-fortran-sources`, so they satisfy
native dependencies without contributing storage-level signatures to the
Python API.

Every source is compiled once and no alternative wrapper is created.

### Build the PRIK wrapper

<!-- prik-doc-source: examples/fortran/fftpack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export FFTPACK_BUILD_ROOT="$(mktemp -d)"
export FFTPACK_NATIVE_DIR="$EXAMPLE_WORKSPACE/examples/fortran/fftpack/native"

FFTPACK_PUBLIC_SOURCES=(
  "$FFTPACK_NATIVE_DIR/rk.f90"
  "$FFTPACK_NATIVE_DIR/fftpack.f90"
  "$FFTPACK_NATIVE_DIR"/fftpack_*.f90
)
FFTPACK_LINK_ONLY_SOURCES=()
for source in "$FFTPACK_NATIVE_DIR"/*.f90; do
  case "${source##*/}" in
    rk.f90|fftpack.f90|fftpack_*.f90) continue ;;
  esac
  FFTPACK_LINK_ONLY_SOURCES+=("$source")
done

mkdir -p "$FFTPACK_BUILD_ROOT/prik/generated"
cd "$FFTPACK_BUILD_ROOT/prik"

python3 -m prik "${FFTPACK_PUBLIC_SOURCES[@]}" \
  --native-fortran-sources "${FFTPACK_LINK_ONLY_SOURCES[@]}" \
  --out prik_reference_fftpack \
  --out-dir "$FFTPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

## Run focused tests

After the quick-start build, run one procedure or family:

```bash
python3 -m pytest -q examples/fortran/fftpack/tests/test_transforms.py
python3 -m pytest -q \
  examples/fortran/fftpack/tests/test_transforms.py::test_zfftf
python3 -m pytest -q examples/fortran/fftpack/tests -k dct
```

## What is validated

The suite covers all 31 public work-array, FFT, DCT, frequency, and shift
procedures. NumPy is the oracle for Fourier transforms, shifts, and frequency
ordering; SciPy is the oracle for cosine and sine families. The tests verify
normalization, in-place mutation, high-level input preservation, dtype, shape,
and allocatable-result cleanup.

The public routine list stays in sync with the generated exports, and every
public procedure is exercised.

## Sources and license

The `.f90` files under [`native/`](native/) match the upstream `src/` files at
[fortran-lang/fftpack commit `0fffe7c05a918363a7cc12ae138a695afd115f36`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36).
See the upstream repository, API documentation, and license before
redistributing the bundled native sources.
