---
title: User Documentation
audience: users
prerequisites: none
related: getting-started/index.md, guide/index.md, performance.md
status: maintained
publication: reviewed
---

# User Documentation

PRIK is the Python Runtime Interop Kit. Use these pages to install PRIK, verify
your environment, build Fortran and C wrappers, and understand the behavior of
generated Python extensions. Current C coverage is documented in C Support.

## Start Here

1. [Getting Started](getting-started/index.md)
2. [User Guide](guide/index.md)
3. [Performance](performance.md)

Getting Started covers installation, environment verification, the first
standalone wrapper, the first module wrapper, and the beginner edit-build-test
loop. The User Guide covers supported Fortran wrapper features, runtime
behavior, and extension builds. Performance presents the reproducible PRIK and
f2py comparison.

## Then

- [Language Support](language-support/index.md) — C and Fortran feature
  coverage, including the evidence behind each claim.
- [Reference](reference/index.md) — the exact CLI, Python API, generated-wrapper,
  and `.pyi` contract surfaces.
- [Examples](examples/index.md) — five complete Fortran projects (BLAS, LAPACK,
  FFTPACK, MINPACK, and BSPLINE-FORTRAN) plus the direct-C libm project.
- [Troubleshooting](troubleshooting/compiler-issues.md) — compiler detection,
  selection, and toolchain problems.
- [FAQ](faq/index.md) — short answers to common questions.
