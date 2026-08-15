---
title: Native Entrypoint and Adapter Adoption Checklist
audience: maintainers
prerequisites: contributor architecture guide, policy stage, planning stage, pipeline component, testing strategy
related: ../architecture.md, ../packages/policy.md, ../packages/planning.md, ../packages/pipeline.md, ../testing-strategy.md, ../../user/reference/semantic-pyi-format.md, ../../user/language-support/feature-matrix.md, index.md
status: active-roadmap
publication: draft
---

# Native Entrypoint and Adapter Adoption Checklist

This checklist tracks two related changes:

1. existing Fortran `bind(C)` operations can bypass the generated Fortran
   adapter when their completed ABI contract is directly callable; and
2. the first C wrapper backend accepts only operations that the generated C
   binding can call directly, without a generated native C adapter.

This is an implementation roadmap, not a current support claim. The
[language feature matrix](../../user/language-support/feature-matrix.md)
remains authoritative until compiled and imported runtime evidence exists.

## Terminology And Fixed Decisions

- The **binding** is the generated CPython C extension. Every wrapped module
  still has a binding even when it has no native adapter.
- A native **adapter** is optional generated Fortran or C code between that
  binding and the user's native operation. The existing generated Fortran
  `bind(C)` bridge is the Fortran adapter.
- A **direct C ABI entrypoint** means that the binding calls the user's
  linkable C ABI symbol. Binding-local conversion, validation, temporary
  storage, writeback, and Python result construction are still allowed and do
  not by themselves require an adapter.
- Every callable native operation owns one completed entrypoint decision.
  Functions, subroutines, overload candidates, methods, constructors,
  destructors, and callable getter, setter, or lifecycle operations are
  decided individually. A class, overload set, or module does not impose one
  route on all of its operations.
- Fortran source records `bind(C)` and its optional native label as ABI facts.
  A source-free Fortran semantic `.pyi` contract uses `@native_abi("c")` to
  record the same fact; `@bind("symbol")` continues to mean symbol naming
  only.
- A C source or C semantic-contract build is C ABI by language identity. It
  does not use an opposite or redundant per-function ABI decorator.
- `bind(C)` is necessary but not sufficient for a direct Fortran route. Policy
  considers the whole operation: linkability, calling convention, argument
  projection, representation, ownership, lifetime, nullability, mutation,
  writeback, callbacks, result projection, and lifecycle behavior. Planning,
  binding generation, and adapter generation never infer the route from a
  datatype or source spelling.
- Initial C wrapper support has no generated native C-adapter fallback. An
  operation is either completed as a direct C ABI entrypoint or rejected by a
  policy diagnostic before planning.
- Traditional compiler-specific Fortran external ABIs, including ordinary
  BLAS/LAPACK-style procedures without `bind(C)`, continue through a Fortran
  adapter. Direct calls to unstandardized compiler symbols are outside this
  roadmap.

## Required Plan And Artifact Shapes

| Native module shape | Required generated artifacts |
| --- | --- |
| Ordinary Fortran procedures only | C binding plus a Fortran adapter containing every wrapped operation. |
| Mixed ordinary and directly callable `bind(C)` Fortran procedures | C binding plus a Fortran adapter containing only operations selected for adaptation. Direct operations are absent from the adapter. |
| Directly callable `bind(C)` Fortran procedures only | C binding and header; no Fortran adapter source or adapter object. |
| Supported initial C module | C binding and header; no native C adapter source or adapter object. |
| C operation that would require a native adapter | Policy diagnostic before planning or source generation. No partial wrapper artifacts. |

The absence of an adapter is derived from the set of completed operation
decisions. It is not a module-level semantic switch. A mixed module therefore
still has an adapter artifact, but that artifact contains only the operations
that selected it.

## Goal 1 — Behavior-Preserving Entrypoint Separation

This is the first implementation goal. It creates the architectural boundary
needed by direct routing without enabling direct routing, making the adapter
optional, adding C runtime wrapping, or changing any generated source.

During this goal every currently supported Fortran operation remains backed by
the generated Fortran adapter. Only the shared wrapper-plan representation and
the plan facets consumed by the two generators change:

```text
FunctionPlan
├── binding
│   └── Python extraction, validation, local storage, and result construction
├── entrypoint
│   └── C ABI symbol, prototype, ordered parameters, actual projection, and result transport
└── bridge
    └── adapter-local conversion and invocation of the original Fortran procedure
```

Argument, result, native-call, and callable-operation plans follow the same
ownership split. The entrypoint is the shared C ABI handshake. The binding
uses it to declare and call the generated adapter; the Fortran bridge uses it
to declare the matching `bind(C)` procedure. Only the bridge plan describes
what happens after entry into that procedure.

Goal 1 applies to every externally linked generated callable, not only ordinary
wrapped functions. The module entrypoint registry therefore also owns class
allocation, derived destruction and holder lifecycle helpers, derived-field
and module-member accessors, derived-origin transactions, native-array
descriptor and lifecycle operations, and callback trampolines. Binding-local
static Python helpers and bridge-internal procedures are not entrypoints.

The entrypoint contract is bidirectional. It owns both arguments sent from the
binding and results returned through a C function return, output parameters,
presence flags, runtime lengths, or descriptor pointers. Binding plans own
conversion of that completed C storage into Python objects; bridge plans own
conversion of original Fortran results into the matching C ABI transport.

### Canonical Developer Documentation

Update the maintained developer documentation as part of Goal 1, before the
corresponding Python implementation. These pages describe implemented state,
so do not mark the separation complete until code and evidence match them.

- [x] Update `docs/developer/packages/planning.md` with the
  binding/entrypoint/bridge plan tree, bidirectional argument and result
  transport, field ownership, validation boundary, and generator consumers.
- [x] Update `docs/developer/packages/codegen/c-binding.md` so the documented
  input is `binding + entrypoint`, including binding-local input extraction,
  entrypoint invocation, returned/output C storage, and Python result
  construction. Its runnable plan example must use the new records while
  preserving the rendered C output.
- [x] Update `docs/developer/packages/codegen/fortran-bridge.md` so the
  documented input is `entrypoint + bridge`: entrypoint records define the
  public `bind(C)` argument/result boundary, while bridge records define
  adapter-local conversion and the original Fortran call. Its runnable plan
  example must preserve the rendered Fortran output.
- [x] Update `docs/developer/packages/codegen.md` and the concise plan/codegen
  wording in `docs/developer/architecture.md` so their stage diagrams and
  boundaries include the shared entrypoint facet without claiming direct-call
  support.
- [x] Update `CHANGELOG.md` under Unreleased for the maintainer-visible wrapper
  plan representation. Do not change user guides or the language feature
  matrix because Goal 1 adds no user-visible wrapper support.
- [x] Run `tests/docs` after the executable documentation examples and links
  have been updated.

### Plan Separation

- [x] Add always-present native-entrypoint function, argument, result, and
  ordered-parameter records to the shared wrapper plan.
- [x] Keep `WrapperPlanner` as the single projection stage and make it
  construct binding, entrypoint, and bridge facets directly from completed
  upstream facts. All three facets must be complete before
  `WrapperGenerator` freezes the plan; neither generator may derive an
  entrypoint from a bridge record or perform a post-planning split.
- [x] Move the C-visible adapter symbol, prototype, parameter order and types,
  value/address projection, hidden-output transport, and direct-return ABI out
  of bridge-only records and into the entrypoint records.
- [x] Keep original Fortran invocation, native barrier actions, adapter-local
  representation conversion, copy reasons, declaration/import behavior, and
  original native-call ordering in bridge records.
- [x] Keep the bridge facet mandatory for every current operation during this
  goal. Do not add a direct action, optional bridge module, C wrapper route, or
  zero-adapter artifact behavior yet.
- [x] Validate that entrypoint roles are produced by binding-local storage and
  consumed by the matching bridge declaration, while bridge-only roles are not
  exposed as binding inputs.
- [x] Remove the old conflated fields rather than retaining aliases or
  compatibility properties.

### Generator Consumption Boundaries

- [x] Make C binding generation consume only binding and entrypoint facets for
  prototypes, argument extraction, call setup, the native call, writeback, and
  Python result construction. It must not read bridge-native actions,
  adapter-local copies, or original Fortran invocation facts.
- [x] Replace generic binding names such as `_bridge_call` only where they now
  represent the shared entrypoint call. Feature-specific helpers that still
  select a real bridge operation may retain bridge terminology.
- [x] Make Fortran bridge generation consume the entrypoint facet for its
  public `bind(C)` declaration and the bridge facet for adapter-local
  conversion and the original Fortran call.
- [x] Keep wrapper orchestration and generated artifact assembly unchanged:
  every current wrapper still contains its existing Fortran bridge, C binding,
  and header.

### Auxiliary Callable Coverage

These items reopen Goal 1 after the ordinary-function separation exposed
remaining implicit ABI agreements. A helper is not separated merely because
the C generator avoids a `.bridge` attribute: its symbol, existence, ordered
parameters, and result transport must be recorded once by planning.

- [x] Add planner-owned auxiliary entrypoint operation and signature records to
  the module entrypoint facet. Each record must identify its owning operation,
  exported symbol, ordered parameters, result ABI, and any rank, descriptor,
  callback, or scalar-type facts needed by both lowerers.
- [x] Plan class allocation, derived destruction, allocatable/pointer holder
  presence and destruction, direct/holder derived-field accessors, and
  module-derived member accessors as individual entrypoint operations.
- [x] Plan derived-origin `present`, `address`, `scoped`, `checkout`, and
  `restore` operations individually. Operation availability must be fixed by
  planning instead of reconstructed from storage kind in either generator.
- [x] Plan native-array auxiliary operations for function results, default
  arguments, module variables, derived fields, and module-derived members,
  including descriptor callbacks and rank-dependent extent parameters.
- [x] Split callback handoff facts so the binding-local context/trampoline
  implementation, shared trampoline entrypoint signature, and bridge-local
  adapter/original callback ABI are explicit. Static abort helpers remain
  binding-local.
- [x] Make the C binding obtain every externally linked auxiliary symbol and C
  prototype from the planned operation registry. It may still construct
  binding-local static helper names and temporaries.
- [x] Make the Fortran generator obtain every auxiliary `bind(C)` symbol and
  public parameter/result contract from the same planned operation registry.
  It may still create adapter-local declarations, conversions, and internal
  procedures after the entrypoint boundary.
- [x] Validate one-to-one coverage: no duplicate operation keys or symbols, no
  missing operation required by a binding/bridge plan, no unconsumed auxiliary
  entrypoint, and no generator-local fallback that reconstructs a symbol or
  ABI when its plan record is absent.
- [x] Add focused tests covering scalar/string/array/derived accessors, origin
  transactions, lifecycle helpers, native-array operations, constructors, and
  callbacks. Editing an auxiliary entrypoint must affect both boundary
  lowerings, while editing bridge-local implementation facts must not affect
  the C declaration or call.

### Behavior-Preservation Evidence

- [x] Add focused planner and generator tests proving that changing a
  bridge-only native-invocation fact cannot change the C binding, while an
  entrypoint change is visible to both sides of the shared C ABI boundary.
- [x] Preserve the existing rendered C binding, Fortran bridge, header,
  generated semantic contracts, compiler inputs, and imported runtime
  behavior. Existing generated fixtures must not be refreshed to accept
  differences from this refactor.
- [x] Run the affected infrastructure, codegen, compilation, and end-to-end
  feature tests across the current Fortran surface. Leave LAPACK runtime
  coverage to GitHub Actions unless it is explicitly requested.
- [x] Run the required static-analysis suite because Python planning and
  generator code changes in this goal.

Goal 1 is complete only when the binding reads `binding + entrypoint`, the
Fortran generator reads `entrypoint + bridge`, every ordinary and auxiliary
C-visible operation has one planner-owned entrypoint contract, every current
forward native operation still uses the bridge, binding-owned callback
trampolines remain reverse-call entrypoints for bridge-local adapters, and
existing generated artifacts and runtime behavior are unchanged.

## Goal 2 — Selective Direct Routing And C Adoption

Start this goal only after Goal 1 is complete. Complete these stages in order.
Each stage must expose a completed record to the next stage; a later stage must
not rediscover the decision.

### Stage 0 — Generated Entrypoint Vocabulary

- [ ] Rename `NativeEntrypointOperationPlan` to
  `GeneratedSupportProcedureEntrypointPlan` before adding routing actions, and
  use **generated support procedure entrypoint** instead of **auxiliary
  operation** in the maintained planning and code-generation documentation.
  “Procedure” covers Fortran functions, Fortran subroutines, and C functions,
  including C functions returning `void`. This record represents a
  wrapper-internal procedure that is nevertheless an externally linked C ABI
  symbol; do not call it `InternalFunctionPlan`, which could incorrectly imply
  a non-linkable helper or a Fortran internal procedure.
- [ ] Update planner construction, model exports, validation, and both lowerers
  atomically without a compatibility alias. Preserve the single shared ABI
  contract and its implementation owner, and make no generated-source or
  runtime change as part of the rename.

### Stage 1 — Semantic Contract And Source Facts

- [ ] Add and document `@native_abi("c")` for Fortran semantic `.pyi`
  procedures, including composition with `@bind("symbol")`, `@standalone`,
  methods, overload candidates, and callable prototypes where applicable.
- [ ] Preserve the ABI marker and renamed native label through Fortran source
  conversion, `.pyi` parsing, generated-stub printing, and source-free `.pyi`
  loading.
- [ ] Preserve the input language on semantic modules and native build inputs
  so C contracts are known to be C ABI without a per-function decorator.
- [ ] Keep `@native_call(...)` as a language- and route-neutral semantic
  mapping from the Python-visible signature to the original native procedure
  signature. Preserve its ordered arguments, hidden results, typed literals,
  `Addr`/`Value` projections, lengths, presence values, shapes, strides, and
  work values without assuming that a Fortran adapter will execute them.
- [ ] Reject contradictory or misplaced ABI annotations with a semantic
  diagnostic instead of ignoring them.

### Stage 2 — Completed Entrypoint Policy

- [ ] Add an explicit per-operation `NativeEntrypointAction` with direct C ABI
  and generated Fortran-adapter actions. Do not add a generated C-adapter
  action until that emitted mechanism is implemented.
- [ ] Complete the entrypoint action before `WrapperPlanner` starts. A missing,
  blocked, or internally inconsistent action must stop at the policy boundary.
- [ ] Define one central eligibility policy that considers all ABI, transfer,
  ownership, result, and lifecycle facts. Do not duplicate eligibility tests in
  the planner or either generator.
- [ ] Complete one entrypoint passing convention for every parameter and result
  transport before planning: C value, pointer/reference, nullable pointer,
  C descriptor pointer, runtime handle, C function return, or output storage.
  Policy owns this decision; neither lowerer may infer it from Fortran `VALUE`,
  datatype, `intent`, pointer syntax, descriptor shape, or the selected route.
- [ ] Separate route-neutral `@native_call` projection facts from
  adapter-specific data actions. Complete one binding-owned projection action
  for every mapping item—including argument selection, ordering, address/value
  choice, hidden output storage, typed literals, computed scalar facts, and
  supported work storage—before selecting a route. The binding action produces
  a C-side entrypoint actual for both direct and adapted operations.
- [ ] Restrict adapter-specific actions to representation or invocation work
  that cannot be performed at the shared C boundary, such as reconstructing
  Fortran character or array views, converting ordinary logical storage,
  handling allocatable/pointer semantics, omitting absent optional dummies on
  noninteroperable original calls, or invoking module, type-bound, generic, or
  defined operations. Select the Fortran adapter when such work is required and
  available; block a C operation before planning when it needs an unsupported
  direct mechanism.
- [ ] Complete an explicit entrypoint optionality action independently of the
  Python default/nullable surface. At minimum distinguish required values,
  absence represented by a null ordinary pointer, absence represented by a
  null C descriptor pointer, an explicit native presence value already present
  in the declared C signature, adapter-side Fortran omission, and blocked.
- [ ] Direct-route a standard-interoperable non-`VALUE` optional `bind(C)` dummy
  by making the binding pass a non-null pointer when present and `NULL` when
  absent; the original Fortran procedure then observes `present(dummy)`
  directly, without an adapter branch. Do not infer native optionality merely
  because a C parameter is a nullable pointer.
- [ ] Preserve descriptor optionality as three distinct states when that
  feature is adopted: a null descriptor pointer means the optional dummy is
  absent, a non-null descriptor with no allocation/association means the dummy
  is present with empty descriptor state, and a non-null populated descriptor
  means present with a value.
- [ ] Do not direct-route an optional Fortran `VALUE` dummy through a
  compiler-specific hidden presence argument. Keep it adapter-backed, or block
  it when no adapter is available, unless a later standard and compiler-probed
  portable C ABI mechanism is explicitly adopted.
- [ ] Treat a Fortran procedure without the C ABI fact as adapter-backed even
  when its scalar signature resembles C.
- [ ] Treat a C operation that lacks a supported direct mechanism as blocked;
  do not silently route it through an unimplemented C adapter.
- [ ] Keep scalar Boolean policy explicit: C `_Bool` and Fortran
  `logical(c_bool)` use the `Bool` contract, accept Python `bool` and
  `numpy.bool_`, and return Python `bool`. Measured ordinary Fortran logical
  storage continues through its existing adapter conversion.

### Stage 3 — Shared Wrapper Planning

- [ ] Make the bridge facet separated in Goal 1 optional while keeping the
  native-entrypoint plan always present. Completed policy alone decides whether
  that optional facet exists.
- [ ] Replace the mandatory module bridge plan with zero or more derived
  adapter groups. For the initial implementation, the only generated group is
  the optional Fortran adapter group.
- [ ] Give the binding one planned call symbol and ABI signature regardless of
  whether that symbol belongs to the user library or a generated adapter.
- [ ] Plan one authoritative ordered call-projection sequence from
  `@native_call` for every route. Each slot must own its binding-side source and
  materialization action, its completed value/reference/descriptor/handle
  passing convention, and its entrypoint ABI actual; an adapted slot may
  additionally own a bridge facet describing only the Fortran-local conversion
  and original-call expression.
- [ ] Derive entrypoint parameter order and actual projection directly from
  that shared sequence, never from `BridgeCallSlotPlan`. Remove the current
  assumption that entrypoint groups can be ordered from original-Fortran bridge
  slots, because a direct operation has no bridge slot.
- [ ] For both direct and adapted actions, make the binding realize reordered
  arguments, typed literals, address/value projection, hidden outputs, lengths,
  presence values, shapes, strides, and supported work storage. An adapted
  entrypoint receives those completed C-side actuals instead of recreating
  their `@native_call` sources inside the Fortran bridge.
- [ ] Store the completed optionality action and its exact pointer, descriptor,
  or declared presence actual in the entrypoint slot. A direct plan must not
  retain a bridge optional-dispatch requirement; an adapted plan may attach an
  omission branch only when the original Fortran invocation requires it.
- [ ] Retain `BridgeCallSlotPlan` only as an optional adapter facet attached to
  a shared projected slot, or replace it with an equivalently narrow adapter
  record. It may select a converted Fortran expression or optional invocation
  branch, but it must not own a second ordering, source mapping, hidden literal,
  or hidden-storage decision. Direct operations have no such facet.
- [ ] Validate that direct operations have no adapter plan, adapted operations
  have exactly one matching adapter plan, and every binding call target is
  linkable through the extension build plan.
- [ ] Derive module build requirements with `any(operation requires adapter)`;
  never store a second module-wide policy choice.

### Stage 4 — Binding And Adapter Lowering

- [ ] Reuse the separated Goal 1 binding/entrypoint boundary, but extend its
  planned actual kinds and mechanical lowering for the route-neutral
  `@native_call` projections that are currently realized only after entering
  the Fortran adapter. Do not create separate direct and adapted binding
  pipelines; both consume only binding and entrypoint facets without
  re-evaluating the mapping or signature.
- [ ] Make binding lowering execute the planned entrypoint actual sequence for
  both direct and adapted operations, without parsing semantic decorators or
  consulting bridge slots. The binding may materialize only the local C
  temporaries selected by completed policy.
- [ ] Make the binding lowerer the sole owner that realizes each planned C
  passing convention at the call site: emit a value expression, address,
  nullable pointer, descriptor pointer, handle, function-return assignment, or
  output-storage address exactly as recorded by the entrypoint plan. This rule
  applies equally when the target symbol is a generated Fortran adapter or the
  user's direct C ABI symbol.
- [ ] Make binding lowering realize direct optional absence mechanically as the
  planned `NULL`, descriptor pointer, or declared presence actual. It must not
  generate a Fortran-style omission decision or treat every nullable C pointer
  as a native optional argument.
- [ ] Generate a Fortran adapter procedure only for operations whose completed
  action selected it.
- [ ] Make Fortran lowering consume only the optional adapter facet of each
  shared projected slot. It may convert an already supplied C-side actual and
  form the original Fortran invocation, but it must not reimplement
  `@native_call` ordering, source selection, literals, or hidden-storage
  materialization, or choose whether the binding-to-entrypoint call passes a
  value or reference. The Fortran compiler still applies the original dummy's
  calling convention when the adapter invokes the original procedure, but the
  adapter only follows its completed conversion and invocation facet. Direct
  Fortran and C entrypoints have no adapter facets.
- [ ] Emit no Fortran adapter module when its selected-operation set is empty.
- [ ] Reuse existing binding-local extraction, conversion, validation,
  temporary-storage, writeback, cleanup, and Python-result paths for direct
  calls whenever their completed plans are identical.
- [ ] Keep generic reusable CPython/NumPy conversion helpers in native support;
  keep operation-specific direct-call glue in the generated binding. Do not add
  a C adapter generator during the initial direct-only C phase.

#### Stages 2-4 Architectural Acceptance

- [ ] Complete the `@native_call` and value/reference ownership relocation
  before enabling selective direct routing. Treat this relocation as an
  architectural change with unchanged feature behavior: every existing
  feature-local policy, codegen, compilation, and end-to-end test must remain
  unmodified and pass normally.
- [ ] Add or update only focused infrastructure tests for this ownership
  relocation, primarily under `tests/fortran/infrastructure/codegen/`. Prove
  that the shared entrypoint plan owns the ordered projections and completed
  passing conventions, that the C binding realizes their call-site actuals for
  an adapted target, and that Fortran lowering consumes only the remaining
  conversion/invocation facets.
- [ ] Do not rewrite a feature test expectation to accommodate the relocation.
  If an existing feature test fails, identify and preserve the feature, ABI,
  ownership, or generated-format invariant that it protects. Later direct-route
  and C adoption stages add their own feature evidence because those stages add
  observable support and artifact shapes.

### Stage 5 — Pipeline, Compilation, And Linking

- [ ] Allow `GeneratedWrapper` to contain zero adapter sources while retaining
  one or more C binding sources and the generated header.
- [ ] Materialize and compile only the adapter groups present in the generated
  result. Progress output, generated-file records, Makefiles, and saved build
  manifests must represent zero-adapter and selective-adapter builds
  factually.
- [ ] Select the final link driver from all native and generated object
  languages and their runtime requirements, not from the presence of a
  Fortran adapter. An all-direct Fortran module can still require the Fortran
  linker and runtime.
- [ ] Preserve native object and library ordering for source-driven and
  semantic-`.pyi` builds in all-direct and mixed routes.
- [ ] Verify that an adapter-required C operation fails before generated files
  are written or compiler commands run.

### Stage 6 — Scalar Adoption Baseline

- [ ] Add a Fortran all-direct fixture containing safely interoperable
  `bind(C)` scalar functions and subroutines, including a renamed native label.
  Its end-to-end build must emit, compile, import, and call successfully with
  no generated Fortran adapter source or object.
- [ ] Add a mixed Fortran fixture containing direct `bind(C)` and ordinary
  procedures. Its end-to-end build must prove equivalent Python behavior and
  that the generated adapter contains only the ordinary procedures.
- [ ] Add source, generated-`.pyi`, and source-free edited-`.pyi` parity for
  the ABI marker, renamed symbol, selected entrypoint, public NumPy scalar
  results, and Boolean exception.
- [ ] Add direct Fortran and C projection fixtures covering reordered scalar
  arguments, `Addr` and `Value`, a hidden scalar result, and a typed hidden
  literal. Prove from generated artifacts and compiled runtime behavior that
  the binding executes the planned `@native_call` sequence without a generated
  adapter; retain equivalent adapted Fortran coverage proving that the same
  binding-owned projection sequence is passed through the adapter without being
  reconstructed there.
- [ ] Add a direct `bind(C)` non-`VALUE` optional scalar fixture proving omitted,
  explicit `None`, and present values produce the expected `present(...)`
  states with no adapter. Add C nullable-pointer evidence that distinguishes
  nullability from native optionality, and prove that an optional Fortran
  `VALUE` dummy selects an adapter or a pre-generation blocker rather than a
  compiler-specific direct ABI.
- [ ] Add initial C scalar fixtures and compiled end-to-end tests for every
  supported integer, real, complex, and Boolean scalar contract. They must
  prove that no native C adapter source or object is generated.
- [ ] Add C diagnostics for at least one parseable operation whose ABI or
  transfer mechanism is not yet supported directly.

## Feature Adoption Matrix

After the scalar baseline, adopt features by native ABI mechanism rather than
by copying the entire existing Fortran suite. A feature row is complete only
when it has policy, plan/lowering, generated-artifact, compiled runtime, and
semantic-`.pyi` parity evidence. Extend the owning feature fixture with direct
and adapted procedures when their behavior differs; use the central mixed and
all-direct fixtures for module-level artifact invariants.

| Feature boundary | Fortran direct and mixed evidence | Initial C direct-only evidence | Special acceptance concerns |
| --- | --- | --- | --- |
| Numeric and Boolean scalars | [ ] | [ ] | Exact NumPy numeric results; Python Boolean results; C `_Bool` versus ordinary Fortran logical storage. |
| Reference, input/output, and projected results | [ ] | [ ] | Address projection, mutation, writeback ordering, tuple results, and direct function returns. |
| Numeric and Boolean arrays | [ ] | [ ] | Dtype, rank, shape, order, alignment, mutability, copy/writeback, and zero extents. NumPy Boolean storage must not be assumed identical to C `_Bool` storage without an explicit safe mechanism. |
| Strings and character buffers | [ ] | [ ] | Length source, terminators, encoding, embedded NUL, mutation, ownership, and returned-buffer lifetime. |
| Enumerations and constants | [ ] | [ ] | Underlying integer ABI, exported constants, and no invented Python enum layout. |
| Optional and nullable values | [ ] | [ ] | Presence representation, null pointers, omitted Python arguments, and output projection. |
| Raw addresses and native pointers | [ ] | [ ] | Pointee type, nullability, ownership, target lifetime, and reassociation or writeback. |
| Structs, derived types, fields, and methods | [ ] | [ ] | By-value versus pointer ABI, opaque/accessor routes, construction, destruction, borrowing, and layout proof. `bind(C)` alone never authorizes direct aggregate layout. |
| Module variables and native global state | [ ] | [ ] | Direct exported storage versus generated accessor operations, mutability, saved state, and ownership. |
| Generics, overloads, and defined operations | [ ] | [ ] | Each candidate owns its entrypoint action; dispatch owns no shared adapter route. |
| Immediate callbacks | [ ] | [ ] | Function-pointer ABI, callback argument/result conversion, GIL entry, exception handling, and call-scoped lifetime. |
| Allocatable, pointer, and descriptor-backed storage | [ ] | N/A in initial C phase | Descriptor ABI, allocation ownership, release responsibility, nullable state, and runtime/compiler dependencies. |
| Error/status projection and GIL release | [ ] | [ ] | Call target remains independent of status checking, cleanup order, and GIL policy. |
| Standalone, multi-source, and external-library builds | [ ] | [ ] | Native symbol scope, object/library order, module dependencies, and final link-driver selection. |

If a C feature needs a generated native adapter, leave its C cell unchecked and
record the blocking diagnostic. Implementing generated C adapters is a later
roadmap decision, not an implicit part of completing the row for Fortran.

## Required Evidence Owners

- Entrypoint completion and blockers:
  `tests/fortran/<feature>/policy/` and future
  `tests/c/<feature>/policy/`.
- Stages 2-4 projection-ownership relocation: focused
  `tests/fortran/infrastructure/codegen/` tests. Existing feature-local tests
  remain unchanged regression evidence and must pass.
- Selective adapter membership, direct binding call targets, and generated
  artifact sets introduced by later adoption stages: the owning
  `tests/fortran/<feature>/codegen/`, matching future C feature owners, and
  infrastructure owners for cross-feature artifact invariants.
- Zero-adapter materialization, compile scheduling, link-driver selection,
  Makefiles, manifests, and progress records:
  `tests/fortran/building_shared_library/pipeline/` and
  `tests/fortran/building_shared_library/compiling/`.
- Compiled Fortran feature behavior: the owning
  `tests/fortran/<feature>/end_to_end/` directory. The scalar adoption starts by
  replacing the current assumption that every procedure in
  `tests/fortran/data_types/end_to_end/test_value_and_bind_c.py` appears in the
  generated adapter.
- Compiled C feature behavior: future `tests/c/<feature>/end_to_end/`
  directories, using the same named invariants without importing Fortran test
  helpers.
- Generated and edited semantic-contract parity:
  `tests/fortran/semantic_pyi_format/` plus feature-local end-to-end fixtures;
  C contracts use the corresponding language-owned semantic-contract owner.

Artifact assertions protect observable generated and build behavior: whether
an adapter source/object exists, which native operations it exports, which
symbol the binding calls, and which link driver is selected. Tests should not
freeze private class names, complete plan field inventories, or incidental
source formatting.

## Definition Of Initial C Readiness

Initial direct-only C wrapper support is ready to claim only when:

- [ ] the scalar baseline passes through C source and authoritative semantic
  `.pyi` contracts;
- [ ] supported C operations never generate a native adapter;
- [ ] unsupported adapter-required operations fail at completed policy with a
  documented diagnostic;
- [ ] all-direct and mixed Fortran routes pass after the same shared-plan and
  pipeline changes;
- [ ] zero-adapter generated artifacts, compilation, linking, manifests,
  Makefiles, verbose output, and imports have focused evidence; and
- [ ] the user-facing feature matrix lists only the C feature rows proved by
  compiled runtime tests.
