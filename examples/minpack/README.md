# Wrap MINPACK with PRIK

Build the bundled modern
[fortran-lang/minpack](https://github.com/fortran-lang/minpack) source with
PRIK and validate all 22 public procedures against SciPy, direct
linear-algebra identities, and deterministic nonlinear problems.

The example also exposes the `dpmpar` machine constants as a Python-owned,
read-only NumPy array. No f2py comparison wrapper is used, and the inventory
has no unsupported or skipped procedures.

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

Build the extension and run the complete maintained suite:

```bash
source examples/minpack/build_all.sh
python3 -m pytest -q examples/minpack/tests
```

Use `source` so the build directory exported by `build_all.sh` remains on
`PYTHONPATH` for pytest.

## How the build works

PRIK reads and compiles the checked-in `minpack.f90` public module together
with its generated bridge. Each source is compiled once and no alternative
wrapper is created.

The immutable `dpmpar` parameter array has no writable native storage. PRIK
copies its compiled values once during module initialization into a
Python-owned NumPy array and marks that snapshot read-only.

### Build the PRIK wrapper

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

## Run focused tests

After the quick-start build, run one family or routine:

```bash
python3 -m pytest -q examples/minpack/tests/test_solvers.py
python3 -m pytest -q \
  examples/minpack/tests/test_solvers.py::test_hybrd1
python3 -m pytest -q examples/minpack/tests -k dpmpar
```

## What is validated

The suite covers all 22 public diagnostics, finite-difference helpers, hybrid
solvers, Levenberg-Marquardt solvers, factorizations, and rank-one updates.
Solver tests check residuals and statuses against known systems and SciPy;
helper tests use nontrivial algebraic invariants. Tests also verify callback
counts, caller-array writebacks, Fortran-order matrices, and `dpmpar` values,
dtype, ownership, and immutability.

The runtime inventory test rejects missing or unexpected generated exports,
and each expected procedure has one explicit invocation test.

## Sources and license

[`native/minpack.f90`](native/minpack.f90) matches upstream `src/minpack.f90`
at
[fortran-lang/minpack commit `c0b5aea9fcd2b83865af921a7a7e881904f8d3c2`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2).
See the upstream repository, API documentation, and license before
redistributing the bundled native source.
