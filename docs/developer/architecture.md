---
title: Contributor Architecture Guide
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: packages/index.md, source-map.md, feature-to-code-map.md, testing-strategy.md
status: maintained
publication: draft
---

# Contributor Architecture Guide

Read this page before changing PRIK. It gives the complete wrapper path, the
handoff at every stage, and the owner of each top-level directory. Then read
the linked package guide for the file you intend to change. Package guides
explain local modules, runnable examples, and focused tests; this page stays
at the workflow level.

## Repository Structure

```text
prik/
├── prik/                 # Production Python package and wrapper stages
├── tests/                # Feature-first and stage-owned verification
├── docs/                 # User and contributor documentation sources
├── docs_theme/           # Maintained MkDocs template customizations
├── examples/             # Complete wrapper projects and real libraries
├── benchmarks/           # Performance workloads and publication tooling
├── tools/                # Repository maintenance and quality scripts
├── .github/              # Continuous integration and release workflows
├── .artifacts/           # Hidden generated documentation and distributions
├── pyproject.toml        # Package and Python-tool configuration
├── mkdocs.yml            # Documentation navigation and site configuration
├── CHANGELOG.md          # Visible unreleased and released changes
├── CONTRIBUTING.md       # Contributor entrypoint
├── README.md             # Public project overview
└── AGENTS.md             # Repository implementation and verification rules
```

The production package is arranged by stage ownership, not alphabetically:

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

The deferred C-input frontend is deliberately not part of this published
Fortran workflow. Generated C bindings are part of the supported backend and
remain visible in the code-generation and printer guides.

## Package-Root Entry Points

Only public entrypoints and values shared across stages live directly in
`prik/`. These modules coordinate work; they do not take ownership from a
stage package.

| File | Read it when | It receives and produces |
| --- | --- | --- |
| `prik/__init__.py` | you need the normal-user build API | Import-only facade for `__version__` and the three build entrypoints. Import parsing, contracts, probes, runtime handles, and semantic tools from their owning packages. |
| `prik/__main__.py` | you are tracing `python3 -m prik` | Calls `prik.cli.main()` only when executed as a module. |
| `prik/cli.py` | you are changing a command or option | Turns terminal arguments into validated stage requests and dispatches them to the owning parser or pipeline. |
| `prik/stage_values.py` | a value crosses from a producing to a consuming stage | Provides `StageRecord` and recursive freezing so completed input cannot be mutated downstream. |

Run the direct command and stage-value demonstrations from the repository
root:

```bash
python3 prik/cli.py --version
python3 prik/stage_values.py
```

```text
prik 0.2.1
Editable parser output: geometry -> ['scale', 'norm']
Frozen consumer input: geometry -> ('scale', 'norm')
Mutation rejected: ParserOutput is frozen by its consuming stage
```

The table identifies the supported import surface. The examples show the
command dispatcher and producer-to-consumer freeze boundary. Their exact
output is checked by the
[central execution-example tests](../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py).

## End-To-End Workflow

The normal source-driven Fortran route is a one-way sequence:

```text
CLI or Python build request
  -> preprocessing and target probes
  -> Fortran parser facts
  -> language-neutral semantic IR
  -> complete interoperability policy
  -> backend-neutral wrapper plan
  -> C and Fortran nodes plus Python facade text
  -> C and Fortran source text
  -> in-memory generated wrapper
  -> native compilation and linking
  -> importable extension and runtime objects
```

Semantic `.pyi` input enters at semantic-IR construction. It is an editable
contract input that uses the same policy, planning, code-generation, and build
path; it is not a second backend. A type-mapping report follows the same
facts for inspection but does not create a wrapper.

## Stage Handoffs

Read the rows top to bottom. Each output is the next row's authoritative
input; a later row may organize or lower it, but may not silently change its
meaning.

| Stage owner | Receives | Produces | Next owner |
| --- | --- | --- | --- |
| `preprocessing/` | source paths, compiler configuration, target requests | prepared source, provenance, dependency facts, measured target facts | `parsers/`, `semantics/` |
| `parsers/` | prepared Fortran text or `.pyi` text | source parser models or a Python AST, with locations and diagnostics | `semantics/` |
| `semantics/` | frontend facts and measured type facts | `SemanticModule`: stable identities, shapes, provenance, and raw metadata | `policy/` |
| `policy/` | semantic IR plus raw requests | complete immutable choices for ownership, transport, projection, lifecycle, setters, and support | `planning/` |
| `planning/` | policy-complete semantic IR | `ModulePlan` with binding and bridge views, ordering, names, and build requirements | `codegen/` |
| `codegen/` | a validated plan | typed C/Fortran nodes and planned Python facade source | `printers/`, `pipeline/` |
| `printers/` | formed native nodes or semantic IR | C, Fortran, or `.pyi` text | `pipeline/` or caller |
| `pipeline/` | completed stage inputs | generated artifacts, written files, native build requests, and public result records | `compiler/`, `runtime/` |
| `compiler/` | explicit source, object, include, library, and link inputs | recorded or executed native commands and a shared extension | `runtime/` |
| `runtime/` | generated extension operations and completed handle contracts | validated Python handle objects and live NumPy views | Python caller |

`naming/` supplies deterministic public and native names where planning or
generation needs them. `utilities/` supplies small stage-neutral mechanisms;
neither is a hidden policy stage. `contracts/` supplies the public `.pyi`
vocabulary before parsing begins.

## Authority And Dependency Rules

The handoff table describes data flow. This table describes decision-making.

| Stage | May decide | Must not decide |
| --- | --- | --- |
| Preprocessing and probes | prepared source, provenance, dependencies, measured target facts | declaration meaning, semantic types, wrapper support |
| Parsers | syntax facts, source structure, source-located diagnostics | ownership, Python API, lowering |
| Semantic IR | language-neutral identities, shapes, origins, raw contract metadata | completed lifetime, projections, or emitted mechanisms |
| Policy | exports, object kind, owner, transfer, destruction, storage, writeback, nullability, projections, setters, support | source grammar or backend text |
| Planning | a typed projection and ordering of completed facts | a new semantic decision or presentation text |
| Code generation | plan-selected backend mechanisms and syntax nodes | fallback policy inferred from datatype, `intent`, aliases, or local memory checks |
| Printers | formatting and serialization | orchestration, filenames, or semantic decisions |
| Pipeline | stage order, artifact assembly, manifests, and compilation scheduling | grammar, policy, lowering, or command mechanics |
| Compiler and runtime | native command execution and enforcement of completed runtime contracts | wrapper API or lifetime-policy selection |

The critical boundary is before `WrapperPlanner.build()`: all semantic choices
needed by binding and bridge generation must be explicit. If a required choice
is absent, downstream code must fail with the owning diagnostic rather than
guess a default.

## Package Guide Map

Use one guide at a time after this page. Every guide has the same reading
order: purpose, input/output handoff, complete Python-module tour, runnable
examples, focused tests, change routes, and invariants.

| Package | Use it for | Guide |
| --- | --- | --- |
| `contracts/` | public semantic `.pyi` names | [Contracts](packages/contracts.md) |
| `compiler/` | native commands, profiles, and support installation | [Compiler](packages/compiler.md) |
| `preprocessing/` | parser input, provenance, includes, and target facts | [Preprocessing](packages/preprocessing.md) |
| `parsers/` | Fortran syntax facts and raw `.pyi` AST | [Parsers](packages/parsers.md) |
| `semantics/` | language-neutral IR and raw metadata | [Semantics](packages/semantics.md) |
| `policy/` | completed interoperability decisions | [Policy](packages/policy.md) |
| `planning/` | deterministic plan projection and ordering | [Planning](packages/planning.md) |
| `codegen/` | binding, bridge, nodes, and Python facade mechanisms | [Code generation](packages/codegen.md) |
| `printers/` | C, Fortran, and `.pyi` serialization | [Printers](packages/printers.md) |
| `pipeline/` | whole-wrapper, contract, report, and build workflows | [Pipeline](packages/pipeline.md) |
| `runtime/` | imported handle behavior and native payload | [Runtime](packages/runtime.md) |
| `naming/` | stable public and generated symbols | [Naming](packages/naming.md) |
| `utilities/` | stage-neutral expression, string, and visitor helpers | [Utilities](packages/utilities.md) |

The [datatype lifecycle](concepts/datatype-lifecycle.md) follows one datatype
across these owners. It is deliberately separate from the package tours.

## Tests And Evidence

Feature tests own behavior; documentation tests own navigation and guide
coverage. Start with the package guide's **Tests And What They Prove** section,
then use the [testing strategy](testing-strategy.md) to choose the narrowest
command for the changed stage.

Direct source-file examples are real production-owned
`if __name__ == "__main__"` flows. Run them from the repository root as:

```bash
python3 <folder>/<file>.py
```

The central execution inventory checks their stable output. Documentation
tests check guide structure, source coverage, links, metadata, and navigation;
they do not replace feature tests for the behavior the example demonstrates.

## Where A Change Begins

| You need to change | Start with | Then inspect |
| --- | --- | --- |
| CLI option or dispatch | `prik/cli.py` | selected owner and CLI/user documentation |
| Source expansion or provenance | `prik/preprocessing/source.py` | parser-boundary tests |
| Fortran syntax fact | `prik/parsers/fortran/` | semantic converter if IR changes |
| Semantic `.pyi` syntax | `prik/parsers/pyi/parser.py` | `semantics/pyi2ir.py`, printer, and contract reference according to meaning |
| Stable IR/type fact | `prik/semantics/` | policy and downstream projections |
| Ownership, projection, setters, or support | `prik/policy/` | planning only to project a completed result |
| Plan representation or ordering | `prik/planning/` | binding/bridge consumers |
| Emitted native mechanism | narrow `prik/codegen/` owner | matching printer only if node representation changes |
| Formatting | matching `prik/printers/` module | golden-output tests |
| Artifact or compilation workflow | `prik/pipeline/build.py` | compiler service for argv mechanics |
| Runtime handle enforcement | `prik/runtime/handles.py` | policy first if permission or ownership is undecided |

For exact file ownership use the [source map](source-map.md). For a documented
feature's supported scope and evidence use the [feature-to-code map](feature-to-code-map.md).

## Contributor Documentation Structure

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
pages belong in Git history after their durable decisions have moved here.
