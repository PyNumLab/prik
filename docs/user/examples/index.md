---
title: Examples Gallery
audience: users
prerequisites: getting started
related: ../tutorials/index.md, ../guide/building-shared-library.md
status: planned-documentation
publication: draft
---

# Examples Gallery

The maintained part of this section is the checked recipes. Use them when you
need a copy-paste command, a short Python API pattern, or the current boundary
between inspection and runtime wrapper support.

The larger project examples below are placeholders for future complete runnable
projects. Each one must include source, build command, import command, runtime
check, limitations, and test evidence before it is marked maintained.

## Choose A Page

| Goal | Page |
| --- | --- |
| Build and import a first extension | [First Wrapped Function](../getting-started/first-wrapped-function.md) |
| Build from several ordered sources | [Building the Shared Library](../guide/building-shared-library.md#multiple-source-files) |
| Generate and edit `Makefile.prik` | [Building the Shared Library](../guide/building-shared-library.md#use-a-makefile) |
| Build through Python code | [Build and import with the Python API](recipes/build-and-import-python-api.md) |
| Inspect a Fortran API | [Inspect a Fortran API](recipes/inspect-fortran-api.md) |
<!-- PRIK_C_DOCS_START
| Inspect a C API | [Inspect a C API](recipes/inspect-c-api.md) |
PRIK_C_DOCS_END -->
| Work with semantic `.pyi` contracts | [Work with semantic `.pyi` contracts](recipes/semantic-pyi-contracts.md) |
| Control command output | [Control CLI output](recipes/control-cli-output.md) |
| Use inspection APIs from Python | [Use Python inspection APIs](recipes/use-python-inspection-apis.md) |
| Pass compiler and preprocessing options | [Use compiler preprocessing options](recipes/compiler-preprocessing.md) |

## Planned Project Examples

- [BLAS wrapper](blas-wrapper.md)
- [LAPACK wrapper](lapack-wrapper.md)
- [ODE solver](ode-solver.md)
- [CFD mini-example](cfd-mini-example.md)
- [Object-oriented Fortran example](object-oriented-fortran.md)
- [MPI example](mpi-example.md)
- [OpenMP example](openmp-example.md)

## TODO

- TODO: Add runnable checked examples one at a time.
- TODO: Keep examples with unavailable runtime support marked not yet
  implemented.
