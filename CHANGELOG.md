# Changelog

This file is the canonical record of user-visible PRIK changes. Add changes to
**Unreleased** as they land, then move them into a versioned section during
release preparation. Versions use [Semantic Versioning](https://semver.org/);
release tags add a leading `v` to the package version.

## Unreleased

### Added

- Added `--assume-intent-in-scalars`, which treats a primitive scalar dummy
  that declares no `intent` as `intent(in)` instead of applying the
  conservative `intent(inout)` default. Fortran permits an undeclared dummy to
  be written, so prik returns its post-call value; for sources that predate the
  `intent` attribute this fills the Python return with unmodified controls, and
  reference BLAS `ddot` returns `(value, n, incx, incy)` rather than the value
  alone. With the option, that call returns `32.0`. The choice is made once in
  semantic conversion, where an absent `intent` is interpreted, so the build
  and `generate --pyi` describe the same Python surface. It is deliberately
  narrow: it covers the primitive and character scalars whose replacement is
  otherwise returned, a declared `intent` always wins, and arrays,
  derived-type objects, and allocatable or pointer scalars are unaffected. It is an
  assertion about the source rather than a fact derived from it — prik does not
  inspect the procedure body, so a procedure that does write such a dummy
  loses that value, exactly as removing the result from the generated contract
  by hand would. The option appears in the first `--help` screen because it
  changes the default Python surface, and every command that produces semantic
  IR accepts it — the build, `generate --pyi`, and `semantics`.
  `--build-manifest` rejects it along with the other saved wrapper settings,
  and a `.pyi` wrapper build rejects it because a contract already states its
  own results.

### Changed

- A scalar `character` dummy that declares no `intent` now uses the same
  conservative `intent(inout)` default as every other scalar, so the value the
  native procedure left behind is returned. It was silently assumed
  `intent(in)`, which meant a procedure that wrote to such a dummy lost that
  write with no diagnostic, while an `integer` dummy on the same call had its
  write returned. The exception was undocumented and untested; the strings
  guide already stated the uniform rule this change makes true. Wrapping
  fixed-form sources, where `intent` cannot be declared, therefore returns
  `(result, text)` where it previously returned `result` —
  `--assume-intent-in-scalars` restores the shorter surface and now covers
  character scalars along with primitive ones. An `allocatable` or `pointer`
  character scalar with no `intent` likewise now matches its numeric
  counterpart and returns a nullable snapshot; the option does not reach either
  one, because a snapshot is not a replacement value the caller supplied.

- Generated wrapper source is now readable. Each generated Fortran adapter and
  each CPython binding function carries a short leading comment naming what it
  is for — the native procedure an adapter wraps and the C symbol it exports,
  the Python callable a binding serves and the entrypoint it calls, and what a
  module accessor reads or writes — and an adapter additionally summarizes the
  conversions it performs. Generated Fortran modules also separate their
  procedures with a blank line instead of running them together. Comment prose
  is wrapped well inside the free-form 132-column limit, and each backend
  describes only its own plan facet, so the binding never names a Fortran
  symbol and the bridge never names a Python one.

### Fixed

- Declared-length `character` module arrays (`character(len=4), allocatable ::
  arr(:)`, and the `pointer` equivalent) no longer fail in the Fortran
  compiler. The generated descriptor-consumer interface and descriptor ABI
  parameter both spelled `character(len=:)` regardless of what the array
  declared, and an allocatable or pointer dummy accepts a deferred-length
  actual only when it declares one itself. Both now spell the declared width.
  A deferred-length `character(len=:), allocatable` module *array* still fails
  to compile under GNU Fortran 11.4 with an internal compiler error, which is a
  compiler defect rather than a wrapper contract.

### Added

- Every `character` module-variable form is now wrapped. Declared-length
  scalars are readable and writable as ordinary `str` properties, matching how
  numeric module variables already behave; a character value has no by-value C
  ABI, so the accessors copy through the same fixed-width buffer a character
  field already used, and assignment requires exactly the declared byte width
  rather than truncating or padding. `allocatable` and `pointer` scalars read
  as a detached `str`, or `None` when unallocated or unassociated, through the
  same nullable snapshot a descriptor numeric scalar uses, carrying the width
  the descriptor holds at the time of the read. `character` `parameter` arrays
  are copied once at import into a read-only fixed-width bytes array, the way
  numeric parameter arrays already were. Character module arrays report their
  own element width through their generated accessor rather than having it
  restated by the binding, so an assumed-length (`character(len=*)`) parameter
  array works too and takes the dtype width its initializer implied. An
  assumed-length scalar still keeps its rejecting setter, having no storage
  width to write into.

- Fixed-shape `character` module arrays with the `target` attribute now expose
  the same live fixed-width bytes view numeric module arrays already did, at
  any rank. The live-view lane rejected them only because it required a
  primitive numeric element type; a character element differs only in carrying
  its Fortran element length as the dtype width. Native writes appear in the
  view, and Python writes reach the storage Fortran reads. `target` is required
  here exactly as it already was for numeric module arrays.

- Pointer array handles now expose `deallocate()` without a `PointerPolicy`
  annotation, matching what allocatable handles already offered. Release stays
  manual and caller-driven — prik never frees a native target on its own, on
  garbage collection or otherwise — so this is the same responsibility a
  Fortran caller takes when writing `deallocate` for the same pointer.
  Previously a wrapped procedure that returned freshly allocated pointer
  storage leaked with no way to reclaim it from Python. `allocate` and `resize`
  still require `PointerPolicy`, because they establish a new target rather
  than releasing the one the handle already names.
- Added wrapper support for `allocatable` and `pointer` scalar `character`
  values in every direction: `intent(in)`, `intent(out)`, and `intent(inout)`
  arguments, and function results, at both deferred (`len=:`) and declared
  (`len=n`) length. Policy now completes the adapter-local storage each dummy
  needs — its attribute, its length, and who releases it — instead of always
  building a plain fixed-length temporary. The C ABI is unchanged: a scalar
  character argument still crosses as a byte buffer and a length whatever the
  dummy declares. Previously most of these forms either stopped at a policy
  diagnostic or reached the Fortran compiler and failed there with
  "Actual argument for 'x' must be ALLOCATABLE"; declared-length allocatable
  and pointer forms additionally failed plan validation.
- Added a character-length subscription to semantic `.pyi` contracts. The first
  subscription after `String` is always the length — `String[...]` assumed,
  `String[8]` or `String[n]` explicit, `String[:]` deferred — and an array adds
  its shape as a second subscription. Deferred-length scalars therefore have a
  contract spelling for the first time, so those procedures rebuild from their
  generated contract; the one-subscription array spellings the printer used to
  emit (`String[::]`, and `String[n]` for an extent) are replaced by
  `String[...][::]` and `String[...][n]`, which the parser had rejected or read
  as a scalar length.
- Added wrapper support for mutable scalar character descriptor arguments
  (`allocatable` or `pointer`, `intent(inout)`). The dummy stays a `str`
  argument and additionally returns the value the native procedure left behind,
  or `None` when it leaves the dummy unallocated or unassociated. Policy
  completes two decisions for the one dummy — a call-local character-buffer
  input and a nullable descriptor result — so the adapter copies back the local
  the native procedure may have replaced rather than the caller's buffer. A
  pointer dummy additionally records who releases the target the adapter
  allocated: the adapter frees it only while the dummy still identifies it, so
  storage the native procedure deallocated or replaced is left alone. The dummy
  spells as `Allocatable(Arg(i))` or `Pointer(Arg(i))` with `String[:]` or
  `String[n]` in a semantic `.pyi` contract, so these procedures also rebuild
  from their generated contract.
- Added wrapper support for `allocatable` scalar `character` function results.
  The adapter moves the result out through an allocatable dummy rather than
  assigning it, which makes allocation a testable fact, so an unallocated
  result becomes `None`. Other allocatable scalar function results remain
  blocked, because they have no such completed move.
- Added a native-entrypoint adoption roadmap for selective direct Fortran
  `bind(C)` calls and the initial direct-only C wrapper backend, including
  conservative starter-contract defaults for ambiguous C pointers.
- Added `@native_abi("c")` to semantic `.pyi` contracts so Fortran `bind(C)`
  procedures retain their ABI and optional link label through generated and
  source-free contract workflows.
- Added selective direct routing for policy-proved Fortran `bind(C)` procedures,
  including direct/mixed compiled feature fixtures and support-only generated
  Fortran artifacts where independent helpers remain necessary.
- Added a separate direct-entrypoint PRIK/f2py runtime and clean-build benchmark
  cohort with untimed correctness, generated-source membership, and linked
  direct-symbol preflight, plus an ordinary-Fortran PRIK control.

### Changed

- Made nested semantic classes use the same complete planning and backend-symbol
  allocation path as top-level classes.
- Published the maintained-run direct-entrypoint runtime, adapter-control, and
  clean-build results separately from the normal-interface benchmark cohort.
- Made direct-entrypoint benchmark preflight identify binding and native
  objects by their inspected symbol relationships across f2py build backends.
- Reduced exact numeric-scalar call overhead by using typed NumPy scalar
  payload access and result allocation while preserving strict dtype checking
  and exact NumPy result types.
- Separated wrapper plans into strict binding, shared native-entrypoint, and
  Fortran-adapter facets, with planner-owned generated support procedure
  entrypoints for accessors, lifecycles, descriptors, and callbacks, without
  changing generated wrappers.
- Build manifest schema 3 records physical generated sources and separate
  adapter/support membership, including zero-generated-native builds.

## 0.3.0 — 2026-08-14

### Added

- Reorganized contributor documentation around a concise architecture guide
  and one canonical page per production package, with local structures,
  important objects, runnable examples, expected outputs, test owners, change
  routes, and invariants.
- Consolidated contributor workflows and removed nonessential concept and
  design drafts, TODO-only pages, duplicate architecture maps, and completed
  migration ledgers.
- Added the persistent Zenodo all-versions DOI badge and citation links to the
  README and About page.
- Included the repository's machine-readable `CITATION.cff` metadata in source
  distributions.

### Changed

- Marked the contributor Architecture and Codebase Map as reviewed for
  publication; the renamed map now focuses on package and cross-stage module
  ownership.
- Clarified the Feature-to-Code Map as the capability-to-owner and evidence
  index, linking reviewed user documentation and retaining only planned
  contributor-documentation paths before their review.
- Revised the Feature-to-Code Map with reviewed package-guide links,
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
- Made every expandable documentation-sidebar section label open its first
  published page, including through nested sections, while the adjacent **+**
  control only expands or collapses it.
- Made documentation tables wrap readable cell content instead of hiding
  later columns behind unnecessary horizontal scrolling.
- Added accessible two-, three-, and four-view example tabs to the User Guide;
  Getting Started remains linear and example results stay visible.
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
- Made the architecture build-path diagram keyboard-accessible and linked each
  route and stage to its reviewed component guide.
- Added accessible explanations for `.pyi`, f2py `.pyf`, ABI, semantic IR,
  array order, and the GIL throughout User Documentation and on the Home page,
  plus per-stage detail panels to the architecture diagram.
- Changed the site-wide repository control into a “★ Star on GitHub” call to
  action while preserving its repository destination.
- Published concise Contracts, Naming, Runtime, and Utilities component guides,
  restored their architecture links, corrected the diagram fallback, and
  clarified the NumPy result type in the architecture example.
- Made numeric scalar results consistently preserve their exact NumPy types;
  Boolean scalar results remain Python `bool` values.
- Corrected user documentation to distinguish numeric and Boolean scalar
  boundaries, and aligned the Getting Started route with normal package
  installation rather than a repository checkout.
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

- Corrected README licensing wording to refer to bundled native-support files
  rather than the removed package-root `binding_support/` path.
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
