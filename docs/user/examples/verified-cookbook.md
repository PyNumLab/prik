---
title: Verified Examples Cookbook
audience: users
prerequisites: basic wrapper tutorial
related: ../tutorials/basic-wrapper.md, index.md
status: maintained
publication: draft
---

# Verified Examples Cookbook

This cookbook is for lookup. Each recipe answers one practical question and
uses checked repository fixtures where the command output is stable.

Start with the [basic wrapper tutorial](../tutorials/basic-wrapper.md) if this
is your first x2py workflow. Use the
[Fortran wrapper guide](../guide/fortran-wrapper.md) for the full runtime
contract. The Semantic .pyi Format reference gives the complete editable
wrapper contract syntax.

## Choose A Recipe

| Goal | Recipe |
| --- | --- |
| Build a Fortran extension with the CLI and import it | [Build and import with the CLI](recipes/build-and-import-cli.md) |
| Build and import through Python code | [Build and import with the Python API](recipes/build-and-import-python-api.md) |
| Generate wrapper sources and an editable Makefile | [Generate an editable Makefile](recipes/generate-editable-makefile.md) |
| Build one extension from multiple ordered Fortran sources | [Build multiple Fortran sources](recipes/build-multiple-fortran-sources.md) |
| Parse and print `.pyi` | [Inspect a Fortran API](recipes/inspect-fortran-api.md) |
| Work with generated or edited `.pyi` contracts | [Work with semantic .pyi contracts](recipes/semantic-pyi-contracts.md) |
| Combine stages or limit human-readable output | [Control CLI output](recipes/control-cli-output.md) |
| Use parser and semantic APIs from Python code | [Use Python inspection APIs](recipes/use-python-inspection-apis.md) |
| Pass compiler and preprocessing flags | [Use compiler preprocessing options](recipes/compiler-preprocessing.md) |

<!-- X2PY_C_DOCS_START
| Inspect a C API without building a wrapper | [Inspect a C API](recipes/inspect-c-api.md) |
X2PY_C_DOCS_END -->

## Fixture Inputs

The recipes reuse these checked fixtures:

| Purpose | Repository fixture |
| --- | --- |
| Compiled Fortran wrapper and scalar call | `tests/data/fortran/wrapper/fruntime_abi_f90.f90` |
| Basic Fortran procedure | `tests/data/fortran/general/basic_subroutine.f90` |
| Rich Fortran module, types, arrays, and visibility | `tests/data/fortran/general/modern_pyi_example.f90` |
| Generated Fortran semantic interface | `tests/pyi/fixtures/general/modern_pyi_example/modern_pyi_example.pyi` |

<!-- X2PY_C_DOCS_START
| Basic C functions, pointers, and arrays | `tests/data/c/general/math_api.h` |
| Generated C semantic interface | `tests/pyi/fixtures/c/general/math_api.pyi` |
X2PY_C_DOCS_END -->

## Current Boundary

<!-- X2PY_C_DOCS_START
The implemented runtime wrapper backend is for Fortran source inputs and the
documented `.pyi` subset with explicit native artifacts. C inputs can be parsed,
lowered to semantic IR and printed as `.pyi`; runtime
wrapping of user-supplied C libraries is not implemented yet.
X2PY_C_DOCS_END -->

## Related Documentation

- [Basic wrapper tutorial](../tutorials/basic-wrapper.md)
- [Fortran wrapper guide](../guide/fortran-wrapper.md)
- Semantic .pyi Format
- Semantic IR Reference
- Diagnostic Codes
