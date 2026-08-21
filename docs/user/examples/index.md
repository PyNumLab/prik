---
title: Examples Gallery
audience: users
prerequisites: getting started
related: ../guide/building-shared-library.md
status: maintained
publication: draft
---

# Examples Gallery

This section includes checked recipes and five complete real-library examples:
BLAS, LAPACK, FFTPACK, MINPACK, and BSPLINE-FORTRAN. Each one provides build commands, Python
usage, and numerical checks for its public routines.

Every page here is runnable. An example earns a place once it has source, a
build command, an import command, a runtime check, its limitations, and test
evidence.

## Choose a page

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
| Build and validate the complete Reference BLAS | [BLAS wrapper](blas-wrapper.md) |
| Build complete Reference LAPACK and validate 127 float64 routines | [LAPACK wrapper](lapack-wrapper.md) |
| Wrap and validate all 31 FFTPACK procedures with NumPy and SciPy | [FFTPACK wrapper](fftpack-wrapper.md) |
| Wrap all 22 MINPACK procedures and use Python callbacks | [MINPACK wrapper](minpack-wrapper.md) |
| Build and validate modern Fortran classes and 15 interpolation routines | [BSPLINE-FORTRAN wrapper](bspline-wrapper.md) |
