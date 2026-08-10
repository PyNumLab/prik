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

Last verified: 2026-07-30
Current work: implementation batches 1-7 and sections 1-8 are complete. GNU
profile generalization, macOS support, alternate compilers, and CI evidence
lanes remain later-roadmap work and are outside this migration.

```text
Test-suite migration through smoke (batches 1-7)
[███████] 7/7 batches

Fortran feature migration
[█████████████████████████] 25/25 features

Complete roadmap (batches 1-10)
[███████░░░] 7/10 batches
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
  architecture/
    fortran/
      test_ci_toolchain_lanes.py
      test_contract_coverage_map.py
      test_language_ownership.py
      test_smoke_selection.py
  fortran/
    README.md
    CONTRACT_COVERAGE.md
    conftest.py
    _support/
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
    source_parsing/
      parsing/
    source_preprocessing/
      preprocessing/
    command_line_interface/
      pipeline/
    semantic_ir/
      semantics/
    semantic_pyi_format/
    pyi_contracts/
      exports_and_modules/
      functions_and_classes/
      calls_and_results/
    infrastructure/
      policy/
      codegen/
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
tests/fortran/arrays/
  parsing/
  semantics/
  policy/
  codegen/
  pipeline/
  end_to_end/
    fixtures/
```

This is feature-first and stage-second. Do not create empty stage directories.
Internal cross-feature frameworks go under `infrastructure/`; user-visible
behavior and public cross-feature capabilities do not.

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

- [x] Normalize each documentation filename to the matching feature directory:
  `data-types.md` → `data_types/`,
  `optional-arguments.md` → `optional_arguments/`, and so on.
- [x] Map the three `.pyi` editing pages beneath `pyi_contracts/` and
  map `semantic-pyi-format.md` to `semantic_pyi_format/`.
- [x] Make `tests/fortran/README.md` a compact table from every feature-bearing
  page listed in the Feature order below to its directory and focused pytest
  command.
- [x] Keep all evidence for a feature beneath that feature whenever possible:
  parsing, semantics, policy, code generation, pipeline, diagnostics, fixtures,
  and end-to-end behavior.
- [x] Use the same stage names inside every feature:
  `parsing`, `probes`, `preprocessing`, `semantics`, `policy`,
  `codegen`, `compiling`, `pipeline`, `runtime`, and `end_to_end`.
  Create only the stages that own real evidence.
- [x] Put pytest modules below a stage directory rather than directly at the
  feature root, so path shape always answers both “which feature?” and “which
  stage?”.
- [x] Use `infrastructure/` only when a test has no honest public-capability
  owner. Public source parsing, preprocessing, command-line behavior, and
  semantic-IR conversion use their named feature owners; internal policy
  dispatch, compiler construction, and runtime-handle plumbing may remain
  infrastructure.
- [x] Give each infrastructure module an owner statement in
  `tests/fortran/README.md`; do not create `misc`, `general`, or catch-all
  feature directories.
- [x] Keep `_support/` limited to test utilities used by several features.
  It contains no pytest modules, native feature sources, or checked contracts;
  feature-specific support stays inside its feature.
- [x] Put an ordinary regression with its current feature and owning stage.
  Minimized cross-feature parser interactions live under
  `source_parsing/parsing/`; full third-party corpora are temporary audit
  inputs and are removed after their unique evidence is replaced.
- [x] During migration, make architecture checks reject an unknown feature
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

- [x] Give each test one primary invariant and one owning stage.
- [x] Put exhaustive syntax and policy combinations at the earliest stage that
  can prove them.
- [x] Add an end-to-end test only when generation, compilation, import, or
  runtime behavior contributes evidence.
- [x] Keep unsupported behavior at the first stage with enough information to
  reject it deliberately.
- [x] Preserve a downstream diagnostic test only when CLI/API propagation is
  itself public behavior.
- [x] Do not let bridge or binding tests accept semantic decisions inferred
  from datatype, `intent`, dotted shape, alias state, or local memory checks.
  Those decisions belong in completed post-IR policy.

### CLI ownership

- [x] Generic argument parsing and output formatting belong in
  `tests/shared/cli/`.
- [x] Cross-feature Fortran command contracts belong in
  `tests/fortran/command_line_interface/pipeline/`.
- [x] A CLI test that builds, imports, calls, and verifies a Fortran extension
  belongs in the owning feature's `end_to_end/` directory, normally
  `building_shared_library/end_to_end/`.
- [x] One end-to-end CLI case may be selected as toolchain smoke. Focused CLI
  contract tests are selected separately by the toolchain CI lane.

### Final layout gates

Register a structural marker for cross-feature selection:

```toml
"fortran_end_to_end: compiled, imported, and called Fortran feature tests"
"real_library: dedicated BLAS/LAPACK native-source end-to-end tests"
```

- [x] A focused `tests/fortran/` command collects no C-input test.
- [x] A focused `tests/c/` command collects no Fortran-input test.
- [x] Shared tests import no language-owned helpers.
- [x] Fortran and C tests import neither each other's helpers nor fixtures.
- [x] Feature-local fixtures live with their owner. Minimized parser
  regressions live under `source_parsing/parsing/`; BLAS and LAPACK live only
  under `examples/blas/` and `examples/lapack/`.
- [x] `python -m pytest tests/fortran/arrays` runs every stage of the
  Arrays contract without collecting unrelated features.
- [x] Every node below a feature's `end_to_end/` directory carries
  `fortran_end_to_end`, and no other node carries it.
- [x] BLAS/LAPACK nodes additionally carry `real_library`, and only those nodes
  carry it.
- [x] `python -m pytest tests/fortran -m "fortran_end_to_end and not real_library"`
  selects the ordinary feature-local end-to-end suite.
- [x] The dedicated real-library lane selects `real_library` separately.
- [x] Positive architecture checks enforce allowed owners. Do not add tests
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

- [x] Record gaps explicitly; one broad example does not cover every dtype,
  rank, state, or edit.
- [x] Give every supported user-visible behavior runtime evidence.
- [x] Give every documented unsafe or unsupported behavior terminal-stage
  diagnostic evidence.
- [x] Record source build, generated-`.pyi` replay, edited-`.pyi`, and
  source-free native-artifact evidence separately when the documentation claims
  each route.
- [x] Make architecture tests resolve documentation links and collected node
  IDs.
- [x] Reject deletion of the last evidence for a contract row.

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

- [x] Resolve every legacy and replacement pytest selector.
- [x] Reject overlapping migration selectors.
- [x] Report `legacy-only`, `dual-proof`, and `retired` node counts.
- [x] Resolve every artifact consumer and final owner.
- [x] Fail when a deleted pytest node remains listed as an artifact consumer.
- [x] Fail when an artifact marked `replacement-verified` has no remaining
  consumer but was not deleted in the current migration slice.
- [x] Remove the temporary migration inventories after final paths and the
  permanent contract ledger become authoritative.

## 3. Fixture ownership rules

Do not move `tests/data/fortran/` wholesale into another central data
directory. Audit and place every artifact beside its final behavioral owner.

### Migration map

| Current family | Final owner |
| --- | --- |
| `tests/data/fortran/wrapper/` | `tests/fortran/<feature>/end_to_end/fixtures/<case>/native/` |
| `tests/data/fortran/general/` | Owning feature/stage; feature-neutral setup is minimized beside its final public-capability owner |
| `tests/data/fortran/errors/` | Fixture directory of the first rejecting stage |
| `tests/data/fortran/blas/` and `lapack/` | `examples/blas/native/` and `examples/lapack/native/` |
| Parser regressions extracted from SciFortran | `tests/fortran/source_parsing/parsing/test_real_world_interaction_regressions.py` |
| Parser source/JSON pairs | Beside their parser owner |
| Language-neutral `.pyi` syntax | `tests/shared/contracts/` |
| Fortran `.pyi` build fixtures | `tests/fortran/semantic_pyi_format/{pipeline,end_to_end}/fixtures/` |
| Generated contract goldens | Beside their generation/package-shape owner |
| Edited contracts | `tests/fortran/pyi_contracts/<edit-family>/end_to_end/fixtures/` |
| Invalid `.pyi` contracts | Fixture directory of the first rejecting stage |

### Native sources

- [x] Reuse a clear, minimal old source when it already owns a distinct
  invariant.
- [x] Minimize or replace a source that mixes unrelated behavior or obscures
  the intended contract.
- [x] Create a coherent new source when documentation has no evidence or one
  compiled fixture can cover a matrix much more efficiently.
- [x] Keep parser-only sources with parsing and semantic/policy setup sources
  with their semantic owner.
- [x] Keep full-pipeline sources with their end-to-end feature.
- [x] Put multi-source projects, include files, and support files under a local
  `native/` directory.
- [x] Give a coherent multi-feature runtime project one primary final owner and
  map secondary features to its nodes. Do not copy it into several directories
  merely to make the tree symmetrical.
- [x] Compile one feature fixture once and share it across its runtime
  assertions when isolation permits.
- [x] Generate all objects, bridge/binding files, and extensions in pytest
  temporary directories. Build products are not checked fixtures.

### Parser sources and JSON

- [x] Keep a source and JSON together only when exact normalized parser
  serialization is the invariant.
- [x] Prefer focused Python assertions when only a few parser facts matter.
- [x] Never replace a meaningful parser assertion with “did not crash.”
- [x] Do not retain a whole JSON snapshot because an unrelated runtime test
  passes through parsing.
- [x] Generate expected JSON with one documented command and review it with the
  source.
- [x] Store ordinary expected diagnostics in Python assertions unless JSON is
  itself a documented public output format.
- [x] Delete each old JSON as soon as its final parser evidence exists and no
  recorded later consumer remains.

### Generated `.pyi` packages

- [x] Check in generated `.pyi` only when generation text, imports, native
  placement, or package shape is the invariant.
- [x] Keep one representative expected package at the pipeline/generation
  owner; do not copy it into every end-to-end feature.
- [x] Regenerate checked output only through an explicit update command and
  review the semantic diff.
- [x] Generate intermediate contracts in a temporary directory when a test
  immediately rebuilds them.
- [x] Compare temporary generated output with a golden only in the
  representative test that owns printer/package compatibility.

### Edited `.pyi` contracts

An edited contract is authoritative input, not expected generated output.

- [x] Store it under the user edit being tested.
- [x] Supply source, objects, or libraries as implementation only. Do not parse
  native source to restore declarations removed from the edited contract.
- [x] Assert the changed Python surface or behavior, not merely successful
  loading or compilation.
- [x] Generate a starter contract temporarily when before/after comparison is
  needed.
- [x] Keep checked starter and edited packages together only when their exact
  difference is the invariant.
- [x] Treat checked `.pyi` as read-only and make test-specific changes in
  temporary copies.
- [x] Place invalid syntax/import, semantic structure, policy, ABI, and runtime
  failures at their earliest respective owners.

### `.pyi` build responsibilities

| Owner | What it proves |
| --- | --- |
| `tests/fortran/semantic_pyi_format/pipeline/` | Loading, import graph, package assembly, build plan, and diagnostics |
| `tests/fortran/semantic_pyi_format/end_to_end/` | An ordinary contract is authoritative input and produces a working extension |
| `tests/fortran/pyi_contracts/<edit-family>/end_to_end/` | A documented edit changes the built API or runtime behavior |

The end-to-end baseline contains:

- [x] source → generated `.pyi` → rebuilt extension → runtime call;
- [x] `.pyi` plus prebuilt native artifacts and no native source, proving there
  is no parser fallback;
- [x] one imported multi-file contract package; and
- [x] each distinct documented native-artifact topology once.

Use one shared `.pyi` build helper. Keep one small unedited baseline for fault
localization; edited tests do not replace it. Do not run every feature through
source, generated-`.pyi`, and edited-`.pyi` modes.

## 4. Establish the structure and baseline

Do these steps before the first Fortran feature migration.

### Structure and guardrails

- [x] Update `tests/README.md` and the developer testing strategy with the
  language-first ownership contract.
- [x] Create only the first needed `tests/{fortran,c,shared}/` destinations.
- [x] Add positive language ownership and contract-ledger architecture checks.
- [x] Add temporary pytest-node and artifact-consumer migration inventories.
- [x] Identify helper and `conftest.py` consumers before moving shared support.
- [x] Update workflow, tooling, cache, and documentation paths in the same
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

| Observation | Recorded baseline |
| --- | ---: |
| Legacy pytest cases | 6,277 |
| Complete repository collection | 6,292, including 15 final-path migration checks |
| Executed coverage selection | 6,289; 6,276 passed and 13 skipped |
| Fortran parser cases | 2,879 |
| SciFortran parser cases | 324 |
| Fortran wrapper cases | 446 |
| Source/generated-`.pyi` parity cases | 110, representing 55 cases in each mode |
| Native wrapper source files | 58 |
| Copied SciFortran files | 303 |
| Native compiler invocations | 1,722 real invocations; 0 ordinary-suite cache hits |
| Combined line/branch coverage | 90.62% |

These are legacy collection observations, not final ownership claims. The
collection-only inventory includes the two full BLAS/LAPACK nodes; the
executed baseline excludes that module, so LAPACK did not run locally.
BLAS/LAPACK are classified only by their final native-source end-to-end owner.
`tests/_migration/baseline/README.md` records the exact accounting,
environment, compiler actions, and reproduction contract.

For the coverage baseline:

- [x] Mirror GitHub Actions, including its deterministic seed and test
  selection.
- [x] Set `COVERAGE_PROCESS_START=pyproject.toml`.
- [x] Combine subprocess data with `python3 -m coverage combine`.
- [x] Run `python3 -m coverage report`.
- [x] Save `coverage json` output with the source revision and environment.
- [x] Record executed lines and branches per Python source file, not only an
  aggregate percentage.

During migration:

- [x] Do not run the complete coverage workflow after every feature.
- [x] Run focused owner tests, collection/layout checks, and required static
  analysis.
- [x] Use focused coverage only to investigate a risky deletion or final
  regression.
- [x] Keep production Python unchanged until the test-migration coverage gate.
  If a new test exposes a product bug, fix it in a separate documented change
  and establish a comparable baseline before resuming.

Coverage is only one guard. Preserve three independent evidence kinds:

1. Python line and branch execution;
2. documented feature and diagnostic evidence; and
3. minimized real-source interaction evidence.

Equal line coverage cannot prove that the same parser interaction, lifetime
state, datatype matrix, or public error remains covered.

### Mechanical C quarantine

- [x] Move C parsing, probe, preprocessing, semantic, pipeline, CLI-dispatch,
  property, and C-specific `.pyi` tests beneath `tests/c/`.
- [x] Move their fixtures and helpers with their consumers.
- [x] Preserve assertions, parameters, markers, skips, and fixture contents.
- [x] Do not expand or redesign C coverage.
- [x] Run focused `tests/c/` collection and execution.

Verified 2026-07-29: `tests/c/` collects 498 nodes and executes as 497 passed
plus one intentionally parked benchmark. The migration ledger retires 511
baseline nodes, records 88 moved artifacts and one moved support module, and
resolves reviewed mixed-node splits to exact collected replacements.

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

- [x] Create the feature directory and only its currently needed stage
  directories.
- [x] Use one read-only inventory tool to collect old node IDs, markers,
  durations, static fixture path references, and current wrapper feature
  directories into the temporary ledgers. Do not hand-enumerate thousands of
  nodes.
- [x] Scaffold the feature's contract rows from documentation headings, then
  review and complete them manually; generated headings are navigation aids,
  not automatic coverage claims.
- [x] Seed the feature from the already clustered wrapper/end-to-end directory
  before searching stage tests, because that usually provides its source
  project and clearest public assertions.
- [x] Move clear existing tests with minimal assertion changes.
- [x] Copy or relocate their fixtures according to last-consumer ownership.
- [x] Update imports, workflow selectors, and ledger node IDs.
- [x] Run the old/new focused comparison only where a rewrite makes equivalence
  uncertain.
- [x] Retire replaced old pytest nodes and immediately delete unconsumed old
  artifacts.
- [x] Run collection and architecture guards before expensive native execution,
  so path and ownership mistakes fail quickly.

**Pass B — complete the documented contract**

- [x] Compare the adopted evidence with every documentation row for the feature.
- [x] Split mixed tests, merge duplicate invariants, improve names, and share
  native builds.
- [x] Add only the missing dtype, rank, state, edit, error, or runtime cases.
- [x] Finish the feature completion gate before starting the next feature.

This is faster than designing an ideal replacement suite from a blank page and
safer than mechanically moving the entire old tree before understanding it.
Automate inventory and path rewriting, but keep disposition and assertion
decisions reviewable. Do not run full coverage between features.

### Feature order

| Status | Documentation | Final feature directory |
| --- | --- | --- |
| [x] | [Data Types](../../user/guide/data-types.md) | `data_types/` |
| [x] | [Arrays](../../user/guide/arrays.md) | `arrays/` |
| [x] | [Strings](../../user/guide/strings.md) | `strings/` |
| [x] | [Wrapping Functions](../../user/guide/wrapping-functions.md) | `functions/` |
| [x] | [Wrapping Subroutines](../../user/guide/wrapping-subroutines.md) | `subroutines/` |
| [x] | [Wrapping Modules](../../user/guide/wrapping-modules.md) | `modules/` |
| [x] | [Optional Arguments](../../user/guide/optional-arguments.md) | `optional_arguments/` |
| [x] | [Generic Interfaces](../../user/guide/generic-interfaces.md) | `generic_interfaces/` |
| [x] | [Wrapping Derived Types](../../user/guide/wrapping-derived-types.md) | `derived_types/` |
| [x] | [Allocatables](../../user/guide/allocatables.md) | `allocatables/` |
| [x] | [Pointers](../../user/guide/pointers.md) | `pointers/` |
| [x] | [Memory Management](../../user/guide/memory-management.md) | `memory_management/` |
| [x] | [Callbacks](../../user/guide/callbacks.md) | `callbacks/` |
| [x] | [Enumerations](../../user/guide/enumerations.md) | `enumerations/` |
| [x] | [Raw Addresses](../../user/guide/raw-addresses.md) | `raw_addresses/` |
| [x] | [Error Handling](../../user/guide/error-handling.md) | `error_handling/` |
| [x] | [Building the Shared Library](../../user/guide/building-shared-library.md) | `building_shared_library/` |
| [x] | [Inspect a Fortran API](../../user/examples/recipes/inspect-fortran-api.md) | `source_parsing/` |
| [x] | [Compiler Preprocessing](../../user/examples/recipes/compiler-preprocessing.md) | `source_preprocessing/` |
| [x] | [CLI Commands](../../user/reference/cli-commands.md) | `command_line_interface/` |
| [x] | [Semantic IR](../../user/reference/semantic-ir.md) | `semantic_ir/` |
| [x] | [Semantic `.pyi` Format](../../user/reference/semantic-pyi-format.md) | `semantic_pyi_format/` |
| [x] | [Exports and Modules](../../user/reference/pyi-contracts/exports-and-modules.md) | `pyi_contracts/exports_and_modules/` |
| [x] | [Functions and Classes](../../user/reference/pyi-contracts/functions-and-classes.md) | `pyi_contracts/functions_and_classes/` |
| [x] | [Calls and Results](../../user/reference/pyi-contracts/calls-and-results.md) | `pyi_contracts/calls_and_results/` |

### Repeat this loop for every feature

1. [x] Read the documentation page and relevant semantic `.pyi` sections.
2. [x] Add every supported form, limitation, error, state transition, and edit
   to `CONTRACT_COVERAGE.md`.
3. [x] Find all old pytest nodes and every source, JSON, `.pyi`, helper, and
   generator that contributes evidence for the feature.
4. [x] Record all consumers before moving or deleting an artifact.
5. [x] Classify each invariant at its cheapest stage.
6. [x] Create final parsing evidence where syntax or parser-model behavior is
   distinct.
7. [x] Create final probe/preprocessing evidence where compiler-derived facts
   or source processing is distinct.
8. [x] Create final semantic-conversion and completed-policy evidence for every
   distinct semantic decision.
9. [x] Create final wrapper-plan/code-generation evidence for every distinct
   selected emitted-code mechanism.
10. [x] Create final compile/pipeline evidence for distinct commands, artifact
    topologies, and build transitions.
11. [x] Create one or more end-to-end journeys for supported public behavior
    that crosses build/import/runtime boundaries.
12. [x] Put each unsupported case at its first decisive stage and verify the
    stable diagnostic.
13. [x] Reuse, minimize, or replace old fixtures according to the artifact
    ledger. Never make a new test fall back to an old fixture path.
14. [x] Run old and new focused evidence together when equivalence needs proof.
15. [x] Update permanent and temporary ledgers with exact new node IDs.
16. [x] Delete each superseded old pytest node once all of its useful
    assertions and secondary features have replacements.
17. [x] Delete each old source, JSON, or `.pyi` immediately when its last
    recorded consumer, feature, and stage have migrated.
18. [x] Run the final focused new feature tests, collection/layout guards, and
    required static analysis.

### Feature completion gate

- [x] Every documentation row for the feature has stage, runtime, or negative
  evidence as required.
- [x] The new feature tests do not import old tests, helpers, or fixtures.
- [x] No superseded pytest node remains.
- [x] Every retained old artifact names a real remaining consumer and next
  feature/stage.
- [x] No unconsumed old artifact remains.
- [x] Native build count is measured and shared fixtures are reused.
- [x] Test names and assertions identify the feature without historical phase
  numbers.

### End-to-end success definition

Every successful end-to-end case must:

- [x] start from user-owned Fortran source or an intentional source-free
  semantic `.pyi`;
- [x] use the public API or CLI route being claimed;
- [x] pass through completed semantics and wrapper planning;
- [x] generate bridge and binding code;
- [x] compile and link a Python extension;
- [x] import from an isolated temporary build location; and
- [x] call the public Python surface and verify values, mutation, lifetime,
  state, identity, exceptions, or another visible result.

Artifact existence, emitted text, compiler success, or import without a public
call is not sufficient.

### General matrix rules

- [x] Preserve combinations whose legality, ABI, storage, ownership, lifetime,
  mutation, projection, or diagnostic differs.
- [x] Put the complete theoretical policy matrix at policy/plan level when it
  does not require compilation.
- [x] Keep all runtime matrix cells when they cheaply reuse one coherent
  extension and perform different public checks.
- [x] Do not multiply independent dimensions when they select the same policy
  and runtime mechanism.
- [x] Use a full cross-product when dimensions interact.
- [x] Add a special case for each distinct mechanism, boundary, prior
  regression, and deliberately unsupported combination.
- [x] Compile one extension per coherent feature fixture, not one extension per
  assertion.

### Data Types

- [x] Cover `Bool`, `Int8`, `Int16`, `Int32`, `Int64`, `Float32`, `Float64`,
  `Complex64`, and `Complex128` wherever documentation supports them.
- [x] Cover scalar input, function result, hidden `intent(out)`, visible
  `intent(inout)`, rank-zero storage, and native value/reference passing.
- [x] Verify exact NumPy scalar acceptance and documented rejection of wrong
  Python/NumPy value types.
- [x] Use zero, signed, boundary, logical, real, imaginary, complex, and
  round-trip values appropriate to each dtype.
- [x] Cover module-variable getters/setters and constants once per distinct
  accessor mechanism.
- [x] Cover documented construction defaults.
- [x] Reject unsupported wider/unmapped kinds explicitly rather than narrowing.
- [x] Keep compiler-kind probing exhaustive at probe/semantic level; smoke uses
  representatives unless compiler mappings differ.

Data Types completion record (2026-07-29): 61 final feature nodes passed before
the final focused fixture additions; the two affected end-to-end nodes were
then rerun directly. The feature uses three extension builds across two
coherent fixtures: source build, generated-`.pyi` replay, and rank-zero/module
storage. Exact contract rows resolve through `CONTRACT_COVERAGE.md`; 83 legacy
nodes were retired after the final primitive-kind duplicate was removed.

### Arrays

- [x] Compile, import, call, and verify every supported primitive element dtype
  at every supported concrete rank 1-15.
- [x] Generate the dtype/rank procedures in one or a few coherent fixtures.
- [x] Verify values, shape, and mutation for every matrix cell.
- [x] Cover rank-zero storage and assumed rank separately.
- [x] Cover `Flat`, fixed/open extents, visible shape expressions, lower bounds,
  assumed shape/size, and zero-sized arrays.
- [x] Cover Fortran order, `ORDER_C`, `COPY_F`, dense arrays, and documented
  positive-stride views.
- [x] Cover inputs, caller storage outputs, in-place writeback, no-`intent`
  mutation, array results, immutable replacement, and optional presence.
- [x] Verify dtype, rank, shape, contiguity, order, alignment, byte order,
  writeability, strides, broadcasting, reversal, and zero-size validation.

Arrays completion record (2026-07-29): 63 final feature nodes pass. The
end-to-end slice uses 11 extension builds across seven coherent subjects after
module-scoped source/generated-`.pyi` parity sharing replaced 17 redundant
multidimensional and assumed-rank builds. One generated source covers all 135
primitive dtype/rank cells; each cell verifies exact dtype, shape, Fortran
layout, and mutation. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 67 additional baseline nodes were retired and 16 old
artifacts received final dispositions. The two allocatable-result cases split
from the old mixed array-result module remain recorded for the later
Allocatables feature.

### Strings

- [x] Cover runtime-length scalar `String`.
- [x] Cover fixed-width scalar input, result, replacement, and discarded
  mutation.
- [x] Cover mutable rank-zero fixed-width storage.
- [x] Cover fixed-width NumPy byte arrays for every documented rank and mode.
- [x] Include length 1, a representative width, and every width boundary that
  changes lowering or ABI behavior.
- [x] Verify bytes, blank preservation, `S<n>` itemsize, embedded NUL behavior,
  empty values, and mutation.
- [x] Reject Unicode/object arrays, wrong itemsize/rank/shape, read-only output
  storage, and unsupported deferred-length mutation.
- [x] Keep fixed-string raw-address evidence separate and record its exact
  retained node for the later Raw Addresses feature.

Strings completion record (2026-07-29): 57 final feature nodes pass using nine
extension builds. The documented edited-`.pyi` journey distinguishes immutable
values, rank-zero mutable storage, rank-one fixed-width arrays, and fixed-width
array results while exercising dtype, rank, itemsize, writeability, NUL,
Unicode/object, trailing-blank, and empty-value behavior. Consolidation folded
six redundant reduced-contract builds into the two source/generated-`.pyi`
parity subjects without losing their allocation-failure branches. Exact
documentation rows resolve through `CONTRACT_COVERAGE.md`; 64 additional
baseline nodes were retired and 13 old artifacts received final dispositions.
Deferred character handles and raw string addresses remain as exact recorded
consumers for their dedicated later features.

Wrapping Functions completion record (updated 2026-07-30): nine final feature
nodes pass using one extension build. The source journey covers direct scalar and
array results, direct-result-first tuple projection, caller-owned array
mutation, and conservative no-`intent` scalar replacement. A second edited
`.pyi` build is no longer duplicated here: standalone external `@bind`
renaming now reuses the final Exports and Modules package-export journey
without changing the native ABI. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; ten additional baseline nodes were retired and the
superseded handwritten rename contract was deleted.

Wrapping Subroutines completion record (2026-07-29): eleven final feature
nodes pass using one extension build. The documented source journey covers
hidden scalar tuples, scalar replacement, caller-owned array output/inout,
visible derived-object mutation, hidden allocatable creation, conservative
no-`intent`, exact dtype rejection, and writeability rejection. Policy,
semantic, and lowering evidence keeps each projection decision at its cheapest
stage. Exact documentation rows resolve through `CONTRACT_COVERAGE.md`; ten
additional baseline nodes were retired without introducing a new checked
contract fixture.

Wrapping Modules completion record (updated 2026-07-30): 22 final feature
nodes pass using five extension builds. Source/generated-contract parity covers public
variables, true constants, common-block hiding, saved and shared native state,
and one allocatable module-array lifecycle. Editable contract initialization,
visibility, namespace shaping, aliases, root externals, and collision
diagnostics now belong to the final Exports and Modules feature and reuse the
reviewed Modules native sources and generated base contracts. Exact
documentation rows resolve through
`CONTRACT_COVERAGE.md`; 38 additional baseline nodes were retired. The old
`fmodule_vars_f90` source and parser golden remain recorded because Derived
Types and package-build tests are still real consumers.

Optional Arguments completion record (2026-07-29): 30 final feature nodes pass
using five extension builds. One source/generated-contract parity subject
covers omission, explicit `None`, concrete positional and keyword values,
skipped positions, scalar, array, string, derived inputs, ordinary outputs,
and exact runtime validation. Three compact `.pyi` subjects cover scalar
allocatable/pointer three-state semantics, array descriptor-handle state, and
edited ordinary-array output identity. Fixed-form syntax remains at parsing,
contract-generation, and lowering stages without redundant runtime builds.
Exact documentation rows resolve through `CONTRACT_COVERAGE.md`; 29
additional baseline nodes and seven old artifacts received final
dispositions.

Generic Interfaces completion record (updated 2026-07-30): 30 final feature
nodes pass using four extension builds. Source/generated-contract parity covers exact scalar, array-rank,
generated-class, type-bound, operator, and assignment dispatch. Edited
contract addition, renaming, and native-private routing now belong to the
final Functions and Classes feature. Fixed form remains at parsing and
contract-generation stages without a redundant runtime build. Exact-match
planning, ambiguity, missing or
duplicate links, generic-constructor rejection, `class(*)`, and derived-array
limitations fail at their earliest decisive stages. Exact documentation rows
resolve through `CONTRACT_COVERAGE.md`; 30 additional baseline nodes and 12 old
artifacts received final dispositions.

Wrapping Derived Types completion record (updated 2026-07-30): 231 final
feature nodes pass. The slice uses 23 extension builds, measured as 23 native-extension link
actions, across source/generated-contract parity, edited contracts, and compact
runtime-mechanism subjects. One shared extension preserves the complete
60-cell scalar actual/dummy matrix plus empty-state, reassociation, rollback,
failure, type-identity, and lifetime paths. Separate focused subjects cover
scalar boundaries, default construction, finalization, borrowed and
module-owned objects, source-generated methods and generics, inheritance, and
opaque `bind(C)`/`sequence` accessors. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 253 additional baseline nodes and 48 old artifacts
received final dispositions. Editable methods, constructors, overloads, and
surface removal now belong to Functions and Classes; the remaining
pointer-field planning node stays recorded for Pointers.

Allocatables completion record (2026-07-30): 61 final feature nodes collect;
58 pass locally and three skip for the recorded compiler limitation and
unavailable Valgrind ownership checks. The successful runtime slice performs
11 native-extension link actions across seven coherent subjects. Shared
source/generated-contract builds cover module and field borrowing, owned and
maybe-unallocated results, scalar nullable values, caller-created descriptors,
same-handle replacement, live views, explicit release, and cross-extension
ABI. Focused semantic, policy, runtime, pipeline, and lowering nodes cover the
remaining descriptor states and deliberate blockers without compilation.
Exact documentation rows resolve through `CONTRACT_COVERAGE.md`; 53 additional
baseline nodes and ten old artifacts received final dispositions. Mixed
pointer operations, scalar pointer/allocatable module values, raw-address
rejection, and callback descriptor blockers remain recorded for their later
feature owners.

Pointers completion record (2026-07-30): 102 final feature nodes pass. The
runtime slice performs 11 native-extension link actions across eight coherent
source and generated-contract subjects. Shared native-array handle paths cover
associated and unassociated state, borrowed contiguous and strided views,
association and nullification, caller-created descriptors, cross-extension
handoff, scalar nullable projection, and pointer-array results whose wrappers
own descriptor storage without owning targets. Focused parsing, semantic,
policy, runtime ABI, pipeline, and lowering evidence covers the remaining
descriptor decisions and deliberate lifetime blockers without compilation.
Exact documentation rows resolve through `CONTRACT_COVERAGE.md`; 104
additional baseline nodes and six old artifacts received final dispositions.
The stale pointer-array-result blocker in the wrapper reference and feature
matrix was corrected. Raw `Addr(...)`, callback-pointer, and semantic-printer
nodes remain exact recorded consumers for their later feature owners.

Memory Management completion record (2026-07-30): 57 final feature nodes pass.
One edited-`.pyi` end-to-end journey performs the feature's single native
extension link action and proves that a borrowed child retains its wrapper
owner and finalizes exactly once. Semantic and completed-policy evidence covers
immutable borrowed-view contradictions and fail-closed owner/transfer/release
triples. Shared runtime and wrapper-planning paths cover public handle objects,
array handoff validation, persistent owner dispatch, live views, owned and
borrowed close behavior, finalization, construction rollback, descriptor
operations, and centralized plan validation without extra compilation. The
missing derived-object/native-dummy guide contract was restored and the last
stale pointer-target ownership wording was corrected. Exact documentation rows
resolve through `CONTRACT_COVERAGE.md`; 57 additional baseline nodes and four
old contract artifacts received final dispositions, and the shared native
handle test support moved to its final Fortran owner.

Callbacks completion record (2026-07-30): 41 final feature nodes pass. The
runtime slice performs six native-extension link actions across three coherent
source/generated-contract subjects. The combined shape subject covers
primitive values, scalar and array reference storage, fixed strings, and
derived objects; focused scalar and array subjects cover nested same-thread
entry, GIL acquisition, reference cleanup, fatal callback failures, writable
views, shaped results, and output identity. Parsing, semantic, completed-policy,
contract-generation, and wrapper-plan evidence covers named prototypes, exact
value/reference ABI, imported identity, shape dependencies, centralized
validation, and deliberate descriptor/optional blockers without more native
builds. The unsupported-feature matrix link was corrected to the maintained
limitations heading. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 49 additional baseline nodes and 15 old artifacts
received final dispositions.

Enumerations completion record (2026-07-30): 13 final feature nodes pass. The
source/generated-contract runtime pair performs two native-extension link
actions and proves exact `np.int32` module constants, ordinary integer
procedure and field values, non-enumerator integer acceptance, and the absence
of generated Python enum classes. Focused parsing, semantic conversion,
compile-time resolution, semantic-`.pyi` round-trip, reviewed-contract, and
diagnostic evidence covers explicit, implicit, negative, and symbolic values,
`Final[...]` emission, malformed enum units, and the deliberate Python
`Enum`/`IntEnum` blocker without additional native builds. Fortran enum
contracts that were accidentally hidden behind C-only documentation markers
are public again, and the guide now distinguishes native constant stability
from rebinding a local imported name. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 18 additional baseline nodes and four old artifacts
received final dispositions.

Raw Addresses completion record (2026-07-30): 54 final feature nodes pass. The
runtime slice performs two native-extension link actions: one edited-contract
build shares primitive scalar, numeric array, fixed-string scalar, and checked
string-storage assertions, while one focused build covers fixed-width string
array addresses. Focused semantic, completed-policy, invalid-contract, and
wrapper-plan evidence covers type-level `Addr(T)`, native `Addr(Arg(...))`
projection, primitive pointee validation, resolved array shapes and order,
fixed string lengths, integer extraction and overflow, and the deliberate
optional, projected-array, wrapped-pointee, unresolved-shape, and callable
blockers without more native builds. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 55 additional baseline nodes received final
dispositions. No old artifact became unconsumed in this feature; two checked
edited-contract packages were added beside the final runtime owners.

Error Handling completion record (2026-07-30): 23 final feature nodes pass.
The runtime slice performs one native-extension link action from a reviewed
edited semantic `.pyi`; it proves successful status consumption, exact native
message translation to `RuntimeError`, repeated failure cleanup, and a later
successful call. Focused parser and CLI diagnostics distinguish concise
compiler-style output from debug tracebacks, while semantic-policy and
wrapper-plan evidence covers `@raises`, optional message targets, hidden scalar
integer status and string message requirements, completed GIL/error facts,
named bridge/binding lowering, and cleanup ordering without more native builds.
The guide's incomplete `@raises` example now includes the required hidden
native-call projections. Exact documentation rows resolve through
`CONTRACT_COVERAGE.md`; 26 additional baseline nodes and five old artifacts
received final dispositions.

Building the Shared Library completion record (2026-07-30): 52 final feature
nodes collect. All 50 ordinary source, semantic-`.pyi`, Makefile, multi-source,
ABI, and mixed-native-bundle nodes pass locally, and the permitted full BLAS
node also passes; the full LAPACK node remains in its dedicated GitHub Actions
lane and was not run locally. The compiler-proxy audit recorded 600 real
invocations: 37 C binding compilations; 249 Fortran compilations; 53 Fortran
probe compile-and-link actions; 44 Fortran extension/library links; 196
preprocessing actions; 20 queries; and one version check. Final ownership now
covers direct source builds, source-free `.pyi` builds from explicit native
artifacts, structured ordered link plans, manifest/Makefile replay, caller-
ordered module and standalone-procedure builds, ABI compatibility, mixed
objects/archives/shared/named libraries, transitive providers, archive groups,
and full BLAS/LAPACK contracts. The guide, wrapper reference, semantic `.pyi`
native-artifact contract, and feature matrix resolve through
`CONTRACT_COVERAGE.md`; 59 additional baseline nodes and 2,250 old artifacts
received final dispositions, including the relocated real-library corpora and
eight superseded wrapper parser goldens.

Semantic `.pyi` Format completion record (2026-07-30): 138 final feature
nodes pass. The compiler-proxy audit records 16 real invocations: one C binding
compilation; two Fortran compilations; five Fortran probe compile-and-link
actions; one Fortran extension link; six preprocessing actions; and one query.
The one authoritative runtime node performs the feature's only native extension
link: it generates a reviewed multi-file contract package, rebuilds from that
package and a precompiled native object without source fallback, and calls both
a contained module procedure and a standalone external procedure.
Focused parser, semantic-conversion, printer-round-trip, and pipeline evidence
covers the Python-AST boundary, canonical types and metadata, imported type
identity, overloads, native-call projections, recursive import discovery and
cache reuse, stable diagnostics, and standalone, mixed, same-name,
multi-module, and transitive-import package layouts without more native builds.
Exact documentation rows resolve through `CONTRACT_COVERAGE.md`; 222 additional
baseline nodes, 55 old artifacts, and nine obsolete support paths received
final dispositions. The broad generated general-corpus goldens were replaced
by one reviewed package corpus owned by this feature, while native artifact and
link behavior remains with Building the Shared Library and editable behavioral
contracts remain with the three later semantic-`.pyi` features.

Exports and Modules completion record (2026-07-30): 11 final feature nodes
pass. The compiler-proxy audit records 15 real invocations: four C binding
compilations; six Fortran compilations; four Fortran extension links; and one
compiler query. Two native module objects are shared across four coherent
extension builds: one editable visibility/initializer surface plus child,
flattened, and aliased/bound package shapes. The successful package journey
also covers selective and repeated exports, nested facade placement, module
and standalone native identity, added and renamed bindings, support-import
hiding, and absence of unselected declarations; focused semantic, policy, and
lowering evidence covers literal initializer acceptance, expression rejection,
completed export pruning and setter policy, and exact emitted literal spelling.
The collision diagnostic remains at the package-planning boundary. Exact
documentation rows resolve through `CONTRACT_COVERAGE.md`; 30 baseline nodes
received final dispositions and four old contract artifacts were moved or
deleted. The runtime paths reuse the existing Modules native sources and
reviewed generated base contracts, while import-graph mechanics remain with
Semantic `.pyi` Format and class/member edits remain with the later contract
features.

Functions and Classes completion record (2026-07-30): 21 final feature nodes
pass. The compiler-proxy audit records 17 real invocations: four C binding
compilations; eight Fortran compilations; four Fortran extension links; and one
compiler query. Two reused native objects support six build attempts, including
two intentional compile-time accessibility failures. One edited overload
extension now covers added and renamed module bindings, exact method overloads,
and overloaded constructors; separate compact surfaces cover a module
procedure reused as a constructor, method, and public function, declaration
removal, and construction suppression. Focused semantic, completed-policy, and
lowering evidence covers `Pass()` placement, independent visibility, native
target selection, exact overload dispatch, contradictory constructors, and
single-initializer emission without more native builds. Defined operators and
assignment reuse the established Generic Interfaces runtime path. Exact
documentation rows resolve through `CONTRACT_COVERAGE.md`; 29 baseline nodes
and 16 old contract artifacts received final dispositions. Native sources and
ordinary generated class/generic behavior remain with Derived Types and
Generic Interfaces; argument and result projection edits remain with Calls and
Results.

Calls and Results completion record (2026-07-30): nine final feature nodes
pass. The compiler-proxy audit records 15 real invocations: four C binding
compilations; six Fortran compilations; four Fortran extension links; and one
compiler query. Two native objects are compiled once and reused across four
source-free edited-contract extensions covering native-order writable slots,
reordered and hidden scalar/string/array/derived results, stable mixed-result
ordering, immutable replacement returns, and hidden fixed-shape array
allocation including zero-size and failure paths. Completed-policy and
lowering evidence covers implicit versus projected native slots, GIL state,
typed hidden values, and copy versus identity writeback without more native
builds. The complete projection grammar, dtype/layout validation, optional
states, status errors, callback GIL behavior, and native-library topology reuse
their established final feature owners. Exact documentation rows resolve
through `CONTRACT_COVERAGE.md`; 16 additional baseline nodes and 12 old source
or contract artifacts received final dispositions, and five superseded runtime
test modules were deleted.

SciFortran and real-library curation record (2026-07-30): the initial audit
attributed all 303 SciFortran sources to upstream revision
`25ec901b25fcdb5802f3d4cdbed475addcfac7ab`, compared normalized models, and
measured 37 lines plus 27 branches that the focused parser suite had not
reached. A follow-up contextual-coverage audit traced all 64 items to 12 source
units and reduced them to five named inline tests in
`tests/fortran/source_parsing/parsing/test_real_world_interaction_regressions.py`.
The focused parser suite now executes all 64 formerly unique items without the
third-party project. Existing focused tests retain the historical
`CLASS(...)`, CPP, scope, `EXTERNAL`, `SAVE`/local-type, `USE`-rename, and
symbolic-parameter fixes. Promotion-only history entries did not identify an
additional behavior contract. The 303 sources, 303 normalized models,
inventory, coverage ledger, license copy, and corpus-only test helper were
therefore deleted; no SciFortran runtime or build evidence was claimed.

BLAS and LAPACK remain solely under the Building Shared Library end-to-end
owner: their 2,216 parser goldens and four checked contract files were deleted,
generated contracts now exist only in pytest temporary directories, and the
BLAS full-pipeline node passes locally without a checked golden. LAPACK was not
run locally.

### Procedures, arguments, and results

- [x] Cover functions and subroutines with `intent(in)`, `intent(out)`,
  `intent(inout)`, omitted `intent`, `value`, optional, and descriptor dummies.
- [x] Cover scalar, array, string, derived, allocatable, pointer, and callback
  families wherever their behavior differs.
- [x] Cover positional/keyword calls, skipped optional positions, omission,
  explicit `None`, and concrete presence.
- [x] Preserve absent, present-empty, and present-with-value states for optional
  allocatables and pointers.
- [x] Cover hidden outputs, caller storage, replacement returns, direct results,
  multiple outputs, and tuple ordering.
- [x] Cover every documented projection mechanism: `Arg`, `Addr(Arg)`,
  `Value(Arg)`, descriptor `Arg`, `Return`, descriptor `Return`, `Pass`, typed
  literals, `Len`, shape, `IsPresent`, and `Work`.
- [x] Cover reordering, hiding, insertion, invalid duplication/missing
  positions, and out-of-range diagnostics.

### Derived types and storage/lifetime

- [x] Preserve the complete scalar-derived actual/dummy matrix where cells
  differ by module origin, storage, dummy form, support, or diagnostic.
- [x] Cover constructors, failed-construction cleanup, methods, state,
  destruction/finalization, type identity, and supported boundaries.
- [x] Separate core compatibility, empty descriptor states, reassociation,
  writeback, rollback, and error propagation while reusing compiled fixtures.
- [x] Cover allocatable and pointer empty/present states, aliasing, ownership,
  replacement, mutation, release, and lifetime.
- [x] Cover module-owned, borrowed, transferred, and Python-owned paths when
  documented policy differs.

### Remaining guide features

- [x] Modules: namespaces, variables, constants, imports, initialization, and
  module procedure identity.
- [x] Optional arguments: every documented call state and presence projection.
- [x] Generics: overload selection, ambiguity, operators, assignments, and
  native-specific routing.
- [x] Callbacks: every distinct scalar, array, derived, lifetime, exception, and
  GIL ABI mechanism.
- [x] Enumerations: supported values, conversion, results, and diagnostics.
- [x] Raw addresses: primitive, array, and fixed-string boundaries with owners
  kept alive and unsafe cases isolated.
- [x] Error handling: native status translation, exception type/message, and
  cleanup on failure.
- [x] Multiple sources/building: module order, external bundles, objects,
  libraries, shared-library paths, and CLI behavior.

### Edited `.pyi`

- [x] Exports/modules: namespaces, flattening, selective/repeated exports,
  aliases, hiding/removal, collisions, native identity, placement, initializers,
  and true constants.
- [x] Functions/classes: module procedure as method, `Pass`, `@bind`,
  overload edits, private-specific routing, constructors, type-bound methods,
  generics, operators, and assignment.
- [x] Calls/results: identity/native order, reordering, hiding/insertion,
  projections, replacement mutation, `Immutable`, optionality, dtype, shape,
  layout, `@raises`, and `@hold_gil`.
- [x] Raw-address edits keep native owners alive.
- [x] Contract imports cover control names, arbitrary aliases, generated alias
  collision safety, and missing-import diagnostics.
- [x] Every rejected form fails at the documented loader, validation, policy,
  build, import, or runtime stage.
- [x] No edited-contract test uses native-source fallback.

## 6. Parser corpora and real-library end-to-end tests

### Former SciFortran corpus

SciFortran was used only as temporary parser-discovery evidence. It was never
compilation, wrapper, runtime, end-to-end, or smoke evidence.

- [x] Inventory every file by parser constructs/interactions and current
  outcome.
- [x] Recover issue, commit, failure, or maintainer provenance for known parser
  regressions.
- [x] Give each file one disposition: retain, reduce, replace with a minimal
  reproducer, or delete as redundant.
- [x] Do not infer redundancy from filename, similar syntax, or equal line
  coverage.
- [x] Compare focused parser coverage with and without SciFortran to find unique
  branches. This is a targeted corpus check, not the complete coverage workflow.
- [x] Preserve a normalized parser-model or focused invariant; “does not crash”
  is insufficient.
- [x] Preserve licensing and attribution while upstream content is retained.
- [x] Keep a full source only when the regression depends on interactions that
  cannot be minimized confidently.
- [x] Trace the 37 unique lines and 27 unique branches to their responsible
  source rows, replace all 64 items with named inline parser tests, and verify
  exact coverage before deletion.
- [x] Delete each old SciFortran source/expectation as soon as its final parser
  owner is verified and it has no remaining consumer.
- [x] Remove SciFortran-specific enumerators and path rewrites when the last
  retained consumer no longer needs them.
- [x] Never list a SciFortran case as end-to-end or smoke evidence.

Historical regression ownership after reduction:

| History | Extracted behavior | Final focused owner |
| --- | --- | --- |
| `3c69d1c5` | `CLASS(...)` declarations in procedure, module, and derived-field scopes | `test_real_world_interaction_regressions.py::test_polymorphic_class_declarations_work_in_each_metadata_scope` |
| `048d003e`, `4581b200`, `6e0db679`, `37b537a4` | Broad source promotions involving includes, declarations, signatures, continuations, statement functions, COMMON blocks, and result-kind parameters | The five tests in `test_real_world_interaction_regressions.py` plus the ordinary declaration, procedure, and scope suites |
| `ca3b7368`, `c887049b`, `30baeb17` | Fixture promotion or model refresh only; repository history records no independent parser defect | No separate contract beyond the measured interaction replacements |
| `e835dfb2` | Raw CPP branches require preprocessing | `source_preprocessing/preprocessing/test_parser_boundaries.py::test_cpp_directives_require_compiler_preprocessing` |
| `29d01111` | Host-procedure `contains` and local-interface scope | `test_fortran_parser_procedures_and_interfaces.py::test_ignore_internal_procedures_in_contains_block` and `::test_procedure_dummy_declaration_tracks_local_interface_kind` |
| `b5612374` | `EXTERNAL` dummy procedures under `implicit none`, including type-before-attribute order | `test_fortran_parser_procedures_and_interfaces.py::test_implicit_none_allows_external_dummy_procedure_argument` and the minimized legacy-procedure interaction test |
| `f9d8d896` | Legacy `SAVE`, COMMON, and local-derived-type boundaries | The minimized legacy-procedure interaction test and `source_preprocessing/preprocessing/test_parser_boundaries.py::test_execution_part_boundaries_and_local_types_are_not_misread_as_declarations` |
| `186f0af5` | Recursive grammar slicing and scoped unit ownership | `source_parsing/parsing/test_developer_tutorial.py` and the source-form/diagnostic regression suite |
| `5898c055` | Preserved `USE` rename mappings | `test_declaration_and_interface_edges.py::test_use_rename_and_intrinsic_forms_are_recorded` |
| `ecc37c0f` | Literal and symbolic parameter-value preservation | The minimized declaration-interaction test and `test_declarations_and_shapes.py` |

### BLAS and LAPACK

- [x] Move the real-library projects to
  `examples/blas/` and `examples/lapack/`.
- [x] Treat them only as full-pipeline evidence: build from the library sources,
  generate wrappers, compile/link, import the extension, and verify the public
  Python surface and representative runtime calls.
- [x] Use the native-source build route only. Keep no BLAS/LAPACK generated
  `.pyi` golden, checked `.pyi` input fixture, edited `.pyi` variant, or
  source-free `.pyi` replay.
- [x] If source wrapping creates an intermediate `.pyi` internally, keep it in
  the temporary build directory and do not treat it as BLAS/LAPACK contract
  evidence.
- [x] Test ordinary and edited `.pyi` behavior with small dedicated fixtures
  under `semantic_pyi_format/{pipeline,end_to_end}/` and
  `pyi_contracts/<edit-family>/end_to_end/`.
- [x] Do not list BLAS or LAPACK as parser, semantic, policy, ordinary
  feature-conformance, or smoke evidence. Parsing occurs inside their journey
  but does not make them parser-owned tests.
- [x] Keep small conformance cases with their ordinary end-to-end feature;
  BLAS/LAPACK own library-scale integration only.
- [x] Do not count thousands of parsed procedures as thousands of independent
  feature contracts.
- [x] Run BLAS/LAPACK end-to-end work in one dedicated scheduled or explicitly
  requested lane.
- [x] Do not run LAPACK locally unless explicitly requested.

### Real-source gate

- [x] Every old corpus artifact has a reviewed final disposition.
- [x] Every known SciFortran-discovered parser regression remains named.
- [x] Unique parser line/branch and interaction evidence is preserved.
- [x] No upstream parser-corpus artifact remains after its evidence is reduced.
- [x] No parser corpus or BLAS/LAPACK real-library test appears in toolchain
  smoke.

## 7. Complete the test migration

Run this gate after all documentation features and corpora have migrated, and
before changing compiler product behavior.

- [x] Every ordinary legacy pytest node is retired.
- [x] Every legacy source, include, JSON, and `.pyi` artifact is migrated,
  replaced, or deleted.
- [x] No old fixture root remains authoritative.
- [x] BLAS, LAPACK, parser-regression, and contract content exists only beneath
  its final owner; no SciFortran snapshot remains.
- [x] Every permanent contract row resolves to final collected nodes.
- [x] Collect `tests/fortran/`, `tests/c/`, and `tests/shared/` independently;
  run the local Fortran verification with `-m "not real_library"`.
- [x] Run the new suites alone under the same CI-equivalent line-and-branch
  coverage procedure used for the baseline.
- [x] Require every baseline-executed line and branch to remain executed per
  Python file. A higher aggregate percentage cannot hide a lost baseline line.
- [x] Compare feature/diagnostic and corpus evidence separately from Python
  coverage.
- [x] Investigate every regression before accepting a deliberate exception.
- [x] Remove temporary migration inventories.
- [x] Update workflow, documentation, generator, cache, and focused-test paths.
- [x] Run repository-wide collection, final focused/ordinary-full tests, and
  required static analysis; leave `real_library` execution to its designated
  lane.

Final coverage evidence from 2026-07-30 uses the same deterministic seed,
`COVERAGE_PROCESS_START`, parallel subprocess data, `coverage combine`, and
`coverage report` procedure as the baseline. The recovered pre-migration rerun
is 90.22%; the final language-root selection is 90.63%. Exact JSON comparison
found no lost executed line or branch in any of the 78 unchanged executable
Python files. In `prik/parsers/fortran/parser.py`, every baseline line remains
executed after remapping the nine-line `CLASS(*)` diagnostic insertion. The
old fallthrough arc at the insertion point is deliberately split into the new
assumed-type decision and its fallthrough, and both that fallthrough and the
new rejection branch execute. This is the only reviewed control-flow
exception; it fixes the documented unsupported-form diagnostic rather than
removing evidence.

The final coverage run found one migrated `.pyi` printer golden with compact
formatting instead of the reviewed multiline output. Restoring the exact
legacy golden at its final owner made its two focused printer nodes pass; the
fixture-only correction does not change executable coverage. The coverage run
otherwise recorded 3,916 passes, 12 documented skips, and 10 deselections.

The clean final ordinary gate collects 3,941 repository nodes. After moving
suite-structure meta-tests outside the language trees, the independent roots
collect 22 architecture nodes, 498 C nodes, 1,275 shared nodes, and 2,146
Fortran nodes: 2,144 are ordinary/smoke nodes and exactly two are the
BLAS/LAPACK `real_library` rows. The unchanged ordinary selection records 3,919
passes, 12 documented skips, and 10 deselections in 643.60 seconds. Strict
smoke separately records exactly eight passes in 18.49 seconds, for 662.09
seconds across the two executed selections. LAPACK was collected but not run.

An uncached compiler-proxy audit across those same two selections records
1,266 real compiler executions: 562 compilations (382 Fortran and 180 C), 186
links, 255 preprocessing runs, 259 compiler queries, and four version checks.
This is 456 executions, or 26.5%, below the 1,722-invocation legacy baseline
and confirms that the final fixture sharing did not inflate native work.

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

- [x] Every marked node is below an `end_to_end/` directory under
  `tests/fortran/`.
- [x] Every `toolchain_smoke` node also carries `fortran_end_to_end`.
- [x] Marker metadata names a distinct mechanism and the compiled fixture it
  reuses.
- [x] The named fixture appears in the item's fixture closure.
- [x] Select exact rows from large matrices; do not mark whole matrices unless
  every row is intentionally smoke.
- [x] Target six to eight distinct compiled fixtures.
- [x] Cover scalar/module procedure plus NumPy array, string behavior, derived
  lifecycle, allocatable/pointer ownership, callback, generic/overload, and
  source → generated `.pyi` → rebuilt extension.
- [x] Prefer a multiple-source or CLI build within those fixtures when it adds
  no redundant extension build.
- [x] Verify values, state, mutation, and lifetime—not compilation alone.
- [x] Use exactly the same marked nodes on Linux, macOS, x86-64, ARM64, and
  every compiler family.
- [x] Add no compiler-family or OS marker to smoke nodes.
- [x] Permit no compiler/platform conditional skip or xfail in strict smoke.
- [x] Include no corpus, BLAS/LAPACK, or parsing-only test.
- [x] Map every smoke node to the permanent contract ledger.

### Smoke enforcement

`tests/fortran/conftest.py`:

- [x] rejects a smoke marker outside end-to-end;
- [x] enforces the exact relationship between `fortran_end_to_end` paths and
  marker membership;
- [x] enforces that `real_library` identifies only BLAS/LAPACK and can never
  overlap `toolchain_smoke`;
- [x] validates `mechanism` and `build_fixture`;
- [x] rejects `skip`, `skipif`, `xfail`, compiler, and OS marks;
- [x] provides `--require-toolchain-smoke`;
- [x] fails strict smoke if no node collects, a requested compiler is missing,
  or any setup/call/teardown report skips or xfails; and
- [x] emits a deterministic collection report.

`tests/architecture/fortran/test_smoke_selection.py`:

- [x] validates marker registration and exact collected nodes;
- [x] validates contract-ledger membership;
- [x] validates the six-to-eight-build budget;
- [x] rejects corpus, BLAS/LAPACK real-library, profile, and platform paths; and
- [x] confirms marked nodes are part of the ordinary unfiltered end-to-end
  suite.

The runtime helper previously hardcoded GFortran. Alternate-compiler smoke now:

- [x] add a session-level option such as
  `--prik-fortran-compiler=<executable>`;
- [x] resolve and log the requested executable and version once;
- [x] propagate its profile through preprocessing, probes, native compilation,
  bridge compilation, linking, and runtime discovery; and
- [x] fail rather than silently substituting GFortran.

## 9. Add compiler profiles and macOS

Document each supported family and limitation before changing product code.
Compiler support means preprocessing, probing, native and generated-source
compilation, linking, loading, and the same runtime smoke all succeed.

### Compiler profiles

- [x] Inventory GNU-specific flags, diagnostics, module assumptions, symbols,
  runtime libraries, and link options.
- [x] Keep family selection in compilation/build integration, not scattered
  compiler-name branches.
- [ ] Implement GNU, Intel ifx, LLVM Flang, and NVIDIA nvfortran one profile at
  a time.
- [x] Add focused command/capability tests under
  `tests/fortran/building_shared_library/compiling/` and
  `tests/fortran/source_preprocessing/preprocessing/`.
- [ ] Carry compiler-derived target facts through semantics and the shared plan;
  bridge/binding generators do not infer semantic policy from compiler family.
- [x] Give unknown and unsupported compilers explicit diagnostics.
- [x] Add runtime smoke only after the profile tests pass.
- [ ] Document version floors and limitations from evidence.

Local Linux evidence on 2026-07-30 runs the unchanged eight-node strict smoke
selection successfully with GNU Fortran 13.4.0, Intel ifx 2026.1.1 plus icx,
and LLVM Flang 22.1.8 plus Clang. NVIDIA nvfortran remains unvalidated, so the
multi-family implementation and version-floor items stay open.

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

The `Tests` workflow now declares one macOS 15 ARM64 lane with Python 3.12 and
GNU Fortran/GCC 13. It logs the hosted environment, delegates focused compiler,
CLI, and strict smoke checks to the shared lane runner, then runs the complete
ordinary suite with BLAS/LAPACK excluded. The execution and platform-audit
items above remain open until the first hosted run provides evidence.

The `Smoke Tests` workflow also declares an LLVM Flang/Clang lane on the same
macOS runner. Intel IFX remains Linux-only because Intel does not distribute
IFX for macOS or Apple Silicon.

### Toolchain lane contract

Focused CLI, profile, and platform tests are not marked `toolchain_smoke`.
Use one repository-owned lane runner with a dry-run plan. Each noncanonical
compiler/platform lane performs the equivalent of:

```text
python -m pytest -q <profile/platform nodes> <focused Fortran CLI nodes>
python -m pytest -q tests/fortran -m toolchain_smoke \
  --prik-fortran-compiler=<executable> --require-toolchain-smoke
```

`tests/architecture/fortran/test_ci_toolchain_lanes.py` verifies:

- [x] every compiler lane includes its profile tests;
- [ ] every macOS lane includes macOS platform tests;
- [x] every compiler/platform lane includes the designated Fortran CLI nodes;
- [x] every referenced node collects;
- [x] every lane invokes strict end-to-end smoke with the requested compiler;
  and
- [x] each explicit GitHub Actions entry delegates to the common runner.

`.github/workflows/fortran-toolchain-smoke.yml` declares pinned IFX/ICX and
Flang/Clang matrix entries. Both delegate profile, CLI, and strict smoke
execution to `tools/run_fortran_toolchain_lane.py`; its `--plan` output is the
dry-run contract checked before execution.

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
- [x] Linux x86-64, middle Python, Intel ifx: profile tests, focused CLI, and
  toolchain smoke when installation cost/licensing is acceptable; otherwise
  schedule it and document that cadence.

### Scheduled lanes

- [x] Linux x86-64, middle Python, LLVM Flang: profile tests, focused CLI, and
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

1. [x] Final structure documentation and positive architecture guards.
2. [x] Baseline collection, artifact inventory, native-build counts, and
   line/branch coverage artifact.
3. [x] Mechanical C quarantine.
4. [x] Fortran features in User Guide order, completing the fast structural
   adoption pass and then the contract-completion pass for each feature,
   including stage, end-to-end, negative, pytest-node, and last-consumer fixture
   cleanup.
5. [x] SciFortran and real-library corpus curation.
6. [x] Final new-suite-only coverage comparison and legacy-root removal.
7. [x] Toolchain smoke selection and structural enforcement.
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
