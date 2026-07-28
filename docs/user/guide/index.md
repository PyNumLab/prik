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

This section builds on the [Getting Started](../getting-started/index.md)
workflow. It explains data type mapping, supported Fortran constructs, runtime
behavior, and how to build the shared library.

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

The recommended workflow is **source-driven** (starting from `.f90` files).
Only move to editing semantic `.pyi` contracts after you understand the default generated behavior and are ready to manage native artifacts manually.

---

Start with **[Data Types](data-types.md)**.
