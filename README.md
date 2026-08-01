# x2py

**Turn Fortran into natural Python APIs.**

Build clean, importable native extensions from supported Fortran without
writing low-level binding code. x2py preserves modules, derived types, arrays,
and native behavior, and generates an editable `.pyi` contract so you can
shape the Python API.

<!-- X2PY_C_DOCS_START
Fortran-to-Python wrapper generation plus wrapper-oriented parser and semantic
interface tooling for Fortran and C. x2py builds importable CPython extensions
from Fortran sources, extracts native declarations into language-neutral
semantic IR, emits editable `.pyi` interfaces, and reports unsupported or
incomplete contracts before code generation.
X2PY_C_DOCS_END -->

[![Tests](https://github.com/PyNumLab/x2py/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/PyNumLab/x2py/actions/workflows/tests.yml)
[![Static Analysis](https://github.com/PyNumLab/x2py/actions/workflows/static-analysis.yml/badge.svg?branch=main)](https://github.com/PyNumLab/x2py/actions/workflows/static-analysis.yml)
[![codecov](https://codecov.io/gh/PyNumLab/x2py/graph/badge.svg?token=QZRRCS5YO6)](https://codecov.io/gh/PyNumLab/x2py)

[Read the documentation](https://pynumlab.github.io/x2py/) for installation,
the user guide, examples, and reference material.

The complete example below builds with one command:

```bash
python3 -m x2py points.f90 --out geometry
```

## See it in action

Create `points.f90`:

<!-- x2py-doc-source: tests/fortran/building_shared_library/end_to_end/fixtures/native/home_points.f90 -->
```fortran
module points
  implicit none

  type :: point
    real(8) :: x = 0.0d0
    real(8) :: y = 0.0d0
  end type point

contains

  subroutine move(item, dx, dy)
    type(point), intent(inout) :: item
    real(8), intent(in) :: dx, dy
    item%x = item%x + dx
    item%y = item%y + dy
  end subroutine move

  real(8) function norm_squared(item) result(value)
    type(point), intent(in) :: item
    value = item%x * item%x + item%y * item%y
  end function norm_squared

end module points
```

**Generated Python API:**

```python
import numpy as np
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
points.move(item, np.float64(1.0), np.float64(-2.0))

print(item.x, item.y)             # 4.0 2.0
print(points.norm_squared(item))  # 20.0
```

No manual bindings are required. From this source, x2py creates a Python
namespace, a class with accessible fields, a mutating procedure, and a
function.

Want a different Python API? Edit the generated `.pyi` contract to rename or
hide exports, flatten namespaces, define constructors and methods, or create
overloads. The
[contract guide](https://pynumlab.github.io/x2py/user/reference/pyi-contracts/)
shows the available edits.

## Key Features

- Fortran modules exposed as Python namespaces and derived types as classes
- NumPy arrays with explicit dtype, shape, and layout checks
- Allocatable and pointer arrays with explicit lifetime operations
- Immediate Python callbacks and overloaded interfaces
- Editable `.pyi` contracts and readable generated docstrings
- Early, clear errors when a boundary cannot be wrapped

## Performance

**Low wrapper overhead, measured against NumPy's f2py.**

The included benchmark suite runs both tools against the same Fortran kernels
through their normal generated interfaces. Results are machine-dependent; the
charts below come from the latest successfully deployed benchmark snapshot.

**Runtime-call performance** — values above `1.0×` mean x2py is faster.

[![Relative performance of x2py and f2py across call, vector, and matrix workloads. Values above 1.0 mean x2py is faster.](https://pynumlab.github.io/x2py/user/assets/performance-comparison.svg)](https://pynumlab.github.io/x2py/user/performance/)

**Clean end-to-end build time** — lower times are better.

[![Clean end-to-end build time for x2py and f2py under development and optimized compiler profiles. Lower times are better.](https://pynumlab.github.io/x2py/user/assets/build-time-comparison.svg)](https://pynumlab.github.io/x2py/user/performance/#clean-build-time)

[See the complete results, test environment, and one-command reproduction instructions.](https://pynumlab.github.io/x2py/user/performance/)

## Installation & Quick Start

x2py requires **Python 3.10 or newer**, NumPy, Python development headers,
standard build tools, and Fortran and C compilers. GNU Fortran is the default
and is tested on Linux and macOS. LLVM Flang is tested on both platforms;
Intel IFX is tested on Linux.

Clone the repository and install x2py in a virtual environment:

```bash
git clone https://github.com/PyNumLab/x2py.git
cd x2py
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

Check the installation:

```bash
python3 -m x2py --help
```

With the `points.f90` source from above in the current directory, build the
extension:

```bash
python3 -m x2py points.f90 --out geometry
```

`--out geometry` selects the import name and the final shared-library name.
x2py places the stable import file beside the source and keeps generated build
artifacts under `__x2py__/`:

```text
.
  points.f90
  geometry.so
  __x2py__/
    geometry.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

The Python code shown at the top of this README can now import `geometry`
directly.

Use `--out-dir` to place the ABI-specific extension and generated files in a
chosen build directory:

```bash
python3 -m x2py points.f90 \
  --out geometry \
  --out-dir build/geometry
```

```text
.
  geometry.so
  build/geometry/
    geometry.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

### Inspect the generated contract

Generate the editable `.pyi` contract for the same `points.f90`:

```bash
python3 -m x2py generate --pyi points.f90 --out contracts
```

The command preserves the Fortran module as a contract module:

```text
contracts/
  __init__.pyi
  points.pyi
```

Generated `contracts/points.pyi`:

```python
from x2py.contracts import Addr, Arg, Float64, native_call

class point:
    def __init__(
        self,
        *,
        x: Float64 = 0.0,
        y: Float64 = 0.0
    ) -> None: ...

    x: Float64 = 0.0
    y: Float64 = 0.0

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move(
    item: point,
    dx: Float64,
    dy: Float64
) -> None: ...

def norm_squared(
    item: point
) -> Float64: ...
```

The contract describes the generated Python class, fields, functions, exact
NumPy scalar types, and native argument order. Editing it changes the wrapper
API; it does not change the Fortran implementation.

### Build from the contract

After editing the contract, rebuild the same Python API from the package entry
and the original Fortran implementation:

```bash
python3 -m x2py contracts/__init__.pyi \
  --native-fortran-sources points.f90 \
  --out geometry \
  --out-dir build/geometry_from_pyi
```

The contract build has the same import name and module layout:

```text
.
  geometry.so
  build/geometry_from_pyi/
    geometry.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

Import the extension from the explicit build directory when needed:

```python
import sys

import numpy as np

sys.path.insert(0, "build/geometry_from_pyi")
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
points.move(item, np.float64(1.0), np.float64(-2.0))
print(points.norm_squared(item))  # 20.0
```

### Inspect the native build

Use `--verbose` when you want to see the compiler commands and confirm which
wrapper flags reached the build:

```bash
python3 -m x2py points.f90 \
  --out geometry_debug \
  --out-dir build/geometry_debug \
  --jobs 4 \
  --verbose \
  --compiler gfortran \
  --wrapper-fortran-flags=-O2 \
  --wrapper-c-flags=-O2
```

The verbose output includes native source compilation, generated bridge
compilation, generated Python binding compilation, and the final link command.
Dependency-ready source files and the generated binding may compile
concurrently; `--jobs 1` selects a serial diagnostic build.
The custom wrapper flags appear in the relevant command lines:

```text
<fortran compiler> ... -O2 ... generated bridge ...
<python-binding compiler> ... -O2 ... generated Python binding ...
<fortran compiler> -shared ... -O2 ... geometry_debug ...
```

## How it works

```text
Fortran sources
  -> compiler preprocessing and target-type probing
  -> Fortran parser
  -> semantic IR construction
  -> post-IR policy completion and ordered wrapper plan
  -> direct native-bridge and Python-binding lowering
  -> native compilation and shared-library link
  -> importable Python extension
```

<!-- X2PY_C_DOCS_START
```text
Fortran sources
  -> compiler preprocessing and target-type probing
  -> Fortran parser
  -> semantic IR construction
  -> post-IR policy completion and ordered wrapper plan
  -> direct Fortran bind(C) bridge lowering
  -> direct C/CPython binding lowering and native binding support
  -> native compilation and shared-library link
  -> importable Python extension
```
X2PY_C_DOCS_END -->

For diagnostic and inspection commands beyond the main build path, start with
`python3 -m x2py --help`, then continue to the
[CLI command reference](docs/user/reference/cli-commands.md).

<!-- X2PY_C_DOCS_START
The runtime build path accepts one or more ordered Fortran sources. C parsing,
semantic IR, and `.pyi` are implemented, but wrapping user-supplied
C libraries is a later backend. The generated C code used internally by the
Fortran wrapper is not that future C-input backend.
The [generated target datatype mapping example](docs/user/reference/semantic-ir.md#generated-linux-x86_64-mapping-example)
shows how the GitHub Actions C and Fortran scalar types map to NumPy dtypes.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
### C
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C inputs require explicit C mode. These commands parse the checked C API
fixture, inspect semantic IR, and generate its `.pyi`:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Input (`tests/c/fixtures/native/general/math_api.h`):
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-source: tests/c/fixtures/native/general/math_api.h -->
<!-- X2PY_C_DOCS_START
```c
#ifndef X2PY_GENERAL_MATH_API_H
#define X2PY_GENERAL_MATH_API_H

double norm2(int n, const double x[static 1]);
void scale(int n, double alpha, double x[static 1]);
double dot(int n, const double *restrict x, const double *restrict y);
void fill_identity3(double a[static 3][3]);

#endif
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: exact -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
File: tests/c/fixtures/native/general/math_api.h
  Language: c
  Functions: 4
  Structs: 0
  Unions: 0
  Enums: 0
  Typedefs: 0
  Variables: 0
  Macros: 0
  Includes: 0
  Diagnostics: 0
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: run -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: run -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: exact -->
<!-- X2PY_C_DOCS_START
```bash
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
File: tests/c/fixtures/native/general/math_api.h
  Source: c
  Semantic modules: math_api
```
X2PY_C_DOCS_END -->

## Native Project Inputs

Fortran builds default to `gfortran`. For a real project, replace the checked
input path with your source path, use `--help` to choose the compiler and native
project options you need, and enable `--verbose` when you want to audit the
exact compiler and linker commands.

<!-- X2PY_C_DOCS_START
The CLI uses compiler preprocessing for native source. C defaults to `cc` and
Fortran defaults to `gfortran`. Pass the native project's important compiler
and target flags:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py include/api.h &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler clang \
  -I include \
  -D API_EXPORT= \
  &#45;&#45;std c11 \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/sdk
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Compiler-backed semantic and `.pyi` stages also measure and cache
target datatype facts. C probing covers primitive ABI widths and signedness;
Fortran probing resolves kind expressions and measures intrinsic storage.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C projects can use a compilation database:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py src/api.c &#45;&#45;language c &#45;&#45;semantics \
  &#45;&#45;compile-commands build/compile_commands.json
```
X2PY_C_DOCS_END -->

Use `--out` to select generated contract locations, wrapper module names, or
explicit build directories, depending on the command mode.

## Python API

Public entrypoints cover Fortran extension builds, parsing, semantic
conversion and `.pyi` emission:

```python
from x2py import build_fortran_extension

result = build_fortran_extension(
    "points.f90",
    output_name="geometry",
    output_dir="build/geometry_api",
)
print(result.module_name)
print(result.shared_library)
```

Parser and semantic entrypoints remain available independently for controlled
strings, focused tests, and already-preprocessed inputs.

<!-- X2PY_C_DOCS_START
```python
from x2py import (
    c_file_to_semantic_modules,
    emit_module_stubs,
    parse_c_file,
)

parsed = parse_c_file("int add(int a, int b);", filename="api.h")
modules = c_file_to_semantic_modules(parsed)
stubs = emit_module_stubs(modules)
```
X2PY_C_DOCS_END -->

For native projects with macros, includes, or target flags, use the
compiler-preprocessed CLI path or an equivalent preprocessing configuration.

## Development

Run the full suite from the repository root:

```bash
PYTHONPATH=. python3 -m pytest -q
```

## License

x2py is distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Said Hadjout.

Using x2py does not impose the MIT License on the user's native sources or on
wrapper code derived from those inputs. Users may distribute generated
wrappers under terms of their choice. Files copied from x2py's
`binding_support/` package remain MIT-licensed and must retain the included
license notice when redistributed.

## Documentation

- **[Documentation](https://pynumlab.github.io/x2py/)** — Learn how to install and use x2py
- **[Getting Started](https://pynumlab.github.io/x2py/user/getting-started/)** — Installation, verification, standalone procedures, modules, and rebuild workflow
- **[User Guide](https://pynumlab.github.io/x2py/user/guide/)** — Data types, functions, modules, arrays, derived types, callbacks, ownership, and runtime behavior
<!--
- **[Tutorials](docs/user/tutorials/index.md)** — Step-by-step walkthroughs
- **[CLI Reference](docs/user/reference/cli-commands.md)** — Complete command-line documentation
- **[Language Support](docs/user/language-support/index.md)** — What is supported, partially supported, or planned
- **[FAQ](docs/user/faq/index.md)** — Concise answers to common questions
- **[Troubleshooting](docs/user/troubleshooting/index.md)** — Solutions for installation, compiler, build, runtime, and platform issues
- **[Changelog](docs/user/changelog/index.md)** — User-visible changes by release
-->
