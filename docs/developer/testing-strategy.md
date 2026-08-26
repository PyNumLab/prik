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
test-suite directory map; `tests/fortran/README.md` and `tests/c/README.md` are
the language-specific feature indexes and command maps.

## Test Ownership

| Change or behavior | Test owner | What it proves |
| --- | --- | --- |
| Documentation content, metadata, navigation, or examples | `tests/docs/` | Published documentation and its repository contracts. |
| Maintainer command or CI-support behavior | `tests/tools/` | Repository tooling behavior. |
| Release or automation safety | `tests/workflows/` | Workflow safety properties. |
| User-visible language feature behavior | `tests/<language>/<feature>/<stage>/` | The language feature at its owning stage. |
| Cross-feature parsing, preprocessing, CLI, semantic representation, contract, build, or policy mechanism | `tests/<language>/infrastructure/<owner>/` | Shared pipeline behavior for that input language, including documented mechanisms. |

For a language feature, choose the feature before the stage:

```text
tests/<language>/<documented-feature>/<owning-stage>/
```

`infrastructure/` is not a fallback for tests that touch many packages. A
language feature remains feature-owned when it crosses parsing, policy,
planning, and lowering. Parsing, preprocessing, CLI, semantic IR and `.pyi`
conversion, build orchestration, and shared policy are cross-feature
infrastructure even when users can invoke or inspect them directly. Fortran
and C keep separate infrastructure owners because the input-language contract
and evidence differ; generated C used by a Fortran wrapper remains Fortran
evidence.

## Stable Contracts

Tests protect observable behavior, public interfaces, serialized or generated
formats, safety properties, and explicit architectural boundaries. A refactor
that preserves those contracts should not require unrelated test changes.

Do not freeze prose, heading order, private names, complete inventories, or
incidental code and directory layout. Test structure only when tooling consumes
it or it prevents a named, costly failure. When an intentional change breaks a
test, identify its invariant: keep or rewrite a durable contract; remove a test
that records only the old implementation or a review preference.

Documentation tests verify publication metadata, links, public references,
marked user examples, and package-guide command/result pairs. The page is the
expected-output source: stable output is exact; excerpts and target-dependent
output are checked only for the facts shown. Editorial wording and organization
remain contributor-review responsibilities.

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

A source build and a build from its unmodified generated contract must expose
the same public API and runtime behavior. That parity is enforced by test
structure, not by two parallel test lists: a parity-eligible test has one
assertion body and receives its imported wrapper from a fixture parametrized
with the `source` and `generated-pyi` build modes, so changing an assertion
changes both paths. Opt out only for a property that cannot apply to both
paths — exact generated `.pyi` text, or proving that a `.pyi` build does not
reparse source — and say why in the test name or a comment beside it. A
modified-contract test stays separate because it asserts a deliberately
different public API.

The real-library lane covers five Fortran projects—BLAS, LAPACK, FFTPACK,
MINPACK, and BSPLINE-FORTRAN—plus the direct-C libm and TA-Lib projects.

## Test And Fixture Placement

Keep a test and its checked fixtures with their final behavioral owner. Use
owner-local `end_to_end/fixtures/` for complete native projects; keep
parser, semantic, and policy setup with the corresponding stage. Generate
build products and temporary contracts in pytest temporary directories.

Within each Fortran feature, permanent end-to-end inputs use
`fixtures/native/`, reviewed generated packages use
`fixtures/contracts/<case>/`, and intentionally modified contracts use
`fixtures/edited_contracts/<case>/`. Direct-versus-adapted route cases may use
the same `native/` and `contracts/<case>/` pair below `fixtures/routing/`.
Scenario labels do not create additional fixture layers.

Check in generated `.pyi` only when its exact text, imports, placement, or
package shape is the invariant. Shared test support may provide builders and
assertions, but it must not become an alternate import surface for production
code.

## Selecting And Expanding Verification

Run the narrowest owner first:

```bash
python3 -m pytest -q tests/<language>/<feature>/<stage>
```

After moving or splitting tests, collect first, then run every destination
touched by the move. The [quality-assurance workflow](workflows/quality-assurance.md)
defines the required static analysis and broader verification.
