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
produces an importable Python extension containing all 22 public MINPACK
procedures. The maintained suite exercises every routine and exposes MINPACK's
three machine constants as one safe, read-only NumPy array.

The result is one module, `prik_reference_minpack`. Numerical evidence comes
from SciPy's MINPACK-backed solvers, direct linear-algebra identities, known
nonlinear systems, and explicit callback checks. No f2py comparison wrapper is
required.

### Why this example exists

- It demonstrates a real solver library with Python callbacks, caller-owned
  work arrays, scalar statuses, and in-place writebacks.
- It verifies residuals, Jacobians, factorizations, solver termination, and
  callback execution rather than stopping after a successful import.
- It gives immutable Fortran parameter arrays an explicit Python ownership and
  lifetime contract.

You should already be comfortable with NumPy arrays, Python callables, and
building a local Fortran extension.

---

## Versions used by the maintained example

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

MINPACK's reviewed public declarations and implementations live in one source
file, so the copyable build is direct:

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

`-O0` keeps this a correctness example and avoids optimization-dependent
claims. PRIK compiles the native source and generated bridge once into the
extension.

For normal use, source the convenience entrypoint:

```bash
source examples/minpack/build_all.sh
```

It builds the extension and exports its directory on `PYTHONPATH` for the
current shell.

---

## 3. Understand the Python contract

MINPACK preserves its native argument order and explicit work arrays. Pass
ordinary NumPy arrays with the generated dtype, shape, and layout. Callback
solvers accept normal Python callables with the generated callback signature;
PRIK keeps those callbacks alive for the native call and reports callback
counts and solver statuses through the documented result projection.

### Immutable machine constants

`dpmpar` is a Fortran parameter array, not writable native storage. At module
initialization, PRIK creates a Python-owned NumPy snapshot with the compiled
dtype, shape, and values, then marks it read-only:

```python
import prik_reference_minpack

constants = prik_reference_minpack.minpack_module.dpmpar
assert constants.shape == (3,)
assert constants.flags.writeable is False
```

The array does not borrow a Fortran address. Rebinding the Python attribute
changes only that Python name and never modifies the compiled parameter.

---

## 4. Run the complete correctness suite

After the build finishes, run:

```bash
python3 -m pytest -q examples/minpack/tests
```

The reviewed inventory covers the complete public procedure surface:

| Family | Procedures |
| --- | ---: |
| Diagnostics and finite differences | 4 |
| Hybrid nonlinear solvers | 4 |
| Levenberg-Marquardt solvers | 6 |
| Factorization and update helpers | 8 |
| **Total** | **22** |

Every procedure has a named invocation test. The suite additionally checks
the dtype, values, and immutability of `dpmpar`; the inventory guard fails if a
reviewed routine loses its explicit test.

---

## 5. Validate behaviour, not just compilation

For callback-driven solvers, the primary evidence is:

```text
PRIK solution == SciPy MINPACK solution
native residual == expected residual
callback and status outputs == documented contract
```

This compact `hybrd1` test is taken verbatim from the runnable suite. Its
`vector`, callback, tolerance, and SciPy reference helpers are small fixtures
defined beside the solver tests:

<!-- prik-doc-source: examples/minpack/tests/test_solvers.py::test_hybrd1 -->
```python
def test_hybrd1(minpack):
    x, fvec = vector(), vector((0.0, 0.0))
    info = minpack.hybrd1(residual_callback, TWO, x, fvec, ROOT_TOLERANCE, np.empty(19), INT(19))

    assert info == INT(1)
    assert_solution(x, scipy_root())
    np.testing.assert_allclose(fvec, 0.0, atol=1.0e-10)
```

The immutable constant contract is also executable evidence:

<!-- prik-doc-source: examples/minpack/tests/test_diagnostics.py::test_dpmpar_is_an_immutable_float64_snapshot -->
```python
def test_dpmpar_is_an_immutable_float64_snapshot(minpack):
    values = minpack.dpmpar

    np.testing.assert_array_equal(
        values,
        np.array([np.finfo(np.float64).eps, np.finfo(np.float64).tiny, np.finfo(np.float64).max]),
    )
    assert values.flags.writeable is False
    with pytest.raises(ValueError, match="read-only"):
        values[0] = 1.0
```

Together these checks cover numerical correctness, callback execution,
in-place outputs, termination status, and ownership of module constants.

---

## 6. Explore the maintained example

Run one family or routine while developing:

```bash
python3 -m pytest -q examples/minpack/tests/test_solvers.py
python3 -m pytest -q \
  examples/minpack/tests/test_solvers.py::test_hybrd1
python3 -m pytest -q examples/minpack/tests -k dpmpar
```

- Callback-driven nonlinear solvers →
  [`test_solvers.py`](../../../examples/minpack/tests/test_solvers.py)
- Diagnostics and immutable constants →
  [`test_diagnostics.py`](../../../examples/minpack/tests/test_diagnostics.py)
- Factorization and update helpers →
  [`test_linear_algebra.py`](../../../examples/minpack/tests/test_linear_algebra.py)
- Authoritative public classification →
  [`routine_inventory.py`](../../../examples/minpack/routine_inventory.py)
- Fail-closed coverage guard →
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
- Keep performance experiments separate from this correctness project. The
  maintained suite uses small deterministic systems and makes no benchmark
  claims.

---

## Source provenance

[`examples/minpack/native/minpack.f90`](../../../examples/minpack/native/minpack.f90)
matches the upstream `src/minpack.f90` at
[fortran-lang/minpack commit `c0b5aea9fcd2b83865af921a7a7e881904f8d3c2`](https://github.com/fortran-lang/minpack/tree/c0b5aea9fcd2b83865af921a7a7e881904f8d3c2).

See the [upstream repository](https://github.com/fortran-lang/minpack), its
[API documentation](https://fortran-lang.github.io/minpack/), and its license
before redistributing the bundled native source.
