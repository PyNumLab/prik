---
# X2PY_C_DOCS: title: Inspect A C API
title: Deferred Native API Inspection
audience: users, developers
prerequisites: installation
related: ../../../developer/c-parser-reference.md
status: maintained
publication: draft
---

<!-- X2PY_C_DOCS_START
# Inspect A C API
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Use this recipe when you want source facts, semantic IR, or `.pyi`
for a C header. This is an inspection workflow, not a runtime C wrapper build.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
## Input
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-source: tests/data/c/general/math_api.h -->
<!-- X2PY_C_DOCS_START
```c
#ifndef X2PY_GENERAL_MATH_API_H
#define X2PY_GENERAL_MATH_API_H

double norm2(int n, const double x[static 1]);
void scale(int n, double alpha, double x[static 1]);
double dot(int n, const double *restrict x, const double *restrict y);
void fill_identity3(double a[static 3][3]);

#endif
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
## Parse Source Facts
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: exact -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Expected output:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
File: tests/data/c/general/math_api.h
  Language: c
  Functions: 4
  Structs: 0
  Unions: 0
  Enums: 0
  Typedefs: 0
  Variables: 0
  Macros: 0
  Includes: 0
  Diagnostics: 0
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
## Generate Semantic IR And `.pyi`
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: run -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: run -->
<!-- X2PY_C_DOCS_START
```bash
python3 -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
X2PY_C_DOCS_END -->


<!-- X2PY_C_DOCS_START
## Notes
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Inspection does not promise that a runtime wrapper backend exists for user C
libraries.
X2PY_C_DOCS_END -->
