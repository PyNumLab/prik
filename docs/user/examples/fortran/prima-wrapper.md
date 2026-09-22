---
title: Build and Validate PRIMA with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: ../../guide/callbacks.md, ../../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Build and Validate PRIMA with PRIK

Build the checked-in [libPRIMA](https://github.com/libprima/prima) Fortran
sources once, wrap five derivative-free solvers with PRIK, and try them from
Python. The example includes runnable numerical tests and an optional SciPy
comparison for COBYLA.

## 1. Prepare the repository and toolchain

You need Python, CMake, a C compiler, and GNU Fortran. The portability job
uses Python 3.12, NumPy 2.5.1, GCC/GNU Fortran 13, and SciPy 1.18.0 for the
optional comparison. A compatible local toolchain also works.

On Ubuntu, install the native tools:

```bash
sudo apt-get update
sudo apt-get install --yes cmake gcc gfortran
```

Clone PRIK and install its test dependencies in a virtual environment:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[qa]"
```

Run the remaining commands from the repository root in this same shell.

## 2. Build the library and Python extension

```bash
source examples/fortran/prima/build_all.sh
```

Source the script rather than executing it in a new shell: it leaves the built
extension on `PYTHONPATH` and records its temporary location in
`PRIMA_BUILD_ROOT`. CMake compiles the 55 native sources into `libprimaf.a`;
PRIK analyzes those sources, writes the selected `.pyi` contract, and links
its wrapper to that archive without recompiling PRIMA.

The public Python API has exactly these entries:

| Module | Solver |
| --- | --- |
| `bobyqa_mod` | `bobyqa` |
| `cobyla_mod` | `cobyla` |
| `lincoa_mod` | `lincoa` |
| `newuoa_mod` | `newuoa` |
| `uobyqa_mod` | `uobyqa` |

## 3. Solve a problem

Run this from the same shell. UOBYQA minimizes a two-variable quadratic whose
known minimum is at `(1, -2)`:

```bash
python3 - <<'PY'
import numpy as np
import prik_prima

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))

def objective(values, result):
    result[...] = (values[0] - 1.0) ** 2 + (values[1] + 2.0) ** 2

prik_prima.uobyqa_mod.uobyqa(objective, x, maxfun=np.int32(100))
np.testing.assert_allclose(x, [1.0, -2.0], atol=2e-3, rtol=0)
print(x)
PY
```

The callback writes the objective value into `result`; the solver updates `x`
in place. The assertion checks the result against the known minimum.

## 4. Run and adapt the tests

Run every selected solver and the callback checks:

```bash
python3 -m pytest -q examples/fortran/prima/tests
```

For a faster edit/test cycle, run one solver test:

```bash
python3 -m pytest -q examples/fortran/prima/tests/test_solvers.py::test_lincoa_minimizes_a_quadratic
```

The checked-in [`test_solvers.py`](../../../../examples/fortran/prima/tests/test_solvers.py)
is a starting point for your own cases. Add a `test_*` function in that file,
or add another `test_*.py` beside it. The shared `prima` fixture imports the
built extension. Change the objective, initial `x`, and expected result, then
run your new test with the same pytest command. The suite covers a numerical
case for each of the five exposed solvers and checks both present and omitted
optional callback arguments; it is not an exhaustive solver-option or
constraint suite.

SciPy is optional. Install it to run the additional COBYLA comparison:

```bash
python3 -m pip install scipy
python3 -m pytest -q examples/fortran/prima/tests/test_solvers.py::test_cobyla_agrees_with_scipy_on_a_quadratic
```

This compares the two COBYLA results with the known mathematical solution; it
does not measure speed. SciPy's
[COBYLA method](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html)
is the direct counterpart among the five exposed solvers. The other four are
checked against the known minimum without requiring SciPy.

## Build inputs and platforms

The checked-in [`export_symbols.txt`](../../../../examples/fortran/prima/export_symbols.txt)
selects the five solver procedures. PRIK keeps the callback declarations
their signatures need in the generated contract. Both the native library and
contract extraction use 64-bit real values and the default PRIMA integer kind.
See the [example README](../../../../examples/fortran/prima/README.md) and
[build script](../../../../examples/fortran/prima/build_prik.sh) to adapt the
build for another project.

The **Real Libraries Portability** workflow runs this build and its numerical
tests with Python 3.12 and GNU Fortran 13 on Linux x86-64, Linux ARM64, macOS
Intel, and macOS ARM64.

The sources under [`native/`](../../../../examples/fortran/prima/native/) are
from [libPRIMA commit `1d76fb88aeffb427cd17ed1e9d0d3b34f414913f`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f)
and retain its [BSD 3-Clause license](../../../../examples/fortran/prima/LICENCE.txt).
