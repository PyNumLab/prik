---
title: Frequently Asked Questions
description: Concise answers about calling Fortran from Python, wrapping libraries, NumPy arrays, derived types, and choosing PRIK or f2py
audience: users
prerequisites: none
related: ../getting-started/index.md, ../guide/index.md, ../performance.md
status: maintained
publication: reviewed
---

# Frequently Asked Questions

Start with the question closest to your task. Each answer links to the complete,
tested workflow.

## How do I call Fortran from Python?

Use PRIK to build your Fortran source into an importable Python extension, then
call it with NumPy values that match the generated contract. Follow
[Call Your First Fortran Function from Python](../getting-started/first-wrapped-function.md)
for a complete source-to-result example.

## How do I generate Python bindings for a Fortran module?

Pass the module source to PRIK. It generates the extension and exposes supported
public procedures and module state through Python. Start with
[Generate Python Bindings for a Fortran Module](../getting-started/first-wrapped-module.md).

## How do I wrap an existing Fortran library for Python?

Build the public Fortran sources with PRIK and link their native dependencies
into the same extension. The
[shared-library guide](../guide/building-shared-library.md) explains the build
options, while the tested [BLAS](../examples/blas-wrapper.md),
[FFTPACK](../examples/fftpack-wrapper.md), and
[MINPACK](../examples/minpack-wrapper.md) examples show complete libraries.

## How do I expose Fortran derived types as Python classes?

PRIK maps supported derived types to Python classes with constructors, methods,
fields, and explicit ownership rules. See
[Wrap Fortran Derived Types as Python Classes](../guide/wrapping-derived-types.md).

## How do I pass NumPy arrays to Fortran without unnecessary copies?

Pass arrays with the dtype, rank, shape, layout, strides, and writeability
required by the generated contract. Compatible arrays can cross the wrapper
without a layout conversion; incompatible inputs are rejected instead of being
silently copied. See [Pass NumPy Arrays to Fortran](../guide/arrays.md).

## Should I use PRIK or f2py?

Use [NumPy's f2py](https://numpy.org/doc/stable/f2py/) when its established
generated API—or an editable
[`.pyf` signature](https://numpy.org/doc/stable/f2py/signature-file.html)—is
enough for your project.

Choose PRIK when you want to design the Python API, not just generate a wrapper.
Its editable [semantic `.pyi` contract](../reference/pyi-contracts/index.md) is
a simpler, more Pythonic place to rename or hide exports, flatten modules,
reorder or hide native arguments, and return native outputs as Python results.

PRIK also covers important Fortran features: supported
[derived types](../guide/wrapping-derived-types.md) as Python classes,
[allocatables](../guide/allocatables.md), documented
[pointer forms](../guide/pointers.md), native errors as
[Python exceptions](../guide/error-handling.md), and
[overloaded procedures](../guide/generic-interfaces.md). PRIK is currently
alpha, so check the linked guides for exact limitations. The
[performance results](../performance.md) cover only their measured runtime and
clean-build workloads.
