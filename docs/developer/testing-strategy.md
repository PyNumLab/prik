---
title: Testing Strategy
audience: developers, contributors
prerequisites: PRIK Architecture, Feature-to-Code Map
related: architecture.md, feature-to-code-map.md, workflows/quality-assurance.md
status: maintained
publication: reviewed
---

# Testing Strategy

This page explains how PRIK assigns test ownership and how to choose the
smallest evidence that can prove a change. `tests/README.md` is the canonical
test-suite directory map; `tests/fortran/README.md` is the Fortran feature
index and command map.

## Test Ownership

| Change or behavior | Test owner | What it proves |
| --- | --- | --- |
| Documentation content, metadata, navigation, or examples | `tests/docs/` | Published documentation and its repository contracts. |
| Maintainer command or CI-support behavior | `tests/tools/` | Repository tooling behavior. |
| Release or automation safety | `tests/workflows/` | Workflow safety properties. |
| User-visible Fortran or semantic `.pyi` wrapper behavior | `tests/fortran/<feature>/<stage>/` | The documented capability at its owning stage. |
| Internal cross-feature mechanism | `tests/fortran/infrastructure/<owner>/` | A mechanism with no honest user-visible feature owner. |

For user-visible behavior, choose the feature before the stage:

```text
tests/fortran/<documented-feature>/<owning-stage>/
```

`infrastructure/` is not a fallback for tests that touch many packages. A
feature remains feature-owned when it crosses parsing, policy, planning, and
lowering. Infrastructure is only for reusable internal mechanisms that have no
public-capability owner.

## Stable Contracts

A test should protect observable behavior, a public interface, a serialized
format, a safety property, or an explicitly documented architectural boundary.
A refactor that preserves those contracts should not require unrelated test
changes.

Do not test exact prose, heading order, private class or function names,
complete file inventories, or incidental directory and call structure. Test a
repository structure only when the structure is itself consumed by tooling or
protects a named, costly failure. Documentation tests therefore enforce
publication metadata, valid links, reviewed/draft boundaries, public reference
synchronization, marked user examples, and package-guide command/result pairs.
Editorial review owns wording and page organization.

Existing tests are evidence, not specifications by themselves. When a test
fails after an intentional refactor, identify the underlying invariant before
changing production code. Keep or rewrite the test when it protects a stable
contract; remove it when it only encodes a recommendation or the previous
implementation.

The contributor making a change owns the review that brittle structural tests
cannot perform. Compare behavior before and after the change, inspect generated
artifacts at the affected boundary, and preserve existing documentation and
example wording as far as the requested change allows. Production-file
demonstrations do not require a fixed inventory or duplicate expected strings
in Python tests. When a package guide shows a command and its result, however,
the documentation suite runs the command and verifies the displayed result
from the page itself. Stable output is compared exactly; excerpts and target-
dependent results are checked only for the facts they claim.

## Evidence By Stage

Run the earliest stage that can prove the invariant.

| Stage | Evidence |
| --- | --- |
| `parsing/` | Source facts and source-located diagnostics. |
| `probes/` or `preprocessing/` | Compiler-derived target facts and prepared source. |
| `semantics/` | Language facts become the intended semantic IR. |
| `policy/` | Ownership, lifetime, projection, mutability, storage, and support choices are complete. |
| `codegen/` or `printers/` | Completed policy selects the intended plan, mechanism, or generated text. |
| `compiling/` or `pipeline/` | Commands, inputs, artifacts, and build transitions are correct. |
| `runtime/` | Shared runtime mechanisms behave correctly outside a complete feature journey. |
| `end_to_end/` | Input produces an imported extension whose public Python behavior is called and verified. |

An unsupported form belongs at its first decisive stage. Assert the owning
PRIK diagnostic there; do not force a known policy rejection through native
compilation only to observe a later failure.

## End-To-End Evidence

End-to-end tests establish a public wrapper journey: source or intentional
`.pyi` input, generated wrapper, compilation and link, imported extension, and
a call to the public Python surface. Successful compilation or import alone is
not end-to-end evidence.

Full-library BLAS and LAPACK evidence is a separate real-library lane. Do not
run LAPACK locally unless explicitly requested.

## Test And Fixture Placement

Keep a test and its checked fixtures with their final behavioral owner. Use
feature-local `end_to_end/fixtures/` for complete native projects; keep
parser, semantic, and policy setup with the corresponding stage. Generate
build products and temporary contracts in pytest temporary directories.

Check in generated `.pyi` only when its exact text, imports, placement, or
package shape is the invariant. Shared test support may provide builders and
assertions, but it must not become an alternate import surface for production
code.

## Selecting And Expanding Verification

Run the narrowest owner first:

```bash
python3 -m pytest -q tests/fortran/<feature>/<stage>
```

After moving or splitting tests, collect first, then run every destination
touched by the move. The [quality-assurance workflow](workflows/quality-assurance.md)
defines the required static analysis and broader verification.
