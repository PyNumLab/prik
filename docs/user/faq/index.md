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

<details class="prik-faq-item" id="how-do-i-call-fortran-from-python" markdown="1">
<summary>How do I call Fortran from Python?</summary>

Use PRIK to build your Fortran source into an importable Python extension, then
call it with NumPy values that match the generated contract. Follow
[Call Your First Fortran Function from Python](../getting-started/first-wrapped-function.md)
for a complete source-to-result example.

</details>

<details class="prik-faq-item" id="how-do-i-generate-python-bindings-for-a-fortran-module" markdown="1">
<summary>How do I generate Python bindings for a Fortran module?</summary>

Pass the module source to PRIK. It generates the extension and exposes supported
public procedures and module state through Python. Start with
[Generate Python Bindings for a Fortran Module](../getting-started/first-wrapped-module.md).

</details>

<details class="prik-faq-item" id="how-do-i-wrap-an-existing-fortran-library-for-python" markdown="1">
<summary>How do I wrap an existing Fortran library for Python?</summary>

Build the public Fortran sources with PRIK and link their native dependencies
into the same extension. The
[shared-library guide](../guide/building-shared-library.md) explains the build
options, while the tested [BLAS](../examples/fortran/blas-wrapper.md),
[LAPACK](../examples/fortran/lapack-wrapper.md), [FFTPACK](../examples/fortran/fftpack-wrapper.md),
[MINPACK](../examples/fortran/minpack-wrapper.md), and
[BSPLINE-FORTRAN](../examples/fortran/bspline-wrapper.md) examples show complete
libraries. The [example gallery](../examples/index.md) also includes direct-C
[libm](../examples/c/libm-wrapper.md) and
[TA-Lib](../examples/c/ta-lib-wrapper.md).

</details>

<details class="prik-faq-item" id="how-do-i-expose-fortran-derived-types-as-python-classes" markdown="1">
<summary>How do I expose Fortran derived types as Python classes?</summary>

PRIK maps supported derived types to Python classes with constructors, methods,
fields, and explicit ownership rules. See
[Wrap Fortran Derived Types as Python Classes](../guide/wrapping-derived-types.md).

</details>

<details class="prik-faq-item" id="how-do-i-pass-numpy-arrays-to-fortran-without-unnecessary-copies" markdown="1">
<summary>How do I pass NumPy arrays to Fortran without unnecessary copies?</summary>

Pass arrays with the dtype, rank, shape, layout, strides, and writeability
required by the generated contract. Compatible arrays can cross the wrapper
without a layout conversion; incompatible inputs are rejected instead of being
silently copied. See [Pass NumPy Arrays to Fortran](../guide/arrays.md).

</details>

<details class="prik-faq-item" id="should-i-use-prik-or-f2py" markdown="1">
<summary>Should I use PRIK or f2py?</summary>

Use [NumPy's f2py](https://numpy.org/doc/stable/f2py/) when its established
generated API — or an editable
[`.pyf` signature](https://numpy.org/doc/stable/f2py/signature-file.html) — is
enough for your project.

Choose PRIK when you want to design the Python API rather than only generate a
wrapper: its editable [semantic `.pyi` contract](../reference/pyi-contracts/index.md)
renames, hides, flattens, and reprojects the surface, and it treats
[NumPy arrays](../guide/arrays.md) as complete contracts covering dtype, rank,
shape, layout, strides, and mutation. PRIK is alpha, so check the
[feature matrix](../language-support/feature-matrix.md) for exact limits.

The [side-by-side comparison](../performance.md#should-i-use-prik-or-f2py)
covers the trade-off in full, with measured runtime and build-time results.

</details>
