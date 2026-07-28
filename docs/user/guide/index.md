---
title: User Guide
description: Detailed guides for wrapping Fortran code with x2py
audience: users
prerequisites: getting started
related: data-types.md, ../reference/fortran-wrapper.md, ../language-support/index.md
status: maintained
publication: reviewed
---

# User Guide

This section continues the [Getting Started](../getting-started/index.md)
workflow. Read it in sidebar order to move from basic values and procedures to
objects, storage, and advanced runtime behavior.

---

## Start Here

- [Data Types](data-types.md) — Fortran types, semantic `.pyi` names, exact NumPy dtypes, strings, and arrays
- [Arrays](arrays.md) — Rank, shape, strides, contiguity, and layout rules
- [Strings](strings.md) — Immutable text, mutable byte storage, and string arrays
- [Wrapping Functions](wrapping-functions.md)
- [Wrapping Subroutines](wrapping-subroutines.md)
- [Wrapping Modules](wrapping-modules.md)
- [Optional Arguments](optional-arguments.md)
- [Generic Interfaces](generic-interfaces.md)
- [Wrapping Derived Types](wrapping-derived-types.md)

---

## Storage and Objects

- [Allocatables](allocatables.md)
- [Pointers](pointers.md)
- [Memory Management](memory-management.md)

---

## Runtime Behavior

- [Callbacks](callbacks.md)
- [Enumerations](enumerations.md)
- [Raw Addresses](raw-addresses.md) — Advanced primitive, array, and fixed-string address boundaries
- [Error Handling](error-handling.md)

---

## Building

- [Building the Shared Library](building-shared-library.md)

---

## Reference

- [Reference Overview](../reference/index.md) — CLI, Python API, wrapper behavior, and semantic contracts
- [Language Feature Matrix](../language-support/feature-matrix.md) — Current support status (supported / partial / unsupported)

---

**Important Note**

The recommended workflow starts from Fortran source. The generated semantic
`.pyi` file describes the Python interface and native call. Editing that file
lets you customize the wrapper without changing the native implementation.
This guide introduces useful edits on the pages where they matter. The
[editing reference](../reference/editing-semantic-pyi-contracts.md) collects
the complete rules in one place.

---

Start with **[Data Types](data-types.md)**.
