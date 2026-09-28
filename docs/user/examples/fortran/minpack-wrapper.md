---
title: Build and Validate MINPACK with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: fftpack-wrapper.md, ../../guide/arrays.md, ../../guide/callbacks.md
status: maintained
publication: reviewed
---

# Build and Validate MINPACK with PRIK

This example turns [fortran-lang/minpack](https://github.com/fortran-lang/minpack),
the modern Fortran MINPACK, into one Python extension with all 22 public
procedures. MINPACK's solvers call back into Python for each residual, so you
write your problem as an ordinary Python function. The suite checks every
procedure against exact solutions and direct linear-algebra identities.

### What you get

One extension, `prik_reference_minpack`, whose Fortran module `minpack_module`
holds all 22 procedures:

| Family | Procedures |
| --- | --- |
| Hybrid nonlinear solvers (root finding) | `hybrd`, `hybrd1`, `hybrj`, `hybrj1` |
| Levenberg-Marquardt solvers (least squares) | `lmder`, `lmder1`, `lmdif`, `lmdif1`, `lmstr`, `lmstr1` |
| Diagnostics and finite differences | `chkder`, `enorm`, `fdjac1`, `fdjac2` |
| Factorization and update helpers | `dogleg`, `lmpar`, `qform`, `qrfac`, `qrsolv`, `r1mpyq`, `r1updt`, `rwupdt` |

---

## Quick start

From a PRIK checkout with PRIK installed and GNU Fortran on `PATH` (see
[Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/minpack/build_all.sh
python3 -m pytest -q examples/fortran/minpack/tests
```

The first command builds the extension and puts it on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
tests.

After this, the solvers import in the same shell:

```python
from prik_reference_minpack import minpack_module as minpack
```

[Use the generated API](#use-the-generated-api) shows complete calls.

---

## Key files

Everything lives under [`examples/fortran/minpack/`](../../../../examples/fortran/minpack/):

| File | What it does |
| --- | --- |
| [`native/minpack.f90`](../../../../examples/fortran/minpack/native/minpack.f90) | The MINPACK source: one file holding the public module and its implementation. |
| [`build_prik.sh`](../../../../examples/fortran/minpack/build_prik.sh) | Builds the extension with one PRIK command. |
| [`build_all.sh`](../../../../examples/fortran/minpack/build_all.sh) | Runs `build_prik.sh` and adds the extension to `PYTHONPATH`. |
| [`routine_inventory.py`](../../../../examples/fortran/minpack/routine_inventory.py) | The list of the 22 procedures, grouped by family. |
| [`tests/test_solvers.py`](../../../../examples/fortran/minpack/tests/test_solvers.py) | The root-finding and least-squares solvers, with Python callbacks. |
| [`tests/test_diagnostics.py`](../../../../examples/fortran/minpack/tests/test_diagnostics.py) | The diagnostics and finite-difference helpers. |
| [`tests/test_linear_algebra.py`](../../../../examples/fortran/minpack/tests/test_linear_algebra.py) | The factorization and update helpers. |
| [`tests/test_routine_coverage.py`](../../../../examples/fortran/minpack/tests/test_routine_coverage.py) | Checks that the inventory, the generated exports, and the tests stay in sync. |

---

## How the build works

MINPACK keeps its public declarations and implementations in one source file,
so one PRIK command generates the wrapper and compiles MINPACK into the same
extension. There is no separate native library:

```text
native/minpack.f90 ──prik──> wrapper + MINPACK, compiled together ──> prik_reference_minpack
```

`build_prik.sh` runs that command:

<!-- prik-doc-source: examples/fortran/minpack/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export MINPACK_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$MINPACK_BUILD_ROOT/prik/generated"
cd "$MINPACK_BUILD_ROOT/prik"

python3 -m prik "$EXAMPLE_WORKSPACE/examples/fortran/minpack/native/minpack.f90" \
  --out prik_reference_minpack \
  --out-dir "$MINPACK_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --jobs 8 \
  --wrapper-fortran-flags="-O0 -g0" \
  --wrapper-c-flags="-O0 -g0"
```

The example uses `-O0` so the tests focus on correct results rather than
optimization-dependent ones. Everything is written to the temporary
`MINPACK_BUILD_ROOT` directory, not to the repository.

---

## Use the generated API

MINPACK routines keep their documented Fortran argument order, including work
arrays and their lengths. The callback receives the problem sizes, the current
point, and an output array it fills with the residuals. Each solver returns
MINPACK's `info` status and updates `x` in place.

**Root finding.** `hybrd1` finds where the circle x² + y² = 4 meets the curve
y = x³:

```python
import numpy as np
from prik_reference_minpack import minpack_module as minpack

def equations(n, x, fvec, iflag):
    fvec[0] = x[0] ** 2 + x[1] ** 2 - 4.0
    fvec[1] = x[1] - x[0] ** 3

x = np.array([1.0, 1.0])
fvec = np.empty(2)
info = minpack.hybrd1(equations, np.int32(2), x, fvec, np.float64(1e-10), np.empty(19), np.int32(19))
print(info, x.round(6))  # 1 [1.174222 1.619013]
```

The work array needs at least n(3n + 13)/2 entries, 19 for two unknowns.
`info == 1` means MINPACK estimates the relative error in `x` is within the
tolerance.

**Least squares.** `lmdif1` fits y = a·exp(b·t) to five points:

```python
t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
y = 2.0 * np.exp(-0.5 * t)

def residuals(m, n, p, fvec, iflag):
    fvec[:] = p[0] * np.exp(p[1] * t) - y

p = np.array([1.0, 0.0])
fvec = np.empty(5)
info = minpack.lmdif1(residuals, np.int32(5), np.int32(2), p, fvec, np.float64(1e-10),
                      np.empty(2, dtype=np.int32), np.empty(25), np.int32(25))
print(info, p.round(6))  # 2 [ 2.  -0.5]
```

Here `m = 5` residuals fit `n = 2` parameters; the work array needs at least
m·n + 5n + m entries, 25 in this case. `lmdif1` estimates the Jacobian by
finite differences; `lmder1` and `hybrj1` take a callback that also supplies
it.

---

## How results are validated

Each procedure is called with representative data and checked against a known
solution or a direct linear-algebra result. The runnable `hybrd1` test solves
`x - [1, -2] = 0`; its `minpack` fixture supplies `minpack_module`:

<!-- prik-doc-source: examples/fortran/minpack/tests/test_solvers.py::test_hybrd1 -->
```python
def test_hybrd1(minpack):
    target = np.array([1.0, -2.0], dtype=np.float64)
    callback_calls = 0

    def residual(_count, x, fvec, _iflag):
        nonlocal callback_calls
        callback_calls += 1
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
    assert callback_calls > 0
    np.testing.assert_allclose(x, target, atol=1.0e-10)
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)
```

The complete suite applies the same pattern to the other root-finding and
least-squares solvers, and checks the helpers with algebraic invariants. It
also verifies callback counts, caller-array writebacks, and Fortran-order
matrices.

---

## Run the tests

Run the complete suite, one family, or one routine:

```bash
python3 -m pytest -q examples/fortran/minpack/tests
python3 -m pytest -q examples/fortran/minpack/tests/test_solvers.py
python3 -m pytest -q \
  examples/fortran/minpack/tests/test_solvers.py::test_hybrd1
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
python3 -m pip install -e ".[qa]" "numpy==2.5.1"
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
| MINPACK | [fortran-lang/minpack commit `c0b5aea`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
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
- Use `source examples/fortran/minpack/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- `AttributeError` on a routine such as `hybrd1`: import it from
  `prik_reference_minpack.minpack_module`, not from the extension's top level.
- Start with one helper or solver test and add `-vv -s` when diagnosing a
  callback or generated-wrapper failure.

---

## Source provenance

[`examples/fortran/minpack/native/minpack.f90`](../../../../examples/fortran/minpack/native/minpack.f90)
matches the upstream `src/minpack.f90` at
[fortran-lang/minpack commit `c0b5aea9fcd2b83865af921a7a7e881904f8d3c2`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2).

See the [upstream repository](https://github.com/fortran-lang/minpack), its
[API documentation](https://fortran-lang.github.io/minpack/), and its license
before redistributing the bundled native source.
