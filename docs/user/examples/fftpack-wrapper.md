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
produces an importable Python extension with all 31 public procedures from the
`fftpack` module. The maintained suite gives every procedure an explicit
numerical test against NumPy, SciPy, or the transform's documented invariant.

The result is one module, `prik_reference_fftpack`, with a reviewed public
boundary and no f2py comparison wrapper. For this library, independent
mathematical references provide clearer evidence than comparing two wrappers.

### Why this example exists

- It demonstrates PRIK on a modern multi-source library built from a parent
  module, submodules, and legacy computational kernels.
- It keeps `fftpack.f90` authoritative when an implementation file uses a
  different internal storage spelling, as happens for `zfftf`.
- It verifies transform values, normalization, frequency ordering, mutation,
  dtype, and shape instead of stopping after a successful import.

You should already be comfortable with NumPy arrays and building a local
Fortran extension.

---

## Versions used by the maintained example

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

The copyable script separates wrapper-facing sources from link-only
implementations:

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

`-O0` keeps this a correctness example and avoids optimization-dependent
claims. Every source is compiled once: the positional files contribute
semantic declarations and native objects, while `--native-fortran-sources`
contribute native objects without becoming Python API inputs.

For normal use, source the convenience entrypoint:

```bash
source examples/fftpack/build_all.sh
```

It builds the extension and exports its directory on `PYTHONPATH` for the
current shell.

---

## 3. Understand the public source boundary

The source groups have deliberately different responsibilities:

| Source group | Responsibility |
| --- | --- |
| `rk.f90` | Supplies the shared real kind used by the public declarations. |
| `fftpack.f90` | Declares the authoritative public module API. |
| `fftpack_*.f90` | Implements parent-module procedures in Fortran submodules. |
| Remaining `.f90` files | Provide legacy kernels as hidden compile-and-link inputs. |

The distinction matters for `zfftf`. Its public declaration accepts a normal
`complex128` array, while the legacy implementation uses a real array as an
internal storage view. Only the declaration in `fftpack.f90` defines the
Python contract; callers never reinterpret a complex array as a float buffer.

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

## 4. Run the complete correctness suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/fftpack/tests
```

The reviewed inventory covers the complete generated module surface:

| Family | Procedures |
| --- | ---: |
| Complex work-array transforms | 3 |
| Real work-array transforms | 6 |
| Cosine and sine work-array transforms | 7 |
| High-level Fourier transforms | 4 |
| High-level cosine transforms | 7 |
| Frequency and spectrum ordering | 4 |
| **Total** | **31** |

Each procedure has a named invocation test. The inventory guard also compares
the expected names with `dir(fftpack)`, so a missing or unexpected generated
entry point fails the suite.

---

## 5. Validate behaviour, not just compilation

The primary evidence is:

```text
PRIK result == independent NumPy, SciPy, or mathematical result
```

Tests also verify in-place mutation, dtype, shape, transform normalization,
and frequency ordering. This `zfftf` test is taken verbatim from the runnable
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

## 6. Explore the maintained example

Run a focused family or one procedure while developing:

```bash
python3 -m pytest -q examples/fftpack/tests/test_transforms.py
python3 -m pytest -q \
  examples/fftpack/tests/test_transforms.py::test_zfftf
python3 -m pytest -q examples/fftpack/tests -k fftshift
```

- Complete numerical examples →
  [`test_transforms.py`](../../../examples/fftpack/tests/test_transforms.py)
- Authoritative public classification →
  [`routine_inventory.py`](../../../examples/fftpack/routine_inventory.py)
- Fail-closed coverage guard →
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
- Keep performance experiments separate from this correctness project. The
  maintained suite uses small deterministic inputs and makes no benchmark
  claims.

---

## Source provenance

The `.f90` files under
[`examples/fftpack/native/`](../../../examples/fftpack/native/) match the
upstream `src/` files at
[fortran-lang/fftpack commit `0fffe7c05a918363a7cc12ae138a695afd115f36`](https://github.com/fortran-lang/fftpack/tree/0fffe7c05a918363a7cc12ae138a695afd115f36).

See the [upstream repository](https://github.com/fortran-lang/fftpack), its
[API documentation](https://fortran-lang.github.io/fftpack/), and its license
before redistributing the bundled native sources.
