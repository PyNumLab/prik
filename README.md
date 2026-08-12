# PRIK — Python Runtime Interop Kit

**Generate native Python bindings for Fortran, with editable `.pyi` contracts
and Pythonic APIs.**

PRIK generates native Python bindings from Fortran projects, producing
importable extensions and editable `.pyi` contracts for Pythonic APIs.

[![Tests](https://github.com/PyNumLab/prik/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/tests.yml)
[![Static Analysis](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml)
[![codecov](https://codecov.io/gh/PyNumLab/prik/graph/badge.svg?token=QZRRCS5YO6)](https://codecov.io/gh/PyNumLab/prik)
[![DOI](https://zenodo.org/badge/1241799694.svg)](https://doi.org/10.5281/zenodo.21881987)

It preserves modules, derived types, arrays, callbacks, and native behavior so
you can shape the resulting API without writing low-level binding code.

**Project status: Alpha.** Core Fortran wrapper workflows are
implemented and tested across supported compilers, but public APIs may still
change before `1.0`.

**PRIK starts with Fortran-to-Python.** Its semantic contract model is designed
to support more native languages over time.

<!-- PRIK_C_DOCS_START
Fortran-to-Python wrapper generation plus wrapper-oriented parser and semantic
interface tooling for Fortran and C. PRIK builds importable CPython extensions
from Fortran sources, extracts native declarations into language-neutral
semantic IR, emits editable `.pyi` interfaces, and reports unsupported or
incomplete contracts before code generation.
PRIK_C_DOCS_END -->

[Read the documentation](https://pynumlab.github.io/prik/) for installation,
the user guide, examples, and reference material.

## Contents

- [Proven on real libraries](#proven-on-real-libraries)
- [See it in action](#see-it-in-action)
- [Key Features](#key-features)
- [Performance](#performance)
- [Current limitations](#current-limitations)
- [Installation & Quick Start](#installation--quick-start)
- [How it works](#how-it-works)
- [Native Project Inputs](#native-project-inputs)
- [Python API](#python-api)
- [Development](#development)
- [Citation](#citation)
- [License](#license)
- [Documentation](#documentation)

## Proven on real libraries

The maintained projects build real numerical libraries with PRIK and validate
their Python behavior, not just whether the generated wrapper compiles.

| Project | Validated surface | Capabilities demonstrated |
| --- | --- | --- |
| [BLAS](examples/blas/README.md) | All 155 discovered routines | Scalar, vector, and matrix operations; increments and leading dimensions; in-place updates; independent expectations and f2py comparisons |
| [LAPACK](examples/lapack/README.md) | Complete implementation corpus with 127 reviewed double-precision routines | Linear solves, factorizations, eigenproblems, singular values, work arrays, and large multi-source linking |
| [FFTPACK](examples/fftpack/README.md) | All 31 public procedures | Fourier, cosine, and sine transforms; low-level workspaces; in-place arrays; allocatable results; NumPy and SciPy oracles |
| [MINPACK](examples/minpack/README.md) | All 22 public procedures | Python callbacks; nonlinear and least-squares solvers; Jacobian and workspace writeback; immutable module constants |

Together they exercise arrays, callbacks, workspaces, in-place mutation,
allocatable results, module constants, and multi-file linking. The dedicated
Real Libraries CI lane builds and tests all four projects.

The complete example below builds with one command:

```bash
python3 -m prik points.f90 --out geometry
```

## See it in action

Create `points.f90`:

<!-- prik-doc-source: tests/fortran/building_shared_library/end_to_end/fixtures/native/home_points.f90 -->
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

No manual bindings are required. From this source, PRIK creates a Python
namespace, a class with accessible fields, a mutating procedure, and a
function.

Want a different Python API? Edit the generated `.pyi` contract to rename or
hide exports, flatten namespaces, define constructors and methods, or create
overloads. The
[contract guide](https://pynumlab.github.io/prik/user/reference/pyi-contracts/)
shows the available edits.

## Key Features

- **Native APIs that feel like Python.** Fortran modules become Python
  namespaces, while derived types become classes with fields and methods.
- **First-class NumPy array interop.** Pass ordinary NumPy arrays to native
  procedures, including multidimensional and in-place data, with generated
  dtype, shape, layout, and mutability handling at the language boundary.
- **Managed access to native memory.** Expose allocatable and pointer arrays
  without hiding their ownership, lifetime, allocation, or release operations.
- **Python callbacks and native overloads.** Pass Python callables into Fortran
  and expose generic interfaces as familiar Python overloads.
- **Generated APIs you can reshape.** Edit the generated `.pyi` contract to
  rename, hide, reorganize, or overload the public interface, backed by readable
  generated docstrings.
- **Unsupported contracts fail before the build.** PRIK identifies the exact
  boundary and reason before attempting code generation or compilation.

## Performance

**Low wrapper overhead, measured against NumPy's f2py.**

The included benchmark suite runs both tools against the same Fortran kernels
through their normal generated interfaces. Results are machine-dependent; the
charts below come from the latest successfully deployed benchmark snapshot.

**Runtime-call performance** — values above `1.0×` mean PRIK is faster.

[![Relative performance of PRIK and f2py across call, vector, and matrix workloads. Values above 1.0 mean PRIK is faster.](https://pynumlab.github.io/prik/user/assets/performance-comparison.svg)](https://pynumlab.github.io/prik/user/performance/)

**Clean end-to-end build time** — lower times are better.

[![Clean end-to-end build time for PRIK and f2py under development and optimized compiler profiles. Lower times are better.](https://pynumlab.github.io/prik/user/assets/build-time-comparison.svg)](https://pynumlab.github.io/prik/user/performance/#clean-build-time)

[See the complete results, test environment, and one-command reproduction instructions.](https://pynumlab.github.io/prik/user/performance/)

## Current limitations

PRIK does not yet support:

- arrays of derived types;
- procedure pointers, including procedure-pointer module variables and callbacks
  retained after the wrapped call; or
- polymorphic outputs, mutable polymorphic arguments, polymorphic arrays,
  unlimited polymorphism (`class(*)`), abstract types, and deferred bindings.

## Installation & Quick Start

PRIK requires **Python 3.10 or newer**, NumPy, Python development headers,
standard build tools, and Fortran and C compilers. GNU Fortran is the default
and is tested on Linux and macOS. LLVM Flang is tested on both platforms;
Intel IFX is tested on Linux.

Install the published PRIK package in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install prik
```

Check the installation:

```bash
prik --version
python3 -m prik --help
```

Contributors can instead clone
[`PyNumLab/prik`](https://github.com/PyNumLab/prik) and install an editable
checkout with `python3 -m pip install -e ".[qa]"`.

With the `points.f90` source from above in the current directory, build the
extension:

```bash
python3 -m prik points.f90 --out geometry
```

`--out geometry` selects the import name and the final shared-library name.
PRIK places the stable import file beside the source and keeps generated build
artifacts under `__prik__/`:

```text
.
  points.f90
  geometry.so
  __prik__/
    geometry.<extension-suffix>.so
    generated-wrapper sources
    binding_support/
```

The Python code shown at the top of this README can now import `geometry`
directly.

Use `--out-dir` to place the ABI-specific extension and generated files in a
chosen build directory:

```bash
python3 -m prik points.f90 \
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
python3 -m prik generate --pyi points.f90 --out contracts
```

The command preserves the Fortran module as a contract module:

```text
contracts/
  __init__.pyi
  points.pyi
```

Generated `contracts/points.pyi`:

```python
from prik.contracts import Addr, Arg, Float64, native_call

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
python3 -m prik contracts/__init__.pyi \
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
python3 -m prik points.f90 \
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

<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

For diagnostic and inspection commands beyond the main build path, start with
`python3 -m prik --help`, then continue to the
[CLI command reference](docs/user/reference/cli-commands.md).

<!-- PRIK_C_DOCS_START
The runtime build path accepts one or more ordered Fortran sources. C parsing,
semantic IR, and `.pyi` are implemented, but wrapping user-supplied
C libraries is a later backend. The generated C code used internally by the
Fortran wrapper is not that future C-input backend.
The [generated target datatype mapping example](docs/user/reference/semantic-ir.md#generated-linux-x86_64-mapping-example)
shows how the GitHub Actions C and Fortran scalar types map to NumPy dtypes.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### C
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C inputs require explicit C mode. These commands parse the checked C API
fixture, inspect semantic IR, and generate its `.pyi`:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Input (`tests/c/fixtures/native/general/math_api.h`):
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-source: tests/c/fixtures/native/general/math_api.h -->
<!-- PRIK_C_DOCS_START
```c
#ifndef PRIK_GENERAL_MATH_API_H
#define PRIK_GENERAL_MATH_API_H

double norm2(int n, const double x[static 1]);
void scale(int n, double alpha, double x[static 1]);
double dot(int n, const double *restrict x, const double *restrict y);
void fill_identity3(double a[static 3][3]);

#endif
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: run -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: run -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact -->
<!-- PRIK_C_DOCS_START
```bash
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```text
File: tests/c/fixtures/native/general/math_api.h
  Source: c
  Semantic modules: math_api
```
PRIK_C_DOCS_END -->

## Native Project Inputs

Fortran builds default to `gfortran`. For a real project, replace the checked
input path with your source path, use `--help` to choose the compiler and native
project options you need, and enable `--verbose` when you want to audit the
exact compiler and linker commands.

<!-- PRIK_C_DOCS_START
The CLI uses compiler preprocessing for native source. C defaults to `cc` and
Fortran defaults to `gfortran`. Pass the native project's important compiler
and target flags:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik include/api.h &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler clang \
  -I include \
  -D API_EXPORT= \
  &#45;&#45;std c11 \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/sdk
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Compiler-backed semantic and `.pyi` stages also measure and cache
target datatype facts. C probing covers primitive ABI widths and signedness;
Fortran probing resolves kind expressions and measures intrinsic storage.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C projects can use a compilation database:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik src/api.c &#45;&#45;language c &#45;&#45;semantics \
  &#45;&#45;compile-commands build/compile_commands.json
```
PRIK_C_DOCS_END -->

Use `--out` to select generated contract locations, wrapper module names, or
explicit build directories, depending on the command mode.

## Python API

Root entrypoints cover normal Fortran extension builds. Advanced parsing,
semantic conversion, and `.pyi` emission use their owning packages:

```python
from prik import build_fortran_extension

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

<!-- PRIK_C_DOCS_START
```python
from prik.parsers.c import parse_c_file
from prik.pipeline.pyi import emit_module_stubs
from prik.semantics.c2ir import c_file_to_semantic_modules

parsed = parse_c_file("int add(int a, int b);", filename="api.h")
modules = c_file_to_semantic_modules(parsed)
stubs = emit_module_stubs(modules)
```
PRIK_C_DOCS_END -->

For native projects with macros, includes, or target flags, use the
compiler-preprocessed CLI path or an equivalent preprocessing configuration.

## Development

PRIK is created and maintained by Said Hadjout, with extensive use of
AI-assisted software-development tools, particularly OpenAI Codex, for
implementation, refactoring, testing, debugging, documentation, investigation,
and review assistance.

Architecture, interoperability semantics, feature design, acceptance criteria,
and final integration remain maintainer-directed. AI-assisted changes are
subject to the same tests, compiler validation, real-library checks, and quality
requirements as other changes.

Run the full suite from the repository root:

```bash
PYTHONPATH=. python3 -m pytest -q
```

## Citation

If you use PRIK in research, cite the release you used. PRIK `0.2.1` is
archived at [10.5281/zenodo.21881988](https://doi.org/10.5281/zenodo.21881988),
while [10.5281/zenodo.21881987](https://doi.org/10.5281/zenodo.21881987) covers
all releases. Machine-readable metadata is available in
[`CITATION.cff`](CITATION.cff).

## License

PRIK is distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Said Hadjout.

Using PRIK does not impose the MIT License on the user's native sources or on
wrapper code derived from those inputs. Users may distribute generated
wrappers under terms of their choice. Files copied from PRIK's
`binding_support/` package remain MIT-licensed and must retain the included
license notice when redistributed.

## Documentation

- **[Documentation](https://pynumlab.github.io/prik/)** — Learn how to install and use PRIK
- **[Getting Started](https://pynumlab.github.io/prik/user/getting-started/)** — Installation, verification, standalone procedures, modules, and rebuild workflow
- **[User Guide](https://pynumlab.github.io/prik/user/guide/)** — Data types, functions, modules, arrays, derived types, callbacks, ownership, and runtime behavior
- **[Changelog](CHANGELOG.md)** — User-visible changes by release
<!--
- **[Tutorials](docs/user/tutorials/index.md)** — Step-by-step walkthroughs
- **[CLI Reference](docs/user/reference/cli-commands.md)** — Complete command-line documentation
- **[Language Support](docs/user/language-support/index.md)** — What is supported, partially supported, or planned
- **[FAQ](docs/user/faq/index.md)** — Concise answers to common questions
- **[Troubleshooting](docs/user/troubleshooting/index.md)** — Solutions for installation, compiler, build, runtime, and platform issues
-->
