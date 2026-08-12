---
title: Continuous Integration And Delivery
audience: developers, maintainers, contributors
prerequisites: testing strategy
related: ../testing-strategy.md, quality-assurance.md, release.md
status: maintained
publication: draft
---

# Continuous Integration And Delivery

GitHub Actions owns repository quality checks and the reviewed-documentation
deployment. The documentation workflow builds the same filtered MkDocs site
that maintainers can preview locally, uploads the generated
`.artifacts/site/` directory, and deploys it through GitHub Pages.

Workflow names identify a unique pipeline scope, and every job display name is
self-contained. The `Pull Request` workflow declares the staged validation jobs
directly, avoiding the extra caller and called-workflow name layers produced by
nested reusable workflows. Pull requests expose one aggregate required check
after those jobs complete. Required status checks must use the exact `workflow
/ job` context documented in the
[quality-assurance guide](quality-assurance.md). Because GitHub
treats a renamed check as a different context, update the repository ruleset
whenever either half of that name changes.

Generated documentation and distribution output lives under the ignored,
hidden `.artifacts/` directory and must never be committed. Packaging scratch
output and setuptools `.egg-info` metadata are directed beneath the same hidden
root. Keeping every generated copy out of the maintained source tree ensures
rename-aware quality gates compare the previous package directly with its
current source path instead of matching it to a generated duplicate.

PyPI publication is deliberately separate from ordinary push and pull-request
workflows. Publishing a GitHub Release triggers a build job, followed by a
protected `pypi` environment job that authenticates through OpenID Connect.
See the [release process](release.md) for the exact trusted-publisher
identity and approval sequence.

## Test Platforms

The `Test Matrix` workflow runs the ordinary suite on Ubuntu with every supported
Python version. It also runs the complete ordinary suite on macOS 15 with
Python 3.12 and GNU Fortran 13, preceded by the portable compiler smoke tests.
Both selections exclude `real_library`; BLAS and LAPACK run only in their
dedicated Ubuntu workflow.

The `Compiler Compatibility` workflow also runs LLVM Flang on macOS 15. Intel
IFX remains Linux-only because Intel does not provide IFX for macOS.

For pull requests, `Pull Request` runs code quality and the parser contract
first. Compiler-compatibility smoke testing starts only after both policy checks
succeed. The Ubuntu Python 3.12 matrix entry records and uploads project
coverage, avoiding a second job that would execute the same suite.
Native-library validation waits for the complete matrix, and the documentation
performance benchmark and strict site build run last. An `always()` aggregate
job converts any failed or dependency-skipped required stage into one stable
ruleset result. The purpose-specific workflows remain independent entry points
for main, release, scheduled, and manual execution; the pull-request workflow
does not call them as nested reusable workflows.

## Documentation Publication

The `Pull Request` workflow runs the pinned performance benchmark, consumes its
generated snapshot, executes the documentation tests, and performs a strict
production build without deploying. The independent `Documentation` workflow
runs on pushes to `main` and manual dispatches, repeats those checks, and
deploys the reviewed site when GitHub Pages is configured to use GitHub
Actions.

Every validated pull request and push to `main` runs the same prik/f2py
correctness and rigorous performance suite. The job extracts its platform and
toolchain metadata, generates the result-dependent Performance page sections
and SVG, and uploads the generated documentation together with the raw
`pyperf` files. The website build overlays that artifact before testing and
building MkDocs. Generated results are deployment inputs, not automated
commits to `main`.

The benchmark job always targets GitHub's `ubuntu-24.04-arm` standard runner,
whose hosted pool is based on Microsoft Cobalt 100 processors. It verifies the
ARM64 architecture and CPU part `0xd49` used by Neoverse N2/Cobalt 100 before
installing dependencies or measuring. This avoids the different AMD processor
generations that may back successive x86-64 Ubuntu jobs. The documentation
build and deployment remain on x86-64 Ubuntu because they consume only the
generated Markdown and SVG artifact.

The pre-merge benchmark catches code-induced failures before `main`. The
`main` run is still required because it generates the deployment artifact for
the merged commit; external runner or service failures can still occur and
must be retried or diagnosed honestly. The workflow pins the benchmark
toolchain. Each runtime group uses an A/B/B/A sequence that splits a reduced
worker budget evenly between PRIK-first and f2py-first measurements, then
merges both passes before publication. Clean-build rounds alternate tool order.
Runtime cases use separate latency, medium, and bulk sampling budgets, giving
nanosecond-scale calls more independent samples without multiplying the cost of
the largest array workloads. The combined budget targets roughly 20 minutes on
the pinned runner while retaining all workloads.

Documentation workflow concurrency is isolated by Git ref. Pull-request runs
may cancel an older run for the same ref, but a `main` run is never canceled by
a pull request or a newer `main` run. This lets the rigorous ARM64 benchmark
finish and publish a complete result artifact while still superseding stale
pull-request documentation checks.

Enable the repository once through **Settings > Pages > Build and deployment >
Source > GitHub Actions**. Then open **Actions > Documentation > Run workflow**,
select `main`, and run it. Later documentation changes deploy automatically
after they are merged or pushed to `main`; maintainers do not build or upload
`.artifacts/site/` themselves.

Before changing a page to `publication: reviewed`, preview the production view
with `python3 -m mkdocs serve`. Use
`PRIK_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve` to review unpublished
pages with their draft warning. The lane index must also be reviewed before a
page in that lane can enter the deployed artifact.

Coverage troubleshooting and the exact local parity commands live in
[Quality Assurance](quality-assurance.md). Workflow-specific implementation
details remain in `.github/workflows/`; this page records the stable pipeline
contract rather than duplicating every YAML step.
