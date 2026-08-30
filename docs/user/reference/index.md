---
title: Reference
audience: users
prerequisites: getting started
related: cli-commands.md, python-api.md, pyi-contracts/index.md, diagnostic-codes.md, ../language-support/index.md
status: maintained
publication: reviewed
---

# Reference

Reference pages describe exact commands, APIs, editable contracts, generated
wrapper behavior, and generated build files. They assume you have already built
a wrapper — start with [Getting
Started](../getting-started/index.md) and the [User Guide](../guide/index.md) if
you have not.

## Drive PRIK

- [CLI commands](cli-commands.md) — every command, option, and checked workflow.
- [Python API](python-api.md) — the build entrypoints and advanced package imports.
- [Build manifests and Makefiles](configuration-files.md) — how both files are
  generated, what they contain, and how to build or replay them.

## Contracts

- [`.pyi` Format](pyi-format.md) — project and namespace structure,
  declarations, C and Fortran forms, decorators, native calls, types, storage,
  and metadata.
- [Editing `.pyi` contracts](pyi-contracts/index.md) — the complete supported
  editing workflow.
- [Exports and modules](pyi-contracts/exports-and-modules.md) — names,
  visibility, and package shape.
- [Functions and classes](pyi-contracts/functions-and-classes.md) — methods,
  overloads, and constructors.
- [Calls and results](pyi-contracts/calls-and-results.md) — native call order,
  arguments, mutation, and results.

The contract pages describe the shared generated Python surface. Start from a
contract generated for the same native implementation, then rebuild and call
the changed path once.

## Check support and diagnostics

- [Fortran Support](../language-support/fortran-support.md) — the complete map
  of supported Fortran wrapper areas, limits, and detailed guides.
- [C User Guide](../guide/c/index.md) — C source, contract, build, and generated
  API workflows.
- [C Support](../language-support/c-support.md) — supported C features and
  boundaries.
- [Language feature matrix](../language-support/feature-matrix.md) — whether a
  feature is supported at all, with its evidence.
- [Diagnostic codes](diagnostic-codes.md) — what a rejected wrapper is telling
  you and which stage owns the rejection.
