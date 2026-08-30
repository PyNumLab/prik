---
title: User Guide
description: Guides for binding Fortran and C code with PRIK
audience: users
prerequisites: getting started
related: data-types.md, c/index.md, building-shared-library.md, ../language-support/feature-matrix.md
status: maintained
publication: reviewed
---

# User Guide

Use the section for your native language, then continue with the shared build
workflow that matches how you run PRIK.

## Fortran

- [Data Types](data-types.md) — Fortran types and exact NumPy dtypes
- [Arrays](arrays.md) — rank, shape, layout, strides, and mutation
- [Strings](strings.md) — scalar text, mutable storage, and string arrays
- [Functions](wrapping-functions.md) and
  [Subroutines](wrapping-subroutines.md)
- [Modules](wrapping-modules.md), [Optional
  Arguments](optional-arguments.md), and [Generic
  Interfaces](generic-interfaces.md)
- [Derived Types](wrapping-derived-types.md)
- [Allocatables](allocatables.md), [Pointers](pointers.md), and [Memory
  Management](memory-management.md)
- [Callbacks](callbacks.md), [Enumerations](enumerations.md), [Raw
  Addresses](raw-addresses.md), and [Error Handling](error-handling.md)

## C

- [Overview](c/index.md) — choose the source-driven or authored-contract path
- [Functions and Scalars](c/functions-and-scalars.md) — build a function and
  shape its Python call surface
- [Pointers, Arrays, and Strings](c/pointers-arrays-and-strings.md) — assign
  precise Python meanings to pointer parameters
- [Outputs and Errors](c/outputs-and-errors.md) — return output storage and
  project native failures
- [Symbols, Headers, and
  Dependencies](c/symbols-headers-and-dependencies.md) — overloads, headers,
  libraries, and API inspection

## Build Workflows

- [Building the Shared Library](building-shared-library.md) — compilers,
  source sets, output placement, and Makefiles
- [IPython and Jupyter Notebooks](notebooks.md) — compile Fortran and C cells
  and edit semantic contracts interactively

The [`.pyi` Format](../reference/pyi-format.md) defines the shared semantic
contract language. Use the [language feature
matrix](../language-support/feature-matrix.md#at-a-glance) to check current
Fortran and C coverage.
