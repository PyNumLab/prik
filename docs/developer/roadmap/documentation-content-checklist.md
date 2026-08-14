---
title: Documentation Content Checklist
audience: maintainers
prerequisites: documentation architecture
related: ../workflows/documentation.md, index.md, semantic-pyi-wrapper-checklist.md
status: active-roadmap
publication: draft
---

# Documentation Content Checklist

This checklist tracks documentation pages that exist but are still placeholders,
thin drafts, or missing evidence. It is not an implementation checklist. Use
[Semantic `.pyi` Wrapper Checklist](semantic-pyi-wrapper-checklist.md) for
runtime parity, policy, and wrapper implementation work.

A page is complete only when it gives readers the information they need without
relying on private conversation or implied project knowledge.

## Completion Rule

Move an item from the open queue to completed content evidence only when all of
these are true:

- [ ] The page status is accurate: `maintained` for current public behavior or
  `not-yet-implemented` for explicit future behavior.
- [ ] The page explains what is supported now and what is unsupported without
  exposing internal test-evidence ledgers in public user-facing prose.
- [ ] User-facing pages include a task-oriented workflow, expected output or API
  shape, limitations, and troubleshooting links.
- [ ] Developer-facing pages include ownership boundaries, source routes,
  focused verification commands, and rules for updating related docs.
- [ ] Examples are polished, copyable, and internally coherent. Executable
  examples and fixture-backed source stay synchronized with their checks.
- [ ] Reuse earlier examples by reference instead of reprinting them, unless the
  page must be self-contained for a first-time user task.
- [ ] User-facing examples use clean copyable filenames and module names; keep
  fixture-style names such as parser/test abbreviations out of beginner docs.
- [ ] Documentation-only changes use focused docs checks and `git diff --check`;
  reserve the full static-analysis suite for code, tests, build/tooling changes,
  or explicit pre-merge verification.
- [ ] User and Contributor area entry points, `mkdocs.yml`, related
  front matter, and `tests/docs/test_navigation.py` stay
  synchronized.

## Open Documentation Queue

Only unfinished documentation content belongs here. When a page is filled, move
the item to completed content evidence and update the page status in the same
change.

The queue is ordered by execution priority and dependency. Complete current
user workflows and their supporting references first. Leave larger example
investments and site-publication decisions until the underlying content is
stable. Within each section, work from foundational pages toward dependent or
more specialized pages.

### Troubleshooting, FAQ, And Releases

- [ ] `docs/user/troubleshooting/index.md`: route users by symptom: install, build,
  compiler, runtime, platform, wrapper contract, and generated artifact issues.
- [ ] `docs/user/troubleshooting/installation-issues.md`: document missing Python
  headers, NumPy, compiler packages, virtual environments, and platform package
  names.
- [ ] `docs/user/troubleshooting/build-issues.md`: document compile/link failures,
  missing native libraries, Makefile regeneration, output directories, and
  verbose logs.
- [ ] `docs/user/troubleshooting/compiler-issues.md`: document compiler detection,
  Fortran flags, preprocessing, ABI probes, GNU ABI assumptions, and kind
  support failures.
- [ ] `docs/user/troubleshooting/runtime-issues.md`: document import failures,
  symbol lookup errors, dtype or shape errors, callback exceptions, finalization,
  and cleanup symptoms.
- [ ] `docs/user/troubleshooting/platform-specific-issues.md`: document Linux,
  macOS, Windows, compiler, linker, and shared-library path caveats.
- [x] `CHANGELOG.md`: defines the changelog policy and release-note shape at the
  repository root, where package users and GitHub visitors can find it.

<!-- PRIK_C_DOCS_START
- [ ] `docs/user/faq/index.md`: add answers for source versus `.pyi` builds,
  supported languages, C-input future work, generated files, editable contracts,
  unsupported features, and where to report bugs.
PRIK_C_DOCS_END -->

### Contributor Architecture And Component Guides

- [x] `docs/developer/architecture.md`: shallow repository/package maps,
  complete wrapper workflow, stage authority, root entrypoints, change routes,
  and links to canonical package owners.
- [x] `docs/developer/packages/`: one maintained guide per top-level production
  package with local structure, essential objects, executable examples, expected
  output, focused tests, change routes, and invariants.
- [x] `docs/developer/workflows/contributing.md`: documentation-first changes,
  ownership lookup, support evidence, test selection, pull requests, review,
  and contribution licensing.
- [x] `docs/developer/workflows/quality-assurance.md`: active blocking/advisory
  tools, exact commands, coverage parity, compiler lanes, and local limits.
- [x] `docs/developer/workflows/ci.md`: pull-request validation and the hosted
  evidence that follows local verification.
- [x] `docs/developer/workflows/documentation.md`: documentation placement,
  local verification, and draft review.
- [x] `docs/developer/deferred/c-parser.md`: retained but unpublished C
  parser/C-to-IR material, separate from the generated CPython C backend.

The old TODO-only contributor pages, duplicate pipeline/codebase maps, completed
wrapper-plan and native-array migration ledgers, and separate internal indexes
were removed after their stable facts moved to these owners.

### Tutorials And Examples

- [ ] `docs/user/tutorials/numerical-solver.md`: add a fast checked solver fixture,
  build command, Python call, expected numeric output, and validation notes.
- [ ] `docs/user/tutorials/scientific-library.md`: document a small multi-routine
  library workflow, package shape, generated `.pyi` review, and regression
  checks.
- [ ] `docs/user/tutorials/modern-fortran-project.md`: document modules, derived
  types, arrays, constructors, and limitations using checked modern Fortran
  examples.
- [ ] `docs/user/tutorials/large-fortran-codebase.md`: document source ordering,
  dependency strategy, generated contract review, staged verification, and
  current limits for automatic dependency discovery.
- [ ] `docs/user/tutorials/packaging.md`: document packaging a generated extension,
  native artifacts, wheel limitations, and reproducible build notes.
- [ ] `docs/user/examples/blas-wrapper.md`: add the minimal BLAS-style
  runtime example or document the external dependency, with build, import, and
  numerical assertions.
- [ ] `docs/user/examples/lapack-wrapper.md`: document the LAPACK example as
  CI-owned by default, including why local runs are optional and what evidence CI
  supplies.
- [ ] `docs/user/examples/openmp-example.md`: document supported OpenMP path,
  required compiler flags, runtime environment variables, and fallback behavior.
- [ ] `docs/user/examples/object-oriented-fortran.md`: document classes,
  type-bound procedures, construction, finalization, and unsupported object
  model features with checked output.
- [ ] `docs/user/examples/ode-solver.md`: add a compact checked ODE fixture,
  expected result tolerance, and failure troubleshooting.
- [ ] `docs/user/examples/cfd-mini-example.md`: define a small enough fixture,
  supported array contracts, build command, and runtime validation.
- [ ] `docs/user/examples/mpi-example.md`: keep this page explicitly
  not-yet-implemented until MPI build, runtime, and distribution constraints have
  real evidence.

### Project Entry And Site Shell

- [ ] `docs/user/tutorials/index.md`: explain which tutorials are maintained and which
  are planned, with expected prerequisites and runtime cost.
- [ ] `docs/user/examples/index.md`: split verified cookbook recipes from
  planned larger examples and state the evidence required for each example.
- [x] `docs/developer/packages/index.md`: route contributors from each production
  package to its canonical guide.
- [x] `docs/developer/index.md`: distinguish implemented package references,
  workflows, active roadmaps, and deferred input-language material.
- [ ] Public documentation site publication gate: deploy the existing MkDocs
  documentation as the project website only after all of the following are
  true; do not create a separate marketing-content system for this milestone.
  - [x] Material for MkDocs, fail-closed `publication` metadata filtering,
    local draft preview, strict production builds, and the GitHub Pages Actions
    workflow are configured.
  - [ ] The landing page states the current project promise, supported workflow,
    and limitations without relying on planned behavior.
  - [ ] Installation and the first-wrapper workflow are complete and verified
    end to end.
  - [ ] The feature matrix is current and links supported behavior to evidence
    and limitations.
  - [ ] Semantic `.pyi` contracts, derived types, ownership, and memory
    management have maintained user-facing explanations.
  - [ ] The architecture overview explains the parser, semantic-policy,
    lowering, bridge, and binding boundaries.
  - [ ] Each page has been reviewed explicitly; change `publication: draft` to
    `publication: reviewed` only after that review.
  - [ ] Each area index is reviewed last, after the pages intended for its
    initial publication are ready. A draft area index keeps the complete area
    out of production.
  - [ ] A local draft preview and the Pages workflow artifact have validated
    navigation, links, search, rendering, and the static site build before
    enabling GitHub Pages.

## Completed Content Evidence

These pages already carry maintained content or active implementation roadmap
evidence. Keep them current as behavior changes, but do not treat them as the
primary placeholder queue.

- [x] `docs/index.md`: maintained website entry point for all reviewed
  documentation areas.
- [x] `docs/user/index.md`: maintained User documentation entry point.
- [x] `docs/developer/index.md`: maintained Contributor documentation entry
  point for developers and maintainers.
- [x] `docs/developer/architecture.md`: canonical contributor architecture
  orientation and folder-by-folder rollout plan.
- [x] `docs/developer/workflows/documentation.md`: maintained two-area
  documentation and local-verification workflow.
- [x] `docs/user/getting-started/index.md`: maintained beginner route from
  installation through the normal rebuild workflow.
- [x] `docs/user/getting-started/installation.md`: maintained user and contributor
  installation, native prerequisites, header checks, and platform boundaries.
- [x] `docs/user/getting-started/verification.md`: maintained package, inspection,
  native build, generated-artifact, and escalation checks.
- [x] `docs/user/getting-started/first-wrapped-function.md`: maintained checked
  scalar build, call result, exact dtype contract, and failure route.
- [x] `docs/user/getting-started/first-wrapped-module.md`: maintained checked module
  namespace, public state, saved state, visibility, and limitation guide.
- [x] `docs/user/getting-started/beginner-workflow.md`: maintained edit, inspect,
  planning, build, smoke-test, artifact-review, and rebuild loop.
- [x] `docs/user/faq/index.md`: maintained task-oriented answers that route
  search questions to checked guides, real-library examples, and the bounded
  PRIK/f2py comparison.
- [x] `docs/user/reference/semantic-ir.md`: maintained Semantic IR contract.
- [x] `docs/user/reference/semantic-pyi-format.md`: maintained semantic `.pyi`
  contract.
- [x] `docs/user/reference/pyi-contracts/`: maintained editable `.pyi`
  contract reference, organized by exports, callable surfaces, and argument
  and result projection.
- [x] `docs/user/reference/fortran-wrapper.md`: maintained Fortran wrapper
  contract reference.
- [x] `docs/user/reference/cli-commands.md`: maintained CLI reference.
- [x] `docs/user/reference/python-api.md`: maintained Python API reference.
- [x] `docs/user/reference/diagnostic-codes.md`: maintained diagnostic registry.
- [x] `docs/user/reference/generated-functions.md`: maintained generated callable
  signature, output projection, validation, and overload reference.
- [x] `docs/user/reference/generated-modules.md`: maintained generated module package
  shape, variables, constants, visibility, binding-name, and import reference.
- [x] `docs/user/reference/generated-classes.md`: maintained generated class,
  constructor, field, method, finalizer, ownership, and unsupported-shape
  reference.
- [x] `docs/user/reference/configuration-files.md`: maintained generated manifest,
  Makefile, coverage, and documentation tooling configuration reference.
- [x] `docs/user/guide/index.md`: maintained workflow-first route from datatype
  mapping through calls, storage, runtime behavior, and deployment.
- [x] `docs/user/guide/data-types.md`: maintained Fortran storage, semantic
  `.pyi`, Python value, and NumPy dtype mapping with compiler-probed limits.
- [x] `docs/user/guide/arrays.md`: maintained dtype, rank, shape, layout,
  C-order zero-copy and `COPY_F`, stride-aware view, assumed-rank, zero-size,
  result, and validation guide; advanced declaration expressions route to the
  contract reference.
- [x] `docs/user/guide/strings.md`: maintained immutable value, replacement,
  mutable storage, fixed-width array, length, and encoding guide.
- [x] `docs/user/guide/wrapping-functions.md`: maintained scalar, array-result,
  mixed-output, signature, native-call-limit, and evidence guide.
- [x] `docs/user/guide/wrapping-subroutines.md`: maintained input, output,
  inout, hidden/visible storage, tuple-order, and scalar-replacement guide.
- [x] `docs/user/guide/wrapping-modules.md`: maintained module namespace,
  procedure, constant, variable, saved-state, module-array, and common-block guide.
- [x] `docs/user/guide/optional-arguments.md`: maintained omission, `None`,
  keyword, input/output, default, limitation, and diagnostic guide.
- [x] `docs/user/guide/generic-interfaces.md`: maintained named, type-bound,
  operator, assignment, exact-dispatch, ambiguity, and overload guide.
- [x] `docs/user/guide/wrapping-derived-types.md`: maintained class, field,
  method, constructor, finalizer, nested borrow, layout, and polymorphism guide.
- [x] `docs/user/guide/allocatables.md`: maintained scalar projection, copy, replacement,
  borrowed module/component view, unallocated, lifetime, and limitation guide.
- [x] `docs/user/guide/pointers.md`: maintained scalar projection, call-local
  input, detached result, nullability, target policy, and blocked-reassociation guide.
- [x] `docs/user/guide/memory-management.md`: maintained ownership, transfer,
  destruction, mutability, release, borrowing, and policy-completion guide.
- [x] `docs/user/guide/callbacks.md`: maintained immediate callback contract,
  values, lifetime, GIL, thread, fatal-error, and unsupported-form guide.
- [x] `docs/user/guide/enumerations.md`: maintained integer-constant surface,
  value, typing, naming, and unsupported-form guide.
- [x] `docs/user/guide/error-handling.md`: maintained failure-layer, Python
  exception, native status projection, callback, diagnostic, and cleanup guide.
- [x] `docs/user/guide/building-shared-library.md`: maintained build, import,
  multi-source, compatibility, and editable-Makefile guide.
- [x] `docs/user/guide/raw-addresses.md`: maintained primitive, array,
  fixed-string, lifetime, validation, and address-safety guide.
- [x] `docs/user/examples/recipes/`: maintained recipe lane for checked
  command and API examples.
- [x] `docs/user/language-support/feature-matrix.md`: maintained support matrix.
- [x] `docs/developer/workflows/contributing.md`: maintained contributor
  development and review workflow.
- [x] `docs/developer/codebase-map.md`: maintained package and module ownership map.
- [x] `docs/developer/feature-to-code-map.md`: maintained feature route
  map.
- [x] `docs/developer/architecture.md`: maintained shallow repository/package
  structure and complete stage workflow.
- [x] `docs/developer/packages/parsers.md`: maintained Fortran
  parser reference.
- [x] `docs/developer/workflows/quality-assurance.md`: maintained quality and QA
  policy reference.
- [x] `docs/developer/packages/index.md`: maintained package ownership map and
  detailed architecture component guide index.
- [x] `docs/developer/packages/policy.md`: maintained
  ownership philosophy, completed policy vocabulary, supported lifetime triples,
  pointer-policy boundary, validation order, source routes, and safety boundary.
- [x] `docs/developer/roadmap/semantic-pyi-wrapper-checklist.md`: active implementation
  roadmap for semantic `.pyi` wrapper parity.

<!-- PRIK_C_DOCS_START
When the C-input documentation phase resumes, extend the maintained user-guide
index with a separate C-input route rather than mixing future behavior into the
current Fortran workflow.
- [x] `docs/developer/deferred/c-parser.md`: retained deferred C parser
  reference.
PRIK_C_DOCS_END -->
