---
title: Fortran Support
description: Which Fortran PRIK reads, and where reading ends and wrapper support begins.
audience: users
prerequisites: installation
related: index.md, feature-matrix.md, ../guide/index.md, ../reference/cli-commands.md, ../reference/fortran-wrapper.md
status: maintained
publication: reviewed
---

# Fortran Support

This page answers one question: **will PRIK read my Fortran?** It is the
inventory of source forms, program units, and declaration syntax the parser
accepts.

Reading is not the same as wrapping. A construct PRIK parses may still be
rejected later, because a wrapper needs facts a declaration alone does not
prove — ownership, lifetime, shape, or ABI. For what PRIK does with what it
reads, use the [User Guide](../guide/index.md); for whether a feature is
supported end to end, use the
[language feature matrix](feature-matrix.md).

## Source Forms

PRIK selects the source form from the filename suffix:

| Form | Suffixes |
| --- | --- |
| Fixed | `.f`, `.for`, `.ftn`, `.f77` |
| Free | `.f90`, `.f95`, `.f03`, `.f08` |

Suffix matching is case-insensitive. When a source arrives without a
recognizable suffix — inline text, or a file named some other way — PRIK
inspects the first twenty lines and treats the source as fixed form if it finds
a continuation character in column six. Both forms handle comment stripping and
continuation folding, and both preserve original line numbers so diagnostics
point at the line you wrote.

Mixed suffixes in one build are fine: each source is classified on its own.

## Program Units

| Unit | Notes |
| --- | --- |
| `module` | Becomes a Python namespace. See [Wrapping Modules](../guide/wrapping-modules.md). |
| `submodule (parent) name` | Parsed, including `module procedure` implementations. |
| `program` | Parsed for its declarations; a program is not an importable API. |
| `block data` | Parsed. Its variables appear in `parse --show-vars` reports. |
| Standalone `subroutine` / `function` | Exposed at the extension root. |
| `interface` / `abstract interface` | Parsed, including generic interface blocks and callback prototypes. |
| `enum, bind(C)` | Enumerators become integer constants. See [Enumerations](../guide/enumerations.md). |

Procedures contained inside another procedure are recognized and then skipped:
they are implementation detail, not public API.

## Procedures

Accepted prefixes are `pure`, `elemental`, `recursive`, `impure`, and `module`,
in any combination the language allows. Function results may be named with
`result(...)`.

Arguments are read with their declared type, kind, shape, and attributes:

| Attribute | Read from a dummy argument, field, or module variable |
| --- | --- |
| `intent(in)`, `intent(out)`, `intent(inout)` | Yes. A missing `intent` is treated conservatively — see [Wrapping Subroutines](../guide/wrapping-subroutines.md). |
| `optional` | Yes. See [Optional Arguments](../guide/optional-arguments.md). |
| `value` | Yes |
| `allocatable` | Yes. See [Allocatables](../guide/allocatables.md). |
| `pointer` | Yes. See [Pointers](../guide/pointers.md). |
| `target` | Yes |
| `contiguous` | Yes |
| `external` | Yes |
| `parameter` | Yes, including compile-time evaluation of its expression |

Array shape is read from `dimension(...)` or from the variable itself
(`x(:)`, `x(n)`, `x(0:n-1)`, `x(*)`, `x(..)`). Intrinsic kinds are read as
written — `real(8)`, `real(real64)`, `real(kind=selected_real_kind(15))`,
legacy `real*8` — and resolved against the selected compiler rather than
assumed. [Data Types](../guide/data-types.md) covers the resulting NumPy dtypes.

## Modules And Imports

`use` statements are read with their full form: `only:` lists, renames, and the
`intrinsic` / `non_intrinsic` qualifiers. A rename keeps both names, so
`use kinds, only: wp => real64` records `real64` as the source name and `wp` as
the local one. Module-level imports are propagated into contained procedures.

Across a directory or a multi-source build, PRIK parses each file once, orders
files by dependency, resolves compile-time symbols that cross files — a kinds
module, for example — and reports duplicate symbols at the project level.

## Derived Types

Both `type :: name` and the legacy `type name` spellings are read, along with:

- the `abstract` attribute and `extends(parent)` inheritance;
- fields with their type, kind, shape, `allocatable`, and `pointer` attributes;
- type-bound procedures, including `pass(name)` and `nopass` bindings;
- `generic :: name => specific1, specific2` bindings; and
- `final` procedures.

[Wrapping Derived Types](../guide/wrapping-derived-types.md) covers what these
become in Python, and [Generic Interfaces](../guide/generic-interfaces.md)
covers overload dispatch.

## Where Reading Ends

Some constructs are recognized and refused at the source level, so you get a
located diagnostic instead of a confusing failure later:

- `class(*)` unlimited polymorphism;
- `select type` constructs;
- coarray syntax;
- procedure pointers (`procedure, pointer`); and
- `type(c_ptr)` values.

Parameterized derived types are not supported. A header such as
`type :: buffer_type(k, n)` is accepted by the parser, but its kind and length
parameters are not modeled as parameters, so builds using them fail rather than
producing a correct wrapper.

Everything else that parses continues to the next stage, where support is
decided from complete facts. When PRIK refuses a wrapper there, the message
carries a diagnostic code. Parameterized derived types are a known exception:
they can currently reach compiler probing and report a compiler diagnostic
instead. [Diagnostic Codes](../reference/diagnostic-codes.md) explains PRIK
diagnostic codes, and the [feature matrix](feature-matrix.md) records which
forms are blocked and why.

## Check A Specific File

To see exactly what PRIK read from your source, without building anything:

```bash
python3 -m prik parse path/to/solver.f90 --show-vars
```

Add `--json` when a tool needs the same report as structured data. The
[CLI reference](../reference/cli-commands.md#parse-and-semantics) documents both
commands.
