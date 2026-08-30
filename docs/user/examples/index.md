---
title: Examples Gallery
audience: users
prerequisites: getting started
related: ../guide/building-shared-library.md, ../guide/c/index.md, ../language-support/c-support.md, ../reference/cli-commands.md, ../reference/python-api.md
status: maintained
publication: reviewed
---

# Examples Gallery

This section includes seven complete real-library examples: BLAS, LAPACK,
FFTPACK, MINPACK, BSPLINE-FORTRAN, libm, and TA-Lib. Each one provides build
commands, Python usage, and numerical checks for its public routines.

The native-language boundary is deliberately explicit:

| Native language | Examples | What PRIK consumes |
| --- | --- | --- |
| Fortran | BLAS, LAPACK, FFTPACK, MINPACK, BSPLINE-FORTRAN | Fortran source and interfaces, which the native build compiles and the wrapper exposes |
| C | libm, TA-Lib | Public C header declarations plus an already compiled library to link; implementation `.c` files are not wrapper inputs |

For libm, the declaration source is the platform's `<math.h>` and the linked
implementation is the platform math library. For TA-Lib, the declaration
source is its public `ta_libc.h` and the linked implementation is compiled
`libta-lib`.

## Tested platforms

The **Real Libraries Portability** workflow runs every example with Python
3.12 on Linux and macOS, using both x86-64/Intel and ARM64 runners. Compiler
coverage differs by project:

| Library | Linux compiler coverage | macOS compiler coverage | Architectures |
| --- | --- | --- | --- |
| BLAS | GNU Fortran 13 + GCC 13 | GNU Fortran 13 + GNU GCC 13 | x86-64 and ARM64 |
| LAPACK | GNU Fortran 13 + GCC 13 | GNU Fortran 13 + GNU GCC 13 | x86-64 and ARM64 |
| FFTPACK | GNU Fortran 13 + GCC 13 | GNU Fortran 13 + GNU GCC 13 | x86-64 and ARM64 |
| MINPACK | GNU Fortran 13 + GCC 13 | GNU Fortran 13 + GNU GCC 13 | x86-64 and ARM64 |
| BSPLINE-FORTRAN | GNU Fortran 13 + GCC 13 | GNU Fortran 13 + GNU GCC 13 | x86-64 and ARM64 |
| libm | GCC 13 and Clang 18 | Apple Clang and GNU GCC 13 | x86-64/Intel and ARM64 |
| TA-Lib | GCC 13 | Apple Clang | x86-64/Intel and ARM64 |

The C compiler beside each Fortran compiler builds the generated Python
binding. BLAS and LAPACK also receive their maintainer full-surface audits on
Linux x86-64. Native Windows/MSVC is outside the current portability matrix.

For a smaller first workflow, start with one of the checked guides below. Each
links to a complete source, build, import, or result path, rather than a
draft-only recipe.

## Fortran libraries

These examples build the supplied Fortran sources and generate bindings from
their source-level declarations and interfaces.

| Goal | Page |
| --- | --- |
| Build and validate the complete Reference BLAS | [BLAS wrapper](fortran/blas-wrapper.md) |
| Build complete Reference LAPACK and validate 127 float64 routines | [LAPACK wrapper](fortran/lapack-wrapper.md) |
| Wrap and validate all 31 FFTPACK procedures with NumPy and SciPy | [FFTPACK wrapper](fortran/fftpack-wrapper.md) |
| Wrap all 22 MINPACK procedures and use Python callbacks | [MINPACK wrapper](fortran/minpack-wrapper.md) |
| Build and validate modern Fortran classes and 15 interpolation routines | [BSPLINE-FORTRAN wrapper](fortran/bspline-wrapper.md) |

## C libraries

These examples obtain declarations from a public C header and link the
generated extension to an existing compiled library. PRIK does not compile the
library's implementation sources as part of the wrapper build.

| Goal | Page |
| --- | --- |
| Wrap 60 target-generated ISO C99 math routines from a system library | [libm wrapper](c/libm-wrapper.md) |
| Wrap and reference-check all 322 TA-Lib double and float-input indicators | [TA-Lib wrapper](c/ta-lib-wrapper.md) |

For a smaller introductory workflow, start with the dual-language [First
Wrapped Function](../getting-started/first-wrapped-function.md). Continue with
[Wrapping Modules](../guide/wrapping-modules.md) for Fortran or the [C User
Guide](../guide/c/index.md) for C.

To learn how an edited `.pyi` contract can reshape a low-level library, follow
the [Pythonic BLAS API tutorial](../tutorials/pythonic-blas.md).
