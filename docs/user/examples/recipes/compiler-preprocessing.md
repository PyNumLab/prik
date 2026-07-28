---
title: Use Compiler Preprocessing Options
audience: users, developers
prerequisites: installation, native project compiler flags
related: ../../../developer/c-parser-reference.md, ../../../developer/fortran-parser-reference.md
status: maintained
publication: draft
---

# Use Compiler Preprocessing Options

Use this recipe when the native project needs include paths, macros, standards,
or compiler-specific flags before x2py can parse it.

## Direct Compiler Settings

<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py include/api.h &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler clang \
  -I include \
  -D API_EXPORT= \
  &#45;&#45;std c11 \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/sdk
```
X2PY_C_DOCS_END -->

## Compilation Database

<!-- X2PY_C_DOCS_START
C projects can use a compilation database:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py src/api.c &#45;&#45;language c &#45;&#45;semantics \
  &#45;&#45;compile-commands build/compile_commands.json
```
X2PY_C_DOCS_END -->

## Notes

- Pass the same important include paths, macros, and target flags used by the
  native project.
- Compiler-backed semantic and `.pyi` stages can also probe target datatype
  facts.
- These examples are environment-dependent, so they are not marked as automatic
  documentation tests.
