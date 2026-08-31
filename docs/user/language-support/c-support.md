---
title: C Support
description: What C PRIK wraps, where the detailed guides live, and which declarations become Python APIs
audience: users
prerequisites: installation
related: index.md, feature-matrix.md, ../guide/c/index.md, ../reference/pyi-format.md, ../reference/pyi-contracts/index.md
status: maintained
publication: reviewed
---

# C Support

This page is the entry point for **what C PRIK wraps**. Start with the wrapper
areas below and follow the linked guide for complete Python behavior,
constraints, and examples. Use the [language feature
matrix](feature-matrix.md) for the exact status, evidence, and limitation of an
individual feature. Use [`.pyi` Format](../reference/pyi-format.md) for the
contract language and [Editing Contracts](../reference/pyi-contracts/index.md)
when shaping the Python API.

## Supported Wrapper Areas

| Area | Supported wrapping surface | Detailed guide |
| --- | --- | --- |
| Functions and primitive values | Externally linked functions with `void`, target-probed arithmetic scalars, and C99 complex values. | [Functions and Scalars](../guide/c/functions-and-scalars.md) |
| Pointers and arrays | One-level primitive pointer parameters start as runtime-rank NumPy storage accepting ranks 0 through 15 with any strides, and can be narrowed to contiguous storage, scalar addresses, exact ranks, or projected results. | [Pointers, Arrays, and Strings](../guide/c/pointers-arrays-and-strings.md) |
| Strings | Rank-zero C string inputs and caller-owned string storage. | [Pointers, Arrays, and Strings](../guide/c/pointers-arrays-and-strings.md#pass-c-strings) |
| Outputs and errors | Returned or hidden output storage, status projection, and Python exception construction. | [Outputs and Errors](../guide/c/outputs-and-errors.md) |
| Names and overloads | Symbol renaming, reordered arguments, typed literals, derived lengths and shapes, and overloads distinguishable by supported dtype or rank. | [Functions and Scalars](../guide/c/functions-and-scalars.md#rename-and-reorder-arguments), [Symbols, Headers, and Dependencies](../guide/c/symbols-headers-and-dependencies.md#present-several-c-symbols-as-one-python-name) |
| Projects and native builds | C source and header preprocessing, explicit source, object, and library dependencies, selected collision forwarders, and `@nogil` calls that do not access Python state. | [Symbols, Headers, and Dependencies](../guide/c/symbols-headers-and-dependencies.md), [Building the Shared Library](../guide/building-shared-library.md) |
| Editable Python interfaces | Generated or authored semantic `.pyi` contracts can select, rename, reorder, and reshape the documented C wrapper surface. | [Editing `.pyi` Contracts](../reference/pyi-contracts/index.md) |

## Important Boundaries

The table above names supported areas, not blanket support for every related C
declaration:

- C pointer syntax does not identify one value, an array, caller-owned
  storage, or an output. The semantic `.pyi` contract supplies that meaning.
- A `const T *` declaration must not be authored as writable storage.
  Attributes that can change ABI, symbol identity, layout, or calling
  convention stop the build instead of being ignored.
- Pointer results, multi-level pointers, raw or nullable pointers, and APIs
  with retained or ownership-sensitive pointers are unsupported.
- Callbacks, function pointers, `struct`, `union`, global-state wrappers, enum
  constants, variadic functions, `static` symbols, `volatile`, and `_Atomic`
  values are unsupported.
- Arrays of strings, Boolean arrays, native C array declarators, and arrays
  above rank 15 are unsupported. An explicitly shaped array requires
  C-contiguous storage; a Fortran-ordered or strided actual is accepted only
  through stride-agnostic `T[...]` storage.
- Parser and contract-generation coverage is broader than wrapper coverage;
  successfully inspecting a declaration is not a build promise.

The [unsupported and blocked forms](feature-matrix.md#unsupported-or-blocked-forms)
table gives the complete feature-by-feature boundary and links to its evidence.
See [C wrapper diagnostics](../reference/diagnostic-codes.md#c-wrapper-diagnostics)
for build rejections.

## Source Files And Public Entry Points

C source and header inputs require `--language c`. A source build exposes
supported externally linked functions from the selected translation units at
the Python extension root. C has no native module namespace, so a generated C
contract is one `.pyi` file rather than the Fortran contract-package layout.

Headers provide declarations and preprocessing context. Included declarations
remain private unless the selected include-exposure policy makes them public.
Implementation-only sources, objects, archives, and libraries must be supplied
explicitly; PRIK does not discover native dependencies.

For broad or system headers, select the reviewed public functions before
building. The [Symbols, Headers, and
Dependencies](../guide/c/symbols-headers-and-dependencies.md) guide shows source,
library, preprocessing, and API-inspection workflows. The [C User
Guide](../guide/c/index.md) provides the complete path from a C declaration to
an imported Python extension.
