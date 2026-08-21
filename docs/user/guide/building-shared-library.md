---
title: Building the Shared Library
description: How to build and import a Python extension shared library with prik
audience: users
prerequisites: common beginner workflow
related: error-handling.md
status: maintained
publication: reviewed
---

# Building the Shared Library

prik turns Fortran source, and the documented direct-only primitive C lane,
into a Python extension module. The final module is a native shared library
that Python imports directly.

This page continues with `scale.f90` from the
[Common Beginner Workflow](../getting-started/beginner-workflow.md).

## Build

Run prik on the source file and choose a build directory:

```bash
python3 -m prik src/scale.f90 --out-dir build/scale
```

The shared library and the generated build files are written to
`build/scale`. By default, the module name comes from the source filename. Use
`--out` to choose it explicitly:

```bash
python3 -m prik src/scale.f90 --out scale_api --out-dir build/scale_api
```

## Choose a Compiler

GNU Fortran is the default. Use `--compiler` to choose Intel IFX or LLVM Flang:

```bash
# Intel IFX + ICX
python3 -m prik src/scale.f90 \
  --compiler ifx \
  --out scale_ifx \
  --out-dir build/scale_ifx

# LLVM Flang + Clang
python3 -m prik src/scale.f90 \
  --compiler flang \
  --out scale_flang \
  --out-dir build/scale_flang
```

The executable may be an absolute path or a versioned name such as
`gfortran-13` or `flang-22`. Its matching C compiler—`gcc`, `icx`, or
`clang`—must also be available. prik keeps both compilers in the same family.

GNU, IFX, and Flang are tested on Linux. See
[Compiler Toolchains](../getting-started/installation.md#compiler-toolchains)
for versions and other recognized options.

## Build a primitive C API directly

The initial C lane is intentionally narrow: target-probed arithmetic values,
`void` results, and completed one-level primitive-pointer contracts. It calls
the user C symbol directly; no native C or Fortran adapter is generated.
Select C explicitly rather than relying on a filename or compiler choice:

```bash
python3 -m prik --language c src/arithmetic.c --compiler cc --out-dir build/arithmetic
```

For an edited source-free semantic contract, `--language c` is the explicit
C-native identity and `--native-c-sources` supplies implementation units:

```bash
python3 -m prik --language c contracts/arithmetic.pyi \
  --native-c-sources src/arithmetic.c --compiler cc --out-dir build/arithmetic
```

C sources are preprocessed with the selected compiler before they are read, so
ordinary `#include`, `#define`, and conditional directives work, and only the
wrapped file's own declarations become public API.

This does not enable callbacks, aggregates, variadics, strings, nullable or
retained pointers, pointer returns, or multi-level pointers. Neither does it
wrap C global variables, `enum` constants, or `struct`/`union` declarations
written in the wrapped file. Those inputs fail with a named diagnostic before
wrapper files or native compiler commands are produced.

## Import

Add the build directory to Python's search path, then import the module by its
name:

```python
import sys

sys.path.insert(0, "build/scale_api")

import scale_api
```

The shared-library filename includes a platform- and Python-specific suffix,
but the import uses only the module name.

## Multiple Source Files

Pass every wrapped source file in one command. Choosing the module name
explicitly keeps the result clear:

```bash
python3 -m prik src/types.f90 src/solver.f90 \
  --out solver \
  --out-dir build/solver
```

prik reads module and submodule dependencies from the wrapped sources. Files
whose dependencies are ready compile concurrently; independent external
procedures can all compile together. The original input order is still used
for the final link.

By default, prik uses the CPUs available to the current process. Limit compiler
concurrency with `--jobs`, or select a serial build with `--jobs 1`:

```bash
python3 -m prik src/types.f90 src/solver.f90 \
  --jobs 4 \
  --out solver \
  --out-dir build/solver
```

Additional native libraries and dependencies outside the supplied wrapped
sources remain explicit build inputs; prik does not search for them
automatically.

Python callers set `jobs=N` on `build_fortran_extension(...)`,
`build_pyi_extension(...)`, or manifest replay.

## Use a Makefile

To inspect or customize the build commands, generate a Makefile without
compiling:

```bash
python3 -m prik generate --makefile src/scale.f90 --out-dir build/scale
```

Edit `Makefile.prik` before running `make` when customization is needed. Its
most useful settings are near the top:

| Setting | What it changes |
| --- | --- |
| `FC` | Fortran compiler |
| `CC` | C compiler, including explicit C implementation sources |
| `PRIK_LD` | Command that creates the shared library |
| `PRIK_FFLAGS` | Extra Fortran compiler flags |
| `PRIK_CFLAGS` | Extra C binding compiler flags |
| `PRIK_LDFLAGS` | Extra linker flags |

The build targets and commands follow these settings and normally do not need
editing. Then build the shared library:

```bash
make -f build/scale/Makefile.prik
```

You can pass the same ordered list of source files used in the previous
example. This workflow requires GNU Make.

## Compatibility

The shared library is not universal. It must match the target machine's
operating system and architecture, Python and NumPy, and required compiler
libraries. Rebuilding it on the target machine is the safest choice.

## Every build option

This page covers the common build paths. For the complete option surface —
native sources, objects, libraries, ordered link items, wrapper compiler flags,
and manifest replay — see the
[CLI commands reference](../reference/cli-commands.md), or run
`python3 -m prik --help-build`. To drive the same builds from Python instead of
a shell, see the [Python API reference](../reference/python-api.md).
