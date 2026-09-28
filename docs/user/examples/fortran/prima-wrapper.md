---
title: Build and Validate PRIMA with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: ../../guide/callbacks.md, ../../guide/optional-arguments.md, ../../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Build and Validate PRIMA with PRIK

This example turns [PRIMA](https://github.com/libprima/prima), the modern
Fortran implementation of Powell's derivative-free optimization solvers, into
one Python extension. It compiles PRIMA once into a static library, asks PRIK
to generate bindings only for the five solvers, and links those bindings
against that library. Your objective function is an ordinary Python callable.

### What you get

One extension, `prik_prima`, with exactly five solvers:

| Module | Solver | Problem type |
| --- | --- | --- |
| `uobyqa_mod` | `uobyqa` | Unconstrained |
| `newuoa_mod` | `newuoa` | Unconstrained |
| `bobyqa_mod` | `bobyqa` | Bound constraints |
| `lincoa_mod` | `lincoa` | Linear constraints |
| `cobyla_mod` | `cobyla` | Nonlinear constraints |

Each solver takes your objective as a Python callback and updates a NumPy `x`
in place. Every optional PRIMA argument stays optional in Python, including a
progress callback that can stop the solver early.

---

## Quick start

From a PRIK checkout with PRIK installed, and with CMake and GNU Fortran on
`PATH` (see [Set up a clean environment](#set-up-a-clean-environment)):

```bash
source examples/fortran/prima/build_all.sh
python3 -m pytest -q examples/fortran/prima/tests
```

The first command builds the extension and puts it on `PYTHONPATH` for this
shell; use `source`, not `bash`, so that setting survives. The second runs the
example's tests.

After this, you can `import prik_prima` in the same shell and call the solvers
as shown in [Use the generated API](#use-the-generated-api).

---

## Key files

Everything lives under
[`examples/fortran/prima/`](../../../../examples/fortran/prima/):

| File | What it does |
| --- | --- |
| [`export_symbols.txt`](../../../../examples/fortran/prima/export_symbols.txt) | Names the five `module::procedure` solvers PRIK exposes. |
| [`sources.txt`](../../../../examples/fortran/prima/sources.txt) | Lists the 55 PRIMA sources, used by both CMake and PRIK. |
| [`CMakeLists.txt`](../../../../examples/fortran/prima/CMakeLists.txt) | Compiles those sources into the static library `libprimaf.a`. |
| [`build_prik.sh`](../../../../examples/fortran/prima/build_prik.sh) | Runs the three build steps below. |
| [`build_all.sh`](../../../../examples/fortran/prima/build_all.sh) | Runs `build_prik.sh` and adds the extension to `PYTHONPATH`. |
| [`tests/test_solvers.py`](../../../../examples/fortran/prima/tests/test_solvers.py) | Checks every solver and the callbacks. |
| [`native/`](../../../../examples/fortran/prima/native/) | The PRIMA source snapshot; the build downloads nothing. |

---

## How the build works

PRIMA is compiled once. PRIK reads the same sources to learn the solvers'
interfaces, but it generates bindings only for the five names in
`export_symbols.txt` and links them to the library CMake already built. Use
this pattern for any Fortran library built as a static archive when Python
needs only a few of its entry points:

```text
55 PRIMA sources ─┬─ cmake ──────────────────────> libprimaf.a ─┐
                  │                                             │
                  └─ prik generate --pyi ──> contract/ ─ prik ──┴─> prik_prima
```

`build_prik.sh` runs those three steps:

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

| Step | Command | Result |
| --- | --- | --- |
| 1. Compile PRIMA | `cmake` | `libprimaf.a` and its Fortran module files |
| 2. Generate the contract | `prik generate --pyi` with `--export-symbols` | One `.pyi` file per solver module, plus the callback interfaces they use |
| 3. Build the extension | `prik` with `--native-link-item archive:…` | `prik_prima`, linked to `libprimaf.a` without recompiling PRIMA |

Steps 1 and 2 use the same `PRIMA_REAL_PRECISION=64` and
`PRIMA_INTEGER_KIND=0`, so the contract describes the library that was
actually compiled. Everything is written to the temporary `PRIMA_BUILD_ROOT`
directory, not to the repository.

The generated contracts live in `$PRIMA_BUILD_ROOT/contract/`, one `.pyi`
file per solver module. Open them to see each solver's exact Python signature,
including every optional argument.

---

## Use the generated API

Every solver follows the same pattern: the objective receives the current point
and writes its value into `result`; the solver updates `x` in place. Pass `x`
as a Fortran-ordered `float64` array and integer options as `np.int32`.

UOBYQA minimizes a quadratic whose minimum is at `(1, -2)`:

```python
import numpy as np
import prik_prima

def objective(values, result):
    result[...] = (values[0] - 1.0) ** 2 + (values[1] + 2.0) ** 2

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
prik_prima.uobyqa_mod.uobyqa(objective, x, maxfun=np.int32(100))
print(x)  # [ 1. -2.]
```

`newuoa`, `bobyqa`, and `lincoa` take the same objective. `cobyla` handles
nonlinear constraints: its callback also fills a `constraints` array, each
entry meaning `constraint <= 0`, and its second argument `m_nlcon` is the
number of constraints. Requiring `x[1] >= -1` moves the minimum to `(1, -1)`:

```python
def objective_and_constraints(values, result, constraints):
    objective(values, result)
    constraints[0] = -1.0 - values[1]  # x[1] >= -1, written as -1 - x[1] <= 0

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
prik_prima.cobyla_mod.cobyla(objective_and_constraints, np.int32(1), x, maxfun=np.int32(200))
print(x.round(3))  # [ 1. -1.]
```

**Progress callback.** Pass `callback_fcn` to follow each iteration. Setting
`terminate[...] = True` stops the solver early; here UOBYQA stops after 8
evaluations instead of 22:

```python
def progress(values, f, nf, tr, cstrv, nlconstr, terminate):
    print(f"evaluation {nf}: f = {f:.3g}")
    if f < 1e-6:
        terminate[...] = True

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
prik_prima.uobyqa_mod.uobyqa(objective, x, maxfun=np.int32(100), callback_fcn=progress)
```

Arguments that a solver does not use arrive as `None`; for example, `cstrv` and
`nlconstr` are `None` in UOBYQA's callback.

**Final value and evaluation count.** `f`, `nf`, and `info` are optional
Fortran outputs. Pass rank-zero arrays to receive them; omitting them keeps them
absent to PRIMA:

```python
f = np.zeros((), dtype=np.float64)
nf = np.zeros((), dtype=np.int32)
x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))
prik_prima.uobyqa_mod.uobyqa(objective, x, f=f, nf=nf, maxfun=np.int32(100))
print(float(f), int(nf))
```

---

## Run the tests

```bash
python3 -m pytest -q examples/fortran/prima/tests
```

The suite checks each solver against the known minimum, that the extension
exposes exactly the five solvers, and the progress callback with optional
arguments present or omitted. It is not an exhaustive solver-option or
constraint suite.

To compare COBYLA with SciPy's, which also comes from PRIMA:

```bash
python3 -m pip install "scipy==1.18.0"
python3 -m pytest -q examples/fortran/prima/tests/test_solvers.py::test_cobyla_agrees_with_scipy_on_a_quadratic
```

To test your own problem, add a case beside the checked-in tests.

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

Install CMake and GNU Fortran separately. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install --yes cmake gcc gfortran
gfortran --version
```

Run the example's commands from the repository root with the virtual
environment active.

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| PRIMA | [libprima/prima commit `1d76fb88`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f) |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 |
| SciPy (optional comparison) | 1.18.0 in CI |
| Native compilers | GNU Fortran 13 + GCC 13 in CI; compatible local compilers work |

## Tested platforms

The Real Libraries Portability workflow builds and runs the numerical suite
with Python 3.12 on:

| Operating system | Architectures | Native toolchain |
| --- | --- | --- |
| Linux | x86-64, ARM64 | GNU Fortran 13 + GCC 13 |
| macOS | Intel, ARM64 | GNU Fortran 13 + GNU GCC 13 |

## Troubleshooting

- Confirm that `cmake` and `gfortran` are available on `PATH`.
- Use `source examples/fortran/prima/build_all.sh`; running it with `bash`
  starts a child shell, so the exported `PYTHONPATH` is lost.
- SciPy is optional. The COBYLA comparison skips if it is not installed.
- Run one failing solver test with `-vv -s` to see its output.

## Source provenance

The files under [`examples/fortran/prima/native/`](../../../../examples/fortran/prima/native/)
match [libprima/prima commit `1d76fb88aeffb427cd17ed1e9d0d3b34f414913f`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f).
They retain the upstream [BSD 3-Clause license](../../../../examples/fortran/prima/LICENCE.txt).
