---
title: LAPACK Wrapper Example
audience: users, advanced users
prerequisites: arrays, BLAS wrapper example
related: blas-wrapper.md, ../guide/error-handling.md
status: maintained
publication: draft
---

# LAPACK Wrapper Example

The runnable example in [`examples/lapack/`](../../../examples/lapack/) builds
the complete Reference LAPACK source corpus once through PRIK, then validates
the 127 callable double-precision routines exposed by SciPy 1.18.0. The full
wrapper is available, but the correctness inventory is intentionally limited
to SciPy's `d*` API and excludes the `_lwork` convenience helpers.

Run it with:

```console
python3 -m pytest -q examples/lapack
python3 -m pytest -q examples/lapack/test_linear_general.py::test_dgesv_solves_general_system
```

Each test compares PRIK with an independent numerical calculation and with
SciPy. The complete native source set is owned by `examples/lapack/native/`;
BLAS dependencies remain owned by `examples/blas/native/`. Native compiler
output is kept in pytest temporary/cache directories. Repository policy leaves
these LAPACK runtime commands to the dedicated GitHub Actions lane unless a
maintainer explicitly requests a local run.
