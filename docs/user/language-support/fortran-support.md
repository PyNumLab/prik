---
title: Fortran Support
description: What Fortran PRIK wraps, where the detailed guides live, and which source files become Python APIs.
audience: users
prerequisites: installation
related: index.md, feature-matrix.md, ../guide/index.md, ../reference/pyi-format.md, ../reference/pyi-contracts/index.md
status: maintained
publication: reviewed
---

# Fortran Support

This page is the entry point for **what Fortran PRIK wraps**. Start with the
wrapper areas below and follow the linked guide for the complete Python
behavior, constraints, and examples. Use the [language feature
matrix](feature-matrix.md) when you need the exact status, evidence, and
limitation for an individual feature. Use [`.pyi` Format](../reference/pyi-format.md)
for the contract language and [Editing Contracts](../reference/pyi-contracts/index.md)
when reshaping the generated Python API.

## Supported Wrapper Areas

| Area | Supported wrapping surface | Detailed guide |
| --- | --- | --- |
| Primitive values and kinds | Documented integer, real, complex, logical, and character kinds, including target-resolved kind expressions, `value` arguments, and guarded existing `bind(C)` procedures. | [Data Types](../guide/data-types.md) |
| Functions and subroutines | Scalar and array arguments, function results, output arguments, multiple Python results, mutation, and documented call projections. | [Wrapping Functions](../guide/wrapping-functions.md), [Wrapping Subroutines](../guide/wrapping-subroutines.md) |
| Arrays | NumPy argument and result arrays with documented rank, shape, lower-bound, layout, stride, contiguity, mutation, and ownership rules. | [Arrays](../guide/arrays.md) |
| Strings | Scalar character inputs, outputs, and results; mutable character storage; allocatable and pointer scalars; and fixed-width character arrays. | [Strings](../guide/strings.md) |
| Modules, state, and constants | Module namespaces, variables, constants, saved state, procedures using common-block state, and Fortran enum constants. | [Wrapping Modules](../guide/wrapping-modules.md), [Enumerations](../guide/enumerations.md) |
| Optional and overloaded APIs | Optional arguments, generic procedure interfaces, defined operators and assignment, public naming, and overload dispatch. | [Optional Arguments](../guide/optional-arguments.md), [Generic Interfaces](../guide/generic-interfaces.md) |
| Derived types | Scalar derived types with fields, methods, constructors, finalizers, type-bound generics, and the documented inheritance and polymorphism subset. | [Wrapping Derived Types](../guide/wrapping-derived-types.md) |
| Managed native storage | Allocatable arrays and values, pointer projections and array handles, borrowed and owned storage, and documented release behavior. Pointer support has additional policy limits. | [Allocatables](../guide/allocatables.md), [Pointers](../guide/pointers.md), [Memory Management](../guide/memory-management.md) |
| Callbacks | Immediate Python callbacks whose lifetime is limited to the active wrapped call. | [Callbacks](../guide/callbacks.md) |
| Errors and status results | Native status projection and Python exception construction under the documented error contract. | [Error Handling](../guide/error-handling.md) |
| Raw addresses | Advanced primitive, array, and fixed-string address boundaries with explicit storage and lifetime requirements. | [Raw Addresses](../guide/raw-addresses.md) |
| Projects and native builds | Ordered single-source and multi-source builds, Makefiles, output placement, compiler selection, and explicit native dependencies. | [Building the Shared Library](../guide/building-shared-library.md) |
| Editable Python interfaces | Generated or authored semantic `.pyi` contracts can rename, select, reorder, and reshape the documented wrapper surface. | [Editing `.pyi` Contracts](../reference/pyi-contracts/index.md) |

## Important Boundaries

The table above names supported areas, not blanket support for every related
Fortran declaration:

- Pointer arrays and projections have useful supported forms, but target
  lifetime, deallocation, and writable reassociation remain policy-gated. See
  [Pointers](../guide/pointers.md) and [Memory Management](../guide/memory-management.md).
- Callbacks are immediate and call-scoped. Stored, asynchronous, optional, and
  cross-thread callbacks are unsupported. See [Callbacks](../guide/callbacks.md).
- Scalar derived types are supported, but arrays of derived types and several
  mutable or result polymorphic forms are not. See [Wrapping Derived
  Types](../guide/wrapping-derived-types.md).
- Assumed-rank and other advanced array forms are supported only where the
  [Arrays](../guide/arrays.md) guide defines a complete runtime contract.
- Parameterized derived types, unlimited polymorphism, procedure pointers, and
  real or complex storage wider than the target C `long double` are unsupported.
  Parameterized derived types can currently reach compiler probing and surface
  a compiler diagnostic instead of a PRIK diagnostic.

The [unsupported and blocked forms](feature-matrix.md#unsupported-or-blocked-forms)
table gives the complete feature-by-feature boundary and links to its evidence.

## Source Files And Public Entry Points

PRIK selects the source form from the filename suffix:

| Form | Suffixes |
| --- | --- |
| Fixed | `.f`, `.for`, `.ftn`, `.f77` |
| Free | `.f90`, `.f95`, `.f03`, `.f08` |

For editable output, `generate --pyi --out DIR` writes a Fortran contract
package: `__init__.pyi` holds standalone procedures and imports one leaf per
native module. The [`.pyi` format reference](../reference/pyi-format.md#source-to-contract-layout)
contrasts that package with C's single-file output.

Suffix matching is case-insensitive, and fixed-form and free-form sources can
be mixed in one build. For multi-source projects, PRIK orders named sources
from their module dependency graph. It does not discover files or external
libraries that were not supplied explicitly; see [Building the Shared
Library](../guide/building-shared-library.md).

The Python-facing entry points are:

- standalone functions and subroutines, exposed at the extension root;
- public module procedures, variables, constants, and derived types, exposed
  through a Python module namespace;
- supported generic interfaces, defined operators, assignment overloads, and
  type-bound procedures; and
- Fortran enumerators, exposed as integer constants.

When a module explicitly lists a procedure from an unnamed, non-abstract
interface as `public`, the interface declaration is the wrapper contract. Its
declared argument types and intents remain authoritative even when its
implementation is supplied as a separate native source. Unlisted interface
declarations remain dependencies and do not become Python entry points.

A Fortran `program` or `block data` unit is not an importable Python API, and a
procedure contained inside another procedure remains an implementation detail.
When a source declaration is readable but lacks a safe wrapper contract, PRIK
rejects the build rather than treating parser acceptance as wrapper support.
See [Diagnostic Codes](../reference/diagnostic-codes.md) for those rejections.
