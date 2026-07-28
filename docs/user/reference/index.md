---
title: Reference
audience: users, developers
prerequisites: getting started
related: cli-commands.md, python-api.md, fortran-wrapper.md, semantic-pyi-format.md, pyi-contracts/index.md
status: maintained
publication: draft
---

# Reference

Reference pages describe the command, API, generated-wrapper, and semantic
contract surfaces that other documentation depends on. They also cover the
advanced contract-editing boundary. Beginner workflows remain in tutorials,
examples, and user guides.

## Pages

- [CLI commands](cli-commands.md)
- [Python API](python-api.md)
- [Fortran wrapper reference](fortran-wrapper.md)
- [Semantic IR](semantic-ir.md)
- [Semantic .pyi format](semantic-pyi-format.md)
- [Editing .pyi contracts](pyi-contracts/index.md)
- [Diagnostic codes](diagnostic-codes.md)
- [Generated functions](generated-functions.md)
- [Generated modules](generated-modules.md)
- [Generated classes](generated-classes.md)
- [Configuration files](configuration-files.md)

## Generated Wrapper Surface

The generated function, module, and class pages document the maintained Python
surface produced by wrapper builds. They are manually maintained references
backed by checked contracts and runtime tests. A generated-reference toolchain
can replace the inventory details later, but it must preserve the same public
rules.
