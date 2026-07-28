---
title: AST Design
audience: maintainers
prerequisites: parser architecture
related: symbol-tables.md, type-system.md
status: planned-documentation
publication: draft
---

# AST Design

Parser models and parsed semantic `.pyi` files may use syntax trees to preserve
source structure. Wrapper generation has no shared codegen AST: completed
semantic policy is projected into `WrapperPlan`, then the C binding and Fortran
bridge lower directly into their backend-specific source-syntax nodes.

## TODO

- TODO: Document AST ownership, source locations, and invariants.
- TODO: Link parser models, wrapper-plan records, and generated source-syntax
  nodes to their tests.
