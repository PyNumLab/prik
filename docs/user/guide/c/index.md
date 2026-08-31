---
title: C User Guide
description: Build C functions as NumPy-aware Python extensions with PRIK
audience: users
prerequisites: installation, basic Python and NumPy
related: functions-and-scalars.md, ../../language-support/c-support.md, ../../examples/c/libm-wrapper.md
status: maintained
publication: reviewed
---

# C User Guide

PRIK builds C functions as importable Python extensions. Start from C source
when its declarations already describe the Python API. Use an editable
semantic `.pyi` contract when a pointer represents an array, output, string,
or another Python-facing value that C syntax cannot identify on its own.

Follow the guide in this order:

1. [Functions and Scalars](functions-and-scalars.md) — build a C function,
   inspect its contract, and shape its Python name and arguments.
2. [Pointers, Arrays, and Strings](pointers-arrays-and-strings.md) — state the
   Python meaning of C pointer parameters.
3. [Outputs and Errors](outputs-and-errors.md) — return output parameters and
   project native status values into Python exceptions.
4. [Symbols, Headers, and Dependencies](symbols-headers-and-dependencies.md) —
   wrap overload sets, broad headers, and linked libraries.

For the exact supported surface and current boundaries, see [C
Support](../../language-support/c-support.md). For complete library examples,
see the [libm](../../examples/c/libm-wrapper.md) and
[TA-Lib](../../examples/c/ta-lib-wrapper.md) guides.

Start with **[Functions and Scalars](functions-and-scalars.md)**.
