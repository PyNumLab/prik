---
# PRIK_C_DOCS: title: Inspect A C API
title: Deferred Native API Inspection
audience: users, developers
prerequisites: installation
related: ../../../developer/deferred/c-parser.md
status: maintained
publication: draft
---

<!-- PRIK_C_DOCS_START
# Inspect A C API
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Use this recipe when you want source facts, semantic IR, or `.pyi`
for a C header. This is an inspection workflow, not a runtime C wrapper build.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## Input
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-source: tests/c/fixtures/native/general/math_api.h -->
<!-- PRIK_C_DOCS_START
```c
#ifndef PRIK_GENERAL_MATH_API_H
#define PRIK_GENERAL_MATH_API_H

double norm2(int n, const double x[static 1]);
void scale(int n, double alpha, double x[static 1]);
double dot(int n, const double *restrict x, const double *restrict y);
void fill_identity3(double a[static 3][3]);

#endif
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## Parse Source Facts
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;parse
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Expected output:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```text
File: tests/c/fixtures/native/general/math_api.h
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## Generate Semantic IR And `.pyi`
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: run -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;semantics
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: run -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik tests/c/fixtures/native/general/math_api.h &#45;&#45;language c &#45;&#45;pyi
```
PRIK_C_DOCS_END -->


<!-- PRIK_C_DOCS_START
## Notes
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Inspection does not promise that a runtime wrapper backend exists for user C
libraries.
PRIK_C_DOCS_END -->
