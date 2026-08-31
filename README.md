<p align="center">
  <img src="https://raw.githubusercontent.com/PyNumLab/prik/main/docs/user/assets/prik-logo.png"
       alt="PRIK — Bring Native Code to Python"
       width="450">
</p>

**PRIK (Python Runtime Interop Kit)** generates native Python bindings for
Fortran and C code.

[![Tests](https://github.com/PyNumLab/prik/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/tests.yml)
[![Static Analysis](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml/badge.svg?branch=main)](https://github.com/PyNumLab/prik/actions/workflows/static-analysis.yml)
[![codecov](https://codecov.io/gh/PyNumLab/prik/graph/badge.svg?token=QZRRCS5YO6)](https://codecov.io/gh/PyNumLab/prik)
[![DOI](https://zenodo.org/badge/1241799694.svg)](https://doi.org/10.5281/zenodo.21881987)

**Try it without installing anything.** The quickstart notebook compiles a
Fortran cell and a C cell, then reshapes the generated API by editing its
`.pyi` contract.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PyNumLab/prik/blob/main/examples/notebooks/quickstart.ipynb)

It preserves modules, derived types, arrays, callbacks, and native behavior
while letting you reshape the resulting Python API through editable `.pyi`
contracts instead of writing low-level binding code.

**Project status: Alpha.** Core Fortran workflows and the currently supported
C wrapper features are implemented and tested across supported compilers, but
public APIs may still change before `1.0`.

PRIK supports both languages. Fortran currently has the broader, more mature
wrapper surface. C currently supports a focused wrapper subset: primitive
values, one-level pointers, NumPy arrays, and strings. In both languages, editable
`.pyi` contracts let you shape the Python API. See the [C User
Guide](https://pynumlab.github.io/prik/user/guide/c/) for C workflows and [C
Support](https://pynumlab.github.io/prik/user/language-support/c-support/) for
current coverage.

[Read the documentation](https://pynumlab.github.io/prik/) for installation,
the user guide, examples, and reference material.

## Contents

- [See it in action](#see-it-in-action)
- [Proven on real libraries](#proven-on-real-libraries)
- [Key Features](#key-features)
- [Performance](#performance)
- [Current Fortran limitations](#current-fortran-limitations)
- [C support](#c-support)
- [Current C limitations](#current-c-limitations)
- [Installation & Quick Start](#installation--quick-start)
- [IPython and Jupyter](#ipython-and-jupyter)
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

<!-- prik-doc-source: tests/fortran/infrastructure/building/end_to_end/fixtures/native/home_points.f90 -->
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

    @native_call([Pass()])
    def norm_squared(self) -> Float64: ...
```

`@bind("move")` is needed because `translate` has a different Python name.
`norm_squared` needs no `@bind`: matching Python and native names select the
same procedure. `Pass()` supplies the receiver (`self`) to the native call;
`Addr(Arg(...))` passes the remaining arguments by address as required by the
native calling convention.

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

The [`.pyi` Format](https://pynumlab.github.io/prik/user/reference/pyi-format/)
defines the contract language. [Editing `.pyi`
Contracts](https://pynumlab.github.io/prik/user/reference/pyi-contracts/)
provides task-oriented recipes for reshaping the API.

## Proven on real libraries

PRIK builds and numerically tests seven maintained libraries, not just generated
wrappers.

| Project | Native language and PRIK input | Validated surface |
| --- | --- | --- |
| [BLAS](https://pynumlab.github.io/prik/user/examples/fortran/blas-wrapper/) | Fortran source/interfaces | 155 routines: vectors, matrices, in-place updates, and f2py comparisons |
| [LAPACK](https://pynumlab.github.io/prik/user/examples/fortran/lapack-wrapper/) | Fortran source/interfaces | 127 float64 routines: solves, factorizations, eigenproblems, and SVD |
| [FFTPACK](https://pynumlab.github.io/prik/user/examples/fortran/fftpack-wrapper/) | Fortran source/interfaces | 31 Fourier, cosine, and sine transform procedures |
| [MINPACK](https://pynumlab.github.io/prik/user/examples/fortran/minpack-wrapper/) | Fortran source/interfaces | 22 nonlinear and least-squares procedures, including callbacks |
| [BSPLINE-FORTRAN](https://pynumlab.github.io/prik/user/examples/fortran/bspline-wrapper/) | Fortran source/interfaces | 15 interpolation routines and modern Fortran classes |
| [libm](https://pynumlab.github.io/prik/user/examples/c/libm-wrapper/) | C declarations from `<math.h>`; link compiled platform libm | 60 target-generated ISO C99 math functions |
| [TA-Lib](https://pynumlab.github.io/prik/user/examples/c/ta-lib-wrapper/) | C declarations from `ta_libc.h`; link compiled `libta-lib` | All 322 double and float-input indicators over NumPy arrays, checked against TA-Lib's reference results |

The **Real Libraries Portability** workflow runs all seven on Linux x86-64,
Linux ARM64, macOS Intel, and macOS ARM64 with Python 3.12. See the [Examples
Gallery](https://pynumlab.github.io/prik/user/examples/#tested-platforms) for the
compiler matrix; each project guide also records its own tested platforms.

## Key Features

- **Native APIs that feel like Python.** Fortran modules become Python
  namespaces, derived types become classes, and C functions expose designed
  scalar, array, string, and output interfaces.
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
- **Interactive notebook builds.** Compile Fortran and C cells with
  `%%fortran` and `%%c`, or edit a generated semantic contract in a `%%pyi`
  cell.
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

## Current Fortran limitations

PRIK rejects these forms rather than wrapping them unsafely. Most fail before
code generation with a diagnostic naming the boundary and the reason.

**Types and arrays**

- arrays of derived types, and assumed-type `type(*)` arrays;
- parameterized derived types such as `type :: buffer_type(k, n)`;
- character arrays that cannot be represented as a fixed-width NumPy bytes
  dtype, and `allocatable` and `pointer` character *fields*.
- real and complex storage wider than the target's `long double`. NumPy's
  `longdouble` is whatever the target C compiler provides, so `real(10)` and C
  `long double` are supported while IEEE quad `real(16)` is refused on a target
  whose `long double` is x87 extended precision. The diagnostic names the
  measured mantissa width on both sides.

**Procedures and polymorphism**

- procedure-pointer module variables, and
  callbacks retained after the wrapped call returns;
- polymorphic outputs, mutable polymorphic arguments, polymorphic
  `allocatable` and `pointer` scalars, and unlimited polymorphism (`class(*)`).

The [language feature matrix](https://pynumlab.github.io/prik/user/language-support/feature-matrix/)
records the full support status of every feature with its evidence. The
[C Support page](https://pynumlab.github.io/prik/user/language-support/c-support/)
states the current C wrapper boundary.

## C support

PRIK builds C and Fortran code into importable Python extensions. For C,
generated binding code calls your exported symbol without ABI conversion. The
one exception is opt-in: `--collision-adapter NAME` writes a small forwarding
translation unit when one of your headers declares a name that `Python.h` also
declares.

C has no `intent` and no shape information, so a bare `double *` could be one
value, a mutable output, or an array. PRIK never guesses: it generates a
conservative contract from the source, and you edit it to say what the pointer
actually means.

Create `stats.c`:

```c
#include <stddef.h>

double mean(const double *values, size_t count) {
    double total = 0.0;
    for (size_t i = 0; i < count; ++i) {
        total += values[i];
    }
    return count == 0 ? 0.0 : total / (double)count;
}

void extremes(const double *values, size_t count, double *low, double *high) {
    *low = values[0];
    *high = values[0];
    for (size_t i = 1; i < count; ++i) {
        if (values[i] < *low) { *low = values[i]; }
        if (values[i] > *high) { *high = values[i]; }
    }
}
```

Generate a starter contract:

```bash
python3 -m prik generate --pyi --language c stats.c --out edited.pyi
```

Then edit `edited.pyi` so `values` is an array, `count` is derived from it,
and the two output pointers become Python results:

```python
from prik.contracts import Arg, Float64, Return, Returns, native_call

@native_call([Arg(0), Arg(0).shape[0]])
def mean(values: Float64[:]) -> Float64: ...

@native_call([Arg(0), Arg(0).shape[0], Return("low", 0), Return("high", 1)])
def extremes(values: Float64[:]) -> tuple[Returns["low", Float64], Returns["high", Float64]]: ...
```

```bash
python3 -m prik --language c edited.pyi --native-c-sources stats.c --out stats
```

```python
import numpy as np
import stats

values = np.array([3.0, 1.0, 4.0, 1.0, 5.0])

print(stats.mean(values))      # 2.8
print(stats.extremes(values))  # (np.float64(1.0), np.float64(5.0))
```

`count` never appears in the Python signature — the contract derives it from
the array — and the two output pointers come back as a tuple instead of being
passed in. `mean` and `extremes` need no `@bind` because their Python and C
names match; use `@bind("native_name")` only when they differ. The same rule
applies to Fortran contracts.

### What C support covers

C wrappers support target-probed arithmetic scalars and `void`,
C-contiguous NumPy arrays of ranks 1–15, and both read-only and writable C
strings. Contracts can also rename or reorder calls, derive lengths and shapes,
return native outputs, overload Python names, and turn status codes into Python
exceptions.

### Current C limitations

Current C support does not cover arrays of strings, multi-level pointers,
structs, unions, function pointers, or callbacks. Unsupported declarations
stop before wrapper generation or compilation; parsing a declaration alone does
not promise that it can be built.

[Continue with the C User Guide for source, `.pyi`, CLI, and Python API
workflows.](https://pynumlab.github.io/prik/user/guide/c/)

## Installation & Quick Start

PRIK requires **Python 3.10 or newer**, NumPy, Python development headers,
standard build tools, and a compiler for the code being wrapped. GNU Fortran is
the default Fortran compiler and is tested on Linux and macOS. LLVM Flang is
tested on both platforms; Intel IFX is tested on Linux.

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

## IPython and Jupyter

Install the optional notebook integration and load it once per session:

```bash
python3 -m pip install "prik[jupyter]"
```

```ipython
%load_ext prik.jupyter
```

Use `%%fortran` or `%%c` to compile native source in a cell. Add `--pyi` to
review and edit the generated contract before compilation, or use `%%pyi` with
existing native source files. See [Run PRIK in a
Notebook](https://pynumlab.github.io/prik/user/tutorials/notebook-quickstart/)
for the guided version, or [IPython and Jupyter
Notebooks](https://pynumlab.github.io/prik/user/guide/notebooks/) for the
complete workflow.

## How it works

```text
Fortran or supported C sources
  -> compiler preprocessing and target-type probing
  -> language parser and semantic IR construction
  -> completed policy and wrapper plan
  -> generated Python binding and native wrapper support
  -> native compilation and shared-library link
  -> importable Python extension
```

For diagnostic and inspection commands beyond the main build path, start with
`python3 -m prik --help`.

## Python API

Root entrypoints cover Fortran and supported C extension builds.
Advanced parsing, semantic conversion, and `.pyi` emission use their owning
packages:

```python
from prik import build_c_extension, build_fortran_extension

result = build_fortran_extension(
    "points.f90",
    output_name="geometry",
    output_dir="build/geometry_api",
)
print(result.module_name)
print(result.shared_library)
```

Use `build_c_extension("api.c", output_dir="build")` for a C source build, or
`build_pyi_extension(..., native_language="c", native_c_sources=[...])`
for an authored C contract. The [C User
Guide](https://pynumlab.github.io/prik/user/guide/c/) shows complete examples.

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
[`CITATION.cff`](https://github.com/PyNumLab/prik/blob/main/CITATION.cff).

## License

PRIK is distributed under the [MIT License](https://github.com/PyNumLab/prik/blob/main/LICENSE).
Copyright (c) 2026 Said Hadjout.

Using PRIK does not impose the MIT License on the user's native sources or on
wrapper code derived from those inputs. Users may distribute generated
wrappers under terms of their choice. Bundled native-support files copied into
generated builds remain MIT-licensed and must retain the included license
notice when redistributed.

## Documentation

- **[Documentation](https://pynumlab.github.io/prik/)** — Learn how to install and use PRIK
- **[Project Vision](https://github.com/PyNumLab/prik/wiki)** — Long-term direction for PRIK's semantic interoperability model
- **[Getting Started](https://pynumlab.github.io/prik/user/getting-started/)** — Installation, verification, matched Fortran and C first functions, and rebuild workflow
- **[User Guide](https://pynumlab.github.io/prik/user/guide/)** — Separate Fortran and C paths followed by shared build workflows
- **[IPython and Jupyter](https://pynumlab.github.io/prik/user/guide/notebooks/)** — Compile native cells and edit semantic contracts interactively
- **[`.pyi` Format](https://pynumlab.github.io/prik/user/reference/pyi-format/)** — Contract projects, declarations, decorators, types, storage, metadata, and C and Fortran forms
- **[Editing `.pyi` Contracts](https://pynumlab.github.io/prik/user/reference/pyi-contracts/)** — Supported recipes for reshaping the generated Python API
- **[CLI Reference](https://pynumlab.github.io/prik/user/reference/cli-commands/)** — Every command, option, and checked workflow
- **[Language Support](https://pynumlab.github.io/prik/user/language-support/)** — Supported, partially supported, and unsupported native-language features
- **[FAQ](https://pynumlab.github.io/prik/user/faq/)** — Concise answers to common questions
