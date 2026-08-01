---
title: CI/CD
audience: maintainers
prerequisites: testing strategy
related: ../developer/testing-strategy.md, release-process.md
status: planned-documentation
publication: draft
---

# CI/CD

GitHub Actions owns repository quality checks and the reviewed-documentation
deployment. The documentation workflow builds the same filtered MkDocs site
that maintainers can preview locally, uploads the generated `site/` directory,
and deploys it through GitHub Pages.

## Test Platforms

The `Tests` workflow runs the ordinary suite on Ubuntu with every supported
Python version. It also runs the complete ordinary suite on macOS 15 with
Python 3.12 and GNU Fortran 13, preceded by the portable compiler smoke tests.
Both selections exclude `real_library`; BLAS and LAPACK run only in their
dedicated Ubuntu workflow.

The `Smoke Tests` workflow also runs LLVM Flang on macOS 15. Intel IFX remains
Linux-only because Intel does not provide IFX for macOS.

## Documentation Publication

The `Documentation` workflow runs for relevant pull requests, pushes to
`main`, and manual dispatches. Pull requests run the documentation tests and a
strict production build without deploying. A push to `main` runs those checks
and deploys the reviewed site when GitHub Pages is configured to use GitHub
Actions.

Every push to `main` first runs the x2py/f2py correctness and rigorous
performance suite. The job extracts its platform and toolchain metadata,
generates the result-dependent Performance page sections and SVG, and uploads
the generated documentation together with the raw `pyperf` files. The website
build overlays that artifact before testing and building MkDocs. Generated
results are deployment inputs, not automated commits to `main`.

Set the repository variable `X2PY_BENCHMARK_RUNNER` to the label of a dedicated
Linux x86-64 runner for stable published measurements. Without that variable,
the workflow uses the pinned Ubuntu 24.04 GitHub-hosted image and publishes its
recorded platform details. Pull requests verify the generator against fixtures
but do not replace the public snapshot. The workflow pins the benchmark
toolchain and alternates whether x2py or f2py is measured first to avoid a
systematic ordering advantage.

Enable the repository once through **Settings > Pages > Build and deployment >
Source > GitHub Actions**. Then open **Actions > Documentation > Run workflow**,
select `main`, and run it. Later documentation changes deploy automatically
after they are merged or pushed to `main`; maintainers do not build or upload
`site/` themselves.

Before changing a page to `publication: reviewed`, preview the production view
with `python3 -m mkdocs serve`. Use
`X2PY_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve` to review unpublished
pages with their draft warning. The lane index must also be reviewed before a
page in that lane can enter the deployed artifact.

## TODO

- TODO: Document the complete current CI quality gates and scheduled jobs.
- TODO: Link coverage troubleshooting to the maintained quality page.
