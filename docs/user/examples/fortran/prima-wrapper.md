---
title: Build and Validate PRIMA with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: ../../guide/callbacks.md, ../../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Build and Validate PRIMA with PRIK

This example builds the checked-in [libPRIMA](https://github.com/libprima/prima)
Fortran sources once and wraps five derivative-free solvers as one Python
extension. Its numerical tests exercise Python callbacks and check known
solutions.

### What this example shows

- Select five `module::procedure` entrypoints while retaining the callback
  declarations their signatures need.
- Link a PRIK wrapper to a prebuilt static Fortran archive without compiling
  the native sources twice.
- Call the solvers from Python, including optional callbacks and optional
  arguments inside callback interfaces.

You should already be comfortable with NumPy arrays, Python callables, and
building a local Fortran extension.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| PRIMA | [libprima/prima commit `1d76fb88`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy (optional comparison) | 1.18.0 in CI |
| Native compilers | GNU Fortran 13 + GCC 13 in CI; compatible local compilers work |

The source snapshot lives under `examples/fortran/prima/native/`; the build
does not download PRIMA.

## Tested platforms

The Real Libraries Portability workflow builds and runs the numerical suite
with Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

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
python3 -m pip install -e ".[qa]" "numpy==2.5.1"
```

Install CMake and GNU Fortran separately. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install --yes cmake gcc gfortran
gfortran --version
```

All remaining commands run from the repository root in this shell with the
virtual environment active. The runnable project lives under
[`examples/fortran/prima/`](../../../../examples/fortran/prima/).

---

## 2. Build the PRIK wrapper

The build script compiles PRIMA into `libprimaf.a`, selects five public
procedures for the generated `.pyi` contract, and links the wrapper against
that archive:

<!-- prik-doc-source: examples/fortran/prima/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export PRIMA_BUILD_ROOT="$(mktemp -d)"

mkdir -p "$PRIMA_BUILD_ROOT/prik/generated"

cmake \
  -S "$EXAMPLE_WORKSPACE/examples/fortran/prima" \
  -B "$PRIMA_BUILD_ROOT/native" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_Fortran_COMPILER="$(command -v gfortran)"
cmake --build "$PRIMA_BUILD_ROOT/native" --target primaf --parallel 2

PRIMA_SOURCES=()
while IFS= read -r source; do
  PRIMA_SOURCES+=("$EXAMPLE_WORKSPACE/examples/fortran/prima/native/$source")
done < "$EXAMPLE_WORKSPACE/examples/fortran/prima/sources.txt"

python3 -m prik generate --pyi \
  "${PRIMA_SOURCES[@]}" \
  --export-symbols "$EXAMPLE_WORKSPACE/examples/fortran/prima/export_symbols.txt" \
  --out "$PRIMA_BUILD_ROOT/contract" \
  --compiler "$(command -v gfortran)" \
  -I "$EXAMPLE_WORKSPACE/examples/fortran/prima/native/common" \
  -D PRIMA_REAL_PRECISION=64 \
  -D PRIMA_INTEGER_KIND=0

cd "$PRIMA_BUILD_ROOT/prik"
python3 -m prik "$PRIMA_BUILD_ROOT/contract/__init__.pyi" \
  --out prik_prima \
  --out-dir "$PRIMA_BUILD_ROOT/prik/generated" \
  --compiler "$(command -v gfortran)" \
  --native-link-item "archive:$PRIMA_BUILD_ROOT/native/libprimaf.a" \
  --native-linker-language fortran \
  -I "$PRIMA_BUILD_ROOT/native/mod" \
  --jobs 2
```

CMake compiles the 55 native sources once. PRIK analyzes those same sources
with matching real-precision and integer-kind settings, then links its
generated wrapper to the archive.

For normal use, source the convenience entrypoint:

```bash
source examples/fortran/prima/build_all.sh
```

It builds the extension, exports its directory on `PYTHONPATH`, and records
the temporary build directory in `PRIMA_BUILD_ROOT` for this shell.

---

## 3. Use the generated Python API

The public Python API has exactly these entries:

| Module | Solver |
| --- | --- |
| `bobyqa_mod` | `bobyqa` |
| `cobyla_mod` | `cobyla` |
| `lincoa_mod` | `lincoa` |
| `newuoa_mod` | `newuoa` |
| `uobyqa_mod` | `uobyqa` |

For example, UOBYQA minimizes a two-variable quadratic whose known minimum is
at `(1, -2)`. After building the extension, run this in Python:

```python
import numpy as np
import prik_prima

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))

def objective(values, result):
    result[...] = (values[0] - 1.0) ** 2 + (values[1] + 2.0) ** 2

prik_prima.uobyqa_mod.uobyqa(objective, x, maxfun=np.int32(100))
np.testing.assert_allclose(x, [1.0, -2.0], atol=2e-3, rtol=0)
print(x)
```

The callback writes the objective value into `result`; the solver updates `x`
in place. The assertion checks the result against the known minimum.

---

## 4. Run the complete test suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/fortran/prima/tests
```

The suite checks a numerical result for each of the five exposed solvers,
exact API selection, and callback behavior when optional arguments are
present or omitted. It is not an exhaustive solver-option or constraint
suite.

---

## 5. See how results are validated

For the quadratic in section 3, the known minimizer `(1, -2)` is the primary
numerical check. The COBYLA test below also confirms that its optional
progress callback receives the expected argument shapes. The test file's
`_objective` helper evaluates `(x[0] - 1)^2 + (x[1] + 2)^2`:

<!-- prik-doc-source: examples/fortran/prima/tests/test_solvers.py::test_cobyla_runs_with_every_optional_callback_dummy_present -->
```python
def test_cobyla_runs_with_every_optional_callback_dummy_present(prima):
    x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
    observed = []

    def objective_and_constraints(values, f, constraints):
        _objective(values, f)

    def progress(values, f, nf, tr, cstrv, nlconstr, terminate):
        observed.append((f, nf, tr, cstrv, nlconstr.shape, terminate.shape))

    prima.cobyla_mod.cobyla(
        objective_and_constraints,
        np.int32(0),
        x,
        maxfun=np.int32(100),
        callback_fcn=progress,
    )

    np.testing.assert_allclose(x, np.array([1.0, -2.0]), atol=2.0e-3, rtol=0.0)
    assert observed
    assert observed[-1][4:] == ((0,), ())
```

SciPy 1.18's
[COBYLA implementation](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html)
also comes from PRIMA, so the optional SciPy test is a cross-interface parity
check rather than an independent algorithmic oracle. Both results are also
checked against the known minimizer `(1, -2)`.

---

## 6. Run focused examples

After building the extension, run one solver test or the optional SciPy
comparison:

```bash
python3 -m pytest -q examples/fortran/prima/tests/test_solvers.py::test_lincoa_minimizes_a_quadratic
python3 -m pip install "scipy==1.18.0"
python3 -m pytest -q examples/fortran/prima/tests/test_solvers.py::test_cobyla_agrees_with_scipy_on_a_quadratic
```

The checked-in test file is a starting point for your own cases: add a
`test_*` function there, or a `test_*.py` file beside it. The shared `prima`
fixture imports the built extension. Change the objective, initial `x`, and
expected result, then run your new test with the same pytest command.

- Solver and callback examples →
  [`test_solvers.py`](../../../../examples/fortran/prima/tests/test_solvers.py)
- Reviewed API selection →
  [`export_symbols.txt`](../../../../examples/fortran/prima/export_symbols.txt)
- Copyable build script →
  [`build_prik.sh`](../../../../examples/fortran/prima/build_prik.sh)
- Project instructions →
  [`examples/fortran/prima/README.md`](../../../../examples/fortran/prima/README.md)

---

## Troubleshooting

- Confirm that `cmake` and `gfortran` are available on `PATH`.
- Use `source examples/fortran/prima/build_all.sh`; executing it in a child
  shell does not preserve the exported `PYTHONPATH`.
- SciPy is optional. The COBYLA comparison skips if it is not installed.
- Run one failing solver test with `-vv -s` to see its output.

---

## Source provenance

The files under [`examples/fortran/prima/native/`](../../../../examples/fortran/prima/native/)
match [libprima/prima commit `1d76fb88aeffb427cd17ed1e9d0d3b34f414913f`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f).
They retain the upstream [BSD 3-Clause license](../../../../examples/fortran/prima/LICENCE.txt).
