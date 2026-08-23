---
title: Build and Validate libm with PRIK
audience: users, advanced users
prerequisites: C support, semantic .pyi contracts
related: ../language-support/c-support.md, ../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Build and Validate libm with PRIK

This example wraps 60 reviewed ISO C99 routines from the platform's standard
math library and validates every one with a named numerical test. The build
regenerates the semantic `.pyi` for the active C compiler and target.

It follows the maintained real-library example structure: a reviewed native
surface, copyable build scripts, a grouped routine inventory, fail-closed
coverage audits, numerical tests, documentation, and CI execution.

### What this example shows

- Generate a target-specific contract from the platform's own `<math.h>` and a
  reviewed function allowlist.
- Link an existing system library without vendoring or compiling its sources.
- Preserve exact native `long`, `long long`, and `int` identities while keeping
  ordinary NumPy types in the public Python signature.
- Test every exported function and audit the inventory against the built module.

Read [C support](../language-support/c-support.md) and the
[CLI reference](../reference/cli-commands.md) first if the direct C workflow is
new to you.

---

## Versions used

| Component | Version / source |
| --- | --- |
| PRIK | current repository checkout |
| libm | the target's C standard math library |
| Python | 3.12 in the dedicated CI job |
| NumPy | 2.5.1 in CI |
| C compiler | Linux GCC and Apple Clang in CI |

The declarations selected by the example are ISO C99. The generated contract,
NumPy dtypes, compiler, and library link remain target-specific.

---

## 1. Prepare the repository and toolchain

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[qa]" "numpy==2.5.1"
```

Install a C compiler and the Python development headers. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install --yes build-essential python3-dev
```

All remaining commands run from the repository root. The runnable project is
under [`examples/libm/`](../../../examples/libm/).

---

## 2. Review the selected API

[`libm_probe.h`](../../../examples/libm/libm_probe.h) contains only
`#include <math.h>`, so the active toolchain supplies every declaration.
[`iso_c99_routines.txt`](../../../examples/libm/iso_c99_routines.txt) is the
reviewed 60-function public surface. The export allowlist excludes the rest of
the platform header and fails if a requested ISO C99 function is missing.

Generate the contract for the active target with:

```bash
mkdir -p build
python3 -m prik generate --pyi --language c examples/libm/libm_probe.h \
  --compiler "$(command -v cc)" \
  --std c99 \
  --include-exposure roots-only \
  --export-symbols examples/libm/iso_c99_routines.txt \
  --out build/libm_api.pyi
```

The compiler probe maps the C types to target-sized public contract dtypes. The
generated `@native_call` expressions retain an exact C scalar type wherever
normalization would otherwise erase a distinction needed by the declaration.

Macros are not part of this surface. If an API must expose a macro, provide an
ordinary native function that evaluates it and wrap that function.

`frexp`, `modf`, and `remquo` are excluded because their output pointers need
an authored direction/projection contract. `nan` needs authored string
semantics, and non-ISO Bessel extensions are outside the reviewed ISO C99
selection.

---

## 3. Build the wrapper

The maintained script generates the target contract, compiles the binding, and
links libm:

<!-- prik-doc-source: examples/libm/build_prik.sh -->
```bash
export EXAMPLE_WORKSPACE="$PWD"
export LIBM_BUILD_ROOT="$(mktemp -d)"

LIBM_COMPILER="${PRIK_LIBM_CC:-cc}"
if ! LIBM_COMPILER_PATH="$(command -v "$LIBM_COMPILER")"; then
  echo "libm example: C compiler not found: $LIBM_COMPILER" >&2
  return 1 2>/dev/null || exit 1
fi
export LIBM_COMPILER_PATH

mkdir -p "$LIBM_BUILD_ROOT/prik/contract" "$LIBM_BUILD_ROOT/prik/generated"
cd "$LIBM_BUILD_ROOT/prik"

if ! python3 -m prik generate --pyi --language c \
  "$EXAMPLE_WORKSPACE/examples/libm/libm_probe.h" \
  --compiler "$LIBM_COMPILER_PATH" \
  --std c99 \
  --include-exposure roots-only \
  --export-symbols "$EXAMPLE_WORKSPACE/examples/libm/iso_c99_routines.txt" \
  --out "$LIBM_BUILD_ROOT/prik/contract/libm_api.pyi"; then
  return 1 2>/dev/null || exit 1
fi

if ! python3 -m prik --language c "$LIBM_BUILD_ROOT/prik/contract/libm_api.pyi" \
  --out prik_reference_libm \
  --out-dir "$LIBM_BUILD_ROOT/prik/generated" \
  --compiler "$LIBM_COMPILER_PATH" \
  --native-library m \
  --positional-only \
  --collision-adapter-all; then
  return 1 2>/dev/null || exit 1
fi
```

For normal use, source the convenience entrypoint:

```bash
source examples/libm/build_all.sh
```

It also exports the built extension directory on `PYTHONPATH` for the current
shell.

---

## 4. Understand exact native scalar types

On an LP64 target, C `long` and `long long` may both map to public `Int64`, but
they remain distinct C types. A target-generated contract keeps the native
result declaration explicitly when needed:

```python
@native_call([Arg(0)], result=CLongLong(Return(0)))
def llrint(x: Float64) -> Int64: ...
```

The expression's position determines its direction. Inside the native argument
list, a cast describes a native parameter. In `result=...`, it declares the
native function result, which the binding converts into Python result slot 0.

The binding therefore declares `llrint` as returning `long long`, receives that
value, and converts it to the public `Int64` storage. `lrint` similarly retains
C `long`, whose public result may be `Int32` or `Int64` on different targets.
When the target's canonical fixed-width typedef is already a typedef of
`long`, no `CLong` expression is needed; otherwise generation emits one even
when the two C types have the same width. These sparse casts preserve ABI type
identity. The separate `--collision-adapter-all` mechanism prevents selected
`math.h` declarations from colliding with identifiers in Python's headers.
LTO is optional and is deliberately not required by this example.

---

## 5. Run the complete test suite

```bash
python3 -m pytest -q examples/libm/tests
```

The inventory contains exactly 60 routines:

| Family | Routines |
| --- | ---: |
| Trigonometric | 7 |
| Hyperbolic | 6 |
| Exponential and logarithmic | 7 |
| Power and roots | 4 |
| Rounding, truncation, and remainder | 12 |
| Floating-point manipulation | 13 |
| Error and gamma functions | 4 |
| Single and extended precision | 7 |
| **Total** | **60** |

---

## 6. See how results are validated

Tests compare Python's `math` module where it has the same operation and use
independent identities elsewhere. The complete elementary group demonstrates
the NumPy scalar boundary, tolerance-based transcendental comparisons, exact
results where the operation permits them, and the precision benefit of
specialized operations such as `expm1`:

<!-- prik-doc-source: examples/libm/tests/test_numerical.py::test_elementary -->
```python
def test_elementary(libm):
    assert np.isclose(libm.sin(np.float64(1.0)), math.sin(1.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.cos(np.float64(1.0)), math.cos(1.0), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.tan(np.float64(0.5)), math.tan(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.asin(np.float64(0.5)), math.asin(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.acos(np.float64(0.5)), math.acos(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.atan(np.float64(0.5)), math.atan(0.5), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(
        libm.atan2(np.float64(1.0), np.float64(2.0)),
        math.atan2(1.0, 2.0),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert np.isclose(libm.sinh(np.float64(0.75)), math.sinh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.cosh(np.float64(0.75)), math.cosh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.tanh(np.float64(0.75)), math.tanh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.asinh(np.float64(0.75)), math.asinh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.acosh(np.float64(1.75)), math.acosh(1.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.atanh(np.float64(0.75)), math.atanh(0.75), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.exp(np.float64(1.0)), math.e, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)

    # exp2 is exact on a whole exponent, so no tolerance is needed.
    assert libm.exp2(np.float64(10.0)) == 1024.0

    # expm1 keeps the precision that exp(x) - 1 loses for small x.
    assert np.isclose(
        libm.expm1(np.float64(1e-9)),
        math.expm1(1e-9),
        rtol=DOUBLE_TOLERANCE,
        atol=DOUBLE_TOLERANCE,
    )
    assert libm.expm1(np.float64(1e-9)) != math.exp(1e-9) - 1.0

    assert np.isclose(libm.log(np.float64(math.e)), 1.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.log2(np.float64(1024.0)) == 10.0
    assert np.isclose(libm.log10(np.float64(1000.0)), 3.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert np.isclose(libm.log1p(np.float64(1e-9)), math.log1p(1e-9), rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.pow(np.float64(2.0), np.float64(10.0)) == 1024.0
    assert libm.sqrt(np.float64(144.0)) == 12.0
    assert np.isclose(libm.cbrt(np.float64(27.0)), 3.0, rtol=DOUBLE_TOLERANCE, atol=DOUBLE_TOLERANCE)
    assert libm.hypot(np.float64(3.0), np.float64(4.0)) == 5.0
```

Precision is asserted rather than assumed. The suite checks `float` results as
`float32`, follows the target representation for `long double`, derives C
`int` and C `long` NumPy dtypes from the running target, and checks supported
`long long` results. Rounding-sensitive functions are compared under the
active floating-point mode, transcendental results use tolerances, and `fma`
is checked for one fused rounding.

---

## 7. Run focused examples

```bash
python3 -m pytest -q examples/libm/tests/test_numerical.py::test_special
python3 -m pytest -q examples/libm/tests/test_numerical.py::test_rounding
python3 -m pytest -q examples/libm/tests/test_numerical.py::test_precision
```

- Platform declaration probe →
  [`libm_probe.h`](../../../examples/libm/libm_probe.h)
- Reviewed function selection →
  [`iso_c99_routines.txt`](../../../examples/libm/iso_c99_routines.txt)
- Public routine list →
  [`routine_inventory.py`](../../../examples/libm/routine_inventory.py)
- Routine coverage checks →
  [`test_routine_coverage.py`](../../../examples/libm/tests/test_routine_coverage.py)
- Copyable project instructions →
  [`examples/libm/README.md`](../../../examples/libm/README.md)

---

## Troubleshooting

- Confirm that `cc` is on `PATH` and Python development headers are installed.
- Set `PRIK_LIBM_CC` to use a compiler other than `cc`.
- Use `source examples/libm/build_all.sh`; a child shell cannot preserve its
  exported `PYTHONPATH`.
- The `--native-library m` spelling is platform build configuration. If the
  target exposes its C math symbols without a separate libm, adjust that link
  item for the target.
- Keep `--collision-adapter-all` when regenerating this wrapper; it isolates
  any selected `math.h` identifier already declared by a binding header.

## CI portability coverage

The Real Libraries Portability workflow runs every maintained example on
Linux x86-64, Linux Arm64, macOS Intel, and macOS Arm64. Within each machine
job, libm runs with GCC and Clang on Linux and with Apple Clang and GNU GCC on
macOS. Together the lanes exercise system `math.h`, native libm, target scalar
probes, generated contracts, collision adapters, two operating systems, both
hosted architectures, and both compiler families. Native Windows/MSVC remains
outside PRIK's current POSIX C build lane.

## Source provenance

There are no vendored implementation sources or copied prototypes. The example
parses the target's `math.h` and links its math library through the reviewed
ISO C99 name selection.
