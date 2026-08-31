---
title: Language Support
audience: users
prerequisites: getting started
related: c-support.md, feature-matrix.md, ../reference/diagnostic-codes.md
status: maintained
publication: reviewed
---

# Language Support

**Will PRIK wrap my code?** Choose the path that matches your source:

- [Fortran Support](fortran-support.md) maps supported wrapper areas to their
  detailed guides and records the source files and program units that become
  Python APIs.
- [C Support](c-support.md) records the supported C wrapper surface and its
  boundaries. The [C User Guide](../guide/c/index.md) teaches the build and
  contract workflow.
- The [language feature matrix](feature-matrix.md) is the authoritative
  Fortran-and-C index for supported, partially supported, and unsupported
  features.

Start with its [**At A Glance** table](feature-matrix.md#at-a-glance) for a
fast yes or no, then read the detailed row for the feature you care about.

Every matrix row gives you:

- the user-facing docs for the behavior;
- runtime, parser, semantic, or documentation evidence; and
- the current limitation or blocker.

A feature is listed as supported only when that linked evidence proves the
behavior in the current repository. Runtime wrapper support requires compiled,
imported, and called tests — not merely a parser that accepts the syntax. In
particular, C parsing accepts a wider set of source facts than the supported C
wrapper subset; use the C guide's limits before treating a parsed C declaration
as buildable.

If a feature is unsupported, PRIK normally blocks it before code generation and
reports the boundary and the reason. The current exception is the
[parameterized-derived-type diagnostic gap](fortran-support.md#important-boundaries),
which can surface during compiler probing. See [diagnostic
codes](../reference/diagnostic-codes.md) for what a PRIK rejection means.
