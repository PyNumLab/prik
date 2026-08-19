<p align="center">
  <img src="docs/user/assets/prik-logo.png"
       alt="PRIK — Bring Native Code to Python"
       width="450">
</p>

**PRIK (Python Runtime Interop Kit)** generates native Python bindings from Fortran projects,
producing importable extensions and editable `.pyi` contracts that let you shape Pythonic APIs.

[![Tests](https://github.com/PyNumLab/prik/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/tests.yml)
[![Static Analysis](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml)
[![codecov](https://codecov.io/gh/PyNumLab/prik/graph/badge.svg?token=QZRRCS5YO6)](https://codecov.io/gh/PyNumLab/prik)
[![DOI](https://zenodo.org/badge/1241799694.svg)](https://doi.org/10.5281/zenodo.21881987)

It preserves modules, derived types, arrays, callbacks, and native behavior
while letting you reshape the resulting Python API through editable `.pyi`
contracts instead of writing low-level binding code.

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

- [See it in action](#see-it-in-action)
- [Proven on real libraries](#proven-on-real-libraries)
- [Key Features](#key-features)
- [Performance](#performance)
- [Current limitations](#current-limitations)
- [Installation & Quick Start](#installation--quick-start)
- [How it works](#how-it-works)
- [Python API](#python-api)
- [Development](#development)
- [Citation](#citation)
- [License](#license)
- [Documentation](#documentation)

## See it in action

PRIK turns the Fortran source below into an importable Python extension with one command:

```bash
python3 -m prik points.f90 --out geometry
```

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

**Default Python API:**

```python
import numpy as np
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
points.move(item, np.float64(1.0), np.float64(-2.0))

print(item.x, item.y)             # 4.0 2.0
print(points.norm_squared(item))  # 20.0
```

No manual bindings are required. PRIK preserves the module and derived-type
structure and exposes the procedures directly to Python.

Generate the editable contract:

```bash
python3 -m prik generate --pyi points.f90 --out contracts
```

Want a more Pythonic API? Edit `contracts/points.pyi`:

```python
from prik.contracts import Addr, Arg, Float64, Pass, bind, native_call

class point:
    x: Float64 = 0.0
    y: Float64 = 0.0

    def __init__(self, *, x: Float64 = 0.0, y: Float64 = 0.0) -> None: ...

    @bind("move")
    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def translate(self, dx: Float64, dy: Float64) -> None: ...

    @bind("norm_squared")
    @native_call([Pass()])
    def norm_squared(self) -> Float64: ...
```

`@bind("move")` keeps the original native target while the declaration's
placement and name define the Python-facing API. `Pass()` supplies the
receiver (`self`) to the native call; `Addr(Arg(...))` passes the remaining
arguments by address as required by the native calling convention.

Build from the contract:

```bash
python3 -m prik contracts/__init__.pyi \
  --native-fortran-sources points.f90 \
  --out geometry
```

The native Fortran is unchanged, but the Python surface is now:

```python
import numpy as np
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
item.translate(np.float64(1.0), np.float64(-2.0))

print(item.x, item.y)       # 4.0 2.0
print(item.norm_squared())  # 20.0
```

The contract reorganizes native procedures into methods and renames them
without changing the underlying Fortran implementation.

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
- **Editable contracts for reshaping APIs.** Edit the generated `.pyi` contract to
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

PRIK rejects these forms rather than wrapping them unsafely. Most fail before
code generation with a diagnostic naming the boundary and the reason.

**Types and arrays**

- arrays of derived types, and assumed-type `type(*)` arrays;
- character arrays that cannot be represented as a fixed-width NumPy bytes
  dtype, `allocatable` and `pointer` character *fields*, and scalar character
  *module variables*.
- quad precision — `real(16)` and `complex(16)` — which has no portable NumPy
  dtype. Everything narrower is supported.

**Procedures and polymorphism**

- procedure-pointer module variables, and
  callbacks retained after the wrapped call returns;
- polymorphic outputs, mutable polymorphic arguments,
  unlimited polymorphism (`class(*)`), abstract types, and deferred bindings;
- constructor overload sets whose candidates are ambiguous or incomplete.

**Storage and ownership**

- establishing a *new* pointer target — `allocate` and `resize` — which stays
  gated behind an explicit `PointerPolicy`. Operations on the target a handle
  already names (`deallocate`, `associate`, `nullify`) need no annotation, and
  carry the same responsibility as writing them in Fortran. prik never frees a
  native target on your behalf, so a wrapped procedure returning freshly
  allocated storage leaks until you call `deallocate()`. Allocatable handles
  additionally get `resize` without an annotation.

The [language feature matrix](https://pynumlab.github.io/prik/user/language-support/feature-matrix/)
records the full support status of every feature with its evidence.

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

`--out geometry` sets the Python import name and the shared-library name.
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

The extension can now be imported directly through the `geometry` package.
For the editable-contract workflow (generate → edit → rebuild), see
[See it in action](#see-it-in-action) above.

Use `--out-dir` to choose where ABI-specific build artifacts are written:

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

### Inspect the native build

Fortran builds use `gfortran` by default. For real projects, pass one or more
source files, select another supported compiler when needed, and use `--verbose`
to inspect the exact compiler and linker commands.

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

For diagnostic and inspection commands beyond the main build path, start with
`python3 -m prik --help`.

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

If you use PRIK in research, cite the release you used.
[10.5281/zenodo.21881987](https://doi.org/10.5281/zenodo.21881987) covers all
archived releases and links to their version-specific records. Machine-readable
metadata is available in
[`CITATION.cff`](CITATION.cff).

## License

PRIK is distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Said Hadjout.

Using PRIK does not impose the MIT License on the user's native sources or on
wrapper code derived from those inputs. Users may distribute generated
wrappers under terms of their choice. Bundled native-support files copied into
generated builds remain MIT-licensed and must retain the included license
notice when redistributed.

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
