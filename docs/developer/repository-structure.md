---
title: Repository Structure
audience: contributors
prerequisites: repository checkout
related: source-map.md, feature-to-code-map.md, build-system.md, testing-strategy.md
status: maintained
publication: draft
---

# Repository Structure

The repository is a Python project with native fixtures and generated wrapper
artifacts used by tests. Navigate by ownership boundary first, then by file.

## Source Tree

| Path | Purpose |
| --- | --- |
| `x2py/` | Python package implementation. Start with [source-map.md](source-map.md) for entrypoints and [feature-to-code-map.md](feature-to-code-map.md) when starting from behavior. |
| `x2py/contracts/` | Public semantic `.pyi` contract vocabulary imported directly by generated and edited contracts. |
| `x2py/pipeline/` | Shared preprocessing, semantic `.pyi` loading, and high-level wrapper build orchestration. |
| `x2py/probes/` | Compiler-derived target facts and target type mapping reports. |
| `x2py/runtime/` | Python runtime objects used by generated extension modules. |
| `x2py/types/` | Cross-layer mappings from resolved semantic types to Python ecosystem types. |
| `x2py/parsers/` | Public namespace for language and semantic-contract frontends and parser models. |
| `x2py/semantics/` | Semantic IR, source-to-IR conversion, `.pyi` parsing, and policy completion. |
| `x2py/wrapper_codegen/` | Typed wrapper plans, direct native bridge/binding lowering, and source and semantic `.pyi` printers. |
| `x2py/compiling/` | Native compile objects, compiler command orchestration, native support installation, and linking. |
| `x2py/binding_support/` | Bundled header-only native support copied into generated wrapper builds. |
| `x2py/naming/` | Unified public-name and generated-symbol policy. |
| `x2py/utilities/` | Small shared Python utilities. |
| `benchmarks/` | Local x2py/f2py correctness and performance comparison harness. Benchmark sources and scripts are maintained; native builds and result files are generated locally. |
| `tools/generate_performance_docs.py` | Validates paired runtime and clean-build `pyperf` results and generates the bounded public Performance snapshot and both charts. |

The major source packages have local README files under `x2py/` for
developers reading directly in the source tree. Those README files should link
back to the maintained source-navigation docs instead of old top-level docs.

Only `x2py/__init__.py`, `x2py/__main__.py`, and `x2py/cli.py` live directly at
the package root. Public library symbols are deliberately flattened through
`x2py/__init__.py`; internal modules are imported through their owning package.
The deliberate public submodule namespaces are `x2py.contracts`, whose import
path is part of semantic `.pyi` syntax, and `x2py.parsers`, which groups the
language-specific frontends. Stable convenience functions remain flattened
through `x2py/__init__.py`.

## Tests

| Path | Purpose |
| --- | --- |
| `tests/architecture/` | Meta-tests for test-suite ownership, evidence-ledger integrity, collection, and bounded selections; language-specific meta-tests use a language subdirectory. |
| `tests/fortran/<feature>/` | User-visible Fortran and semantic `.pyi` behavior, with documented features directly below the language root and stages below each feature. |
| `tests/fortran/{source_parsing,source_preprocessing,command_line_interface,semantic_ir}/` | Public cross-feature capabilities that begin from source or expose an inspection/reporting surface. |
| `tests/fortran/infrastructure/` | Internal cross-feature policy, wrapper-generation, compiler, and runtime frameworks with no honest public-capability owner. |
| `tests/c/` | C input-language parsing, preprocessing, probe, semantic, CLI, and fixture evidence. |
| `tests/shared/` | Language-neutral product architecture, documentation, naming, tools, type mapping, and utility checks. |

<!-- X2PY_C_DOCS_START
| `tests/c/fixtures/parser/` | C parser-specific tests and fixture maintenance. |
X2PY_C_DOCS_END -->

## Documentation

| Path | Purpose |
| --- | --- |
| `docs/index.md` | Documentation landing page. |
| `docs/user/` | Product workflows, examples, reference, support status, and troubleshooting. |
| `docs/developer/` | Contributor-facing workflows and source navigation. |
| `docs/old_docs/` | Archived pre-reorganization material. Do not link active docs here unless explicitly discussing history. |

## Source Navigation Contract

Source navigation is considered maintained when these files agree:

- [source-map.md](source-map.md): package ownership, hotspot index, and common
  change routes.
- [feature-to-code-map.md](feature-to-code-map.md): user-visible features to
  docs, implementation files, tests, and support evidence.
- `x2py/README.md` and package README files: local entry points for developers
  already browsing the source tree.
- `tests/shared/docs/test_structure.py`: mechanical coverage for the
  navigation pages and README links.
- `tests/shared/docs/test_publication.py`: fail-closed website publication, lane
  gating, navigation filtering, and repository-evidence link coverage.

## Generated And Fixture Areas

- `__x2py__/` directories are wrapper build artifacts and should not be
  hand-edited as source.
- `benchmarks/build/f2py/` and `benchmarks/results/` contain generated
  comparison artifacts and are not repository sources. CI retains paired
  result files as workflow artifacts and generates the website snapshot from
  them without committing the raw files.
- Parser and `.pyi` fixture files should be regenerated with the documented
  fixture commands instead of edited loosely.
- `x2py.egg-info/`, caches, and benchmark output are generated local artifacts,
  not source ownership boundaries.

<!-- X2PY_C_DOCS_START
- Native Fortran sources and semantic `.pyi` contracts live below the feature
  or infrastructure test that owns their behavior. C fixtures remain below
  `tests/c/fixtures/`.
X2PY_C_DOCS_END -->
