---
title: Reference
audience: users
prerequisites: getting started
related: cli-commands.md, python-api.md, pyi-contracts/index.md, diagnostic-codes.md, ../language-support/index.md
status: maintained
publication: reviewed
---

# Reference

Reference pages describe the exact command, API, and editable-contract
surfaces. They assume you have already built a wrapper — start with [Getting
Started](../getting-started/index.md) and the [User Guide](../guide/index.md)
if you have not.

## Drive PRIK

- [CLI commands](cli-commands.md) — every command, option, and checked workflow.
- [Python API](python-api.md) — the build entrypoints and advanced package imports.
- [C Support](../language-support/c-support.md) — the direct C lane's source,
  contract, and build workflows.

## Shape the API with contracts

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

## Diagnose and check support

- [Diagnostic codes](diagnostic-codes.md) — what a rejected wrapper is telling you.
- [Language feature matrix](../language-support/feature-matrix.md) — whether a
  feature is supported at all, with its evidence.
