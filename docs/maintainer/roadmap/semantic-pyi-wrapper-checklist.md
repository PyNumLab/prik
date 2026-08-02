---
title: Semantic .pyi Wrapper Checklist
audience: maintainers
prerequisites: semantic .pyi format, Fortran wrapper reference
related: ../../user/reference/semantic-pyi-format.md, index.md
status: active-roadmap
publication: draft
---

# Semantic `.pyi` Wrapper Checklist

This checklist tracks the path from semantic `.pyi` files to a fully editable
wrapper contract. A `.pyi` file may be generated from source as a starter
contract or written by the user directly. After that point the `.pyi` file is
the source of truth for the Python wrapper API.

Every `.pyi` wrapper build accepts exactly one entry contract. That entry may
import any number of module leaves or contract fragments through relative
imports. Imported files are discovered recursively; they are not additional
CLI or Python API inputs. Multiple positional `.pyi` inputs and contract
directories are intentionally unsupported.

The end state is that every runtime scenario covered by `tests/wrapper` is
exercised through three build paths:

1. **Source path**: build directly from one or more ordered Fortran sources.
2. **Generated-contract path**: generate the module-aligned `.pyi` files from
   those sources with `--pyi`, then build from the unmodified `.pyi` files plus
   native artifacts. This path must expose the same Python API and runtime
   behavior as the source path.
3. **Modified-contract path**: copy or extend the generated `.pyi` files with
   user-authored visibility, validation, ownership, lifetime, error, or other
   wrapper contracts, then build from the modified `.pyi` files plus the same
   native artifacts. This path must apply the documented edits while preserving
   unaffected behavior.

Equivalence means the same public API and observable runtime behavior; generated
extension binaries are not required to be byte-for-byte identical. Native
source is optional in the second and third paths. Tests may use source to create
the baseline `.pyi` and native artifacts, but `.pyi`-driven wrapper generation
must not reparse source to reconstruct the Python API.

Native implementation sources may still be supplied explicitly as build inputs.
In that mode prik compiles them without using them as a semantic input: the
entry `.pyi` remains the sole source of truth for the Python API. Precompiled
objects and libraries remain supported and may be mixed with native sources in
one extension-level native build plan.

The remaining work is centralized below in implementation order. Complete each
stage and its focused runtime evidence before starting the next stage. When an
item is complete, move its checked acceptance criterion to the completed
evidence section instead of leaving completed and incomplete work interleaved.

## Remaining implementation queue

Only unfinished work belongs in this section. When a new editable-contract gap
is found, add it here with the exact missing runtime fixture, diagnostic, or
policy-dispatch evidence before starting implementation.

### Callback Adapter Policy Contracts

Callbacks are the inverse of wrapped procedures: Fortran calls the generated
adapter, the adapter converts Fortran arguments into Python objects, Python
executes the callable, and the adapter converts Python results or mutations
back to Fortran. Future callback contract work should make that adapter policy
explicit through named `@prototype` declarations without turning ordinary
Python-facing argument annotations into callback projection syntax.

- [ ] Define callback-specific policy metadata for copy-in, copy-out,
  borrowed-view, zero-copy, dtype conversion, fixed-length character writeback,
  ownership, lifetime, and result/error conversion.
- [ ] Preserve callback argument order and Fortran value/reference/storage
  shape as the callback interface contract; do not add argument reordering,
  hidden native-call projection, or Python convenience mapping unless a later
  design proves it is necessary.
- [ ] Add runtime fixtures and generated `.pyi` parity evidence for each
  supported callback policy shape before moving it to completed evidence.

## Completed evidence

### Barrier Policy Split And Model Visitor Dispatch

Python-extension extraction and native handoff are separate completed policy actions.
Policy completion records a Python barrier action and a native barrier action
on each `OwnershipDecision` before wrapper planning. Python binding generation
dispatches from the Python barrier action; the native bridge dispatches
argument handoff from the native barrier action.

- [x] Python barrier actions cover scalar value, rank-0 scalar storage, NumPy
  array storage, Python string value, raw address value, and generated wrapper
  instance extraction.
- [x] Native barrier actions cover direct value, call-local address, storage
  address, raw address, packed array descriptor, and wrapper native-address
  handoff.
- [x] Bridge and binding argument routers no longer infer barrier policy from
  datatype, `intent`, `is_alias`, local memory checks, or
  `fortran_array_category`; the remaining category field is ABI metadata.
- [x] Parser grammar units, parser-model converters, `.pyi` AST conversion,
  semantic lowering, bridges, bindings, and printers now share
  `prik.utilities.visitor.ClassVisitor` and configured `<prefix>_<ClassName>` handlers
  instead of parallel visitor implementations or local `isinstance` dispatch
  ladders.
- [x] Structural evidence lives in `tests/architecture/test_visitor_protocol.py`
  and `tests/semantics/policy/`; runtime evidence covers scalar
  value/address projection, rank-0 scalar storage, arrays, strings, raw
  addresses, and wrapper instances through focused `tests/wrapper/fortran/`
  slices.

### Stage 1 — Searchable Test Layout, Contract Output, And Fixtures

Runtime wrapper tests are organized by stable subjects under
`tests/wrapper/fortran/`: `build_from_source/`, `build_from_pyi/`,
`multiple_files/`, `external_routines/`, `real_libraries/`,
`edit_pyi_contracts/`, `arrays/`, `scalars/`, `function_calls/`,
`strings/`, `derived_types/`, `callbacks/`, `module_state/`,
`runtime_behavior/`, `naming/`, and `layout_rules/`.

- [x] Wrapper test modules live under the stable subject directories above,
  using descriptive filenames and subject README files. The index is
  `tests/wrapper/fortran/README.md`.
- [x] Native wrapper source fixtures live under shared `tests/data/fortran/`
  corpora: ordinary wrapper fixtures use `tests/data/fortran/wrapper/`, and
  real-library evidence reads `examples/blas/native/` and
  `examples/lapack/native/` directly. The wrapper test tree contains no
  Fortran source files.
- [x] Runtime wrapper tests resolve native fixtures through
  `tests/wrapper/fortran/_support.py`, so moved tests no longer depend on
  colocated source fixtures.
- [x] Runtime `.pyi` contracts stay under the consuming subject's
  `contracts/<case>/` tree. Current checked fixtures include
  `build_from_pyi/contracts/runtime_abi/fruntime_abi_f90.pyi`,
  `build_from_pyi/modified_contracts/basic_subroutine/flatten_m1.pyi`,
  `build_from_pyi/modified_contracts/basic_subroutine/alias_increment.pyi`,
  and
  `tests/fortran/semantic_pyi_format/pipeline/fixtures/invalid/projection_metadata/incomplete_native_call.pyi`.
- [x] Generated `.pyi` packages are checked fixtures. Runtime wrapper contract
  packages live under
  `tests/wrapper/fortran/<subject>/contracts/<case>/`; explicit
  `--pyi --out` package-shape fixtures that do not compile wrappers live under
  `tests/fortran/semantic_pyi_format/pipeline/fixtures/contracts/`.
  Refresh is explicit through
  `WRAPPER_UPDATE_PYI_FIXTURES=1`.
- [x] Modified runtime fixtures use `.pyi`, record their intentional difference
  in the fixture text, and have runtime assertions for both the changed export
  contract and unaffected native behavior.
- [x] `.py` files are rejected as semantic `.pyi` contract inputs by the Python
  API.
- [x] The reviewed packages under
  `tests/fortran/semantic_pyi_format/pipeline/fixtures/contracts/`
  are the canonical exact `.pyi` generation-regression corpus and are not used
  as edited runtime contracts.
- [x] Explicit Fortran `--pyi --out` package-shape fixtures that do not compile
  runtime wrappers live under the owning semantic-format feature's `pipeline/`
  fixture tree.
- [x] `tests/wrapper/CHECKLIST_COVERAGE.md` maps roadmap subjects to exact test
  paths.
- [x] `tests/wrapper/fortran/layout_rules/test_wrapper_guide_layout.py`
  enforces the subject tree, README fields, checklist routing, shared native
  fixture data, runtime contract placement, and stale-path rejection.
- [x] Explicit Fortran `--pyi --out` output writes contract packages and rejects
  ambiguous single-file `.pyi` targets so the one-module-per-file rule is
  preserved.

### Stage 2 — Structured Native Build Model

`WrapperBuildResult.native_build_plan` records the extension-level native
implementation build plan separately from semantic `sources`.

- [x] The build result records one structured, extension-level native build plan
  separately from semantic contract paths. The plan distinguishes native
  compilation units, produced objects, prebuilt artifacts, module/include
  directories, library directories, and ordered link items instead of flattening
  them into strings.
- [x] One ordered native-link representation preserves interleaving across
  objects, archives, direct shared libraries, named libraries, and explicit
  linker arguments instead of grouping inputs in a way that changes linker
  semantics.
- [x] Source-driven wrapper builds record caller-supplied native source
  compilation units, produced objects, module/include directories, and object
  link items in `NativeBuildPlan`.
- [x] `.pyi` wrapper builds record semantic contract paths in `sources` and
  caller-supplied native artifacts, include/module directories, library
  directories, and ordered link items in `NativeBuildPlan`.
- [x] The lower compiler object dependency model preserves caller order for
  native object inputs instead of converting them through an unordered set.
- [x] Documentation explains the native build plan with five examples covering
  source builds, `.pyi` object builds, object/archive ordering, direct shared
  libraries, and explicit linker-argument representation.

### Stage 3 — Multi-Source Combined Contract Generation

Explicit Fortran `--pyi --out PATH` now treats `PATH` as the generated contract
package itself. The package entry is `PATH/__init__.pyi`; native module leaves
sit directly under `PATH`.

- [x] Source, generated-contract, and modified-contract parity builds use the
  same extension name and native namespace structure. Only documented Python
  export policy or wrapper contracts may differ.
- [x] Multiple ordered native sources generate one combined contract package
  without losing native imports, dependency objects, cross-module types, source
  order, link order, or extension identity.
- [x] The requested output directory is the contract package itself. It contains
  one `__init__.pyi` entry and one flat `<fortran-module>.pyi` leaf per native
  module; generation adds neither a `combined_extensions/` directory nor
  per-source subdirectories.
- [x] For two ordered sources that each define two native modules,
  `--pyi --out contracts` writes four module leaves directly under `contracts/`
  plus `contracts/__init__.pyi`. The entry imports all four leaves and is the
  sole wrapper input. With no external dependency stubs, these are the only five
  generated contract files.
- [x] Runtime evidence covers source, generated-contract, and modified-entry
  builds for the same two-source package. The generated and modified builds use
  the same extension name as the source build, preserve child module namespaces,
  and link native objects in caller order.
- [x] Documentation explains the combined package behavior with five examples
  covering single-source packages, two-source/four-module packages,
  source-free wrapper builds, Python API parity builds, and modified entry
  export policy.

### Stage 4 — Shared Parity Harness And Standalone Procedures

Standalone external procedure parity now lives in
`tests/wrapper/fortran/external_routines/test_external_procedures.py`. Generated
external-only contract bundles keep one compact entry `.pyi`; native sources,
objects, archives, and libraries remain separate build-plan facts.

- [x] Standalone parity tests use the shared `source` / `generated-pyi`
  parametrized fixture shape, so fixed-form, free-form, and multi-procedure
  external cases share one assertion body per behavior.
- [x] Source-only and generated-`.pyi`-only checks are limited to path-specific
  properties such as exact generated contract text, bridge-source inspection,
  and validation-before-codegen failures.
- [x] One fixed-form source containing one standalone procedure generates a
  non-empty root fragment with `@external` and rebuilds equivalently.
- [x] One free-form source containing one standalone procedure has the same
  `@external` generation and runtime parity.
- [x] One source containing several standalone procedures generates external
  declarations for all of them and exposes each at the extension root.
- [x] Several file-level BLAS/LAPACK-style standalone sources can generate one
  compact entry `.pyi` containing all external declarations while the native
  build plan links the separated objects in caller order.
- [x] `@external` makes the bridge emit a completed implicit `external`
  declaration or a required explicit interface and no module `use`; a module
  procedure makes the bridge emit the correct `use <module>`.
- [x] `@external` composes with `@bind("native_name")`: the native external is
  called while the wrapper declaration and root export may use different names.
- [x] A handwritten external `.pyi` plus native artifacts builds without source
  and follows the same placement, binding, validation, and export rules.
- [x] Removing `@external` from a generated package-entry declaration or adding
  it to a declaration inside a child-namespace module contract fails during
  validation before wrapper code generation.

### Stage 5 — Full Generated-Contract Runtime Parity

- [x] Function-call parity covers optional arguments, hidden output arguments,
  projected return ordering, nullable allocatable copy returns, and validation
  failures in both `source` and `generated-pyi` modes through shared assertion
  bodies. Generated `.pyi` builds clear Fortran `optional` attributes from
  bridge-local result temporaries while preserving Python `None` behavior for
  unallocated allocatables.
- [x] Array parity covers dtype, rank, shape, order, stride, lower-bound,
  writeability, byte-order, alignment, zero-extent validation, multidimensional
  order/stride checks, assumed-rank runtime dispatch up to the supported rank
  boundary, and Python-owned array results in both `source` and `generated-pyi`
  modes through shared assertion bodies.
- [x] Character parity covers fixed-length buffers, assumed-length strings,
  deferred character results, copy-in/copy-out for mutable strings, optional
  character arguments, Unicode round-trips, and embedded-NUL validation in both
  `source` and `generated-pyi` modes. `.pyi` parser regressions keep visible
  inout projected returns visible while preserving explicit output-only
  projection.
- [x] Derived-type parity covers fields, methods, type-bound root target
  procedures, default/keyword constructors, finalizers, borrowed child
  lifetime, scalar object boundaries, inheritance, polymorphic dispatch, and
  pointer handle planning errors in both `source` and `generated-pyi` modes.
  `.pyi` parser regressions restore type-bound target metadata from class method
  declarations.
- [x] Callback parity covers scalar, array, and derived callback conversions,
  call-scoped callback lifetime, GIL entry handling, reference cleanup, and
  callback exception abort behavior in both `source` and `generated-pyi` modes.
  `.pyi` parser regressions infer callback dimension argument names so callback
  array result shapes remain explicit.
- [x] Module-state parity covers scalar module attributes, parameter behavior,
  saved native state shared across imports, allocatable module and derived-type
  borrowed views, allocatable replacement/copy-return ownership, nullability,
  and common-block encapsulation in both `source` and `generated-pyi` modes.
- [x] Runtime behavior parity covers recursive native calls in both `source`
  and `generated-pyi` modes, plus edited `.pyi` runtime policy decorators for
  `@hold_gil` and `@raises(...)` using native object builds. OpenMP remains
  source/makefile evidence; Stage 6 now provides the `.pyi`
  makefile/native-flag surface needed for future OpenMP-specific `.pyi`
  evidence.
- [x] Naming and generic-interface parity covers public-name normalization,
  visibility filtering, keyword/collision policy, public generic dispatch,
  type-bound binding names, defined operators, comparisons, named operators,
  and assignment behavior in both `source` and `generated-pyi` modes.
  `.pyi` regressions keep class/member name reservations scoped separately,
  import public native generics instead of private specific procedures, and
  preserve keyword-normalized type-bound binding names.

<!-- PRIK_C_DOCS_START
- [x] The verified scalar baseline and legacy/F90 fmath array baseline run in
  both `source` and `generated-pyi` modes through the same assertion bodies.
  The generated contracts are compared against checked fixtures, the `.pyi`
  build links only explicit native objects, and generated contracts encode
  normalized Python public names with `@bind(...)` when the native Fortran name
  differs. Scalar-kind, enum-like constant, `value`, and existing `bind(C)`
  ABI cases also run from generated contracts with the same runtime assertions.
PRIK_C_DOCS_END -->

### Stage 6 — Replayable JSON, Native Compilation, And Makefiles

Runtime evidence lives in
`tests/fortran/building_shared_library/pipeline/test_pyi_build_modes.py`,
`tests/fortran/semantic_pyi_format/end_to_end/`, and CLI surface
evidence lives in `tests/cli/`.

- [x] Python API `.pyi` builds accept output directory, extension naming,
  Makefile, verbose, and strict-wrapper-name controls. `--makefile` and
  `--verbose` remain mutually exclusive.
- [x] Semantic `.pyi` build JSON includes a schema-versioned replay `manifest`
  with the entry contract, recursively discovered contract paths, extension
  identity, output policy, compiler configuration, native compilation units,
  and ordered native link plan as separate fields. Manifest-relative paths are
  resolved relative to the manifest during replay.
- [x] Grouped or repeated `--native-fortran-sources` inputs compile native
  implementation sources in caller order without using them to reconstruct the
  Python API. Produced objects and module files are recorded in
  `NativeBuildPlan` and used by the extension link.
- [x] Grouped or repeated `--native-compile-flags` inputs are recorded in the
  manifest and in each native compilation unit while prik still emits its
  required compiler flags, including position-independent code.
- [x] Native sources, prebuilt objects, archives, direct shared libraries, named
  libraries, and ordered native link items can be mixed without changing the
  `.pyi`-defined Python API or reparsing native implementation sources.
- [x] `.pyi --makefile --json` writes `<out-dir>/prik-build.json` and
  `<out-dir>/Makefile.prik`; JSON output reports both artifacts and the
  normalized manifest.
- [x] `--build-manifest PATH` validates and executes a saved manifest, and
  `--build-manifest PATH --makefile` regenerates `Makefile.prik`
  without positional contracts or repeated native flags.
- [x] `Makefile.prik` tracks the manifest, complete `.pyi` graph, native
  implementation inputs, compile outputs, and link target while preserving
  source compile order and native link order.
- [x] `--native-link-item` supports grouped or repeated ordered explicit linker
  arguments, including linker groups around objects or archives and repeated
  path items.
- [x] Runtime shared-library lookup is recorded through `native_library_dirs`
  and direct shared-library parent directories in the native build plan.

### Stage 7 — Library-Scale And Mixed-Bundle Evidence

Real BLAS/LAPACK artifact-shape evidence lives in
`tests/fortran/building_shared_library/end_to_end/real_libraries/test_full_libraries.py`. Native
bundle, order, transitive-library, and failure-path evidence lives in
`tests/fortran/building_shared_library/end_to_end/test_native_bundles.py`.

- [x] Full real BLAS and LAPACK source corpora under `examples/blas/native/`
  and `examples/lapack/native/`
  each generate an importable intermediate contract package inside the pytest
  temporary directory.
- [x] The full generated BLAS and LAPACK contracts are audited dynamically for
  root procedure counts, sentinel declarations, source-stem coverage, known
  helper declarations, imported symbols, and representative runtime behavior.
  Real-library evidence keeps no checked generated `.pyi`, edited `.pyi`, or
  source-free replay fixture.
- [x] The full-library evidence builds each full root procedure contract with
  `build_pyi_extension`, links it against a cached full native shared library,
  imports every generated root procedure through the normalized Python names,
  and checks that source stems and known generated helper declarations line up
  with the shared native corpora.
- [x] Full native BLAS/LAPACK object files are compiled once into a deterministic
  `.pytest_cache/prik/real-library-native` cache, archived once, and linked once
  into the shared libraries reused by repeated wrapper test runs; CI can move
  the cache with `PRIK_REAL_LIBRARY_NATIVE_CACHE_DIR`, and cold object builds
  compile independent sources in parallel after required module sources.
- [x] Selected runtime smoke calls run against the fully wrapped BLAS/LAPACK
  modules and check NumPy-style behavior for `daxpy`, `ddot`, `dasum`, `dscal`,
  and `dlamrg`.
- [x] Several contracts imported by one entry resolve from one static archive
  and one direct shared library while preserving child module namespaces.
- [x] Module procedures build with separately supplied `.mod` directories, while
  standalone `@external` procedures build without module search inputs.
- [x] A mixed bundle containing native modules and standalone external
  procedures exposes module members below child namespaces and standalone
  externals at the extension root.
- [x] Mixed object, archive, direct shared-library, and named-library inputs
  preserve dependency-safe link order in `NativeBuildPlan` and resolve all
  runtime symbols.
- [x] Static archive dependency order, GNU linker archive groups for cyclic
  archive dependencies, and required transitive named libraries have runtime
  tests.
- [x] Missing symbols, duplicate native definitions, incompatible artifacts,
  missing `.mod` directories, and unavailable dependent shared libraries report
  native linker/compiler/loader diagnostics without falling back to source
  reparsing.

<!-- PRIK_C_DOCS_START
- [x] Handwritten external-contract evidence covers C-order flat storage
  (`Annotated[Float64[Flat, 3], ORDER_C]`) by validating a multidimensional
  Python view while passing a rank-preserving bridge view to an assumed-size
  native dummy.
PRIK_C_DOCS_END -->

### Stage 8 — Editable Contract Semantics

- [x] Editable native-order contracts can omit `@native_call` when every native
  dummy argument remains visible in native order. Scalar `intent(out)` dummies
  are writable arguments supplied by the caller, array output slots stay
  visible where mutable storage exists, fixed-length string identity calls can
  return `None` even though ordinary Python `str` mutation is not observable,
  function results remain ordinary return values, and derived-type output
  dummies update the supplied wrapper object. Runtime evidence lives in
  `tests/wrapper/fortran/edit_pyi_contracts/test_native_order_contracts.py`.
- [x] Ownership, transfer, and destruction policy is completed after full
  signatures are known and before wrapper planning. The shared post-IR
  entrypoint is `complete_semantic_policies(...)` in
  `prik/semantics/policy_completion.py`; direct ownership subpasses stay behind
  that entrypoint. Planning and lowering consume completed policy metadata
  instead of recomputing policy from raw datatypes. Evidence:
  `tests/semantics/policy/`,
  `tests/wrapper_codegen/`,
  `tests/semantics/policy/`,
  and `prik/semantics/README.md`.
- [x] `.pyi` parsing and `.pyi` semantic conversion are separate stages:
  `prik/parsers/pyi/parser.py` parses text/files to Python AST, and
  `prik/semantics/pyi2ir.py` converts that AST into `SemanticModule` objects
  before semantic policy completion runs. Evidence:
  `tests/fortran/semantic_pyi_format/parsing/test_python_ast_contracts.py::test_pyi_parser_returns_python_ast_only`,
  `prik/semantics/README.md`, and
  `docs/maintainer/internal-architecture/pipeline-map.md`.
- [x] Risky-but-explicit identity contracts document their exact behavior
  instead of being silently healed. Fixed-length `String[n]` `intent(inout)`
  identity calls may return `None` with no observable Python mutation when the
  caller passes an immutable `str`; Python-visible replacement requires an
  explicit projected return contract. Evidence:
  `docs/user/reference/semantic-pyi-format.md` and
  `tests/wrapper/fortran/edit_pyi_contracts/test_native_order_contracts.py`.
- [x] Contradictory policy metadata fails before lowering. In particular,
  `Immutable` means replace-only Python value semantics, while
  `Transfer("borrowed_view")` means no-copy shared storage; combining them on a
  writable native argument reports a direct `.pyi` contract error. Evidence:
  `docs/user/reference/semantic-pyi-format.md` and
  `tests/fortran/memory_management/semantics/test_memory_contract_semantics.py::test_convert_pyi_to_ir_rejects_immutable_writable_borrowed_view_argument`.
- [x] Edited-contract misuse has a documented diagnostic model: loader errors,
  structural contract errors, wrapper-planning errors, and native artifact failures
  are separated, and diagnostics identify the contract path, declaration,
  invalid fact, and expected form where that information is available. File
  loader semantic errors prefix messages with the `.pyi` contract path while
  syntax errors keep Python's filename field. Evidence:
  `docs/user/reference/semantic-pyi-format.md` and
  `tests/fortran/semantic_pyi_format/semantics/test_imports_and_packages.py::test_pyi_file_to_semantic_module_and_modules_forward_module_name_encoding_and_filename`.
- [x] A modified module `.pyi` can remove a public function and hide public
  declarations with `@private` or `private[...]` while preserving unaffected
  runtime behavior. Evidence:
  `tests/fortran/pyi_contracts/exports_and_modules/end_to_end/test_visibility_and_initialization.py`
  and
  `tests/fortran/pyi_contracts/exports_and_modules/end_to_end/fixtures/edited_contracts/module_variables_visibility/`.
- [x] A dedicated user guide documents the supported editable contract surface,
  including what users may remove, hide, add, rename, project, validate, make
  immutable, and declare as ownership/lifetime policy. It separates editable
  wrapper policy from native ABI facts and records the failure layers for
  edited contracts. Evidence:
  `docs/user/reference/pyi-contracts/`,
  `docs/user/reference/fortran-wrapper.md`, and
  `tests/docs/test_structure.py`.
- [x] Edited contracts can remove a class, method, generated constructor, class
  member, and individual overload candidate from the Python API. They can also
  add renamed `@bind(...)` declarations and a renamed module overload group
  without reparsing native source. Evidence:
  `tests/fortran/pyi_contracts/functions_and_classes/end_to_end/test_edited_class_surfaces.py`
  and
  `tests/fortran/pyi_contracts/functions_and_classes/end_to_end/fixtures/edited_contracts/`.
- [x] Module overload candidates can override the linked specific's native call
  with `@bind("native_generic")`, and the printer round-trips that metadata.
  Evidence:
  `tests/fortran/pyi_contracts/functions_and_classes/semantics/test_method_and_constructor_contracts.py::test_bind_selects_module_method_and_constructor_overload_targets`
  and `docs/user/reference/semantic-pyi-format.md`.
- [x] Explicit owner, transfer, and destruction triples are validated as a
  complete lifetime policy instead of independent switches. Supported triples
  remain codegen-ready; contradictory triples normalize to a blocked policy and
  fail before bridge source is emitted. Evidence:
  `tests/fortran/pointers/policy/test_pointer_ownership_policy.py::test_explicit_supported_ownership_triples_remain_codegen_ready`,
  `tests/fortran/pointers/policy/test_pointer_ownership_policy.py::test_contradictory_ownership_triples_fail_closed`,
  and
  `tests/fortran/memory_management/policy/test_memory_ownership_policy.py::test_contradictory_ownership_contract_fails_before_lowering`.
- [x] Every ownership transfer mode and destruction responsibility documented
  in
  [Semantic `.pyi` format](../../user/reference/semantic-pyi-format.md#ownership-transfer-and-destruction-policies)
  resolves during policy completion to either a concrete codegen action or a
  fail-closed blocker. Evidence:
  `tests/fortran/pointers/policy/test_pointer_ownership_policy.py::test_documented_transfer_and_destruction_modes_resolve_or_fail_closed`.
- [x] One editable ownership fixture proves three lifetimes for the same
  rank-one `Float64` array concept: native-owned borrowed module storage,
  wrapper-owned borrowed component storage, and Python/NumPy-owned copy-return
  storage. A second fixture proves wrapper-owned borrowed children retain the
  owner and finalize exactly once. Evidence:
  `tests/fortran/allocatables/end_to_end/test_edited_ownership.py`,
  `tests/fortran/allocatables/end_to_end/fixtures/edited_contracts/explicit_ownership/`,
  and
  `tests/fortran/memory_management/end_to_end/test_explicit_borrowed_owner.py`.
- [x] `Immutable` writable scalar, string, array, and supported derived-type
  output contracts use policy-selected mutable native temporaries, return
  replacements, and do not mutate the original Python-visible value. Immutable
  derived `intent(inout)` replacement remains blocked until a copy/finalization
  policy exists. Evidence:
  `tests/wrapper/fortran/edit_pyi_contracts/test_policy_dispatch_contracts.py::test_immutable_scalar_string_array_and_derived_policies_return_replacements`
  and
  `tests/semantics/policy/test_policy_defaults_and_validation.py::test_immutable_derived_output_selects_wrapper_instance_and_replacement_blocks`.
- [x] Generic `Annotated` constraints and semantic coercions are not silently
  accepted as runtime validation. Fortran wrapper planning reports direct
  blockers until named validators or conversion actions exist. Evidence:
  wrapper-plan tests that prove generic constraints without a runtime validator
  fail.
- [ ] Implement runtime validators for `Bounded(...)` and `Finite`, connect
  them to completed wrapper policy and generated calls, and document them for
  users only after runtime enforcement is tested.
- [ ] Implement explicit runtime dtype-conversion actions before documenting
  contract-controlled coercion as a user feature.
- [x] The currently documented editable-contract surface has direct modified
  runtime evidence or focused semantic/planning evidence: removal and hiding,
  added and renamed bindings, overload pruning and renamed overload groups,
  native-order identity calls without `@native_call`, immutable replacement,
  ownership triples, pointer-policy blockers, `@raises`,
  `@hold_gil`, and native-artifact failures. Evidence:
  `docs/user/reference/pyi-contracts/`,
  `tests/wrapper/fortran/edit_pyi_contracts/`,
  `tests/semantics/policy/`,
  `tests/fortran/error_handling/semantics/test_status_contract_semantics.py`,
  `tests/fortran/error_handling/wrapper_codegen/test_status_error_lowering.py`,
  `tests/fortran/error_handling/end_to_end/test_status_projection.py`,
  `tests/fortran/building_shared_library/pipeline/test_pyi_build_modes.py`,
  `tests/fortran/pyi_contracts/exports_and_modules/`, and
  `tests/wrapper/CHECKLIST_COVERAGE.md`.

<!-- PRIK_C_DOCS_START
- [x] Direct bridge and binding lowering dispatches projected outputs,
  copy-in/copy-out, native-array handles, field access, and cleanup from typed
  wrapper-plan actions completed before backend entry. The generators do not
  select semantic behavior from raw datatype, `intent`, alias, or local-memory
  checks. Evidence: `prik/wrapper_codegen/fortran/bridge.py`,
  `prik/wrapper_codegen/c/binding.py`, `tests/wrapper_codegen/`, and compiled
  feature evidence under `tests/wrapper/fortran/`.
- [x] The remaining Stage 8 bridge and binding policy dispatch audit is closed
  for the current supported surface. Bridge field getters and setters dispatch
  from completed getter/setter policy, derived value-copy setters are selected
  by policy, explicit borrowed derived fields reject replacement setters, and
  pointer-array module-variable or field handle accessors fail closed before
  lowering until descriptor extraction, target lifetime, and release policy are
  implemented. Remaining rank, datatype, `is_alias`, and storage checks in
  bridge and binding code are local emitted-code, ABI, documentation, or
  object-model mechanics rather than semantic policy selection. Evidence:
  `prik/semantics/ownership.py`,
  `prik/wrapper_codegen/fortran/bridge.py`,
  `prik/wrapper_codegen/c/binding.py`,
  `tests/semantics/policy/`,
  `tests/wrapper_codegen/`,
  `tests/wrapper/fortran/derived_types/test_derived_layout.py`, and
  `tests/fortran/memory_management/end_to_end/test_explicit_borrowed_owner.py`.
PRIK_C_DOCS_END -->

### Immutable Native Contract

Establish the source-free native facts before adding bundle or export policy.
The guarantees in this phase apply to every wrapper construct that prik claims
to support. Validation proves that the semantic contract is complete and
internally consistent; it cannot inspect an arbitrary object, archive, or
shared library to prove that the supplied binary implements the declared ABI.
Compiler, linker, import, and runtime parity tests provide the remaining
artifact-level evidence.

- [x] A module leaf is named `<fortran-module>.pyi`; that filename is its native
  module identity. Procedure kind, native symbol, contained-versus-external
  status, argument order, ABI types and kinds, rank, intent, and required
  native imports are inferred from ordinary declarations plus `@external`,
  `@bind`, and `@native_call` only where those facts are not implicit.
- [x] Generated `.pyi` retains every native binding fact needed for module
  procedures, standalone external procedures, type-bound procedures, operators,
  assignment overloads, constructors, callbacks, finalizers, and module
  variables.
- [x] User edits may add wrapper validation, ownership, lifetime, error,
  visibility, and projection policy. Validation rejects structurally
  inconsistent declarations and projections; matching an editable contract to
  an opaque caller-supplied binary remains the caller's native build
  responsibility.
- [x] A generated module `.pyi` is sufficient to select the correct native
  module and symbol from supplied objects, archives, or shared libraries; code
  generation never reparses unavailable Fortran source.
- [x] Missing, contradictory, or structurally altered native facts fail during
  `.pyi` validation or wrapper planning with a precise diagnostic before bridge code is
  emitted or native compilation begins.

### Single-Contract Build Foundation

Prove one source-free module contract can build before adding contract bundles.

- [x] Load a generated module-level `.pyi` file and use it as the semantic IR
  input for wrapper code generation.
- [x] Link caller-supplied native object files while skipping parser and
  semantic lowering for native source.
- [x] Build and import a callable-only Fortran module extension from
  `module.pyi --native-objects module.o`.
- [x] Preserve the existing source-driven wrapper path and makefile/verbose
  modes while adding the `.pyi`-driven entrypoint.
- [x] CLI `.pyi` builds accept native object, archive, and shared-library paths
  with `--native-objects`.
- [x] CLI `.pyi` builds accept `-l` libraries with `--native-library`.
- [x] CLI `.pyi` builds accept library search/rpath directories with
  `--native-library-dir`.
- [x] CLI `.pyi` builds accept native module/interface include directories with
  the build-wide `-I` / `--include-dir` option.
- [x] CLI `.pyi` builds reject missing native build inputs with a direct error.
- [x] JSON build output reports both the semantic contract sources and the
  explicit native artifact and link inputs.
- [x] Native object files, module search paths, libraries, and library paths can
  be supplied without parsing native source. Stage 6 adds the general ordered
  linker-argument interface.
- [x] Contract files and native artifacts are many-to-many: no code path assumes
  that `name.pyi` must be implemented by `name.o`, or infers an artifact name
  from a contract filename.
### Deterministic Contract Generation And Fixtures

Make generated contracts complete and reproducible before composing them.

- [x] One Fortran module maps to exactly one semantic leaf `.pyi` file named for
  the module, independent of which source file contains it.
- [x] Source-owned fixture generation records a root-contract `.pyi` that
  imports its module leaves. One source containing two modules therefore emits
  two module leaves plus one root contract instead of concatenating
  declarations. That root contract is the sole wrapper input.
- [x] Standalone fixed-form and free-form procedures emit non-empty `.pyi`
  contracts with explicit `@external` placement.
- [x] The semantic-format feature checks in representative source-owned
  contract packages under its `pipeline/fixtures/contracts/` tree; runtime
  parity fixtures live under the consuming feature's `contracts/` tree as they
  are added.
- [x] The reviewed semantic-format package corpus and runtime parity baselines
  compare regenerated `.pyi` text exactly with the checked-in contract, so
  generator drift is explicit in review.
### Single-Entry Assembly And Extension Identity

Compose complete contract graphs from one explicit entry. The old plan for
passing multiple positional `.pyi` files is removed; it conflicts with the
implemented single-entry contract and is not a future feature.

- [x] The CLI and Python API accept exactly one entry `.pyi` and recursively
  discover its relative import graph. Multiple positional `.pyi` inputs and
  contract directories are rejected.
- [x] Imports and cross-module references between `.pyi` files retain the
  native dependency relationship without relying on source-file boundaries.
- [x] A generated entry defines the default Python export surface without
  redefining native module structure. For explicit `--out PATH`, `PATH` is the
  package and `PATH/__init__.pyi` is the entry.
- [x] The entry stem determines extension identity. For `__init__.pyi`, the
  parent directory name is used. Wrapper `--out NAME` explicitly overrides either
  inference path.
### Python Namespace And Root Export Policy

Only after imported contracts retain native structure may the entry contract
reshape exports.

- [x] The generated Python extension is the root namespace inferred from the
  entry contract or selected by wrapper `--out NAME`.
- [x] Every imported Fortran module is preserved as one child namespace of the extension;
  its procedures, variables, derived types, constructors, and overloads remain
  under that namespace instead of being flattened into the extension root.
- [x] Two modules may expose the same public member name without collision. For
  example, `library.module1.func` and `library.module2.func` are distinct.
- [x] Generated, unmodified `.pyi`, and modified module `.pyi` builds preserve
  exactly the same native Fortran module namespace structure. A modified module
  contract cannot move declarations between modules, turn a module procedure
  into a standalone procedure, or otherwise rewrite native topology.
- [x] Standalone external procedures in a mixed entry are exported at the
  extension root while imported modules remain child namespaces.
- [x] The entry `.pyi` may contain standalone external procedures that contribute a root
  contract fragment rather than creating a child namespace from its filename.
- [x] Duplicate public names exported at the extension root fail with a direct
  collision diagnostic unless a modified `.pyi` explicitly renames or hides a
  declaration.
- [x] Module members are not automatically re-exported at the extension root;
  any root-level re-export must be explicit in the entry contract.
- [x] The generated default entry preserves module namespaces with
  imports such as `from . import module1` and `from . import module2`.
- [x] Only the entry contract can reshape the Python-facing export tree by hiding,
  aliasing, selectively re-exporting, or flattening declarations from module
  `.pyi` files.
- [x] `from .module import *` flattening is explicit export policy; duplicate
  exported names fail with a direct collision diagnostic instead of depending
  on import order.

### Parity Harness And Required Test Progression

Each test is added only after the corresponding behavior in Phases 1–5 exists.
Every successful scenario exercises the applicable source,
unmodified-generated-contract, and modified-contract paths. Tests compare the
public API and observable runtime behavior, regenerate checked-in fixtures
exactly, and build `.pyi` paths without reparsing native source.

Source and unmodified-generated-contract parity is enforced by test structure,
not by maintaining two similar test lists. Each parity-eligible test has one
behavioral assertion body and receives an imported wrapper from a fixture
parametrized with the `source` and `generated-pyi` build modes. Pytest therefore
collects both modes from the same test function, so adding or changing an
assertion changes both paths automatically. Do not create separate source and
generated-`.pyi` assertion functions or modules. A path-specific test may opt
out only when it verifies a build-path property that cannot apply to the other
path, such as exact generated `.pyi` text or proving that a `.pyi` build does
not reparse source; the test name or a nearby comment must state that reason.
Modified-contract tests remain separate when they intentionally assert a
different public API or runtime contract.

- [x] Store `.pyi` parity fixtures under the consuming wrapper subject, with
  source-free native-object wrapper smoke coverage under
  `tests/wrapper/fortran/build_from_pyi/contracts/`.
- [x] Generate a `.pyi` from a source fixture, rebuild from the generated `.pyi`
  plus a native object, and compare runtime behavior with the source-driven
  build for the first callable-only fixture.
- [x] Feed the source and generated-`.pyi` builds through one parametrized
  module fixture and the exact same behavioral assertion body for the first
  callable-only fixture.
#### Single-module baseline

- [x] One source containing one Fortran module generates one module leaf plus an
  entry `.pyi`, and produces equivalent source and `.pyi` extensions.

#### Multi-module generation and assembly

- [x] Source-owned fixture generation keeps one contract directory per source.
  Explicit `--pyi --out PATH` instead treats `PATH` as the package directory and
  writes `PATH/__init__.pyi`.
- [x] One source containing two Fortran modules generates two module `.pyi`
  files plus an entry contract inside the package; passing only that entry
  produces both child namespaces in one extension.
- [x] `.pyi` wrapper commands and the Python build API accept exactly one entry
  contract and recursively discover its relative imports; multiple positional
  `.pyi` inputs and contract directories are rejected.
- [x] A module leaf supplied as the entry exposes its declarations at the
  extension root without changing their native module placement.
- [x] The entry stem controls the extension filename, `PyInit_<name>`, JSON
  build result, and import name; `__init__.pyi` uses its resolved parent
  directory, including when invoked from inside that directory.
- [x] Wrapper `--out NAME` overrides the inferred extension filename, `PyInit_<name>`, JSON
  build result, and successful Python import in every contract-bundle path.

#### Namespace and export policy

- [x] Two modules may each expose `func`, producing `library.module1.func` and
  `library.module2.func` without collision.
- [x] A modified root contract can alias a module procedure at the root
  without changing its native module contract.
- [x] A modified root contract can flatten a module's public names explicitly.
- [x] Flattening modules with colliding public names fails before codegen and
  identifies every conflicting origin; explicit aliases resolve the failure.
- [x] `from . import module1 as solver` exports only `solver` while retaining
  native module `module1`; selective procedure aliases retain native symbols.
- [x] A reduced entry contract may repeat a selective module-variable import
  and export both the original name and an alias; declarations omitted from the
  entry export policy are pruned before bridge and binding generation.
- [x] A three-level relative import graph discovers every transitive contract,
  while absolute `typing` and `types` support imports create no graph edge or
  runtime export. Missing files and cycles fail before code generation.
- [x] Source-driven and generated-`.pyi` builds expose the same module children
  and root-level standalone procedures without implicit flattening.

### Established Runtime Feature Contracts

Expand the proven three-path harness across wrapper behavior feature by feature.

- [x] Public module variables are declared directly as module-level annotations.
  Generated native getter/setter bridge functions remain internal and never
  appear in the `.pyi` or as Python-callable procedures.
- [x] Fixed character length uses `String[n]`; non-fixed length uses `String`.
  Resolved semantic dtypes are emitted without source-language kind imports.
