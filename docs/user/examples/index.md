---
title: Examples Gallery
audience: users
prerequisites: getting started
related: ../guide/building-shared-library.md, ../language-support/c-support.md, ../reference/cli-commands.md, ../reference/python-api.md
status: maintained
publication: reviewed
---

# Examples Gallery

This section includes six complete real-library examples: BLAS, LAPACK,
FFTPACK, MINPACK, BSPLINE-FORTRAN, and libm. Each one provides build commands,
Python usage, and numerical checks for its public routines.

For a smaller first workflow, start with one of the checked guides below. Each
links to a complete source, build, import, or result path, rather than a
draft-only recipe.

## Choose a page

| Goal | Page |
| --- | --- |
| Build and import a first extension | [First Wrapped Function](../getting-started/first-wrapped-function.md) |
| Build a first Fortran module | [First Wrapped Module](../getting-started/first-wrapped-module.md) |
| Build from several ordered sources | [Building the Shared Library](../guide/building-shared-library.md#multiple-source-files) |
| Generate and edit `Makefile.prik` | [Building the Shared Library](../guide/building-shared-library.md#use-a-makefile) |
| Build through Python code | [Python API](../reference/python-api.md#building-an-extension) |
| Inspect source or control command output | [CLI Commands](../reference/cli-commands.md#parse-and-semantics) |
| Work with semantic `.pyi` contracts | [Editing `.pyi` Contracts](../reference/pyi-contracts/index.md) |
| Build a supported C API | [C Support](../language-support/c-support.md) |
| Build and validate the complete Reference BLAS | [BLAS wrapper](blas-wrapper.md) |
| Build complete Reference LAPACK and validate 127 float64 routines | [LAPACK wrapper](lapack-wrapper.md) |
| Wrap and validate all 31 FFTPACK procedures with NumPy and SciPy | [FFTPACK wrapper](fftpack-wrapper.md) |
| Wrap all 22 MINPACK procedures and use Python callbacks | [MINPACK wrapper](minpack-wrapper.md) |
| Build and validate modern Fortran classes and 15 interpolation routines | [BSPLINE-FORTRAN wrapper](bspline-wrapper.md) |
| Wrap 60 target-generated ISO C99 math routines from a system library | [libm wrapper](libm-wrapper.md) |
