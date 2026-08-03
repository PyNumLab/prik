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
| `prik/` | Python package implementation. Start with [source-map.md](source-map.md) for entrypoints and [feature-to-code-map.md](feature-to-code-map.md) when starting from behavior. |
| `prik/contracts/` | Public semantic `.pyi` contract vocabulary imported directly by generated and edited contracts. |
| `prik/pipeline/` | Shared preprocessing, semantic `.pyi` loading, and high-level wrapper build orchestration. |
| `prik/probes/` | Compiler-derived target facts and target type mapping reports. |
| `prik/runtime/` | Python runtime objects used by generated extension modules. |
| `prik/types/` | Cross-layer mappings from resolved semantic types to Python ecosystem types. |
| `prik/parsers/` | Public namespace for language and semantic-contract frontends and parser models. |
| `prik/semantics/` | Semantic IR, source-to-IR conversion, `.pyi` parsing, and policy completion. |
| `prik/wrapper_codegen/` | Typed wrapper plans, direct native bridge/binding lowering, and source and semantic `.pyi` printers. |
| `prik/compiling/` | Native compile objects, compiler command orchestration, native support installation, and linking. |
| `prik/binding_support/` | Bundled header-only native support copied into generated wrapper builds. |
| `prik/naming/` | Unified public-name and generated-symbol policy. |
| `prik/utilities/` | Small shared Python utilities. |
| `examples/blas/` | Complete runnable Reference BLAS correctness project and the repository's single authoritative full BLAS source set under `native/`. |
| `examples/lapack/` | Complete Reference LAPACK build and SciPy-backed float64 correctness project, with the repository's single authoritative LAPACK implementation source set under `native/`. |
| `benchmarks/` | Local prik/f2py correctness and performance comparison harness. Benchmark sources and scripts are maintained; native builds and result files are generated locally. |
| `tools/generate_performance_docs.py` | Validates paired runtime and clean-build `pyperf` results and generates the bounded public Performance snapshot and both charts. |

The major source packages have local README files under `prik/` for
developers reading directly in the source tree. Those README files should link
back to the maintained source-navigation docs instead of old top-level docs.

Only `prik/__init__.py`, `prik/__main__.py`, and `prik/cli.py` live directly at
the package root. Public library symbols are deliberately flattened through
`prik/__init__.py`; internal modules are imported through their owning package.
The deliberate public submodule namespaces are `prik.contracts`, whose import
path is part of semantic `.pyi` syntax, and `prik.parsers`, which groups the
language-specific frontends. Stable convenience functions remain flattened
through `prik/__init__.py`.

## Tests

| Path | Purpose |
| --- | --- |
| `tests/architecture/` | Meta-tests for test-suite ownership, evidence-ledger integrity, collection, and bounded selections; language-specific meta-tests use a language subdirectory. |
| `tests/fortran/<feature>/` | User-visible Fortran and semantic `.pyi` behavior, with documented features directly below the language root and stages below each feature. |
| `tests/fortran/{source_parsing,source_preprocessing,command_line_interface,semantic_ir}/` | Public cross-feature capabilities that begin from source or expose an inspection/reporting surface. |
| `tests/fortran/infrastructure/` | Internal cross-feature policy, wrapper-generation, compiler, and runtime frameworks with no honest public-capability owner. |
| `tests/c/` | C input-language parsing, preprocessing, probe, semantic, CLI, and fixture evidence. |
| `tests/shared/` | Language-neutral product architecture, documentation, naming, tools, type mapping, and utility checks. |
| `examples/blas/tests/test_*.py` | User-facing real-library correctness documentation: explicit independent and PRIK/f2py differential validation for every Reference BLAS routine. |
| `examples/blas/ci/full_surface.py` | Maintainer-only complete BLAS export and smoke audit, selected explicitly by CI. |
| `examples/lapack/tests/test_*.py` | User-facing real-library correctness documentation: explicit independent and PRIK/SciPy/f2py validation for the reviewed double-precision routine inventory. |
| `examples/lapack/ci/full_surface.py` | Maintainer-only complete LAPACK export and smoke audit, selected explicitly by CI. |

<!-- PRIK_C_DOCS_START
| `tests/c/fixtures/parser/` | C parser-specific tests and fixture maintenance. |
PRIK_C_DOCS_END -->

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
- `prik/README.md` and package README files: local entry points for developers
  already browsing the source tree.
- `tests/shared/docs/test_structure.py`: mechanical coverage for the
  navigation pages and README links.
- `tests/shared/docs/test_publication.py`: fail-closed website publication, lane
  gating, navigation filtering, and repository-evidence link coverage.

## Generated And Fixture Areas

- `__prik__/` directories are wrapper build artifacts and should not be
  hand-edited as source.
- `benchmarks/build/f2py/` and `benchmarks/results/` contain generated
  comparison artifacts and are not repository sources. CI retains paired
  result files as workflow artifacts and generates the website snapshot from
  them without committing the raw files.
- Parser and `.pyi` fixture files should be regenerated with the documented
  fixture commands instead of edited loosely.
- `examples/blas/native/` is maintained source, not generated test output. The
  full-library and LAPACK integrations consume it directly rather than owning
  another BLAS copy.
- `examples/lapack/native/` is maintained Reference LAPACK implementation
  source, not generated test output. Upstream testing, timing, example, and
  matrix-generator programs are outside this ownership boundary.
- `prik.egg-info/`, caches, and benchmark output are generated local artifacts,
  not source ownership boundaries.

<!-- PRIK_C_DOCS_START
- Native Fortran sources and semantic `.pyi` contracts live below the feature
  or infrastructure test that owns their behavior. C fixtures remain below
  `tests/c/fixtures/`.
PRIK_C_DOCS_END -->
