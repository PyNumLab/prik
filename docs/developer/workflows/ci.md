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
| Real Libraries Portability | Maintained real-library examples across the hosted Linux and macOS architecture/compiler matrix, with deep BLAS and LAPACK audits on Linux x86-64. |
| Documentation and benchmarks | Required performance benchmark and generated snapshot, documentation tests, and a strict site build. |

Run the applicable local checks from [Quality Assurance](quality-assurance.md)
before opening a pull request. If CI fails, start with the named failing test
or check and fix the owning behavior. Do not change workflow configuration
unless the task specifically concerns automation.

`Pull Request / Validation · all required checks` is the aggregate required
status before merge. The exact CI implementation lives in
`.github/workflows/merge-validation.yml`.
