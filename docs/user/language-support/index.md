---
title: Language Support
audience: users, developers
prerequisites: user guide
related: feature-matrix.md, ../reference/fortran-wrapper.md
status: maintained
publication: draft
---

# Language Support

**Will PRIK wrap my code?** The
[language feature matrix](feature-matrix.md) answers that. It is the
authoritative support index for implemented, partially implemented,
unsupported, and planned language features.

Start with its **At A Glance** table for a fast yes or no, then read the
detailed row for the feature you care about.

Every row links:

- the user-facing docs for the behavior;
- the source-navigation route for developers;
- runtime, parser, semantic, or documentation evidence; and
- the current limitation or blocker.

A feature is listed as supported only when that linked evidence proves the
behavior in the current repository. Runtime wrapper support requires compiled,
imported, and called tests — not merely a parser that accepts the syntax.

If a feature is unsupported, PRIK blocks it before code generation and reports
the boundary and the reason. See [diagnostic codes](../reference/diagnostic-codes.md)
for what a specific rejection means.
