# Changelog

This file is the canonical record of user-visible PRIK changes. Add changes to
**Unreleased** as they land, then move them into a versioned section during
release preparation. Versions use [Semantic Versioning](https://semver.org/);
release tags add a leading `v` to the package version.

## Unreleased

### Added

- Reorganized contributor documentation around a concise architecture guide
  and one canonical page per production package, with local structures,
  important objects, runnable examples, expected outputs, test owners, change
  routes, and invariants.
- Consolidated contributor workflows and removed nonessential concept and
  design drafts, TODO-only pages, duplicate architecture maps, and completed
  migration ledgers.
- Added Zenodo version and concept DOI links to the citation metadata, README,
  and About page.

### Changed

- Marked the contributor Architecture and Codebase Map as reviewed for
  publication; the renamed map now focuses on package and cross-stage module
  ownership.
- Clarified the Feature-to-Code Map as the capability-to-owner and evidence
  index, linking reviewed user documentation and retaining only planned
  contributor-documentation paths before their review.
- Revised the Feature-to-Code Map with visible draft documentation markers,
  stage-ordered change routes, narrower focused evidence, and separate array,
  callback, and error routes.
- Condensed the contributor Testing Strategy around test ownership, stage
  evidence, stable contracts, end-to-end evidence, fixture placement, and
  verification scope.
- Clarified contributor workflows for changing PRIK, local verification, pull
  request checks, and documentation maintenance.
- Linked the Contributing workflow to the Feature-to-Code Map and Testing
  Strategy, explained its pre-push hook setup, and normalized its editable
  checkout test commands.
- Clarified that pull-request validation requires the performance benchmark and
  identified its workflow implementation.
- Renamed the Package Guides section to Architecture Components and grouped its
  build stages separately from its supporting components, distinguishing
  cross-build pipeline orchestration from sequential stages.
- Ordered the Developer Documentation sidebar by the architecture reading path,
  with build stages before supporting components.
- Reviewed the Pipeline Component guide around the source-build handoff,
  independent contract and inspection workflows, and build-result ownership.
- Reviewed the Preprocessing Stage guide around its Fortran source route,
  compiler-derived target probes, module navigation, and executable examples.
- Reviewed the Parsing Stage guide around its Fortran and semantic-`.pyi`
  algorithms, source-level navigation, executable examples, and ownership
  boundaries.
- Reviewed the Semantics Stage guide around its shared IR, frontend-conversion
  algorithms, raw contract facts, executable examples, and policy boundary.
- Reviewed the Policy Stage guide around ordered policy completion, immutable
  interoperability decisions, module algorithms, executable examples, and the
  planning boundary.
- Reviewed the Planning Stage guide around deterministic policy projection,
  editable plan ownership, module algorithms, executable examples, and the
  generator freeze boundary.
- Reviewed the Code Generation Stage guide around its generator handoff,
  backend lowering algorithms, plan-only decisions, executable examples, and
  focused evidence.
- Reviewed the Printing Stage guide around representation-specific traversal,
  safe source formatting, isolated `.pyi` emission, executable examples, and
  focused evidence.
- Reviewed the Compiler Stage guide around coherent toolchain selection,
  explicit command construction, conditional native-support installation,
  executable examples, and focused evidence.
- Added focused C Binding and Fortran Bridge lowering guides with executable
  manually constructed plans and printed backend-source examples.
- Moved binding and bridge algorithms and rendered-source demonstrations out
  of the Code Generation overview and into their focused lowering guides.
- Explained each reviewed package-guide execution example in terms of its
  in-memory setup and the stage boundary established by its output.
- Added Pipeline Component and source-level navigation for contract loading,
  wrapper generation, build-manifest replay, and `build.py` orchestration.
- Removed empty package-marker entries from the Pipeline Component and Compiler
  Stage guides.
- Added a brief Developer Documentation overview that routes readers to
  Architecture, then Architecture Components, and linked it from the website
  home page.
- Replaced the contributor architecture's text-only build path with a rendered
  diagram of its two input routes and shared pipeline.
- Reduced documentation tests to enforce publication, link integrity,
  executable examples, and public-reference contracts without freezing prose,
  headings, page inventories, private names, or source-tree layout.
- Reclassified implementation-structure and codegen-complexity checks as
  contributor recommendations, while retaining hard behavioral, safety, ABI,
  publication, and architectural-boundary contracts.
- Moved contributor package-guide execution checks into the documentation
  suite, using each guide's displayed result instead of a duplicate exact-
  output inventory.
- Reduced the root `prik` API to its version and normal-user build entrypoints;
  parser, semantic, probe, runtime, and planning tools now use their owning
  package import paths.
- Moved stage-record freezing from `prik.stage_values` to
  `prik.utilities.stage_values`; the root module path was removed.
- Made `prik` an import-only package boundary by removing its direct-script
  demonstration; command and stage-value examples remain available from their
  owning modules.
- Expanded the contributor architecture and package guides with concrete stage
  handoffs, runnable example results, focused test purposes, and change routes.
- Moved generated documentation and distribution output under the hidden
  `.artifacts/` directory in local commands and CI workflows.
- Consolidated developer and maintainer material under one Contributor
  Documentation tree and removed the separate maintainer documentation lane.
- Moved the bundled header-only binding runtime from the package root into
  `prik.runtime.native_support`; generated builds continue to receive it under
  their internal `binding_support/` include directory.
- Deferred the contributor architecture sections for the immature C input
  parser and C-to-IR path while retaining the generated CPython C binding
  backend documentation required by Fortran wrappers.
- Reorganized compiler and pre-parse infrastructure into `prik.compiler` and
  `prik.preprocessing`, including C/Fortran preprocessing and target probes;
  the former `prik.compiling`, `prik.probes`, parser-local C preprocessor, and
  pipeline-local preprocessing import paths were removed.
- Replaced the public semantic-to-NumPy helper API with stage-owned semantic,
  contract-runtime, and code-generation datatype catalogues.
- Separated post-IR policy and wrapper planning into `prik.policy` and
  `prik.planning`; code generation now renders plan-driven docstrings, and the
  former maintainer import paths were removed.
- Added a top-level language-printer package for C, Fortran, and semantic
  `.pyi` output, and made `pipeline.wrapper.WrapperGenerator` the single
  plan-to-rendered-wrapper orchestration boundary.
- Documented the completed ownership vocabulary, lifetime-policy philosophy,
  pointer-policy boundary, and maintainer change routes in one maintained
  architecture reference.
- Moved exact overload selection from generated Python predicate chains to
  generated C dispatchers with planned candidate IDs and direct switch-based
  calls to the selected existing wrapper.
- Stopped standalone Fortran parser discovery from descending into inaccessible
  procedure-internal subprograms; procedure-local callback interfaces remain
  classified and discoverable.
- Made directory project parsing read and parse each discovered Fortran file
  once before dependency ordering and project assembly.

### Fixed

- Unified source-level compile-time resolution across project and CLI parsing
  so imported and host-associated kind facts also reach derived-type fields.

## 0.2.1 — 2026-08-11

### Added

- Added machine-readable citation metadata through the repository-root
  `CITATION.cff` file.
- Added an About page and public development disclosure covering PRIK's
  motivation, design principles, stewardship, and use of AI-assisted tools.

### Fixed

- Removed the stale `0.1.x` qualifier from the README and website alpha-status
  wording after the `0.2.0` release.

## 0.2.0 — 2026-08-10

### Added

- Added maintained FFTPACK and MINPACK examples built from the upstream
  fortran-lang projects. Their build scripts, user guides, and numerical tests
  cover all 31 FFTPACK and 22 MINPACK public procedures.
- Added Python-owned, read-only NumPy snapshots for supported public Fortran
  parameter arrays, including MINPACK's `dpmpar` constants.
- Added declaration-expression support for richer arithmetic, comparisons,
  conditionals, array inquiries, and local, imported, or standalone
  specification functions, including native-dependent result extents.
- Added exact NumPy Boolean-array conversion for compiler-measured 8-, 16-,
  32-, and 64-bit Fortran logical kinds, with canonical writeback.
- Added `WrapperBuildResult.import_module()` to load a generated extension
  explicitly without changing `sys.path`.

### Changed

- Moved documentation and maintainer-tool tests to `tests/docs/` and
  `tests/tools/`, removed the generic `tests/shared/` bucket, and mirrored
  internal tests by production package with narrower support helpers; removed
  recursive layout-policing tests that froze maintainer organization, retaining
  exceptional release safety under `tests/workflows/`. The maintainer-tool and
  workflow-safety suites, blocking static analysis, and focused documentation
  smoke checks now also run through the repository's tracked pre-push hook,
  together with one compiled scalar-wrapper smoke test, for earlier local
  feedback while remaining enforced by GitHub Actions.
- Simplified the documented DGESV validation and the LAPACK test suite to use
  explicit NumPy Fortran-order copies, with documented numerical-test helper
  conventions.
- Aligned the documented MINPACK `hybrd1` callback example with its runnable
  test, made it verify callback invocation, and made its test problems
  self-contained; FFTPACK workspace initializer tests now validate a paired
  transform against NumPy or SciPy.
- Renamed the developer-facing wrapper generation package from
  `prik.wrapper_codegen` to `prik.codegen`; the old import path was removed.
- Expanded public interface resolution so implemented unnamed interfaces and
  public generics can be wrapped without exposing private implementation
  procedures.
- Expanded the Real Libraries CI lane to build and test BLAS, LAPACK, FFTPACK,
  and MINPACK, with cached native BLAS and LAPACK builds where available.
- Made performance comparisons faster and less order-sensitive with balanced
  A/B/B/A runtime measurements, merged samples, smaller worker budgets, and
  four measured clean builds after warm-up.
- Refreshed the README and website around the canonical
  **PRIK — Python Runtime Interop Kit** identity, with a concise FAQ, a fair
  PRIK-versus-f2py guide, clearer array guidance, and searchable real-library
  examples, including a four-library capability and validation summary, a
  concise statement of current limitations, and a derived-type inheritance
  walkthrough.
- Hardened preprocessing, compiler-derived type probes, semantic policy
  completion, and multi-source build reporting so unsupported contracts fail
  earlier with clearer diagnostics.

### Fixed

- Preserved authoritative public interface signatures when linked legacy
  implementations use different internal storage declarations, including
  FFTPACK's `zfftf` complex-array interface.
- Corrected SciPy reference inputs for the LAPACK `dstemr` and `dstebz` tests
  and strengthened BLAS and LAPACK routine validation with independent
  mathematical expectations.

## 0.1.1 — 2026-08-03

- Update README and CONTRIBUTING
- Change the Description section and add more tags


## 0.1.0 — 2026-08-03

- First public release under the PRIK name.
- Build importable Python extensions from supported Fortran sources.
- Generate, inspect, edit, and rebuild from semantic `.pyi` contracts.
- Expose the `prik` console command and the equivalent `python -m prik`
  module command.
- Report the installed release through `prik --version` and
  `prik.__version__`.
- Added a complete runnable Reference BLAS correctness example covering all 155
  discovered routines through PRIK, independent mathematical expectations, and
  f2py differential comparisons.
- Moved the repository's authoritative Reference BLAS sources to
  `examples/blas/native/` for shared use by the example, integration tests,
  LAPACK CI build, and build comparison tooling.
- Added a complete Reference LAPACK build and correctness project. It wraps all
  2,062 implementation sources once and explicitly validates the reviewed 127
  SciPy 1.18.0 double-precision real routines against independent mathematical
  invariants and f2py comparisons in the dedicated CI lane.
- Moved the repository's authoritative Reference LAPACK implementation sources
  to `examples/lapack/native/` and updated full-library integration and CI to
  consume that single source owner alongside `examples/blas/native/`.
- Fixed dependency-safe Python argument conversion ordering for wrappers whose
  array extents depend on later native scalar arguments, including padded BLAS
  leading dimensions.
