---
title: Testing Strategy
audience: developers, contributors
prerequisites: repository structure
related: quality-assurance.md, development-workflow.md
status: maintained
publication: draft
---

# Testing Strategy

The canonical ownership and command map is
[`../../tests/README.md`](../../tests/README.md). The Fortran feature index is
[`../../tests/fortran/README.md`](../../tests/fortran/README.md). Maintainers
record the active migration gates in
`docs/maintainer/roadmap/fortran-test-suite-cleanup-checklist.md`.

## Choose tests by language, feature, and stage

Tests first answer which native input contract they exercise:

- `tests/architecture/` owns meta-tests of the test suite's structure,
  evidence indexes, and selections;
- `tests/fortran/` owns Fortran input and semantic `.pyi` wrapper behavior;
- `tests/c/` owns C input-language inspection behavior; and
- `tests/shared/` owns behavior that neither imports nor selects a native
  language.

The architecture root is deliberately outside the language trees it validates.
Use a language subdirectory such as `tests/architecture/fortran/` when a
meta-invariant is language-specific.

Within Fortran, user-visible behavior is feature first and pipeline stage
second:

```text
tests/fortran/<documented-feature>/<owning-stage>/
```

This makes a documentation feature independently navigable:

```bash
python3 -m pytest -q tests/fortran/arrays
python3 -m pytest -q tests/fortran/derived_types
python3 -m pytest -q tests/fortran/source_parsing
python3 -m pytest -q tests/fortran/command_line_interface
python3 -m pytest -q tests/fortran/pyi_contracts/calls_and_results
```

Use `tests/fortran/infrastructure/` only for a cross-feature mechanism with no
honest public-capability owner. Public Fortran parsing, preprocessing,
command-line behavior, and semantic-IR conversion have the explicit
`source_parsing/`, `source_preprocessing/`, `command_line_interface/`, and
`semantic_ir/` owners. Generic internal policy dispatch, typed-plan mechanics,
compiler construction, and runtime-handle plumbing may remain infrastructure.
Ordinary regressions stay with their feature and stage. Minimized,
cross-feature parser interactions discovered in real-world sources belong in
`tests/fortran/source_parsing/parsing/`.

Treat a full third-party parser corpus as temporary evidence. Use contextual
line/branch coverage and named model assertions to identify what it uniquely
proves, replace those facts with minimized regressions, and delete the upstream
snapshot once the focused suite subsumes it. Aggregate coverage alone is not a
reason to keep hundreds of sources. A temporary corpus may be staged outside
the authoritative test tree while it is being reduced.

## Stage tests and end-to-end tests

Stage tests answer where a fact, policy decision, mechanism, or diagnostic is
owned. Use the earliest stage that can prove the invariant:

- parsing for source-model facts and parser diagnostics;
- probes or preprocessing for compiler facts and source processing;
- semantics for IR construction;
- policy for ownership, transfer, destruction, writeback, nullability,
  projection, storage, getter/setter, and Python-exposure decisions;
- wrapper code generation for typed-plan dispatch and emitted mechanisms;
- compiling or pipeline for commands, native inputs, artifacts, and build
  transitions; and
- runtime for shared execution mechanisms that are not complete feature
  journeys.

End-to-end tests answer whether a supported public feature survives the whole
journey. They start from user-owned Fortran source or an intentional `.pyi`,
generate wrappers, compile and link an extension, import it from an isolated
build directory, call the public Python surface, and verify visible behavior.
Successful compilation or import without a public call is insufficient.

All such tests live below the owning feature's `end_to_end/` directory and
carry `fortran_end_to_end`. BLAS and LAPACK additionally carry `real_library`
and remain native-source end-to-end evidence only.

## Diagnostics and unsupported behavior

Put an unsupported case at its first decisive stage and assert a stable prik
diagnostic. Do not force a known policy rejection through compilation merely
to observe a compiler failure.

Error cases stay with their owning feature. The Error Handling feature owns
only behavior that is itself an error-handling contract, such as native-status
projection, exception type/message behavior, cleanup on failure, and public
diagnostic routing. `tests/fortran/CONTRACT_COVERAGE.md` indexes negative
evidence and terminal stages across all features.

## Fixture ownership

Keep fixtures beside their final behavioral owner:

- parser-only sources with parsing;
- semantic/policy setup with that stage;
- complete native projects below feature-local `end_to_end/fixtures/`;
- edited `.pyi` below the edit family it proves;
- minimized real-world parser interactions with source parsing; and
- BLAS/LAPACK below their dedicated real-library end-to-end owner.

Generate build products and temporary contracts in pytest temporary
directories. Check in generated `.pyi` only where exact generation text,
imports, placement, or package shape is the invariant.

## Ownership discipline

Every maintained test and checked fixture has one final language-first owner.
The only non-language owner is `tests/architecture/`, for tests of the suite's
own structure and evidence system. Do not use it for product behavior or as a
stage-first compatibility root. Do not add forwarding fixtures, import
aliases, or fixture path fallbacks. Cross-feature mechanics require an explicit
infrastructure owner; language-neutral product checks require a shared owner.

## Required verification

Run the narrowest owning directory first. After moving or splitting tests, run
collection before execution and compare node IDs, parametrized suffixes,
markers, skips, and xfails. Then run every destination touched by the move.

For code or test changes, run the complete static-analysis suite documented in
`AGENTS.md`. Documentation-only changes use the focused documentation checks
and whitespace check.

Do not run the complete coverage workflow after each feature. The migration
records one CI-equivalent baseline and one final new-suite-only comparison.
Both use `COVERAGE_PROCESS_START=pyproject.toml`, combine subprocess data with
`python3 -m coverage combine`, and retain per-file executed line and branch
data. LAPACK remains CI-only unless a maintainer explicitly requests a local
run.
