---
title: Build and Validate FFTPACK with PRIK
audience: users, advanced users
prerequisites: arrays, packaging
related: minpack-wrapper.md, ../guide/arrays.md
status: maintained
publication: reviewed
---

# Build and Validate FFTPACK with PRIK

This example takes the checked-in
[fortran-lang/fftpack](https://github.com/fortran-lang/fftpack) sources and
builds an importable Python extension containing all 31 public procedures from
the `fftpack` module.

The example compares Fourier, cosine, sine, frequency, and spectrum operations
with NumPy, SciPy, or known transform properties.

### What this example shows

- Wrap a complete multi-file Fortran library as one Python extension.
- Call both low-level and high-level transforms with NumPy arrays.
- Check transform values, normalization, frequency ordering, dtype, and shape.

You should already be comfortable with NumPy arrays and building a local
Fortran extension.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| FFTPACK | [fortran-lang/fftpack commit `0fffe7c`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy | 1.18.0 |
| Fortran compiler | GNU Fortran 13 in CI; a compatible `gfortran` works locally |

The repository owns the checked-in source snapshot under
`examples/fftpack/native/`, so the example does not download code during its
build.

---

## 1. Prepare the repository and toolchain

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

All remaining commands run from the repository root with the virtual
environment active. The complete runnable project lives under
[`examples/fftpack/`](../../../examples/fftpack/).

---

## 2. Build the PRIK wrapper

FFTPACK uses public module declarations, submodule implementations, and
link-only computational kernels. The build command gives each source the role
it needs:

<!-- prik-doc-source: examples/fftpack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export FFTPACK_BUILD_ROOT="$(mktemp -d)"
export FFTPACK_NATIVE_DIR="$EXAMPLE_WORKSPACE/examples/fftpack/native"

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

The example uses `-O0` so the tests focus on correct results. Every source is
compiled once: positional files define the Python-facing API, while
`--native-fortran-sources` adds implementation code without exposing it to
Python.

For normal use, source the convenience entrypoint:

```bash
source examples/fftpack/build_all.sh
```

It builds the extension and exports its directory on `PYTHONPATH` for the
current shell.

---

## 3. Understand how sources define the API

The source groups have different roles:

| Source group | Responsibility |
| --- | --- |
| `rk.f90` | Defines the real kind used by the public API. |
| `fftpack.f90` | Declares the public FFTPACK module. |
| `fftpack_*.f90` | Implements its procedures in Fortran submodules. |
| Remaining `.f90` files | Supply linked computational kernels. |

The public declarations define the Python types. For example, `zfftf` accepts
an ordinary NumPy `complex128` array.

High-level transform results that are allocatable in Fortran use PRIK's
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

Fixed-shape frequency and shift results are returned directly as NumPy arrays.

---

## 4. Run the complete test suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/fftpack/tests
```

The tests cover all 31 public procedures:

| Family | Procedures |
| --- | ---: |
| Complex work-array transforms | 3 |
| Real work-array transforms | 6 |
| Cosine and sine work-array transforms | 7 |
| High-level Fourier transforms | 4 |
| High-level cosine transforms | 7 |
| Frequency and spectrum ordering | 4 |
| **Total** | **31** |

Each procedure is called with representative data and checked against NumPy,
SciPy, or a known transform property.

---

## 5. See how results are validated

The suite compares transform results with independent NumPy or SciPy results
and also checks in-place mutation, dtype, shape, normalization, and frequency
ordering. For example, this `zfftf` test comes directly from the runnable
suite:

<!-- prik-doc-source: examples/fftpack/tests/test_transforms.py::test_zfftf -->
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

## 6. Run focused examples

After building the extension, run a family or one procedure:

```bash
python3 -m pytest -q examples/fftpack/tests/test_transforms.py
python3 -m pytest -q \
  examples/fftpack/tests/test_transforms.py::test_zfftf
python3 -m pytest -q examples/fftpack/tests -k fftshift
```

- Complete numerical examples →
  [`test_transforms.py`](../../../examples/fftpack/tests/test_transforms.py)
- Public routine list →
  [`routine_inventory.py`](../../../examples/fftpack/routine_inventory.py)
- Routine coverage check →
  [`test_routine_coverage.py`](../../../examples/fftpack/tests/test_routine_coverage.py)
- Copyable project instructions →
  [`examples/fftpack/README.md`](../../../examples/fftpack/README.md)

---

## Troubleshooting

- Confirm that `gfortran` is available on `PATH`.
- Use `source examples/fftpack/build_all.sh`; executing it in a child shell
  does not preserve the exported `PYTHONPATH`.
- Run one failing procedure with `-vv -s` to retain its compiler and wrapper
  diagnostics.

---

## Source provenance

The `.f90` files under
[`examples/fftpack/native/`](../../../examples/fftpack/native/) match the
upstream `src/` files at
[fortran-lang/fftpack commit `0fffe7c05a918363a7cc12ae138a695afd115f36`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36).

See the [upstream repository](https://github.com/fortran-lang/fftpack), its
[API documentation](https://fortran-lang.github.io/fftpack/), and its license
before redistributing the bundled native sources.
