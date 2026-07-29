---
title: Language-First Test Suite and Fortran Pipeline Cleanup Checklist
audience: maintainers
prerequisites: testing strategy, pipeline map, current test-suite organization record
related: ../../developer/testing-strategy.md, ../../../tests/README.md, ../internal-architecture/pipeline-map.md
status: active-roadmap
publication: draft
---

# Language-First Test Suite and Fortran Pipeline Cleanup Checklist

This checklist defines one chronological migration:

1. establish the final language-first structure and its architecture guards;
2. record the current test, artifact, build-count, and coverage baselines;
3. quarantine C tests mechanically;
4. migrate Fortran tests one documented feature at a time;
5. delete each old pytest node when that feature evidence is replaced;
6. delete each old source, JSON, or `.pyi` artifact when its last recorded
   consumer has migrated;
7. validate the new suite alone against the baseline;
8. select portable end-to-end smoke nodes; and
9. implement compiler profiles, macOS support, and cost-conscious CI lanes.

The maintained User Guide, semantic `.pyi` references, and Fortran feature
matrix are the source of truth. The old test tree is evidence to inspect, not
the specification and not the destination structure.

## Implementation progress

Last verified: 2026-07-29  
Current work: not started; next is implementation batch 1.

```text
Test-suite migration through smoke (batches 1-7)
[░░░░░░░] 0/7 batches

Fortran feature migration
[░░░░░░░░░░░░░░░░░░░░░] 0/21 features

Complete roadmap (batches 1-10)
[░░░░░░░░░░] 0/10 batches
```

The batch checkboxes in [Implementation batches](#11-implementation-batches)
and the status cells in [Feature order](#feature-order) are the auditable
sources for these bars. Update the matching checkbox or status cell, all three
applicable counts and bars, `Last verified`, and `Current work` in the same
change.

A feature advances the feature bar only after both migration passes and its
feature completion gate pass. A batch advances a batch bar only after all of
its referenced checklist gates pass. Do not calculate headline progress from
the raw checkbox total: checklist items have unequal scope, some are accepted
design decisions, and some are repeatable templates.

## 1. Final structure and ownership

Create a directory only when a real test or fixture moves into it. This tree is
an ownership map, not a requirement to create every sketched file.

```text
tests/
  fortran/
    README.md
    CONTRACT_COVERAGE.md
    conftest.py
    _support/
    architecture/
      test_ci_toolchain_lanes.py
      test_contract_coverage_map.py
      test_language_ownership.py
      test_smoke_selection.py
    features/
      data_types/
      arrays/
      strings/
      functions/
      subroutines/
      modules/
      optional_arguments/
      generic_interfaces/
      derived_types/
      allocatables/
      pointers/
      memory_management/
      callbacks/
      enumerations/
      raw_addresses/
      error_handling/
      building_shared_library/
        pipeline/
        end_to_end/
          real_libraries/
            blas/
            lapack/
      semantic_pyi_format/
      pyi_contracts/
        exports_and_modules/
        functions_and_classes/
        calls_and_results/
    infrastructure/
      cli/
      parsing/
      probes/
      preprocessing/
      semantics/
      wrapper_codegen/
        printers/
      compiling/
        commands/
        linking/
        profiles/
        platforms/
      pipeline/
        artifacts/
        diagnostics/
      runtime/
        handles/
    corpus/
      parsing/
        regressions/
        real_world/
  c/
    README.md
    parsing/
    probes/
    preprocessing/
    semantics/
      conversion/
    pipeline/
    fixtures/
  shared/
    architecture/
    cli/
    contracts/
    docs/
    naming/
    tools/
    types/
    utilities/
```

Each documentation feature may contain only the stages it actually needs:

```text
tests/fortran/features/arrays/
  parsing/
  semantics/
  policy/
  wrapper_codegen/
  pipeline/
  end_to_end/
    fixtures/
```

This is feature-first and stage-second. Do not create empty stage directories.
Cross-feature mechanics go under `infrastructure/`; user-visible behavior does
not.

### Language ownership

- [x] `tests/fortran/` owns tests whose native input contract is Fortran,
  including generated Fortran bridge and C/CPython binding behavior for that
  Fortran contract.
- [x] `tests/c/` means C is the input language. It does not own generated C
  used to implement a Fortran wrapper.
- [x] `tests/shared/` contains only language-neutral behavior. A shared test or
  fixture must not select C versus Fortran through a parameter, conditional,
  suffix, compiler name, or fallback path.
- [x] C receives a mechanical quarantine only. Its behavior is not redesigned
  in this project.
- [x] Fortran receives the documentation-led behavioral cleanup.
- [x] Old imports, forwarding fixtures, collection shims, path aliases, and
  compatibility fallbacks are not retained.

### Feature navigation

- [ ] Normalize each documentation filename to the matching feature directory:
  `data-types.md` → `features/data_types/`,
  `optional-arguments.md` → `features/optional_arguments/`, and so on.
- [ ] Map the three `.pyi` editing pages beneath `features/pyi_contracts/` and
  map `semantic-pyi-format.md` to `features/semantic_pyi_format/`.
- [ ] Make `tests/fortran/README.md` a compact table from every feature-bearing
  page listed in the Feature order below to its directory and focused pytest
  command.
- [ ] Keep all evidence for a feature beneath that feature whenever possible:
  parsing, semantics, policy, code generation, pipeline, diagnostics, fixtures,
  and end-to-end behavior.
- [ ] Use the same stage names inside every feature:
  `parsing`, `probes`, `preprocessing`, `semantics`, `policy`,
  `wrapper_codegen`, `compiling`, `pipeline`, `runtime`, and `end_to_end`.
  Create only the stages that own real evidence.
- [ ] Put pytest modules below a stage directory rather than directly at the
  feature root, so path shape always answers both “which feature?” and “which
  stage?”.
- [ ] Use `infrastructure/` only when a test has no honest User Guide or `.pyi`
  feature owner, such as source-form lexing, compiler discovery, generic
  command construction, or runtime-handle plumbing.
- [ ] Give each infrastructure module an owner statement in
  `tests/fortran/README.md`; do not create `misc`, `general`, or catch-all
  feature directories.
- [ ] Keep `_support/` limited to test utilities used by several features.
  It contains no pytest modules, native feature sources, or checked contracts;
  feature-specific support stays inside its feature.
- [ ] Put an ordinary regression with its current feature and owning stage.
  Only real-world parser-corpus cases remain grouped under `corpus/parsing/`.
- [ ] During migration, make architecture checks reject an unknown feature
  directory and require every completed Feature order row to have its directory.
  At the final gate, enforce a one-to-one mapping for all rows. Cross-cutting
  indexes, the feature matrix, and the Fortran wrapper reference map through
  `CONTRACT_COVERAGE.md`; they do not create catch-all feature directories.

### Stage ownership

| Owner | What it proves |
| --- | --- |
| Parsing | Source becomes the intended parser model, or parsing stops with the intended diagnostic |
| Probes and preprocessing | Compiler facts, preprocessing recipes, dependencies, and source mappings are correct |
| Semantic conversion | Parser facts become the intended semantic IR |
| Post-IR policy | Ownership, transfer, destruction, mutation/writeback, nullability, projection, release, storage mode, getter/setter behavior, and Python exposure are complete |
| Wrapper planning and generation | Completed policy selects a typed plan and named bridge/binding mechanisms |
| Compiling and pipeline | Commands, objects, libraries, artifacts, and build-stage transitions are correct |
| End to end | Source or an intentional `.pyi` contract produces an imported extension whose public behavior is called and verified |
| Corpus | A real-source interaction or library-scale input supplies evidence that a minimal conformance fixture cannot replace |

Rules:

- [ ] Give each test one primary invariant and one owning stage.
- [ ] Put exhaustive syntax and policy combinations at the earliest stage that
  can prove them.
- [ ] Add an end-to-end test only when generation, compilation, import, or
  runtime behavior contributes evidence.
- [ ] Keep unsupported behavior at the first stage with enough information to
  reject it deliberately.
- [ ] Preserve a downstream diagnostic test only when CLI/API propagation is
  itself public behavior.
- [ ] Do not let bridge or binding tests accept semantic decisions inferred
  from datatype, `intent`, dotted shape, alias state, or local memory checks.
  Those decisions belong in completed post-IR policy.

### CLI ownership

- [ ] Generic argument parsing and output formatting belong in
  `tests/shared/cli/`.
- [ ] Cross-feature Fortran command contracts belong in
  `tests/fortran/infrastructure/cli/`.
- [ ] A CLI test that builds, imports, calls, and verifies a Fortran extension
  belongs in the owning feature's `end_to_end/` directory, normally
  `features/building_shared_library/end_to_end/`.
- [ ] One end-to-end CLI case may be selected as toolchain smoke. Focused CLI
  contract tests are selected separately by the toolchain CI lane.

### Final layout gates

Register a structural marker for cross-feature selection:

```toml
"fortran_end_to_end: compiled, imported, and called Fortran feature tests"
"real_library: dedicated BLAS/LAPACK native-source end-to-end tests"
```

- [ ] A focused `tests/fortran/` command collects no C-input test.
- [ ] A focused `tests/c/` command collects no Fortran-input test.
- [ ] Shared tests import no language-owned helpers.
- [ ] Fortran and C tests import neither each other's helpers nor fixtures.
- [ ] Feature-local fixtures live with their owner. Parser corpora live under
  `corpus/parsing/`; BLAS and LAPACK live only under
  `features/building_shared_library/end_to_end/real_libraries/`.
- [ ] `python -m pytest tests/fortran/features/arrays` runs every stage of the
  Arrays contract without collecting unrelated features.
- [ ] Every node below a feature's `end_to_end/` directory carries
  `fortran_end_to_end`, and no other node carries it.
- [ ] BLAS/LAPACK nodes additionally carry `real_library`, and only those nodes
  carry it.
- [ ] `python -m pytest tests/fortran/features -m "fortran_end_to_end and not real_library"`
  selects the ordinary feature-local end-to-end suite.
- [ ] The dedicated real-library lane selects `real_library` separately.
- [ ] Positive architecture checks enforce allowed owners. Do not add tests
  whose only purpose is to assert that an intentionally removed old path does
  not exist.

## 2. Evidence records and migration states

### Permanent contract ledger

Create `tests/fortran/CONTRACT_COVERAGE.md` before deleting or merging
behavioral tests. It is an evidence index, not a second product specification.

The authoritative documentation is:

- every page under `docs/user/guide/`;
- `docs/user/reference/pyi-contracts/`;
- `docs/user/reference/semantic-pyi-format.md`;
- `docs/user/reference/fortran-wrapper.md`; and
- `docs/user/language-support/feature-matrix.md`.

Each testable documentation claim gets one row with this minimum schema:

| Field | Meaning |
| --- | --- |
| Documentation contract | Page and stable heading anchor |
| Status | Supported, partially supported, or blocked |
| Dimensions | Dtypes, ranks, storage, argument modes, states, or edit forms |
| Stage evidence | Exact pytest node at the cheapest owner |
| Runtime evidence | Exact compiled/imported/called node when user-visible |
| Negative evidence | Exact diagnostic node and terminal stage |
| CI lane | Canonical, smoke, corpus, scheduled, or release |

- [ ] Record gaps explicitly; one broad example does not cover every dtype,
  rank, state, or edit.
- [ ] Give every supported user-visible behavior runtime evidence.
- [ ] Give every documented unsafe or unsupported behavior terminal-stage
  diagnostic evidence.
- [ ] Record source build, generated-`.pyi` replay, edited-`.pyi`, and
  source-free native-artifact evidence separately when the documentation claims
  each route.
- [ ] Make architecture tests resolve documentation links and collected node
  IDs.
- [ ] Reject deletion of the last evidence for a contract row.

### Temporary pytest migration ledger

Track each legacy pytest node until it is retired:

| Field | Meaning |
| --- | --- |
| Legacy node | Exact collected node or non-overlapping selector |
| Features | Every documentation feature asserted by the node |
| Primary stage | Cheapest owner of its main invariant |
| Disposition | Move, merge, split, minimize, delete, or defer |
| Replacement nodes | One or more exact final nodes |
| State | `legacy-only`, `dual-proof`, or `retired` |

One old node may map to several features and several replacement nodes.
`dual-proof` is temporary while old and new evidence are compared. Mark a node
`retired` and delete it as soon as every useful assertion and secondary feature
has a final owner. Do not wait for all other features.

### Temporary artifact-consumer ledger

Track native sources, include files, JSON goldens, and `.pyi` packages
independently from pytest nodes:

| Field | Meaning |
| --- | --- |
| Legacy artifact | Exact path and artifact type |
| Consumers | Every current pytest node or generator that reads it |
| Features and stages | Every remaining role it serves |
| Final owner | Replacement path, final shared owner, or redundant disposition |
| Next consumer | Next unmigrated feature/stage that still needs it |
| State | `needed`, `replacement-verified`, or `deleted` |

The deletion rule is singular:

> Delete a legacy artifact immediately after its last recorded consumer,
> feature, and stage have migrated and its replacement evidence is verified.

Consequences:

- A parser-only JSON golden can be deleted when its parser evidence moves.
- A parser source can be deleted at the same point unless a recorded semantic,
  pipeline, corpus, or runtime consumer still needs it.
- A `.pyi` syntax/validation fixture can be deleted after that stage moves
  unless a recorded build or end-to-end test still consumes it.
- A native source shared by several runtime features remains only until the
  last of those features migrates.
- An artifact is never retained merely for a final bulk cleanup.
- A new test never reads from a legacy fixture root, even while the legacy
  artifact remains for another old consumer.

### Architecture enforcement during migration

- [ ] Resolve every legacy and replacement pytest selector.
- [ ] Reject overlapping migration selectors.
- [ ] Report `legacy-only`, `dual-proof`, and `retired` node counts.
- [ ] Resolve every artifact consumer and final owner.
- [ ] Fail when a deleted pytest node remains listed as an artifact consumer.
- [ ] Fail when an artifact marked `replacement-verified` has no remaining
  consumer but was not deleted in the current migration slice.
- [ ] Remove the temporary migration inventories after final paths and the
  permanent contract ledger become authoritative.

## 3. Fixture ownership rules

Do not move `tests/data/fortran/` wholesale into another central data
directory. Audit and place every artifact beside its final behavioral owner.

### Migration map

| Current family | Final owner |
| --- | --- |
| `tests/data/fortran/wrapper/` | `tests/fortran/features/<feature>/end_to_end/fixtures/<case>/native/` |
| `tests/data/fortran/general/` | Owning feature/stage, or `tests/fortran/infrastructure/pipeline/fixtures/` for genuinely feature-neutral mechanics |
| `tests/data/fortran/errors/` | Fixture directory of the first rejecting stage |
| `tests/data/fortran/blas/` and `lapack/` | `tests/fortran/features/building_shared_library/end_to_end/real_libraries/{blas,lapack}/native/` |
| Retained SciFortran content | `tests/fortran/corpus/parsing/{regressions,real_world}/` |
| Parser source/JSON pairs | Beside their parser or corpus owner |
| Language-neutral `.pyi` syntax | `tests/shared/contracts/` |
| Fortran `.pyi` build fixtures | `tests/fortran/features/semantic_pyi_format/{pipeline,end_to_end}/fixtures/` |
| Generated contract goldens | Beside their generation/package-shape owner |
| Edited contracts | `tests/fortran/features/pyi_contracts/<edit-family>/end_to_end/fixtures/` |
| Invalid `.pyi` contracts | Fixture directory of the first rejecting stage |

### Native sources

- [ ] Reuse a clear, minimal old source when it already owns a distinct
  invariant.
- [ ] Minimize or replace a source that mixes unrelated behavior or obscures
  the intended contract.
- [ ] Create a coherent new source when documentation has no evidence or one
  compiled fixture can cover a matrix much more efficiently.
- [ ] Keep parser-only sources with parsing and semantic/policy setup sources
  with their semantic owner.
- [ ] Keep full-pipeline sources with their end-to-end feature.
- [ ] Put multi-source projects, include files, and support files under a local
  `native/` directory.
- [ ] Give a coherent multi-feature runtime project one primary final owner and
  map secondary features to its nodes. Do not copy it into several directories
  merely to make the tree symmetrical.
- [ ] Compile one feature fixture once and share it across its runtime
  assertions when isolation permits.
- [ ] Generate all objects, bridge/binding files, and extensions in pytest
  temporary directories. Build products are not checked fixtures.

### Parser sources and JSON

- [ ] Keep a source and JSON together only when exact normalized parser
  serialization is the invariant.
- [ ] Prefer focused Python assertions when only a few parser facts matter.
- [ ] Never replace a meaningful parser assertion with “did not crash.”
- [ ] Do not retain a whole JSON snapshot because an unrelated runtime test
  passes through parsing.
- [ ] Generate expected JSON with one documented command and review it with the
  source.
- [ ] Store ordinary expected diagnostics in Python assertions unless JSON is
  itself a documented public output format.
- [ ] Delete each old JSON as soon as its final parser evidence exists and no
  recorded later consumer remains.

### Generated `.pyi` packages

- [ ] Check in generated `.pyi` only when generation text, imports, native
  placement, or package shape is the invariant.
- [ ] Keep one representative expected package at the pipeline/generation
  owner; do not copy it into every end-to-end feature.
- [ ] Regenerate checked output only through an explicit update command and
  review the semantic diff.
- [ ] Generate intermediate contracts in a temporary directory when a test
  immediately rebuilds them.
- [ ] Compare temporary generated output with a golden only in the
  representative test that owns printer/package compatibility.

### Edited `.pyi` contracts

An edited contract is authoritative input, not expected generated output.

- [ ] Store it under the user edit being tested.
- [ ] Supply source, objects, or libraries as implementation only. Do not parse
  native source to restore declarations removed from the edited contract.
- [ ] Assert the changed Python surface or behavior, not merely successful
  loading or compilation.
- [ ] Generate a starter contract temporarily when before/after comparison is
  needed.
- [ ] Keep checked starter and edited packages together only when their exact
  difference is the invariant.
- [ ] Treat checked `.pyi` as read-only and make test-specific changes in
  temporary copies.
- [ ] Place invalid syntax/import, semantic structure, policy, ABI, and runtime
  failures at their earliest respective owners.

### `.pyi` build responsibilities

| Owner | What it proves |
| --- | --- |
| `tests/fortran/features/semantic_pyi_format/pipeline/` | Loading, import graph, package assembly, build plan, and diagnostics |
| `tests/fortran/features/semantic_pyi_format/end_to_end/` | An ordinary contract is authoritative input and produces a working extension |
| `tests/fortran/features/pyi_contracts/<edit-family>/end_to_end/` | A documented edit changes the built API or runtime behavior |

The end-to-end baseline contains:

- [ ] source → generated `.pyi` → rebuilt extension → runtime call;
- [ ] `.pyi` plus prebuilt native artifacts and no native source, proving there
  is no parser fallback;
- [ ] one imported multi-file contract package; and
- [ ] each distinct documented native-artifact topology once.

Use one shared `.pyi` build helper. Keep one small unedited baseline for fault
localization; edited tests do not replace it. Do not run every feature through
source, generated-`.pyi`, and edited-`.pyi` modes.

## 4. Establish the structure and baseline

Do these steps before the first Fortran feature migration.

### Structure and guardrails

- [ ] Update `tests/README.md` and the developer testing strategy with the
  language-first ownership contract.
- [ ] Create only the first needed `tests/{fortran,c,shared}/` destinations.
- [ ] Add positive language ownership and contract-ledger architecture checks.
- [ ] Add temporary pytest-node and artifact-consumer migration inventories.
- [ ] Identify helper and `conftest.py` consumers before moving shared support.
- [ ] Update workflow, tooling, cache, and documentation paths in the same
  change that makes each new path authoritative.

### Baseline records

Record immediately before the first move:

- repository-wide collected node IDs;
- stage and feature counts;
- markers, skips, and xfails;
- wall time;
- native compile/link invocations and cache hits; and
- one CI-equivalent Python line-and-branch coverage artifact.

Initial observations from 2026-07-29, to be remeasured:

| Observation | Initial result |
| --- | ---: |
| Collected pytest cases | 6,277 |
| Fortran parser cases | 2,879 |
| SciFortran parser cases | 324 |
| Fortran wrapper cases | 446 |
| Source/generated-`.pyi` parity cases | 110, representing 55 cases in each mode |
| Native wrapper source files | 58 |
| Copied SciFortran files | 303 |

These are legacy collection observations, not final ownership claims.
BLAS/LAPACK are classified only by their final native-source end-to-end owner.

For the coverage baseline:

- [ ] Mirror GitHub Actions, including its deterministic seed and test
  selection.
- [ ] Set `COVERAGE_PROCESS_START=pyproject.toml`.
- [ ] Combine subprocess data with `python3 -m coverage combine`.
- [ ] Run `python3 -m coverage report`.
- [ ] Save `coverage json` output with the source revision and environment.
- [ ] Record executed lines and branches per Python source file, not only an
  aggregate percentage.

During migration:

- [ ] Do not run the complete coverage workflow after every feature.
- [ ] Run focused owner tests, collection/layout checks, and required static
  analysis.
- [ ] Use focused coverage only to investigate a risky deletion or final
  regression.
- [ ] Keep production Python unchanged until the test-migration coverage gate.
  If a new test exposes a product bug, fix it in a separate documented change
  and establish a comparable baseline before resuming.

Coverage is only one guard. Preserve three independent evidence kinds:

1. Python line and branch execution;
2. documented feature and diagnostic evidence; and
3. corpus syntax and real-source interaction evidence.

Equal line coverage cannot prove that the same parser interaction, lifetime
state, datatype matrix, or public error remains covered.

### Mechanical C quarantine

- [ ] Move C parsing, probe, preprocessing, semantic, pipeline, CLI-dispatch,
  property, and C-specific `.pyi` tests beneath `tests/c/`.
- [ ] Move their fixtures and helpers with their consumers.
- [ ] Preserve assertions, parameters, markers, skips, and fixture contents.
- [ ] Do not expand or redesign C coverage.
- [ ] Run focused `tests/c/` collection and execution.

## 5. Migrate Fortran feature by feature

Use the User Guide sidebar order. Finish a feature slice before starting the
next unless a shared fixture makes two adjacent features inseparable.
When an introductory page points to a dedicated later page, migrate only the
introductory contract in the first slice; the dedicated page owns its detailed
matrix. For example, Data Types owns scalar types, while Arrays and Strings own
their full specialized behavior.

### Fast adoption within each feature

Use two short passes inside one feature before moving to the next:

**Pass A — adopt the final structure**

- [ ] Create the feature directory and only its currently needed stage
  directories.
- [ ] Use one read-only inventory tool to collect old node IDs, markers,
  durations, static fixture path references, and current wrapper feature
  directories into the temporary ledgers. Do not hand-enumerate thousands of
  nodes.
- [ ] Scaffold the feature's contract rows from documentation headings, then
  review and complete them manually; generated headings are navigation aids,
  not automatic coverage claims.
- [ ] Seed the feature from the already clustered wrapper/end-to-end directory
  before searching stage tests, because that usually provides its source
  project and clearest public assertions.
- [ ] Move clear existing tests with minimal assertion changes.
- [ ] Copy or relocate their fixtures according to last-consumer ownership.
- [ ] Update imports, workflow selectors, and ledger node IDs.
- [ ] Run the old/new focused comparison only where a rewrite makes equivalence
  uncertain.
- [ ] Retire replaced old pytest nodes and immediately delete unconsumed old
  artifacts.
- [ ] Run collection and architecture guards before expensive native execution,
  so path and ownership mistakes fail quickly.

**Pass B — complete the documented contract**

- [ ] Compare the adopted evidence with every documentation row for the feature.
- [ ] Split mixed tests, merge duplicate invariants, improve names, and share
  native builds.
- [ ] Add only the missing dtype, rank, state, edit, error, or runtime cases.
- [ ] Finish the feature completion gate before starting the next feature.

This is faster than designing an ideal replacement suite from a blank page and
safer than mechanically moving the entire old tree before understanding it.
Automate inventory and path rewriting, but keep disposition and assertion
decisions reviewable. Do not run full coverage between features.

### Feature order

| Status | Documentation | Final feature directory |
| --- | --- | --- |
| [ ] | [Data Types](../../user/guide/data-types.md) | `features/data_types/` |
| [ ] | [Arrays](../../user/guide/arrays.md) | `features/arrays/` |
| [ ] | [Strings](../../user/guide/strings.md) | `features/strings/` |
| [ ] | [Wrapping Functions](../../user/guide/wrapping-functions.md) | `features/functions/` |
| [ ] | [Wrapping Subroutines](../../user/guide/wrapping-subroutines.md) | `features/subroutines/` |
| [ ] | [Wrapping Modules](../../user/guide/wrapping-modules.md) | `features/modules/` |
| [ ] | [Optional Arguments](../../user/guide/optional-arguments.md) | `features/optional_arguments/` |
| [ ] | [Generic Interfaces](../../user/guide/generic-interfaces.md) | `features/generic_interfaces/` |
| [ ] | [Wrapping Derived Types](../../user/guide/wrapping-derived-types.md) | `features/derived_types/` |
| [ ] | [Allocatables](../../user/guide/allocatables.md) | `features/allocatables/` |
| [ ] | [Pointers](../../user/guide/pointers.md) | `features/pointers/` |
| [ ] | [Memory Management](../../user/guide/memory-management.md) | `features/memory_management/` |
| [ ] | [Callbacks](../../user/guide/callbacks.md) | `features/callbacks/` |
| [ ] | [Enumerations](../../user/guide/enumerations.md) | `features/enumerations/` |
| [ ] | [Raw Addresses](../../user/guide/raw-addresses.md) | `features/raw_addresses/` |
| [ ] | [Error Handling](../../user/guide/error-handling.md) | `features/error_handling/` |
| [ ] | [Building the Shared Library](../../user/guide/building-shared-library.md) | `features/building_shared_library/` |
| [ ] | [Semantic `.pyi` Format](../../user/reference/semantic-pyi-format.md) | `features/semantic_pyi_format/` |
| [ ] | [Exports and Modules](../../user/reference/pyi-contracts/exports-and-modules.md) | `features/pyi_contracts/exports_and_modules/` |
| [ ] | [Functions and Classes](../../user/reference/pyi-contracts/functions-and-classes.md) | `features/pyi_contracts/functions_and_classes/` |
| [ ] | [Calls and Results](../../user/reference/pyi-contracts/calls-and-results.md) | `features/pyi_contracts/calls_and_results/` |

### Repeat this loop for every feature

1. [ ] Read the documentation page and relevant semantic `.pyi` sections.
2. [ ] Add every supported form, limitation, error, state transition, and edit
   to `CONTRACT_COVERAGE.md`.
3. [ ] Find all old pytest nodes and every source, JSON, `.pyi`, helper, and
   generator that contributes evidence for the feature.
4. [ ] Record all consumers before moving or deleting an artifact.
5. [ ] Classify each invariant at its cheapest stage.
6. [ ] Create final parsing evidence where syntax or parser-model behavior is
   distinct.
7. [ ] Create final probe/preprocessing evidence where compiler-derived facts
   or source processing is distinct.
8. [ ] Create final semantic-conversion and completed-policy evidence for every
   distinct semantic decision.
9. [ ] Create final wrapper-plan/code-generation evidence for every distinct
   selected emitted-code mechanism.
10. [ ] Create final compile/pipeline evidence for distinct commands, artifact
    topologies, and build transitions.
11. [ ] Create one or more end-to-end journeys for supported public behavior
    that crosses build/import/runtime boundaries.
12. [ ] Put each unsupported case at its first decisive stage and verify the
    stable diagnostic.
13. [ ] Reuse, minimize, or replace old fixtures according to the artifact
    ledger. Never make a new test fall back to an old fixture path.
14. [ ] Run old and new focused evidence together when equivalence needs proof.
15. [ ] Update permanent and temporary ledgers with exact new node IDs.
16. [ ] Delete each superseded old pytest node once all of its useful
    assertions and secondary features have replacements.
17. [ ] Delete each old source, JSON, or `.pyi` immediately when its last
    recorded consumer, feature, and stage have migrated.
18. [ ] Run the final focused new feature tests, collection/layout guards, and
    required static analysis.

### Feature completion gate

- [ ] Every documentation row for the feature has stage, runtime, or negative
  evidence as required.
- [ ] The new feature tests do not import old tests, helpers, or fixtures.
- [ ] No superseded pytest node remains.
- [ ] Every retained old artifact names a real remaining consumer and next
  feature/stage.
- [ ] No unconsumed old artifact remains.
- [ ] Native build count is measured and shared fixtures are reused.
- [ ] Test names and assertions identify the feature without historical phase
  numbers.

### End-to-end success definition

Every successful end-to-end case must:

- [ ] start from user-owned Fortran source or an intentional source-free
  semantic `.pyi`;
- [ ] use the public API or CLI route being claimed;
- [ ] pass through completed semantics and wrapper planning;
- [ ] generate bridge and binding code;
- [ ] compile and link a Python extension;
- [ ] import from an isolated temporary build location; and
- [ ] call the public Python surface and verify values, mutation, lifetime,
  state, identity, exceptions, or another visible result.

Artifact existence, emitted text, compiler success, or import without a public
call is not sufficient.

### General matrix rules

- [ ] Preserve combinations whose legality, ABI, storage, ownership, lifetime,
  mutation, projection, or diagnostic differs.
- [ ] Put the complete theoretical policy matrix at policy/plan level when it
  does not require compilation.
- [ ] Keep all runtime matrix cells when they cheaply reuse one coherent
  extension and perform different public checks.
- [ ] Do not multiply independent dimensions when they select the same policy
  and runtime mechanism.
- [ ] Use a full cross-product when dimensions interact.
- [ ] Add a special case for each distinct mechanism, boundary, prior
  regression, and deliberately unsupported combination.
- [ ] Compile one extension per coherent feature fixture, not one extension per
  assertion.

### Data Types

- [ ] Cover `Bool`, `Int8`, `Int16`, `Int32`, `Int64`, `Float32`, `Float64`,
  `Complex64`, and `Complex128` wherever documentation supports them.
- [ ] Cover scalar input, function result, hidden `intent(out)`, visible
  `intent(inout)`, rank-zero storage, and native value/reference passing.
- [ ] Verify exact NumPy scalar acceptance and documented rejection of wrong
  Python/NumPy value types.
- [ ] Use zero, signed, boundary, logical, real, imaginary, complex, and
  round-trip values appropriate to each dtype.
- [ ] Cover module-variable getters/setters and constants once per distinct
  accessor mechanism.
- [ ] Cover documented construction defaults.
- [ ] Reject unsupported wider/unmapped kinds explicitly rather than narrowing.
- [ ] Keep compiler-kind probing exhaustive at probe/semantic level; smoke uses
  representatives unless compiler mappings differ.

### Arrays

- [ ] Compile, import, call, and verify every supported primitive element dtype
  at every supported concrete rank 1-15.
- [ ] Generate the dtype/rank procedures in one or a few coherent fixtures.
- [ ] Verify values, shape, and mutation for every matrix cell.
- [ ] Cover rank-zero storage and assumed rank separately.
- [ ] Cover `Flat`, fixed/open extents, visible shape expressions, lower bounds,
  assumed shape/size, and zero-sized arrays.
- [ ] Cover Fortran order, `ORDER_C`, `COPY_F`, dense arrays, and documented
  positive-stride views.
- [ ] Cover inputs, caller storage outputs, in-place writeback, no-`intent`
  mutation, array results, immutable replacement, and optional presence.
- [ ] Verify dtype, rank, shape, contiguity, order, alignment, byte order,
  writeability, strides, broadcasting, reversal, and zero-size validation.

### Strings

- [ ] Cover runtime-length scalar `String`.
- [ ] Cover fixed-width scalar input, result, replacement, and discarded
  mutation.
- [ ] Cover mutable rank-zero fixed-width storage.
- [ ] Cover fixed-width NumPy byte arrays for every documented rank and mode.
- [ ] Include length 1, a representative width, and every width boundary that
  changes lowering or ABI behavior.
- [ ] Verify bytes, blank preservation, `S<n>` itemsize, embedded NUL behavior,
  empty values, and mutation.
- [ ] Reject Unicode/object arrays, wrong itemsize/rank/shape, read-only output
  storage, and unsupported deferred-length mutation.
- [ ] Cover fixed-string raw addresses separately.

### Procedures, arguments, and results

- [ ] Cover functions and subroutines with `intent(in)`, `intent(out)`,
  `intent(inout)`, omitted `intent`, `value`, optional, and descriptor dummies.
- [ ] Cover scalar, array, string, derived, allocatable, pointer, and callback
  families wherever their behavior differs.
- [ ] Cover positional/keyword calls, skipped optional positions, omission,
  explicit `None`, and concrete presence.
- [ ] Preserve absent, present-empty, and present-with-value states for optional
  allocatables and pointers.
- [ ] Cover hidden outputs, caller storage, replacement returns, direct results,
  multiple outputs, and tuple ordering.
- [ ] Cover every documented projection mechanism: `Arg`, `Addr(Arg)`,
  `Value(Arg)`, descriptor `Arg`, `Return`, descriptor `Return`, `Pass`, typed
  literals, `Len`, shape, `IsPresent`, and `Work`.
- [ ] Cover reordering, hiding, insertion, invalid duplication/missing
  positions, and out-of-range diagnostics.

### Derived types and storage/lifetime

- [ ] Preserve the complete scalar-derived actual/dummy matrix where cells
  differ by module origin, storage, dummy form, support, or diagnostic.
- [ ] Cover constructors, failed-construction cleanup, methods, state,
  destruction/finalization, type identity, and supported boundaries.
- [ ] Separate core compatibility, empty descriptor states, reassociation,
  writeback, rollback, and error propagation while reusing compiled fixtures.
- [ ] Cover allocatable and pointer empty/present states, aliasing, ownership,
  replacement, mutation, release, and lifetime.
- [ ] Cover module-owned, borrowed, transferred, and Python-owned paths when
  documented policy differs.

### Remaining guide features

- [ ] Modules: namespaces, variables, constants, imports, initialization, and
  module procedure identity.
- [ ] Optional arguments: every documented call state and presence projection.
- [ ] Generics: overload selection, ambiguity, operators, assignments, and
  native-specific routing.
- [ ] Callbacks: every distinct scalar, array, derived, lifetime, exception, and
  GIL ABI mechanism.
- [ ] Enumerations: supported values, conversion, results, and diagnostics.
- [ ] Raw addresses: primitive, array, and fixed-string boundaries with owners
  kept alive and unsafe cases isolated.
- [ ] Error handling: native status translation, exception type/message, and
  cleanup on failure.
- [ ] Multiple sources/building: module order, external bundles, objects,
  libraries, shared-library paths, and CLI behavior.

### Edited `.pyi`

- [ ] Exports/modules: namespaces, flattening, selective/repeated exports,
  aliases, hiding/removal, collisions, native identity, placement, initializers,
  and true constants.
- [ ] Functions/classes: module procedure as method, `Pass`, `@bind`,
  overload edits, private-specific routing, constructors, type-bound methods,
  generics, operators, and assignment.
- [ ] Calls/results: identity/native order, reordering, hiding/insertion,
  projections, replacement mutation, `Immutable`, optionality, dtype, shape,
  layout, `@raises`, and `@hold_gil`.
- [ ] Raw-address edits keep native owners alive.
- [ ] Contract imports cover control names, arbitrary aliases, generated alias
  collision safety, and missing-import diagnostics.
- [ ] Every rejected form fails at the documented loader, validation, policy,
  build, import, or runtime stage.
- [ ] No edited-contract test uses native-source fallback.

## 6. Parser corpora and real-library end-to-end tests

### SciFortran

SciFortran is parser evidence only. It is not compilation, wrapper, runtime,
end-to-end, or smoke evidence.

- [ ] Inventory every file by parser constructs/interactions and current
  outcome.
- [ ] Recover issue, commit, failure, or maintainer provenance for known parser
  regressions.
- [ ] Give each file one disposition: retain, reduce, replace with a minimal
  reproducer, or delete as redundant.
- [ ] Do not infer redundancy from filename, similar syntax, or equal line
  coverage.
- [ ] Compare focused parser coverage with and without SciFortran to find unique
  branches. This is a targeted corpus check, not the complete coverage workflow.
- [ ] Preserve a normalized parser-model or focused invariant; “does not crash”
  is insufficient.
- [ ] Preserve licensing and attribution for retained upstream content.
- [ ] Keep a full source only when the regression depends on interactions that
  cannot be minimized confidently.
- [ ] Move retained content to
  `tests/fortran/corpus/parsing/{regressions,real_world}/`.
- [ ] Delete each old SciFortran source/expectation as soon as its final parser
  owner is verified and it has no remaining consumer.
- [ ] Remove SciFortran-specific enumerators and path rewrites when the last
  retained consumer no longer needs them.
- [ ] Never list a SciFortran case as end-to-end or smoke evidence.

### BLAS and LAPACK

- [ ] Move the real-library projects to
  `tests/fortran/features/building_shared_library/end_to_end/real_libraries/{blas,lapack}/`.
- [ ] Treat them only as full-pipeline evidence: build from the library sources,
  generate wrappers, compile/link, import the extension, and verify the public
  Python surface and representative runtime calls.
- [ ] Use the native-source build route only. Keep no BLAS/LAPACK generated
  `.pyi` golden, checked `.pyi` input fixture, edited `.pyi` variant, or
  source-free `.pyi` replay.
- [ ] If source wrapping creates an intermediate `.pyi` internally, keep it in
  the temporary build directory and do not treat it as BLAS/LAPACK contract
  evidence.
- [ ] Test ordinary and edited `.pyi` behavior with small dedicated fixtures
  under `features/semantic_pyi_format/{pipeline,end_to_end}/` and
  `features/pyi_contracts/<edit-family>/end_to_end/`.
- [ ] Do not list BLAS or LAPACK as parser, semantic, policy, ordinary
  feature-conformance, or smoke evidence. Parsing occurs inside their journey
  but does not make them parser-owned tests.
- [ ] Keep small conformance cases with their ordinary end-to-end feature;
  BLAS/LAPACK own library-scale integration only.
- [ ] Do not count thousands of parsed procedures as thousands of independent
  feature contracts.
- [ ] Run BLAS/LAPACK end-to-end work in one dedicated scheduled or explicitly
  requested lane.
- [ ] Do not run LAPACK locally unless explicitly requested.

### Real-source gate

- [ ] Every old corpus artifact has a reviewed final disposition.
- [ ] Every known SciFortran-discovered parser regression remains named.
- [ ] Unique parser line/branch and interaction evidence is preserved.
- [ ] Every retained upstream artifact has attribution and a unique purpose.
- [ ] No parser corpus or BLAS/LAPACK real-library test appears in toolchain
  smoke.

## 7. Complete the test migration

Run this gate after all documentation features and corpora have migrated, and
before changing compiler product behavior.

- [ ] Every ordinary legacy pytest node is retired.
- [ ] Every legacy source, include, JSON, and `.pyi` artifact is migrated,
  replaced, or deleted.
- [ ] No old fixture root remains authoritative.
- [ ] Retained SciFortran, BLAS, LAPACK, regression, or contract content exists
  only beneath its final owner.
- [ ] Every permanent contract row resolves to final collected nodes.
- [ ] Collect `tests/fortran/`, `tests/c/`, and `tests/shared/` independently;
  run the local Fortran verification with `-m "not real_library"`.
- [ ] Run the new suites alone under the same CI-equivalent line-and-branch
  coverage procedure used for the baseline.
- [ ] Require every baseline-executed line and branch to remain executed per
  Python file. A higher aggregate percentage cannot hide a lost baseline line.
- [ ] Compare feature/diagnostic and corpus evidence separately from Python
  coverage.
- [ ] Investigate every regression before accepting a deliberate exception.
- [ ] Remove temporary migration inventories.
- [ ] Update workflow, documentation, generator, cache, and focused-test paths.
- [ ] Run repository-wide collection, final focused/ordinary-full tests, and
  required static analysis; leave `real_library` execution to its designated
  lane.

## 8. Select one portable toolchain smoke suite

Smoke is a marked selection from the completed Fortran end-to-end suite. It is
not a separate directory, copied implementation, parser selection, or compiler
profile suite.

Register one additional strict subset marker:

```toml
"toolchain_smoke: portable compiled Fortran end-to-end cases reused across compiler, OS, and architecture lanes"
```

Mark exact tests or parameter rows:

```python
pytest.param(
    "representative_case",
    ...,
    marks=pytest.mark.toolchain_smoke(
        mechanism="derived_type_lifecycle",
        build_fixture="compiled_derived_types",
    ),
)
```

Rules:

- [ ] Every marked node is below an `end_to_end/` directory under
  `tests/fortran/features/`.
- [ ] Every `toolchain_smoke` node also carries `fortran_end_to_end`.
- [ ] Marker metadata names a distinct mechanism and the compiled fixture it
  reuses.
- [ ] The named fixture appears in the item's fixture closure.
- [ ] Select exact rows from large matrices; do not mark whole matrices unless
  every row is intentionally smoke.
- [ ] Target six to eight distinct compiled fixtures.
- [ ] Cover scalar/module procedure plus NumPy array, string behavior, derived
  lifecycle, allocatable/pointer ownership, callback, generic/overload, and
  source → generated `.pyi` → rebuilt extension.
- [ ] Prefer a multiple-source or CLI build within those fixtures when it adds
  no redundant extension build.
- [ ] Verify values, state, mutation, and lifetime—not compilation alone.
- [ ] Use exactly the same marked nodes on Linux, macOS, x86-64, ARM64, and
  every compiler family.
- [ ] Add no compiler-family or OS marker to smoke nodes.
- [ ] Permit no compiler/platform conditional skip or xfail in strict smoke.
- [ ] Include no corpus, BLAS/LAPACK, or parsing-only test.
- [ ] Map every smoke node to the permanent contract ledger.

### Smoke enforcement

`tests/fortran/conftest.py`:

- [ ] rejects a smoke marker outside end-to-end;
- [ ] enforces the exact relationship between `fortran_end_to_end` paths and
  marker membership;
- [ ] enforces that `real_library` identifies only BLAS/LAPACK and can never
  overlap `toolchain_smoke`;
- [ ] validates `mechanism` and `build_fixture`;
- [ ] rejects `skip`, `skipif`, `xfail`, compiler, and OS marks;
- [ ] provides `--require-toolchain-smoke`;
- [ ] fails strict smoke if no node collects, a requested compiler is missing,
  or any setup/call/teardown report skips or xfails; and
- [ ] emits a deterministic collection report.

`tests/fortran/architecture/test_smoke_selection.py`:

- [ ] validates marker registration and exact collected nodes;
- [ ] validates contract-ledger membership;
- [ ] validates the six-to-eight-build budget;
- [ ] rejects corpus, BLAS/LAPACK real-library, profile, and platform paths; and
- [ ] confirms marked nodes are part of the ordinary unfiltered end-to-end
  suite.

The current runtime helper hardcodes GFortran. Before alternate-compiler smoke:

- [ ] add a session-level option such as
  `--x2py-fortran-compiler=<executable>`;
- [ ] resolve and log the requested executable and version once;
- [ ] propagate its profile through preprocessing, probes, native compilation,
  bridge compilation, linking, and runtime discovery; and
- [ ] fail rather than silently substituting GFortran.

## 9. Add compiler profiles and macOS

Document each supported family and limitation before changing product code.
Compiler support means preprocessing, probing, native and generated-source
compilation, linking, loading, and the same runtime smoke all succeed.

### Compiler profiles

- [ ] Inventory GNU-specific flags, diagnostics, module assumptions, symbols,
  runtime libraries, and link options.
- [ ] Keep family selection in compilation/build integration, not scattered
  compiler-name branches.
- [ ] Implement GNU, Intel ifx, LLVM Flang, and NVIDIA nvfortran one profile at
  a time.
- [ ] Add focused command/capability tests under
  `tests/fortran/infrastructure/compiling/profiles/`.
- [ ] Carry compiler-derived target facts through semantics and the shared plan;
  bridge/binding generators do not infer semantic policy from compiler family.
- [ ] Give unknown and unsupported compilers explicit diagnostics.
- [ ] Add runtime smoke only after the profile tests pass.
- [ ] Document version floors and limitations from evidence.

### macOS

- [ ] Audit extension suffixes, shared-library flags, undefined-symbol
  handling, install names, runtime paths, temporary paths, and discovery.
- [ ] Keep platform mechanics in compilation/build integration.
- [ ] Add focused command/path tests under
  `tests/fortran/infrastructure/compiling/platforms/`.
- [ ] Run the unchanged smoke selection on Apple Silicon.
- [ ] Reserve Intel macOS for release validation unless current evidence
  justifies a more frequent lane.
- [ ] Log runner image, architecture, Python, compiler path, and version.

### Toolchain lane contract

Focused CLI, profile, and platform tests are not marked `toolchain_smoke`.
Use one repository-owned lane runner with a dry-run plan. Each noncanonical
compiler/platform lane performs the equivalent of:

```text
python -m pytest -q <profile/platform nodes> <focused Fortran CLI nodes>
python -m pytest -q tests/fortran/features -m toolchain_smoke \
  --x2py-fortran-compiler=<executable> --require-toolchain-smoke
```

`tests/fortran/architecture/test_ci_toolchain_lanes.py` verifies:

- [ ] every compiler lane includes its profile tests;
- [ ] every macOS lane includes macOS platform tests;
- [ ] every compiler/platform lane includes the designated Fortran CLI nodes;
- [ ] every referenced node collects;
- [ ] every lane invokes strict end-to-end smoke with the requested compiler;
  and
- [ ] each explicit GitHub Actions entry delegates to the common runner.

## 10. Replace the CI Cartesian product with evidence lanes

Verify the declared Python floor and tested ceiling immediately before editing
CI. Use explicit `matrix.include` records only.

### Pull-request lanes

- [ ] Canonical Linux x86-64, middle Python, GFortran: all non-corpus Fortran
  stage tests, ordinary non-real-library Fortran end-to-end, the mechanically
  preserved C suite, shared tests, and canonical coverage.
- [ ] Oldest Python, Linux x86-64, GFortran: install/import, selected
  Python-facing stage tests, and toolchain smoke.
- [ ] Newest Python, Linux x86-64, GFortran: the same compatibility selection.
- [ ] macOS ARM64, middle Python, GFortran: macOS platform tests, focused CLI,
  and toolchain smoke.
- [ ] Linux x86-64, middle Python, Intel ifx: profile tests, focused CLI, and
  toolchain smoke when installation cost/licensing is acceptable; otherwise
  schedule it and document that cadence.

### Scheduled lanes

- [ ] Linux x86-64, middle Python, LLVM Flang: profile tests, focused CLI, and
  smoke.
- [ ] Linux x86-64, middle Python, NVIDIA nvfortran: profile tests, focused CLI,
  and smoke.
- [ ] Linux ARM64, middle Python, GFortran: architecture tests, focused CLI, and
  smoke.
- [ ] Linux x86-64, middle Python, GFortran with ASan/UBSan: compatible runtime
  selection and memory-safety checks.
- [ ] Full BLAS/LAPACK end-to-end library cases: one dedicated scheduled or
  requested lane.

### Release lane

- [ ] macOS Intel x86-64, middle Python, GFortran: extended smoke while
  supported.
- [ ] Run release-only packaging/corpus checks once on their canonical
  compiler.

### CI rules

- [ ] Keep static analysis and docs independent of compiler families.
- [ ] Keep Python coverage on the canonical job only.
- [ ] Cache only reproducible compiler packages or corpus artifacts with
  OS/architecture/compiler/version/fixture-aware keys.
- [ ] Report test time and compiler installation time.
- [ ] Verify runner labels, architectures, distribution terms, URLs, and
  package availability before enabling each lane.
- [ ] Make scheduled/release workflows manually dispatchable.
- [ ] State the exact cadence behind every support claim.
- [ ] Measure CI cost and feedback time before and after.

## 11. Implementation batches

1. [ ] Final structure documentation and positive architecture guards.
2. [ ] Baseline collection, artifact inventory, native-build counts, and
   line/branch coverage artifact.
3. [ ] Mechanical C quarantine.
4. [ ] Fortran features in User Guide order, completing the fast structural
   adoption pass and then the contract-completion pass for each feature,
   including stage, end-to-end, negative, pytest-node, and last-consumer fixture
   cleanup.
5. [ ] SciFortran and real-library corpus curation.
6. [ ] Final new-suite-only coverage comparison and legacy-root removal.
7. [ ] Toolchain smoke selection and structural enforcement.
8. [ ] GNU profile generalization and macOS.
9. [ ] Intel, LLVM, and NVIDIA profiles one at a time.
10. [ ] Explicit CI evidence lanes and support documentation.

For every implementation change:

- update relevant public/maintainer docs first;
- state which pipeline stages changed;
- name reused or changed implementation paths;
- identify added, updated, moved, and deleted tests and fixtures;
- run focused verification and required static analysis;
- do not run complete coverage except at the planned baseline/final checkpoints
  or when explicitly investigating a regression; and
- do not run LAPACK locally unless explicitly requested.

## 12. SOL xhigh implementation estimate

This estimates one uninterrupted SOL agent at xhigh reasoning effort, using
focused local verification and the fast-adoption sequence above. It is active
agent working time, not human review time. It assumes the existing GNU build
works, documentation remains stable, and migration tests do not expose major
product defects.

| Deliverable | Estimated SOL xhigh active time |
| --- | ---: |
| Feature-first structure, navigation index, architecture guards, inventories, baseline, and C quarantine | 3-6 hours |
| Pass A for all Fortran features: adopt existing tests and fixtures in final paths | 8-14 hours |
| Pass B: documentation comparison, missing cases, deduplication, and native-build reuse | 8-20 hours |
| SciFortran curation, BLAS/LAPACK end-to-end relocation, final coverage comparison, and smoke selection | 4-8 hours |
| **Complete test-suite migration through smoke** | **23-48 hours** |
| Compiler-profile generalization, macOS, ifx, Flang, nvfortran, and CI lanes | **16-40 additional hours** |
| **Entire checklist** | **39-88 active hours** |

Best case, the new feature-first suite through smoke is adoptable in roughly
one to two continuous working days. A more realistic elapsed estimate is two
to four days because native compilation, static analysis, and final coverage
consume wall time. The entire checklist including vendor compilers and macOS is
roughly three to six elapsed days when hosted runners and compiler packages are
available.

The quickest safe milestone is the first table row: it makes the destination
authoritative and navigable in a few hours. Then each feature becomes final
independently; no later all-suite reshuffle is required.

Add time separately when:

- a documentation row exposes missing product behavior rather than missing
  tests;
- a source/`.pyi` fixture has dynamic consumers that static inventory cannot
  resolve;
- a compiler family needs a genuinely new build or ABI mechanism; or
- vendor installation, licensing, or hosted-runner availability blocks
  verification.

## 13. Final acceptance

- [ ] The authoritative tree is language-first and feature-first within
  Fortran.
- [ ] C is isolated without behavioral redesign.
- [ ] Every Fortran test and fixture has a final Fortran owner.
- [ ] Every maintained User Guide and `.pyi` feature page maps to one obvious
  feature directory and focused command.
- [ ] Every infrastructure exception is feature-neutral and documented.
- [ ] Shared tests are demonstrably language-neutral.
- [ ] No compatibility layer or old authoritative path remains.
- [ ] Every User Guide and semantic `.pyi` claim has exact evidence.
- [ ] Every old pytest node and artifact has a reviewed final disposition.
- [ ] Every SciFortran regression and non-minimizable parser interaction remains
  covered as parser evidence only.
- [ ] Every supported Fortran feature has end-to-end runtime proof.
- [ ] Scalar, array-rank, string, argument, derived/storage, and edited-`.pyi`
  matrices satisfy the documented contract.
- [ ] Every unsupported case stops at the correct stage with a deliberate
  error.
- [ ] Final per-file line and branch coverage contains all baseline-executed
  lines and branches or a reviewed exception.
- [ ] Native build count and suite duration are measured and not inflated by
  avoidable duplication.
- [ ] One six-to-eight-build end-to-end smoke selection is reused unchanged
  across supported toolchains.
- [ ] `fortran_end_to_end` selects all and only the end-to-end stage nested
  across feature directories.
- [ ] BLAS/LAPACK remain native-source end-to-end-only tests with no checked or
  edited `.pyi` fixtures.
- [ ] Compiler, OS, architecture, Python, and cadence claims match actual CI
  evidence.
- [ ] Full BLAS/LAPACK and sanitizer work use deliberate nonduplicated lanes.
- [ ] Repository-wide collection, focused/full tests, static analysis, and CI
  pass under repository policy.
