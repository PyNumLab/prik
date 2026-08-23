---
title: Pull Request Checks
audience: developers, contributors
prerequisites: quality assurance
related: contributing.md, quality-assurance.md
status: maintained
publication: reviewed
---

# Pull Request Checks

GitHub Actions supplies the evidence that is impractical to run for every
local change. It is the final verification for a pull request, not a workflow
contributors need to administer.

| Check | What it covers |
| --- | --- |
| Static analysis | Linting, formatting, security, dead code, and changed-code complexity policy. |
| Compiler and platform tests | Supported Python versions, Linux and macOS, GNU Fortran, IFX, and Flang. |
| Real Libraries Portability | BLAS, LAPACK, FFTPACK, MINPACK, BSPLINE-FORTRAN, and libm suites on Linux x86-64, Linux Arm64, macOS Intel, and macOS Arm64; libm additionally uses GCC and Clang, while Linux x86-64 retains the deep BLAS and LAPACK full-surface audits. |
| Documentation and benchmarks | Required performance benchmark and generated snapshot, documentation tests, and a strict site build. |

Temporary validation mode: the Linux and macOS unit-test jobs are skipped while
the libm Clang portability fix is revalidated. Real Libraries Portability starts
without waiting for those jobs. The aggregate merge gate still rejects the
skipped unit-test results, so restore the jobs before merging.

Run the applicable local checks from [Quality Assurance](quality-assurance.md)
before opening a pull request. If CI fails, start with the named failing test
or check and fix the owning behavior. Do not change workflow configuration
unless the task specifically concerns automation.

`Pull Request / Validation · all required checks` is the aggregate required
status before merge. The exact CI implementation lives in
`.github/workflows/merge-validation.yml`.
