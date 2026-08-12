---
title: Contributor Architecture Guide
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: packages/index.md, source-map.md, feature-to-code-map.md, testing-strategy.md
status: maintained
publication: draft
---

# Contributor Architecture Guide

This is the first internal document to read before changing PRIK. It explains
the repository at a shallow level, the complete Fortran wrapper workflow, the
authority of every stage, the package-root entrypoints, and where to find the
detailed package and test documentation.

## Repository Structure

The first tree is intentionally shallow. Detailed contents belong in the guide
for the owning folder.

```text
prik/
├── prik/                 # Production Python package
├── tests/                # Feature-first, stage-owned verification
├── docs/                 # User and contributor documentation sources
├── docs_theme/           # Maintained MkDocs template customizations
├── examples/             # Complete wrapper projects and real libraries
├── benchmarks/           # Performance workloads and publication tooling
├── tools/                # Repository maintenance and quality scripts
├── .github/              # Continuous integration and release workflows
├── .artifacts/           # Hidden generated documentation/distributions
├── pyproject.toml        # Package and Python-tool configuration
├── mkdocs.yml            # Documentation navigation and site configuration
├── CHANGELOG.md          # Visible unreleased and released changes
├── CONTRIBUTING.md       # Contributor entrypoint
├── README.md             # Public project overview
└── AGENTS.md             # Repository implementation and verification rules
```

The production package follows the implemented workflow rather than
alphabetical order:

```text
prik/
├── __init__.py           # Supported public Python API
├── __main__.py           # python3 -m prik launcher
├── cli.py                # Command validation and stage dispatch
├── stage_values.py       # Shared mutable-to-frozen stage records
├── contracts/            # Public semantic .pyi vocabulary
├── compiler/             # Native compiler and linker services
├── preprocessing/        # Source preparation and target probes
├── parsers/              # Fortran and semantic .pyi syntax frontends
├── semantics/            # Language-neutral semantic IR
├── policy/               # Completed post-IR interoperability decisions
├── planning/             # Backend-neutral wrapper plans
├── codegen/              # Backend nodes and Python facade generation
├── printers/             # C, Fortran, and semantic .pyi serialization
├── pipeline/             # Cross-stage workflow orchestration
├── runtime/              # Imported-extension handles and native support
├── naming/               # Shared public and generated-symbol rules
└── utilities/            # Genuinely stage-neutral mechanisms
```

## Package-Root Entry Points

Only public entrypoints and genuinely shared stage values live directly in
`prik/`.

| File | Essential objects | Role |
| --- | --- | --- |
| `prik/__init__.py` | public exports and `__version__` | Flattens the supported Python API and lazily exposes heavyweight parse, probe, CLI, and build functions. It is not an implementation owner. |
| `prik/__main__.py` | guarded launcher | Delegates `python3 -m prik` to `prik.cli.main()`. Importing it does not run the CLI. |
| `prik/cli.py` | `main()` and stage request handlers | Parses commands, validates cross-option combinations, formats diagnostics, and dispatches to parser or pipeline owners. |
| `prik/stage_values.py` | `StageRecord`, `FrozenStageRecordError` | Supports mutable construction followed by recursive freezing at a consuming-stage boundary. |

The CLI is an orchestrator, not a semantic authority. A new option may select
or configure a stage, but parser grammar, semantic rules, policy, codegen, and
compiler mechanics remain in their owning packages.

Run the public entrypoints directly:

```bash
python3 prik/__init__.py
python3 prik/cli.py --version
python3 prik/stage_values.py
```

```text
PRIK 0.2.1
Public parser result: subroutine ping from ping.f90
prik 0.2.1
Editable parser output: geometry -> ['scale', 'norm']
Frozen consumer input: geometry -> ('scale', 'norm')
Mutation rejected: ParserOutput is frozen by its consuming stage
```

The output shows the stable root API, the real CLI dispatcher, and the explicit
producer-to-consumer freeze boundary. Exact output is maintained by the
[central execution-example tests](../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py).

## End-To-End Workflow

The implemented source-driven Fortran path is:

```text
CLI or Python build request
  -> compiler-backed preprocessing and target probing
  -> Fortran parser facts
  -> language-neutral semantic IR
  -> complete post-IR interoperability policy
  -> backend-neutral wrapper plan
  -> C and Fortran syntax-node generation
  -> language printers
  -> GeneratedWrapper
  -> compiler and linker services
  -> importable extension and runtime objects
```

Semantic `.pyi` input joins at semantic IR construction. It is an editable
contract input, not a second backend or a parser for Fortran source.

The C parser and C-to-IR frontend are intentionally deferred from the
published contributor workflow until the C input path is mature. Generated C
for the CPython/NumPy binding remains an essential, fully documented part of
the Fortran wrapper backend.

## Authority And Dependency Rules

Each stage may depend on completed output from the stage above it. Authority
does not flow backward.

| Stage | May decide | Must not decide |
| --- | --- | --- |
| Preprocessing/probes | prepared source, provenance, dependencies, measured target facts | declaration meaning, semantic dtypes, wrapper support |
| Parsers | syntax facts, source structure, source-located diagnostics | ownership, Python API, lowering |
| Semantic IR | language-neutral identities, shapes, origins, raw contract metadata | completed ownership or emitted mechanisms |
| Policy | exports, object kind, owner, transfer, destruction, storage, writeback, nullability, projections, lifecycle, setters, support | source syntax or backend text |
| Planning | typed projection and organization of completed facts | new semantic decisions or presentation text |
| Codegen | backend-local mechanisms and syntax nodes selected by the plan | fallback policy inference |
| Printers | formatting and serialization | orchestration, filenames, semantic decisions |
| Pipeline | workflow order, artifacts, manifests, compilation scheduling | stage-local grammar or rules |
| Compiler/runtime | native command mechanics and enforcement of completed runtime contracts | wrapper API or lifetime policy selection |

The most important rule is the policy boundary: before
`WrapperPlanner.build()` begins, every semantic choice needed by binding and
bridge generation must already be explicit. Lower stages dispatch from those
choices and fail closed when a required decision is missing.

## Package Guide Map

Each package has one canonical detailed guide containing its local structure,
important files and objects, direct examples with output, focused test links,
change routes, and invariants.

| Package | Brief role | Detailed guide |
| --- | --- | --- |
| `contracts/` | Public semantic `.pyi` vocabulary | [Contracts](packages/contracts.md) |
| `compiler/` | Native command construction and execution | [Compiler](packages/compiler.md) |
| `preprocessing/` | Source preparation, provenance, includes, and target probes | [Preprocessing](packages/preprocessing.md) |
| `parsers/` | Fortran source and semantic `.pyi` syntax facts | [Parsers](packages/parsers.md) |
| `semantics/` | Language-neutral semantic IR construction | [Semantics](packages/semantics.md) |
| `policy/` | Complete post-IR interoperability decisions | [Policy](packages/policy.md) |
| `planning/` | Mechanical typed wrapper-plan projection | [Planning](packages/planning.md) |
| `codegen/` | Plan-driven backend nodes and Python facade | [Code generation](packages/codegen.md) |
| `printers/` | Serialization of formed representations | [Printers](packages/printers.md) |
| `pipeline/` | Cross-stage wrapper/build workflows and artifacts | [Pipeline](packages/pipeline.md) |
| `runtime/` | Imported-extension handles and bundled native support | [Runtime](packages/runtime.md) |
| `naming/` | Shared public and generated symbol rules | [Naming](packages/naming.md) |
| `utilities/` | Stage-neutral expressions, strings, and visitor dispatch | [Utilities](packages/utilities.md) |

The [datatype lifecycle](concepts/datatype-lifecycle.md) remains a separate
cross-cutting concept because one native datatype passes through probing,
semantic normalization, policy, codegen mapping, and runtime validation.

## Tests And Evidence

Choose tests by native language, public feature, and owning stage. The
[testing strategy](testing-strategy.md) is canonical for placement and command
selection. Package guides link directly to their focused suites.

Direct source-file examples are production-owned `if __name__ == "__main__"`
flows, run from the repository root as:

```bash
python3 <folder>/<file>.py
```

Their exact results are grouped in
[`tests/fortran/infrastructure/execution_examples/test_execution_examples.py`](../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py).
Documentation tests own links, navigation, metadata, publication, and package
guide structure; feature and stage tests own the demonstrated behavior.

## Where A Change Begins

| Change | Start here | Continue only when needed |
| --- | --- | --- |
| CLI option or dispatch | `prik/cli.py` | selected package and CLI/user documentation |
| Source expansion or provenance | `prik/preprocessing/source.py` | parser boundary tests |
| Fortran syntax fact | `prik/parsers/fortran/` | semantic converter if the IR changes |
| Semantic `.pyi` syntax | `prik/parsers/pyi/parser.py` or `prik/semantics/pyi2ir.py` | printer, policy, and user reference according to meaning |
| Stable semantic model/type | `prik/semantics/` | policy and downstream projections |
| Ownership, projection, setters, or support | `prik/policy/` | planning only to project the completed result |
| Plan representation | `prik/planning/` | binding/bridge generation consumers |
| Emitted native mechanism | narrow `prik/codegen/` owner | matching printer only if representation changes |
| Formatting | matching `prik/printers/` file | golden output tests |
| Build artifact or compilation workflow | `prik/pipeline/build.py` | compiler service when argv mechanics change |
| Runtime handle enforcement | `prik/runtime/handles.py` | policy first if permission/ownership is undecided |

For exact file ownership use the [source map](source-map.md). When starting
from a documented capability use the [feature-to-code map](feature-to-code-map.md).

## Contributor Documentation Structure

All developer, maintainer, design, testing, release, and roadmap material lives
in one contributor area:

```text
docs/developer/
├── index.md
├── architecture.md
├── source-map.md
├── feature-to-code-map.md
├── testing-strategy.md
├── packages/             # One detailed guide per production package
├── concepts/             # Cross-stage concepts
├── workflows/            # Contribution, QA, CI, docs, and releases
├── design/               # Accepted future architecture and open decisions
├── roadmap/              # Active incomplete work only
└── deferred/             # Intentionally unpublished input-language material
```

There is no separate maintainer tree. Completed migration logs and placeholder
pages are not maintained architecture; Git history retains them after their
still-valid decisions have moved to canonical guides.
