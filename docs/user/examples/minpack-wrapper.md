---
title: Build and Validate MINPACK with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: fftpack-wrapper.md, ../guide/arrays.md, ../guide/callbacks.md
status: maintained
publication: reviewed
---

# Build and Validate MINPACK with PRIK

This example takes the checked-in
[fortran-lang/minpack](https://github.com/fortran-lang/minpack) source and
builds an importable Python extension containing all 22 public MINPACK
procedures.

The example solves known nonlinear and least-squares problems and compares the
results with SciPy and direct linear-algebra checks.

### What this example shows

- Wrap a complete numerical solver library as one Python extension.
- Pass NumPy arrays and ordinary Python functions to MINPACK routines.
- Check root-finding, least-squares, Jacobian, and factorization results.

You should already be comfortable with NumPy arrays, Python callables, and
building a local Fortran extension.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| MINPACK | [fortran-lang/minpack commit `c0b5aea`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy | 1.18.0 |
| Fortran compiler | GNU Fortran 13 in CI; a compatible `gfortran` works locally |

The repository owns the checked-in source snapshot under
`examples/minpack/native/`, so the example does not download code during its
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
[`examples/minpack/`](../../../examples/minpack/).

---

## 2. Build the PRIK wrapper

MINPACK keeps its public declarations and implementations in one source file,
so one command can generate the wrapper and compile the library:

<!-- prik-doc-source: examples/minpack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export MINPACK_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$MINPACK_BUILD_ROOT/prik/generated"
cd "$MINPACK_BUILD_ROOT/prik"

python3 -m prik "$EXAMPLE_WORKSPACE/examples/minpack/native/minpack.f90" \
  --out prik_reference_minpack \
  --out-dir "$MINPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

The example uses `-O0` so the tests focus on correct results. PRIK compiles the
native source and generated bridge into one extension.

For normal use, source the convenience entrypoint:

```bash
source examples/minpack/build_all.sh
```

It builds the extension and exports its directory on `PYTHONPATH` for the
current shell.

---

## 3. Use the generated Python API

MINPACK routines keep their documented argument order, including work arrays
and status values. Pass NumPy arrays with the generated dtype, shape, and
layout. Solver callbacks are ordinary Python functions with the generated
callback signature.

---

## 4. Run the complete test suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/minpack/tests
```

The tests cover all 22 public procedures:

| Family | Procedures |
| --- | ---: |
| Diagnostics and finite differences | 4 |
| Hybrid nonlinear solvers | 4 |
| Levenberg-Marquardt solvers | 6 |
| Factorization and update helpers | 8 |
| **Total** | **22** |

Each procedure is called with representative data and checked against SciPy, a
known solution, or a direct linear-algebra result.

---

## 5. See how results are validated

For example, `hybrd1` can solve the two-variable equation
`x - [1, -2] = 0`. MINPACK calls the Python function whenever it needs the
current residual:

```python
import numpy as np
from prik_reference_minpack import minpack_module as minpack

target = np.array([1.0, -2.0], dtype=np.float64)


def residual(_count, x, fvec, _iflag):
    fvec[:] = x - target


x = np.array([4.0, 4.0], dtype=np.float64)
fvec = np.empty(2, dtype=np.float64)
info = minpack.hybrd1(
    residual,
    np.int32(2),
    x,
    fvec,
    np.float64(1.0e-12),
    np.empty(19, dtype=np.float64),
    np.int32(19),
)

assert info == np.int32(1)
np.testing.assert_allclose(x, target, atol=1.0e-10)
np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)
```

The complete suite applies the same pattern to root-finding and least-squares
solvers, then compares their solutions with SciPy.

---

## 6. Run focused examples

After building the extension, run a family or one routine:

```bash
python3 -m pytest -q examples/minpack/tests/test_solvers.py
python3 -m pytest -q \
  examples/minpack/tests/test_solvers.py::test_hybrd1
```

- Callback-driven nonlinear solvers →
  [`test_solvers.py`](../../../examples/minpack/tests/test_solvers.py)
- Diagnostics and finite-difference helpers →
  [`test_diagnostics.py`](../../../examples/minpack/tests/test_diagnostics.py)
- Factorization and update helpers →
  [`test_linear_algebra.py`](../../../examples/minpack/tests/test_linear_algebra.py)
- Public routine list →
  [`routine_inventory.py`](../../../examples/minpack/routine_inventory.py)
- Routine coverage check →
  [`test_routine_coverage.py`](../../../examples/minpack/tests/test_routine_coverage.py)
- Copyable project instructions →
  [`examples/minpack/README.md`](../../../examples/minpack/README.md)

---

## Troubleshooting

- Confirm that `gfortran` is available on `PATH`.
- Use `source examples/minpack/build_all.sh`; executing it in a child shell
  does not preserve the exported `PYTHONPATH`.
- Start with one helper or solver test and add `-vv -s` when diagnosing a
  callback or generated-wrapper failure.

---

## Source provenance

[`examples/minpack/native/minpack.f90`](../../../examples/minpack/native/minpack.f90)
matches the upstream `src/minpack.f90` at
[fortran-lang/minpack commit `c0b5aea9fcd2b83865af921a7a7e881904f8d3c2`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2).

See the [upstream repository](https://github.com/fortran-lang/minpack), its
[API documentation](https://fortran-lang.github.io/minpack/), and its license
before redistributing the bundled native source.
