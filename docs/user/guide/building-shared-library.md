---
title: Building the Shared Library
description: How to build and import a Python extension shared library with PRIK
audience: users
prerequisites: common beginner workflow
related: error-handling.md
status: maintained
publication: reviewed
---

# Building the Shared Library

PRIK turns Fortran and C source into Python extension modules. The final module
is a native shared library that Python imports directly. The C workflow has its
own documented support boundary.

This page continues with `scale.f90` from the
[Common Beginner Workflow](../getting-started/beginner-workflow.md).

## Build

Run PRIK on the source file and choose a build directory:

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
`clang`—must also be available. PRIK keeps both compilers in the same family.

GNU, IFX, and Flang are tested on Linux. See
[Compiler Toolchains](../getting-started/installation.md#compiler-toolchains)
for versions and other recognized options.

## Build a primitive C API directly

PRIK supports C source as well. Start with [C
Support](../language-support/c-support.md) for complete source and
semantic-contract examples, Python API, supported C and NumPy types, pointer
contracts, preprocessing, generated Makefiles, and current limits. C input
always requires `--language c`.

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

The imported module name is also part of each wrapped function's public
identity. If `--out geometry` contains a child namespace `points`, its function
is identified as `geometry.points.distance`. A standalone function is
identified as `geometry.distance`. PRIK keeps this user-selected package path;
only private build and cache names are excluded from public function metadata.

## Multiple Source Files

Pass every wrapped source file in one command. Choosing the module name
explicitly keeps the result clear:

```bash
python3 -m prik src/types.f90 src/solver.f90 \
  --out solver \
  --out-dir build/solver
```

PRIK reads module and submodule dependencies from the wrapped sources. Files
whose dependencies are ready compile concurrently; independent external
procedures can all compile together. The original input order is still used
for the final link.

By default, PRIK uses the CPUs available to the current process. Limit compiler
concurrency with `--jobs`, or select a serial build with `--jobs 1`:

```bash
python3 -m prik src/types.f90 src/solver.f90 \
  --jobs 4 \
  --out solver \
  --out-dir build/solver
```

Additional native libraries and dependencies outside the supplied wrapped
sources remain explicit build inputs; PRIK does not search for them
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

## Next

You have reached the end of the User Guide.

- [Examples](../examples/index.md) — complete wrappers for real Fortran
  libraries.
- [Reference](../reference/index.md) — the exact CLI, Python API, and contract
  surfaces.
- [Language feature matrix](../language-support/feature-matrix.md) — every
  supported, partial, and blocked form in one table.
