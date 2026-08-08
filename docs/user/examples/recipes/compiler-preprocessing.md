---
title: Use Compiler Preprocessing Options
audience: users, developers
prerequisites: installation, native project compiler flags
related: ../../../developer/compiler-preprocessing.md, ../../../developer/c-parser-reference.md, ../../../developer/fortran-parser-reference.md
status: maintained
publication: draft
---

# Use Compiler Preprocessing Options

Use this recipe when the native project needs include paths, macros, standards,
or compiler-specific flags before prik can parse it.

## Direct Compiler Settings

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik include/api.h &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler clang \
  -I include \
  -D API_EXPORT= \
  &#45;&#45;std c11 \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/sdk
```
PRIK_C_DOCS_END -->

## Compilation Database

<!-- PRIK_C_DOCS_START
C projects can use a compilation database:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```bash
python3 -m prik src/api.c &#45;&#45;language c &#45;&#45;semantics \
  &#45;&#45;compile-commands build/compile_commands.json
```
PRIK_C_DOCS_END -->

## Notes

- For the pipeline model, adapters, diagnostics, and include-exposure policy,
  see the [compiler preprocessing reference](../../../developer/compiler-preprocessing.md).
- Pass the same important include paths, macros, and target flags used by the
  native project.
- Compiler-backed semantic and `.pyi` stages can also probe target datatype
  facts.
- These examples are environment-dependent, so they are not marked as automatic
  documentation tests.
