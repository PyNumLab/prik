---
title: Build and Validate FFTPACK with PRIK
audience: users, advanced users
prerequisites: arrays, packaging
related: minpack-wrapper.md, ../../guide/arrays.md
status: maintained
publication: reviewed
---

# Build and Validate FFTPACK with PRIK

This example turns [fortran-lang/fftpack](https://github.com/fortran-lang/fftpack),
the modern Fortran FFTPACK, into one Python extension with all 31 public
procedures of its `fftpack` module. It checks every procedure against NumPy,
SciPy, or a known transform property.

### What you get

One extension, `prik_reference_fftpack`, whose `fftpack` namespace holds:

| Family | Procedures |
| --- | --- |
| High-level Fourier transforms | `fft`, `ifft`, `rfft`, `irfft` |
| High-level cosine transforms | `dct`, `idct`, `dct_t1i`, `dct_t1`, `dct_t23i`, `dct_t2`, `dct_t3` |
| Frequency and spectrum ordering | `fftfreq`, `rfftfreq`, `fftshift`, `ifftshift` |
| Complex work-array transforms | `zffti`, `zfftf`, `zfftb` |
| Real work-array transforms | `dffti`, `dfftf`, `dfftb`, `dzffti`, `dzfftf`, `dzfftb` |
| Cosine and sine work-array transforms | `dcosqi`, `dcosqf`, `dcosqb`, `dcosti`, `dcost`, `dsinti`, `dsint` |

---

## Quick start

From a PRIK checkout with PRIK installed, GNU Fortran on `PATH`, and the pinned
NumPy and SciPy (see [Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/fftpack/build_all.sh
python3 -m pytest -q examples/fortran/fftpack/tests
```

The first command builds the extension and puts it on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
tests.

After this, the transforms import in the same shell:

```python
import prik_reference_fftpack

fftpack = prik_reference_fftpack.fftpack
```

[Use the generated API](#use-the-generated-api) shows complete calls.

---

## Key files

Everything lives under [`examples/fortran/fftpack/`](../../../../examples/fortran/fftpack/):

| File | What it does |
| --- | --- |
| [`native/fftpack.f90`](../../../../examples/fortran/fftpack/native/fftpack.f90) | Declares the public `fftpack` module, which defines the Python API. |
| [`native/rk.f90`](../../../../examples/fortran/fftpack/native/rk.f90) | Defines the real kind used by that API. |
| `native/fftpack_*.f90` | Implement the module's procedures as Fortran submodules. |
| The other files in [`native/`](../../../../examples/fortran/fftpack/native/) | The computational kernels, compiled and linked but not exposed to Python. |
| [`build_prik.sh`](../../../../examples/fortran/fftpack/build_prik.sh) | Builds the extension with one PRIK command that gives each source its role. |
| [`build_all.sh`](../../../../examples/fortran/fftpack/build_all.sh) | Runs `build_prik.sh` and adds the extension to `PYTHONPATH`. |
| [`routine_inventory.py`](../../../../examples/fortran/fftpack/routine_inventory.py) | The list of the 31 procedures, grouped by family. |
| [`tests/test_transforms.py`](../../../../examples/fortran/fftpack/tests/test_transforms.py) | One test per procedure, checked against NumPy, SciPy, or a transform property. |
| [`tests/helpers.py`](../../../../examples/fortran/fftpack/tests/helpers.py) | Helpers such as converting between FFTPACK's and NumPy's real-FFT layouts. |
| [`tests/test_routine_coverage.py`](../../../../examples/fortran/fftpack/tests/test_routine_coverage.py) | Checks that the inventory, the generated exports, and the tests stay in sync. |

---

## How the build works

FFTPACK splits into public declarations, submodule implementations, and
low-level kernels. One PRIK command compiles all of them once, but only the
first group shapes the Python API:

```text
rk.f90, fftpack.f90, fftpack_*.f90 ── the Python API ──┐
                                                       ├──prik──> prik_reference_fftpack
the other .f90 kernels ── --native-fortran-sources ────┘
```

| Source group | Passed as | Role |
| --- | --- | --- |
| `rk.f90`, `fftpack.f90`, `fftpack_*.f90` | Positional sources | Define the Python-facing API and its implementation. |
| The remaining `.f90` kernels | `--native-fortran-sources` | Satisfy native dependencies without adding their storage-level signatures to the Python API. |

`build_prik.sh` runs that command:

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

The example uses `-O0` so the tests focus on correct results. Everything is
written to the temporary `FFTPACK_BUILD_ROOT` directory, not to the
repository.

---

## Use the generated API

High-level transforms whose Fortran results are allocatable return PRIK's
`AllocatableArray` handle. Read the NumPy view with `to_numpy()` and release
the native allocation with `close()`:

```python
import numpy as np
import prik_reference_fftpack

fftpack = prik_reference_fftpack.fftpack
result = fftpack.fft(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128))
try:
    np.testing.assert_allclose(result.to_numpy(), np.ones(4))
finally:
    result.close()
```

Fixed-shape frequency and shift results, such as `fftfreq`, return NumPy arrays
directly. The work-array routines (`zffti`, `zfftf`, …) keep FFTPACK's
initialize-then-transform pattern and update the caller's array in place; see
the `zfftf` test [below](#how-results-are-validated).

**FFTPACK's conventions differ from `numpy.fft`.** The same inputs give:

| Call | FFTPACK | `numpy.fft` |
| --- | --- | --- |
| `fftfreq(4)` | `[0, 1, -2, -1]`: integer frequency indices | `[0, 0.25, -0.5, -0.25]`: the indices divided by `n` |
| `ifft(fft(x))` | `n * x`: the inverse is not normalized | `x` |
| `rfft([1, 2, 3, 4])` | `[10, -2, 2, -2]`: packed real and imaginary parts | `[10, -2+2j, -2]`: complex values |

Divide an `ifft` result by `n` to recover the input. The tests convert the
packed real layout with a helper in `tests/helpers.py`.

---

## How results are validated

NumPy is the reference for the Fourier transforms, shifts, and frequency
ordering; SciPy is the reference for the cosine and sine families. The suite
also checks normalization, in-place mutation, preservation of high-level
inputs, dtype, shape, frequency ordering, and release of allocatable results.
For example, this `zfftf` test comes directly from the runnable suite:

<!-- prik-doc-source: examples/fortran/fftpack/tests/test_transforms.py::test_zfftf -->
```python
def test_zfftf(fftpack):
    values = np.array([1.0 + 2.0j, -2.0 + 1.0j, 4.0 - 3.0j, 3.0 + 0.5j, -1.0j], dtype=np.complex128)
    expected = np.fft.fft(values)
    wsave = np.empty(4 * values.size + 15, dtype=np.float64)
    fftpack.zffti(np.int32(values.size), wsave)

    fftpack.zfftf(np.int32(values.size), values, wsave)

    np.testing.assert_allclose(values, expected, rtol=0.0, atol=1.0e-12)
```

The call uses the public complex-array signature, mutates the caller's array
in place, and compares the result with NumPy's independently implemented FFT.

---

## Run the tests

Run the complete suite, one procedure, or every test that mentions a name:

```bash
python3 -m pytest -q examples/fortran/fftpack/tests
python3 -m pytest -q \
  examples/fortran/fftpack/tests/test_transforms.py::test_zfftf
python3 -m pytest -q examples/fortran/fftpack/tests -k fftshift
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
| FFTPACK | [fortran-lang/fftpack commit `0fffe7c`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36) |
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
- Use `source examples/fortran/fftpack/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- A result off by a factor of `n`, or in an unexpected order: see the
  [convention table](#use-the-generated-api) above.
- Run one failing procedure with `-vv -s` to see its compiler and wrapper
  diagnostics.

---

## Source provenance

The `.f90` files under
[`examples/fortran/fftpack/native/`](../../../../examples/fortran/fftpack/native/) match the
upstream `src/` files at
[fortran-lang/fftpack commit `0fffe7c05a918363a7cc12ae138a695afd115f36`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36).

See the [upstream repository](https://github.com/fortran-lang/fftpack), its
[API documentation](https://fortran-lang.github.io/fftpack/), and its license
before redistributing the bundled native sources.
