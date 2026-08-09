---
title: Semantic .pyi Wrapper Checklist
audience: developers, maintainers
prerequisites: semantic .pyi format, Fortran wrapper guide
related: pyi_format.md, roadmap/index.md
status: active-roadmap
---

# Semantic `.pyi` Wrapper Checklist

This checklist tracks the path from semantic `.pyi` files to a fully editable
wrapper contract. A `.pyi` file may be generated from source as a starter
contract or written by the user directly. After that point the `.pyi` file is
the source of truth for the Python wrapper API.

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

The phases below are dependency ordered. A later phase may be designed while an
earlier phase is in progress, but support is not complete until its prerequisite
phases and required runtime tests are complete.

## Phase 1 — Immutable Native Contract

Establish the source-free native facts before adding bundle or export policy.

- [ ] Module `.pyi` files retain every native fact required without consulting
  source: Fortran module membership, native scope and symbol name, procedure
  kind, contained-versus-external status, argument order, ABI types and kinds,
  rank, intent, and required native imports.
- [ ] Generated `.pyi` retains every native binding fact needed for module
  procedures, standalone external procedures, type-bound procedures, operators,
  assignment overloads, constructors, callbacks, finalizers, and module
  variables.
- [ ] User edits may add wrapper validation, ownership, lifetime, error,
  visibility, and projection policy, but cannot contradict the retained native
  ABI or binding topology.
- [ ] A generated module `.pyi` is sufficient to select the correct native
  module and symbol from supplied objects, archives, or shared libraries; code
  generation never reparses unavailable Fortran source.
- [ ] Missing, contradictory, or structurally altered native facts fail during
  `.pyi` validation or wrapper planning with a precise diagnostic before bridge code is
  emitted or native compilation begins.

## Phase 2 — Single-Contract Build Foundation

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
  `--native-include-dir`.
- [x] CLI `.pyi` builds reject missing native build inputs with a direct error.
- [x] JSON build output reports both the semantic contract sources and the
  explicit native artifact and link inputs.
- [ ] Native object files, module search paths, libraries, library paths, and
  linker flags can be supplied without parsing native source.
- [ ] Contract files and native artifacts are many-to-many: no code path assumes
  that `name.pyi` must be implemented by `name.o`, or infers an artifact name
  from a contract filename.
- [ ] The build result records one extension-level native link plan separately
  from semantic contract paths.

## Phase 3 — Deterministic Contract Generation And Fixtures

Make generated contracts complete and reproducible before composing them.

- [ ] One Fortran module maps to exactly one semantic `.pyi` file named for the
  module, independent of which source file contains it.
- [ ] A Fortran source containing two modules generates two separate `.pyi`
  files; it does not combine both modules into a source-named aggregate stub.
- [ ] Standalone fixed-form and free-form procedures emit non-empty `.pyi`
  contracts that can drive the same wrapper extension as the source-driven
  path.
- [ ] Explicit `.pyi` output options preserve the one-module-per-file rule and
  reject ambiguous single-file output when the source contains several modules.
- [ ] Each supported wrapper scenario checks in the unmodified generated
  fixtures as `tests/wrapper/fortran/contract_generation/contracts/<module>.pyi`.
- [ ] Regenerating fixtures with `--pyi` exactly matches the checked-in baseline
  `.pyi` text, so generator drift is explicit in review.
- [ ] Edited variants use the `.pyi` suffix, for example
  `tests/wrapper/fortran/contract_generation/contracts/modified_<module>.pyi`; `.py` is not a semantic contract
  input.
- [ ] A modified fixture records the intentional difference from its generated
  baseline and has runtime assertions for both the changed contract and
  unaffected API behavior.

## Phase 4 — Bundle Assembly, Root Selection, And Extension Identity

Compose complete leaf contracts without defining namespace reshaping yet.

- [ ] Multiple ordered Fortran sources generate the complete set of their
  module-aligned `.pyi` files, and the CLI and Python API can consume multiple
  `.pyi` inputs to build the same single extension as the source path.
- [ ] Imports and cross-module references between `.pyi` files retain the
  native dependency relationship without relying on source-file boundaries.
- [ ] A multi-module contract set includes a generated `__init__.pyi` that
  defines the default Python export surface without redefining native module
  structure.
- [ ] The caller supplies an explicit extension name for multi-module and
  standalone-only contract sets. `__init__.pyi` controls exports but does not
  silently choose or change the compiled extension name.
- [ ] Source, generated-contract, and modified-contract parity builds use the
  same extension name and native namespace structure. Only their documented
  Python export policy or wrapper contracts may differ.
- [ ] Multi-source builds can emit and consume multiple module-aligned `.pyi`
  contracts without losing native module imports, dependency objects, link
  ordering, or extension identity.

## Phase 5 — Python Namespace And Root Export Policy

Only after bundles retain native structure may `__init__.pyi` reshape exports.

- [ ] The generated Python extension is the root namespace selected by the
  explicit extension name for a multi-module build.
- [ ] Every Fortran module is preserved as one child namespace of the extension;
  its procedures, variables, derived types, constructors, and overloads remain
  under that namespace instead of being flattened into the extension root.
- [ ] Two modules may expose the same public member name without collision. For
  example, `library.module1.func` and `library.module2.func` are distinct.
- [ ] Generated, unmodified `.pyi`, and modified module `.pyi` builds preserve
  exactly the same native Fortran module namespace structure. A modified module
  contract cannot move declarations between modules, turn a module procedure
  into a standalone procedure, or otherwise rewrite native topology.
- [ ] Standalone external procedures that are not contained in a Fortran module
  are merged into the extension root, including BLAS/LAPACK-style procedures
  collected from multiple source files or native artifacts.
- [ ] A `.pyi` file containing standalone external procedures contributes a root
  contract fragment rather than creating a child namespace from its filename.
- [ ] Duplicate standalone public names at the extension root fail with a direct
  collision diagnostic unless a modified `.pyi` explicitly renames or hides a
  declaration.
- [ ] Module members are not automatically re-exported at the extension root;
  any root-level re-export must be explicit in `__init__.pyi`.
- [ ] The generated default `__init__.pyi` preserves module namespaces with
  imports such as `from . import module1` and `from . import module2`.
- [ ] Only `__init__.pyi` can reshape the Python-facing export tree by hiding,
  aliasing, selectively re-exporting, or flattening declarations from module
  `.pyi` files.
- [ ] `from .module import *` flattening is explicit export policy; duplicate
  exported names fail with a direct collision diagnostic instead of depending
  on import order.

## Phase 6 — Parity Harness And Required Test Progression

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

- [x] Store `.pyi` parity fixtures under `tests/wrapper/fortran/contract_generation/contracts/`.
- [x] Generate a `.pyi` from a source fixture, rebuild from the generated `.pyi`
  plus a native object, and compare runtime behavior with the source-driven
  build for the first callable-only fixture.
- [x] Feed the source and generated-`.pyi` builds through one parametrized
  module fixture and the exact same behavioral assertion body for the first
  callable-only fixture.
- [ ] Apply that parametrized-fixture pattern to every parity-eligible wrapper
  feature: one test function and one assertion body must be collected once for
  `source` and once for `generated-pyi`.
- [ ] Keep source-only and generated-`.pyi`-only tests limited to path-specific
  properties, with the reason for the exception explicit in the test name or a
  nearby comment.

### 6.1 Single-module baseline

- [ ] One source containing one Fortran module generates one module `.pyi` and
  produces equivalent source and `.pyi` extensions.

### 6.2 Standalone native placement

- [ ] One fixed-form source containing one standalone procedure generates a
  non-empty root fragment with `@standalone` and rebuilds equivalently.
- [ ] One free-form source containing one standalone procedure has the same
  `@standalone` generation and runtime parity.
- [ ] One source containing several standalone procedures generates external
  declarations for all of them and exposes each at the extension root.
- [ ] `@standalone` makes the bridge emit an implicit external declaration or a
  required explicit interface and no module `use`; a module procedure makes
  the bridge emit the correct `use <module>`.
- [ ] `@standalone` composes with `@bind("native_name")`: the native external is
  called while the wrapper declaration and root export may use different names.
- [ ] A handwritten external `.pyi` plus native artifacts builds without source
  and follows the same placement, binding, validation, and export rules.

### 6.3 Multi-module generation and assembly

- [ ] One source containing two Fortran modules generates two module `.pyi`
  files plus `__init__.pyi`; both namespaces work in one extension.
- [ ] Two or more source files containing modules generate one `.pyi` per module
  plus `__init__.pyi`; dependency ordering and cross-module types remain valid.
- [ ] An explicit `--root-contract` overrides generated `__init__.pyi`; absent
  that flag, `__init__.pyi` is selected automatically.
- [ ] One supplied `.pyi` works as an implicit root, while multiple `.pyi` files
  without `--root-contract` or `__init__.pyi` fail as ambiguous.
- [ ] wrapper wrapper `--out` controls the extension filename, `PyInit_<name>`, JSON
  build result, and successful Python import in every contract-bundle path.

### 6.4 Namespace and export policy

- [ ] Two modules may each expose `func`, producing `library.module1.func` and
  `library.module2.func` without collision.
- [ ] A modified root contract can alias those same-named procedures to distinct
  root names without changing either native module contract.
- [ ] A modified root contract can flatten modules with disjoint public names.
- [ ] Flattening modules with colliding public names fails before codegen and
  identifies every conflicting origin; explicit aliases resolve the failure.

### 6.5 Library-scale and mixed bundles

- [ ] Several standalone-procedure files build one BLAS/LAPACK-style extension
  from generated external fragments and a generated `__init__.pyi`.
- [ ] The BLAS/LAPACK-style path is tested independently with object files, a
  static archive, a direct shared-library path, and `--native-library` plus
  `--native-library-dir`.
- [ ] Several `.pyi` contracts can resolve from one archive or shared library,
  and one `.pyi` contract can resolve from several objects and libraries.
- [ ] Mixed object, archive, direct shared-library, and named-library inputs
  preserve dependency-safe link order and resolve every native symbol.
- [ ] Module procedures are tested with separately supplied `.mod` directories;
  standalone `@standalone` procedures are tested without `.mod` inputs.
- [ ] Static archive dependency order, repeated archives or linker groups for
  cyclic dependencies, and required transitive libraries have runtime tests.
- [ ] Missing symbols, duplicate definitions, incompatible artifacts, missing
  `.mod` files, and unavailable dependent shared libraries produce direct
  diagnostics without any source fallback.
- [ ] A mixed bundle containing native modules and standalone external
  procedures exposes module members below their namespaces and externals at the
  extension root.

### 6.6 Invalid structural edits

- [ ] Removing `@standalone` from a generated external declaration, adding it to a
  module procedure, changing native scope, or moving a declaration between
  module contracts fails during validation or wrapper planning before codegen.

## Phase 7 — Full Runtime Feature Parity

Expand the proven three-path harness across wrapper behavior feature by feature.

- [ ] Every runtime fixture in `tests/wrapper` has a parity test that first
  builds from source, emits the module-aligned `.pyi` fixtures, rebuilds from
  the unmodified `.pyi` set, and runs the same behavioral assertions against
  both extensions.
- [ ] Scalar module variable accessors round-trip as module variable accessors,
  not as ordinary native `get_*` and `set_*` procedures.
- [ ] Allocatable and pointer module variables round-trip their target,
  lifetime, nullability, shape, and transfer contracts.
- [ ] Generic interfaces and overload sets rebuild from `.pyi` with the same
  dispatch table, concrete target links, error messages, and Python-visible
  names as the source-driven build.
- [ ] Derived-type fields, methods, inheritance metadata, constructors,
  finalizers, borrowed children, and owned result behavior rebuild from `.pyi`
  without consulting the original source declarations.
- [ ] Array dtype, rank, shape, order, stride, lower-bound, writeability,
  alignment, byte-order, and zero-extent validation rebuild from `.pyi` with the
  same runtime failures and success cases.
- [ ] Character length, kind, deferred/allocatable storage, fixed buffer, and
  copy-in/copy-out behavior rebuild from `.pyi` with the same Python string
  contract.
- [ ] Runtime policies from `.pyi`, including `@hold_gil` and `@raises(...)`,
  are honored by generated C bindings.
- [ ] Callback contracts rebuild from `.pyi` with the same call-scoped lifetime,
  GIL handling, exception failure mode, array validation, and derived-type
  conversion behavior.

## Phase 8 — Editable Contract Semantics

Add user policy only after unmodified generated contracts have full parity.

- [ ] Every editable wrapper feature has a modified `.pyi` fixture and a third
  build whose runtime assertions prove the intentional contract change.
- [ ] Removing a public function, method, variable, constructor, overload
  candidate, or class member from `.pyi` removes it from the generated Python
  API.
- [ ] Marking a declaration `@private` or `private[...]` keeps it available as a
  wrapper input when needed internally, but hides it from the public Python
  surface.
- [ ] User-private declarations remain printable and loadable, while ordinary
  source-private Fortran declarations remain omitted from generated `.pyi`.
- [ ] `@bind(...)`, `@module_variable(...)`, `@overload(...)`, and
  `@native_call(...)` are sufficient to express renamed or projected native
  calls without source reparse.
- [ ] Function and method contracts can express validation, coercion,
  ownership, lifetime, shape, and error-status projection policy that is
  consumed by policy completion and wrapper generation.
- [ ] Contradictory or incomplete edited contracts fail during policy completion or
  wrapper generation with precise diagnostics instead of silently falling back
  to source-derived behavior.

## Phase 9 — Advanced Build Modes

Finish nonessential build conveniences after runtime and editing parity.

- [ ] Python API `.pyi` builds accept the same output directory, naming,
  makefile, verbose, and strict-wrapper-name controls as source-driven builds.
- [ ] Generated Makefiles preserve the `.pyi` contract input and the ordered
  native build inputs.
- [ ] One ordered native-link interface preserves interleaving across objects,
  archives, direct shared libraries, named libraries, and explicit linker
  arguments instead of grouping inputs in a way that changes linker semantics.
- [ ] Explicit linker arguments support static archive groups, repeated
  archives, whole-archive policy, and required platform-specific link flags.
- [ ] Runtime shared-library lookup is reproducible through recorded rpath or
  documented loader-path policy, including transitive shared dependencies.
