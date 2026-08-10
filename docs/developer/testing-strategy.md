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

- `tests/docs/` owns documentation metadata, navigation, examples, and content;
- `tests/tools/` owns maintainer commands and CI support scripts;
- `tests/workflows/` owns exceptional automation-safety checks;
- `tests/fortran/` owns Fortran input and semantic `.pyi` wrapper behavior;
- `tests/c/` owns C input-language inspection behavior.

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

Feature end-to-end tests live below the owning feature's `end_to_end/`
directory and carry `fortran_end_to_end`. Full-library integration nodes carry
`real_library`. The complete correctness examples under `examples/blas/` and
`examples/lapack/` use both markers and run only in the dedicated BLAS/LAPACK
lane.

The opt-in numerical showcases under
`tests/fortran/building_shared_library/end_to_end/real_libraries/` locate a
sibling checkout or an explicitly configured source directory, build the real
library sources, call representative generated routines, and compare against
independently known numerical answers. `PRIK_FFTPACK_SOURCE_DIR` and
`PRIK_MINPACK_SOURCE_DIR` override the default sibling `fftpack/src` and
`minpack/src` locations. The tests skip when the corresponding checkout is
absent.

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
- the authoritative full BLAS source set below `examples/blas/native/`, shared
  by the correctness example, full-library integration, LAPACK CI build, and
  build comparison tooling;
- the authoritative Reference LAPACK implementation corpus below
  `examples/lapack/native/`, shared by its correctness example and full-library
  integration.

Generate build products and temporary contracts in temporary directories.
Check in generated `.pyi` only where exact generation text,
imports, placement, or package shape is the invariant.

For BLAS behavior, source `examples/blas/build_all.sh`, then run
`python3 -m pytest -q examples/blas/tests` or one of its named test functions.
The aggregate script sources the exact documented `build_prik.sh` and
`build_f2py.sh` sequences. This compiles the sorted 155-source implementation
once and builds each wrapper once; the direct f2py script compiles the
committed reviewed `blas.pyf` and links the native artifact produced by the
PRIK script.
Documentation source markers require the displayed commands to remain
byte-for-byte equal to the executed scripts. `test_routine_coverage.py` audits
the parsed source inventory, f2py signature drift, both export sets, visible
named tests, and terminal outcomes. The dedicated CI lane explicitly adds
`examples/blas/ci/full_surface.py` to the same pytest invocation and does not
rebuild its wrappers afterward. User-run correctness tests and maintainer-only
audits therefore have separate directories.

For LAPACK behavior, the dedicated lane sources `examples/lapack/build_all.sh`
and then runs `python3 -m pytest -q examples/lapack/tests`. The aggregate
script sources the exact documented `build_prik.sh` and `build_f2py.sh`
sequences. The complete native corpus is compiled once, each wrapper is built
once, and the direct f2py script compiles the committed reviewed `lapack.pyf`
against the native artifact produced by the PRIK script while testing the
127-routine SciPy 1.18.0 `float64` inventory. Documentation source markers keep
the displayed commands equal to the executed scripts. The inventory audit
fails on SciPy drift, signature drift, missing sources or exports, missing
explicitly named tests, and divergent documentation claims. CI explicitly
adds `examples/lapack/ci/full_surface.py`
to the same pytest invocation, reusing the complete PRIK extension to require
all 2,066 procedure exports, including module namespaces, and run a
non-inventory runtime smoke call. User-run
correctness tests and maintainer-only audits have separate directories.

The complete `examples/` tree is a copyable execution boundary. Example code
may depend on an installed `prik` and its documented external toolchain, but it
must not import repository-only helpers from `tests/`. The workflow must source
the documented build scripts through `build_all.sh` before starting pytest,
rather than run a second build test that repeats native compilation or wrapper
construction.

## Ownership discipline

Every maintained test and checked fixture has one behavioral owner. Directory
layout, exact file inventories, and the current organization of the tests are
maintainer conventions rather than executable product contracts. Do not add
tests whose only purpose is to make an intentional reorganization fail. Add a
structural check only for a concrete, unusually costly risk that cannot be
protected by a behavior test. Cross-feature product mechanics require an
explicit infrastructure owner; documentation and maintainer tools use their
named top-level feature owners.

A test has one of two navigation shapes after language ownership is known:

- user-visible behavior lives under
  `tests/fortran/<documented-feature>/<owning-stage>/`; or
- a genuinely internal mechanism lives under
  `tests/fortran/infrastructure/<production-package>/test_<production-module>.py`.

For example, semantic-policy internals use
`infrastructure/semantics/test_ownership.py` and
`test_policy_completion.py`; wrapper internals use
`infrastructure/codegen/test_plan.py`, `test_planner.py`, and
`test_generator.py`. Other internal owners mirror `prik/compiling/`,
`prik/contracts/`, `prik/pipeline/`, `prik/runtime/`, and the remaining source
packages when they have real internal tests. Do not create empty mirror
directories or combine multiple production owners in generic backend or policy
collection modules. A retained direct-execution example
under `if __name__ == "__main__"` is maintained by the same dedicated test
module.

Documentation tests are grouped by invariant rather than by Markdown page.
Generic metadata, navigation, source-marker, link, and executable-example
validators stay parameterized over applicable pages. Page-specific content
contracts live in a module named for the documentation area they protect.
Workflow checks belong under `tests/workflows/` only when they
protect concrete behavior or release safety; they should not duplicate or
freeze the current CI organization. Tests for maintainer tools and workflow
safety and all blocking static-analysis checks run through the tracked pre-push
hook for early feedback, together with the fast publication and user-content
documentation checks and one compiled scalar-wrapper test that exercises the
public source-build path through a native call. They remain in GitHub Actions
for shared enforcement. Enable the hook once per clone with
`git config core.hooksPath .githooks`.

Test support contains reusable construction or assertion behavior, not an
alternate import surface for production code. Tests import `pytest`, Python
standard-library names, and production symbols from their real owners; support
modules do not re-export them merely to shorten imports.

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
