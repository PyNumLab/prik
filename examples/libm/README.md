# Wrap the C Standard Math Library with PRIK

This maintained example wraps 60 reviewed ISO C99 functions from the target's
math library. It generates a target-specific semantic `.pyi`, builds the direct
C wrapper, tests every exported routine, and audits the built surface against
the reviewed inventory.

Its layout mirrors the other real-library examples:

- `libm_probe.h` includes the target toolchain's own `<math.h>`.
- `iso_c99_routines.txt` is the reviewed 60-function allowlist.
- `build_prik.sh` generates the target contract and builds the extension.
- `build_all.sh` exposes the built module on `PYTHONPATH`.
- `routine_inventory.py` groups every public function and names its test.
- `tests/` contains numerical tests and fail-closed surface audits.

## Requirements

Install a C compiler, Python development headers, NumPy, and pytest. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes build-essential python3-dev
python3 -m pip install "numpy>=2" pytest
```

Run the remaining commands from the repository root.

## Quick start

```bash
source examples/libm/build_all.sh
python3 -m pytest -q examples/libm/tests
```

Use `source` so the build paths exported by `build_all.sh` remain available to
the test process.

## How the build stays portable

The committed [`libm_probe.h`](libm_probe.h) contains only `#include <math.h>`.
The generated contract therefore uses the declarations supplied by the active
compiler and platform. [`iso_c99_routines.txt`](iso_c99_routines.txt) selects
the reviewed ISO C99 functions and excludes implementation internals, macros,
constants, and unsupported pointer or string forms. Unknown names fail the
build instead of producing a smaller module silently.

The build keeps included headers private with `--include-exposure roots-only`,
then promotes only the allowlisted functions with `--export-symbols`. It also
removes implementation parameter names from the Python API and isolates every
selected C declaration from names already present in Python's headers:

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

The public signature uses target-sized NumPy contract types. Exact native C
identities appear only at the native boundary. For example, an LP64 target may
generate:

```python
@native_call([Arg(0)], result=CLongLong(Return(0)))
def llrint(x: Float64) -> Int64: ...
```

Here the native function is declared with a `long long` result and that result
is converted to public `Int64` storage. C `long`, C `int`, and `long double`
tests derive their expected NumPy dtypes from the active target. A native cast
is sparse: it is omitted when the canonical fixed-width typedef already has
the exact source C identity and emitted otherwise. Exact type preservation
handles ABI identity; `--collision-adapter-all` separately prevents a selected
`math.h` declaration such as `remainder` from colliding with a declaration in a
binding header. LTO is not required, so this example does not use `--lto`.

Macros are intentionally outside the example. Expose a macro through an
ordinary native function when an API needs one.

The inventory also leaves out `frexp`, `modf`, and `remquo`, whose output
pointers need an authored direction/projection contract, and `nan`, whose
string argument needs authored semantics. Non-ISO Bessel extensions are not
part of the ISO C99 selection.

## What is validated

Every inventory entry has one visibly named numerical test. The audits verify
that the generated contract, built module, inventory, and tests all expose the
same 60 functions.

The numerical oracles are mixed: Python's `math` module where it matches,
independent identities for error and gamma functions, target-aware rounding
checks, tolerance-based transcendental comparisons, exact dtype assertions,
and a fused-rounding check for `fma`.

Run focused groups with:

```bash
python3 -m pytest -q examples/libm/tests/test_special.py
python3 -m pytest -q examples/libm/tests/test_rounding.py::test_llrint
python3 -m pytest -q examples/libm/tests/test_precision.py
```

## Portability boundary

The API selection is ISO C99, but build configuration is still target-specific.
`--native-library m` is the conventional Unix link spelling; targets that put
math symbols in a different library should adjust that link item. PRIK fails
when the compiler probe reports a scalar representation outside its supported
contract widths.

Set `PRIK_LIBM_CC` to select another compiler executable; it defaults to `cc`.
CI reuses the existing Linux x86-64 and macOS Arm64 jobs, then adds one focused
15-minute Linux Arm64 job. Each target runs only this example for its libm
coverage, so the full real-library suite is not repeated across architectures.
The lanes cover GCC-compatible and Apple Clang toolchains. Native Windows/MSVC
is outside PRIK's current POSIX C build lane.

There are no vendored implementation sources or copied prototypes. The
extension parses and calls the math library supplied by the active platform.
