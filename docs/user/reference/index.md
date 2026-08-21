---
title: Reference
audience: users, developers
prerequisites: getting started
related: cli-commands.md, python-api.md, fortran-wrapper.md, semantic-pyi-format.md, pyi-contracts/index.md
status: maintained
publication: draft
---

# Reference

Reference pages describe the exact command, API, generated-wrapper, and
contract surfaces. They assume you have already built a wrapper — start with
[Getting Started](../getting-started/index.md) and the
[User Guide](../guide/index.md) if you have not.

## Drive PRIK

- [CLI commands](cli-commands.md) — every command, option, and checked workflow.
- [Python API](python-api.md) — the build entrypoints and advanced package imports.

## Understand the generated wrapper

- [Fortran wrapper reference](fortran-wrapper.md) — how Fortran declarations become a Python API.
- [Generated functions](generated-functions.md)
- [Generated modules](generated-modules.md)
- [Generated classes](generated-classes.md)

The generated function, module, and class pages document the maintained Python
surface produced by wrapper builds. They are manually maintained references
backed by checked contracts and runtime tests.

## Shape the API with contracts

- [Editing `.pyi` contracts](pyi-contracts/index.md) — the complete editing rules.
- [Semantic `.pyi` format](semantic-pyi-format.md) — the contract file format.
- [Semantic IR](semantic-ir.md) — the language-neutral model behind contracts.

## Diagnose problems

- [Diagnostic codes](diagnostic-codes.md) — what a rejected wrapper is telling you.
- [Language feature matrix](../language-support/feature-matrix.md) — whether a
  feature is supported at all, with its evidence.
