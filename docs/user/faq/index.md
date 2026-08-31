---
title: Frequently Asked Questions
description: Concise answers about wrapping Fortran and C code, native libraries, NumPy arrays, and choosing PRIK or f2py
audience: users
prerequisites: none
related: ../getting-started/index.md, ../guide/index.md, ../language-support/c-support.md, ../language-support/feature-matrix.md, ../performance.md
status: maintained
publication: reviewed
---

# Frequently Asked Questions

Start with the question closest to your task. Each answer links to the complete,
tested workflow.

## Fortran

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
[Generate Python Bindings for a Fortran Module](../guide/wrapping-modules.md).

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
libraries. The [example gallery](../examples/index.md) also includes the C
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

## C

<details class="prik-faq-item" id="how-do-i-call-c-from-python" markdown="1">
<summary>How do I call C from Python?</summary>

Build a supported C source with PRIK and import the generated extension. A
primitive function can be wrapped directly from source; pointers, arrays,
strings, hidden outputs, and status handling use an editable semantic `.pyi`
contract. Follow [Build a Scalar C Function](../guide/c/functions-and-scalars.md#build-a-scalar-c-function)
for the complete first example.

</details>

<details class="prik-faq-item" id="why-do-i-need-to-edit-the-generated-c-pyi-contract" markdown="1">
<summary>Why do I need to edit the generated C `.pyi` contract?</summary>

C pointer syntax does not say whether a pointer represents one value, an
output, an array, or caller-owned storage. PRIK generates a conservative
starter contract instead of guessing. Edit it to state the intended storage,
shape, and result projection, then build it against the C implementation. See
[Author a Contract for Pointers and Arrays](../guide/c/pointers-arrays-and-strings.md#author-a-contract-for-pointers-and-arrays).

</details>

<details class="prik-faq-item" id="which-c-arrays-and-strings-are-supported" markdown="1">
<summary>Which C arrays and strings are supported?</summary>

C pointer contracts support primitive non-Boolean NumPy storage of ranks 0–15.
Runtime-rank `T[...]` storage accepts any strides; an explicit shape such as
`T[:]` requires C-contiguous storage. Strings are supported as rank-zero
inputs and caller-owned storage. Arrays of strings, Boolean arrays, native C
array declarators, and ranks above 15 are unsupported.
See [C Support: Supported Wrapper Areas](../language-support/c-support.md#supported-wrapper-areas)
for the complete boundary.

</details>

<details class="prik-faq-item" id="how-do-i-wrap-an-existing-c-library-or-large-header" markdown="1">
<summary>How do I wrap an existing C library or large header?</summary>

First create `symbols.txt` with one C function name per line:

```text
vendor_add
vendor_scale
```

Generate a target-specific contract containing only those functions:

```bash
python3 -m prik generate --pyi --language c include/vendor.h \
  --include-exposure roots-only \
  --export-symbols symbols.txt \
  --out vendor.pyi
```

Pass the header's normal `-I`, `-D`, and `--std` options when it needs them.
Review `vendor.pyi` before building. Primitive scalar signatures are ready to
use; edit pointer parameters when they represent arrays, outputs, or strings.

Build the contract against the installed library:

```bash
python3 -m prik --language c vendor.pyi \
  --native-library vendor \
  --native-library-dir /path/to/lib \
  --out vendor
```

Here `vendor` is the linker name for a library such as `libvendor.so`. Use
`--native-library-dir` only when the library is outside the linker's normal
search path. Use `--native-c-sources` instead when you have implementation
sources, or `--native-objects` for existing objects or archives.

Continue with the page that matches the part you need:

- [Select functions from a large or system
  header](../reference/cli-commands.md#c-include-exposure) explains the
  `symbols.txt` format, included-header visibility, and selection failures.
- [Choose the pointer
  contract](../guide/c/pointers-arrays-and-strings.md#choose-the-pointer-contract)
  explains how to describe one value, an output, an array, or caller-owned
  storage in `vendor.pyi`.
- [Supply native
  dependencies](../guide/c/symbols-headers-and-dependencies.md#native-dependencies) explains
  when to use implementation sources, objects, library names, library
  directories, include paths, and compiler definitions.
- [Wrap the system math library](../examples/c/libm-wrapper.md) is the complete
  example for selecting scalar functions from an installed system header and
  linking an already compiled library.
- [Wrap TA-Lib](../examples/c/ta-lib-wrapper.md) is the complete example for a
  large third-party header with NumPy arrays, output storage, an edited
  contract, and a reviewed API inventory.

</details>

<details class="prik-faq-item" id="what-happens-when-a-c-api-is-not-supported" markdown="1">
<summary>What happens when a C API is not supported?</summary>

PRIK rejects unsupported C forms before wrapper planning or native
compilation; parser acceptance alone is not a build promise. The diagnostic
identifies the blocked declaration or contract. Check [Important C
Boundaries](../language-support/c-support.md#important-boundaries), the [feature
matrix](../language-support/feature-matrix.md#unsupported-or-blocked-forms),
and [diagnostic codes](../reference/diagnostic-codes.md#c-wrapper-diagnostics).

</details>

## Choosing a Tool

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
