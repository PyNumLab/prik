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

- [C Support](c-support.md) is the complete workflow for C projects. Current
  C wrapper coverage is the direct ABI subset documented on that page.
- The [language feature matrix](feature-matrix.md) is the authoritative
  Fortran-and-C index for implemented, partial, unsupported, and planned
  features.

Start with its **At A Glance** table for a fast yes or no, then read the
detailed row for the feature you care about.

Every matrix row gives you:

- the user-facing docs for the behavior;
- the implementation route for contributors;
- runtime, parser, semantic, or documentation evidence; and
- the current limitation or blocker.

A feature is listed as supported only when that linked evidence proves the
behavior in the current repository. Runtime wrapper support requires compiled,
imported, and called tests — not merely a parser that accepts the syntax. In
particular, C parsing accepts a wider set of source facts than the current
direct C wrapper lane; use the C guide's limits before treating a parsed C
declaration as buildable.

If a feature is unsupported, PRIK blocks it before code generation and reports
the boundary and the reason. See [diagnostic codes](../reference/diagnostic-codes.md)
for what a specific rejection means.
