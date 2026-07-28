# x2py

x2py generates importable Python extensions from Fortran sources, extracts
native declarations into language-neutral semantic IR, emits editable `.pyi`
interfaces, and reports unsupported or incomplete contracts before code
generation.

<!-- X2PY_C_DOCS_START
Fortran-to-Python wrapper generation plus wrapper-oriented parser and semantic
interface tooling for Fortran and C. x2py builds importable CPython extensions
from Fortran sources, extracts native declarations into language-neutral
semantic IR, emits editable `.pyi` interfaces, and reports unsupported or
incomplete contracts before code generation.
X2PY_C_DOCS_END -->

[![Quality](https://github.com/PyNumLab/x2py/actions/workflows/quality.yml/badge.svg?branch=main)](https://github.com/PyNumLab/x2py/actions/workflows/quality.yml)
[![codecov](https://codecov.io/gh/PyNumLab/x2py/graph/badge.svg?token=QZRRCS5YO6)](https://codecov.io/gh/PyNumLab/x2py)

## Installation & Quick Start

Requires **Python 3.10+**.

```bash
# Install in development mode
pip install -e .

# See all available commands
python3 -m x2py --help
```

Expected result: the install command completes successfully, and `--help`
prints the CLI usage with input selection, wrapper builds, `.pyi` contracts,
verbose mode, and output options.

The default user-facing action for a single Fortran source is to build a Python
extension. Create `scale.f90` with this input:

<!-- x2py-doc-source: tests/data/fortran/wrapper/scale.f90 -->
```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

The concise `python3 -m x2py --help` examples reuse this `scale.f90`
source. Help entries labeled "README Quick Start" refer to the complete source
and workflow in this section.

Build it with the default output locations:

```bash
python3 -m x2py scale.f90
```

By default, x2py writes generated build artifacts, including the ABI-suffixed
extension, under `__x2py__/` in the directory where you run the command. It
also creates a stable `scale.so` import alias alongside your source file, so
you can simply `import scale`.

```bash
.
  scale.f90
  scale.so
  __x2py__/
    scale.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

Name the Python extension and final `.so` explicitly with `--out NAME`:

```bash
python3 -m x2py scale.f90 --out SCALE
```

Expected result:

```text
.
  scale.f90
  SCALE.so
  __x2py__/
    SCALE.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

For a wrapper build, `--out SCALE` selects the Python module name and the final
shared-library filename. This first example is a standalone procedure, so it is
exposed directly at the extension root.

Use `--out-dir` when you want the ABI-specific shared library and generated
intermediates in an explicit build directory:

```bash
python3 -m x2py scale.f90 \
  --out SCALE \
  --out-dir build/SCALE
```

Expected result:

```text
.
  SCALE.so
  build/SCALE/
    SCALE.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

Generate the semantic `.pyi` contract for the same source:

```bash
python3 -m x2py generate --pyi scale.f90 --out contracts
```

The command writes the contract package:

```text
contracts/
  __init__.pyi
```

Expected contract (`contracts/__init__.pyi`):

```python
from x2py.contracts import Addr, Arg, Float64, external, native_call

@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

The semantic contract does not repeat Fortran `intent`. Source `intent` helps
x2py choose the generated Python arguments and results, while `@native_call`
records the exact native argument order and transport. The compiled native
procedure keeps its own `intent`; editing the `.pyi` changes the wrapper call
contract, not the native procedure declaration.

Then build the shared library from the package-entry `.pyi` contract and the
same native implementation source:

```bash
python3 -m x2py contracts/__init__.pyi \
  --native-fortran-sources scale.f90 \
  --out SCALE \
  --out-dir build/SCALE_from_pyi
```

Use `--out NAME` with wrapper builds when you want the import name and final
`.so` filename to differ from the default inferred name.

The `.pyi` build produces the same importable extension shape:

```text
.
  SCALE.so
  build/SCALE_from_pyi/
    SCALE.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

The direct source build exposes the standalone procedure at the extension root:

```python
import sys

import numpy as np

sys.path.insert(0, "build/SCALE")
import SCALE

print(SCALE.scale(np.float64(3.0), np.float64(2.5)))  # 7.5
```

The package-entry `.pyi` build exposes the same Python API:

```python
import sys

import numpy as np

sys.path.insert(0, "build/SCALE_from_pyi")
import SCALE

print(SCALE.scale(np.float64(3.0), np.float64(2.5)))  # 7.5
```

Both calls print:

```text
7.5
```

For a small derived-type wrapper, create `points.f90`:

```fortran
module points
  implicit none
  type :: point
    real(8) :: x
    real(8) :: y
  end type point
contains
  subroutine move(item, dx, dy)
    type(point), intent(inout) :: item
    real(8), intent(in) :: dx
    real(8), intent(in) :: dy
    item%x = item%x + dx
    item%y = item%y + dy
  end subroutine move

  real(8) function norm_squared(item) result(value)
    type(point), intent(in) :: item
    value = item%x * item%x + item%y * item%y
  end function norm_squared
end module points
```

Generate its semantic contract:

```bash
python3 -m x2py generate --pyi points.f90 --out contracts
```

Expected contract (`contracts/points.pyi`):

```python
from x2py.contracts import Addr, Arg, Float64, native_call

class point:
    def __init__(
        self,
        *,
        x: Float64 = ...,
        y: Float64 = ...
    ) -> None: ...

    x: Float64
    y: Float64

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

Build and import it with a clean Python module name:

```bash
python3 -m x2py points.f90 --out geometry --out-dir build/geometry
```

```python
import sys

import numpy as np

sys.path.insert(0, "build/geometry")
import geometry

p = geometry.points.point(x=np.float64(3.0), y=np.float64(4.0))
geometry.points.move(p, np.float64(1.0), np.float64(-2.0))

print(p.x, p.y)
print(geometry.points.norm_squared(p))
```

Expected result:

```text
4.0 2.0
20.0
```

Use `--verbose` when you want to see the compiler commands and confirm which
wrapper flags reached the build:

```bash
python3 -m x2py scale.f90 \
  --out SCALE_debug \
  --out-dir build/SCALE_debug \
  --verbose \
  --compiler gfortran \
  --wrapper-fortran-flags=-O2 \
  --wrapper-c-flags=-O2
```

The verbose output includes native source compilation, generated bridge
compilation, generated Python binding compilation, and the final link command.
The custom wrapper flags appear in the relevant command lines:

```text
<fortran compiler> ... -O2 ... generated bridge ...
<python-binding compiler> ... -O2 ... generated Python binding ...
<fortran compiler> -shared ... -O2 ... SCALE_debug ...
```

Standalone procedures are the smallest wrapper surface and therefore come
first. Contained Fortran module procedures are preserved under Python child
modules; continue with the
[first wrapped module](docs/user/getting-started/first-wrapped-module.md) for that
layout and for public module state.

The runtime wrapper mechanism is:

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
Input (`tests/data/c/general/math_api.h`):
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-source: tests/data/c/general/math_api.h -->
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
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
File: tests/data/c/general/math_api.h
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
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: run -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
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
File: tests/data/c/general/math_api.h
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
    "scale.f90",
    output_name="SCALE",
    output_dir="build/SCALE",
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

## Supported Scope

x2py preserves wrapper-relevant declarations, signatures, types, source
locations, include/use relationships, diagnostics, and semantic metadata.
Current support includes:

- free-form and fixed-form Fortran, procedures, modules, derived types,
  imports, arrays, and wrapper-relevant declaration attributes;
- language-neutral semantic IR and editable `.pyi` interfaces;
- compiled Python extensions from one or more ordered fixed-form or free-form
  Fortran sources, with an optional GNU Make build;
- documented runtime wrapper behavior for scalar and array calls, strings,
  module state, derived types, generic interfaces, optional and output
  arguments, and immediate call-scoped Python callbacks. The
  [language feature matrix](docs/user/language-support/feature-matrix.md) is the
  authoritative support-status summary.

<!-- X2PY_C_DOCS_START
- compiled CPython extensions from one or more ordered fixed-form or free-form
  Fortran sources, including generated Fortran/C bridges and an optional GNU
  Make build;
- C declarations and definitions, variables, typedefs, aggregates, enums,
  pointers, arrays, function pointers, includes, and preprocessing facts;
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Runtime wrapper generation from user C inputs is not implemented yet. It will
reuse the shared semantic contracts after the C backend and its ownership,
ABI, and runtime tests are complete.
X2PY_C_DOCS_END -->

x2py is not a full compiler frontend. It does not silently infer pointer
ownership, callback lifetime, ABI shims, or Python-visible projections.

## Documentation


- **[Getting Started](docs/user/getting-started/index.md)** — Installation, verification, standalone procedures, modules, and rebuild workflow
- **[User Guide](docs/user/guide/index.md)** — Detailed guidance on data types, functions, subroutines, modules, arrays, derived types, callbacks, ownership, runtime behavior, and packaging
<!--
- **[Tutorials](docs/user/tutorials/index.md)** — Step-by-step walkthroughs
- **[Examples Cookbook](docs/user/examples/verified-cookbook.md)** — Ready-to-use Fortran wrapper patterns and recipes
- **[CLI Reference](docs/user/reference/cli-commands.md)** — Complete command-line documentation
- **[Language Support](docs/user/language-support/index.md)** — What is supported, partially supported, or planned
- **[FAQ](docs/user/faq/index.md)** — Concise answers to common questions
- **[Troubleshooting](docs/user/troubleshooting/index.md)** — Solutions for installation, compiler, build, runtime, and platform issues
- **[Changelog](docs/user/changelog/index.md)** — User-visible changes by release
-->

Run the full suite from the repository root:

```bash
PYTHONPATH=. python3 -m pytest -q
```
