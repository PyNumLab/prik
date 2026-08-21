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
- Generated support procedures are not adapters for a user procedure. Derived
  field accessors, module-variable accessors, constructors, destructors, holder
  lifecycle operations, descriptor operations, and callback trampolines keep
  their own implementation owner. A module whose user procedures are all
  direct may therefore still require generated Fortran support source; that
  source must not contain adapter wrappers for those direct procedures.
- Traditional compiler-specific Fortran external ABIs, including ordinary
  BLAS/LAPACK-style procedures without `bind(C)`, continue through a Fortran
  adapter. Direct calls to unstandardized compiler symbols are outside this
  roadmap.

## Required Plan And Artifact Shapes

| Native module shape | Required generated artifacts |
| --- | --- |
| Ordinary Fortran procedures only | C binding plus a Fortran adapter containing every wrapped operation. |
| Mixed ordinary and directly callable `bind(C)` Fortran procedures | C binding plus generated Fortran source containing only operations selected for adaptation and independently required support procedures. Direct user operations are absent from the adapter membership. |
| Directly callable `bind(C)` Fortran procedures only, with no Fortran-owned support operations | C binding and header; no generated Fortran source or object. |
| Directly callable `bind(C)` Fortran procedures plus Fortran-owned support operations | C binding and header plus support-only Fortran source/object. No direct user procedure receives an adapter wrapper. |
| Supported initial C module | C binding and header; no native C adapter source or adapter object. |
| C operation that would require a native adapter | Policy diagnostic before planning or source generation. No partial wrapper artifacts. |

Adapter membership and generated-support membership are derived independently
from completed per-operation decisions. Neither is a module-level semantic
switch. A generated Fortran file may initially contain both groups, but an
artifact assertion must still distinguish adapted user operations from
generated support procedures. The file and object are absent only when both
groups are empty.

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

Goal 1 established the target in which the binding reads
`binding + entrypoint`, the Fortran generator reads `entrypoint + bridge`, and
every C-visible operation has one planner-owned entrypoint contract. A
follow-up consumer audit found remaining cross-facet reads and backend-specific
auxiliary signature fields. Goal 2 Stage 0 owns that closure before direct
routing begins; existing generated artifacts and runtime behavior remain the
baseline.

## Goal 2 — Selective Direct Fortran Routing

Start this goal by closing the remaining Goal 1 consumer-boundary leaks in
Stage 0. Do not enable selective direct routing until that stage is complete.
Complete the stages in order. Each stage must expose a completed record to the
next stage; a later stage must not rediscover the decision.

Goal 2 accepts only Fortran native inputs. It may change the generated C
binding because that binding must call direct Fortran `bind(C)` entrypoints,
but it does not add C source parsing, C semantic-contract input, or native C
wrapping. Goal 3 owns those capabilities.

### Current Goal 2 Status (2026-08-15)

Goal 2 is **complete by checklist items**: **96 of 96 items are complete**.
Stages 0–8, all fourteen feature rows, source/generated/source-free contract
parity, zero-adapter and mixed builds, broad verification, and the maintained
direct-entrypoint benchmark evidence are complete.

The maintained ARM64 runner used Python 3.12 and NumPy/f2py 2.5.1. Its pinned
preflight found no generated Fortran procedure wrapper in either direct route.
The f2py C/API object referred to all three user labels and its native object
defined them despite Meson's `.c.o` and `.f90.o` filenames; the linked extension
also defined all three. The corresponding PRIK binding object, native object,
and linked extension proved the same relationships. The paired runtime,
adapter-control, and clean-build results are published as separate generated
sections of the Performance page without changing the normal-interface
geometric-mean population.

### Goal 2 Testing Layers

Keep architectural ownership evidence separate from feature behavior:

- **Infrastructure tests** may construct, freeze, or deliberately edit
  completed semantic policies and wrapper-plan facets. They prove stage
  handoffs, facet ownership, cross-facet isolation, validation, selected
  symbols and signatures, passing conventions, adapter membership, and
  generated-artifact assembly. Place them with the focused owner under
  `tests/fortran/infrastructure/`, primarily its `semantics/`, `codegen/`, and
  `pipeline/` directories. They must not stand in for a user-input or compiled
  feature test.
- **Feature tests** must start from a real Fortran source fixture or an
  authoritative semantic `.pyi` fixture and pass through the canonical
  parsing/contract, semantic, policy, planning, generation, compilation, and
  import routes applicable to the assertion. Policy and codegen tests may stop
  at their owning stage, while end-to-end tests compile, import, call the
  Python API, and inspect only the relevant generated-artifact membership or
  ABI invariant. Direct and mixed source fixtures, plus generated and edited
  `.pyi` replay where supported, provide the adoption evidence.
- **Exact-output regression evidence** belongs centrally in infrastructure,
  not as a snapshot duplicated by every feature. Before Stage 0 changes code,
  record one representative ordinary non-`bind(C)` source/semantic-contract
  baseline and protect the exact generated C binding, C header, and Fortran
  adapter bytes. Stage 0 must not refresh that baseline. Keep it passing in
  later stages for ordinary operations whose completed projection and passing
  plan did not change.
- Do not require old generated bytes for a non-`bind(C)` operation whose
  route-neutral `@native_call` materialization intentionally moves from the
  Fortran adapter to the C binding in Stages 2-4. For that case, focused
  infrastructure assertions must prove the new owner and generated ABI
  structure, while source/`.pyi` feature tests preserve compiled Python
  behavior. Any golden update must identify this planned mechanism change; it
  cannot be used to conceal unrelated formatting or output churn.

### Stage 0 — Strict Consumer Boundaries And Entrypoint Vocabulary

- [x] Audit every C-binding read and make C lowering consume only binding plus
  native-entrypoint facets. Audit every Fortran-adapter read and make Fortran
  lowering consume only native-entrypoint plus bridge facets. Neutral parent
  records may retain owner/type identity needed to locate those facets, but
  must not carry backend behavioral choices that let one lowerer bypass the
  boundary.
- [x] Remove every current Fortran-lowering dependency on binding facts. In
  particular, replace the module-getter, raw-address selection, raw-array call
  selection, and argument-role reads of `.binding` with the corresponding
  completed bridge or entrypoint facts. Remove `PythonBarrierAction` from the
  Fortran generator once no adapter mechanism consumes Python-boundary policy.
- [x] Confirm that C lowering contains no bridge-facet read. Names of real
  adapter symbols may still use adapter/bridge terminology, but the C generator
  must obtain their existence, symbol, signature, and call transport from the
  shared entrypoint plan rather than a bridge record.
- [x] Audit every ordinary and generated-support entrypoint field. An
  entrypoint record may contain only the symbol, ordered C ABI, parameter and
  result roles, and matching C/Fortran declaration facts that describe the
  same shared boundary, plus the single implementation-owner flag needed to
  decide which side defines the operation. Move binding-only extraction,
  temporaries, Python actions, and local C expressions into binding plans; move
  adapter-body locals, conversion, and original invocation into bridge plans.
- [x] Keep `c_name` and `fortran_name` together in the shared entrypoint when
  they name the corresponding formal parameter in the C declaration and
  Fortran `bind(C)` declaration of that same operation. They need not be
  textually equal. Likewise, `const`, `intent`, or a neutral direction may stay
  in the entrypoint when they describe the matching declarations of that
  boundary. Move a name or attribute out only when it instead describes a
  binding local, an adapter-body local, or the original Fortran procedure after
  the entrypoint boundary.
- [x] Validate that paired C and Fortran entrypoint spellings describe one
  interoperable parameter/result contract. Do not require neutral vocabulary
  merely to avoid language-specific names, and do not use a paired spelling as
  a container for unrelated backend behavior.
- [x] Audit facts duplicated between binding and entrypoint or between bridge
  and entrypoint, including handoff and length roles. Store a true C ABI fact
  once in the entrypoint. Keep two records only when they describe genuinely
  different boundaries, and name the distinction explicitly rather than
  validating accidental equality.
- [x] Project backend-local derived capsule and holder inventories explicitly
  alongside the generated support procedure registry. Make C lowering consume
  binding inventories for static CPython helper membership, make Fortran
  lowering consume bridge inventories for typed-holder definitions and field
  bodies, and make both consume only registry records for external procedure
  existence, symbols, and ABIs. Remove result, argument, module-variable,
  constructor, release, storage, and call-case walks that rediscover module
  inventories in either lowerer, including namespace-level holder-method
  copies.
- [x] Rename `NativeEntrypointOperationPlan` to
  `GeneratedSupportProcedureEntrypointPlan` before adding routing actions, and
  use **generated support procedure entrypoint** instead of **auxiliary
  operation** in the maintained planning and code-generation documentation.
  “Procedure” covers Fortran functions, Fortran subroutines, and C functions,
  including C functions returning `void`. This record represents a
  wrapper-internal procedure that is nevertheless an externally linked C ABI
  symbol; do not call it `InternalFunctionPlan`, which could incorrectly imply
  a non-linkable helper or a Fortran internal procedure.
- [x] Update planner construction, model exports, validation, and both lowerers
  atomically without a compatibility alias. Preserve the single shared ABI
  contract. Retain exactly one clearly named implementation-owner field whose
  only job is to select which generated side defines the support procedure and
  which side declares or calls it. Make no generated-source or runtime change
  as part of Stage 0.
- [x] Keep `WrapperGenerator` free to validate relationships across the frozen
  complete plan before lowering, but do not let that orchestration validation
  become a fallback that copies or repairs missing backend/entrypoint facts.
  Backend generators themselves must respect the strict facet boundary.
- [x] Add or update only focused infrastructure tests for Stage 0. Prove that a
  binding-only edit cannot change Fortran output, a bridge-only edit cannot
  change C output, and a shared entrypoint edit changes both sides of the same
  ABI. Cover ordinary functions and generated support procedures, including
  both implementation owners, and add a focused guard against future direct
  cross-facet reads.
- [x] Capture the canonical ordinary non-`bind(C)` exact-output baseline before
  implementation and prove that Stage 0 preserves every byte of its generated
  C binding, C header, and Fortran adapter. Do not regenerate the expected
  files to accept a Stage 0 difference.
- [x] Preserve all rendered C, Fortran, header, build, and runtime behavior in
  Stage 0. Existing feature-local behavioral, ABI, compilation, and end-to-end
  invariants must pass normally. Feature tests may change only to remove
  obsolete assertions about duplicated internal plan fields; infrastructure
  tests own the new architectural boundary assertions.

### Stage 1 — Semantic Contract And Source Facts

- [x] Add and document `@native_abi("c")` for Fortran semantic `.pyi`
  procedures, including composition with `@bind("symbol")`, `@standalone`,
  methods, overload candidates, and callable prototypes where applicable.
- [x] Preserve the ABI marker and renamed native label through Fortran source
  conversion, `.pyi` parsing, generated-stub printing, and source-free `.pyi`
  loading.
- [x] Preserve Fortran language and source-origin facts so
  `@native_abi("c")` is interpreted as the ABI of a Fortran procedure rather
  than as evidence of a C native input.
- [x] Keep `@native_call(...)` as a language- and route-neutral semantic
  mapping from the Python-visible signature to the original native procedure
  signature. Preserve its ordered arguments, hidden results, typed literals,
  `Addr`/`Value` projections, lengths, presence values, shapes, strides, and
  work values without assuming that a Fortran adapter will execute them.
- [x] Reject contradictory or misplaced ABI annotations with a semantic
  diagnostic instead of ignoring them.

### Stage 2 — Completed Entrypoint Policy

- [x] Add an explicit per-operation `NativeEntrypointAction` with direct C ABI
  and generated Fortran-adapter actions. Do not add a generated C-adapter
  action until that emitted mechanism is implemented.
- [x] Complete the entrypoint action before `WrapperPlanner` starts. A missing,
  blocked, or internally inconsistent action must stop at the policy boundary.
- [x] Define one central eligibility policy that considers all ABI, transfer,
  ownership, result, and lifecycle facts. Do not duplicate eligibility tests in
  the planner or either generator.
- [x] Complete one entrypoint passing convention for every parameter and result
  transport before planning: C value, pointer/reference, nullable pointer,
  C descriptor pointer, runtime handle, C function return, or output storage.
  Policy owns this decision; neither lowerer may infer it from Fortran `VALUE`,
  datatype, `intent`, pointer syntax, descriptor shape, or the selected route.
- [x] Separate route-neutral `@native_call` projection facts from
  adapter-specific data actions. Complete one binding-owned projection action
  for every mapping item—including argument selection, ordering, address/value
  choice, hidden output storage, typed literals, computed scalar facts, and
  supported work storage—before selecting a route. The binding action produces
  a C-side entrypoint actual for both direct and adapted operations.
- [x] Restrict adapter-specific actions to representation or invocation work
  that cannot be performed at the shared C boundary, such as reconstructing
  Fortran character or array views, converting ordinary logical storage,
  handling allocatable/pointer semantics, omitting absent optional dummies on
  noninteroperable original calls, or invoking module, type-bound, generic, or
  defined operations. Select the Fortran adapter when such work is required.
- [x] Complete an explicit entrypoint optionality action independently of the
  Python default/nullable surface. At minimum distinguish required values,
  absence represented by a null ordinary pointer, absence represented by a
  null C descriptor pointer, an explicit native presence value already present
  in the declared C signature, adapter-side Fortran omission, and blocked.
- [x] Direct-route a standard-interoperable non-`VALUE` optional `bind(C)` dummy
  by making the binding pass a non-null pointer when present and `NULL` when
  absent; the original Fortran procedure then observes `present(dummy)`
  directly, without an adapter branch. Do not infer native optionality merely
  because a C parameter is a nullable pointer.
- [x] Preserve descriptor optionality as three distinct states when that
  feature is adopted: a null descriptor pointer means the optional dummy is
  absent, a non-null descriptor with no allocation/association means the dummy
  is present with empty descriptor state, and a non-null populated descriptor
  means present with a value.
- [x] Do not direct-route an optional Fortran `VALUE` dummy through a
  compiler-specific hidden presence argument. Keep it adapter-backed, or block
  it when no adapter is available, unless a later standard and compiler-probed
  portable C ABI mechanism is explicitly adopted.
- [x] Treat a Fortran procedure without the C ABI fact as adapter-backed even
  when its scalar signature resembles C.
- [x] Keep scalar Boolean policy explicit: directly routed Fortran
  `logical(c_bool)` uses the `Bool` contract, accepts Python `bool` and
  `numpy.bool_`, and returns Python `bool`. Measured ordinary Fortran logical
  storage continues through its existing adapter conversion.

### Stage 3 — Shared Wrapper Planning

- [x] Make the bridge facet separated in Goal 1 optional while keeping the
  native-entrypoint plan always present. Completed policy alone decides whether
  that optional facet exists.
- [x] Replace the mandatory module bridge plan with zero or more native
  generated-code groups. Keep adapted user-operation membership distinct from
  generated-support-procedure membership even if the initial implementation
  emits both groups in one Fortran source. Goal 2 creates only
  Fortran-generated groups; Goal 3 owns native C grouping.
- [x] Give the binding one planned call symbol and ABI signature regardless of
  whether that symbol belongs to the user library or a generated adapter.
- [x] Plan one authoritative ordered call-projection sequence from
  `@native_call` for every route. Each slot must own its binding-side source and
  materialization action, its completed value/reference/descriptor/handle
  passing convention, and its entrypoint ABI actual; an adapted slot may
  additionally own a bridge facet describing only the Fortran-local conversion
  and original-call expression.
- [x] Derive entrypoint parameter order and actual projection directly from
  that shared sequence, never from `BridgeCallSlotPlan`. Remove the current
  assumption that entrypoint groups can be ordered from original-Fortran bridge
  slots, because a direct operation has no bridge slot.
- [x] For both direct and adapted actions, make the binding realize reordered
  arguments, typed literals, address/value projection, hidden outputs, lengths,
  presence values, shapes, strides, and supported work storage. An adapted
  entrypoint receives those completed C-side actuals instead of recreating
  their `@native_call` sources inside the Fortran bridge.
- [x] Store the completed optionality action and its exact pointer, descriptor,
  or declared presence actual in the entrypoint slot. A direct plan must not
  retain a bridge optional-dispatch requirement; an adapted plan may attach an
  omission branch only when the original Fortran invocation requires it.
- [x] Retain `BridgeCallSlotPlan` only as an optional adapter facet attached to
  a shared projected slot, or replace it with an equivalently narrow adapter
  record. It may select a converted Fortran expression or optional invocation
  branch, but it must not own a second ordering, source mapping, hidden literal,
  or hidden-storage decision. Direct operations have no such facet.
- [x] Store the original Fortran invocation kind only in the optional adapter
  facet: subroutine `call` or function-result assignment, including the planned
  assignment target. Do not infer it from the C entrypoint return transport; a
  Fortran function may use a `void` C entrypoint with output storage, and a C
  return may instead carry status. The binding does not consume this fact, and
  a direct operation has no original-call facet.
- [x] Validate that direct operations have no adapter plan, adapted operations
  have exactly one matching adapter plan, and every binding call target is
  linkable through the extension build plan.
- [x] Derive module build requirements from both independent sets:
  `any(operation requires adapter)` and
  `any(support entrypoint has a Fortran implementation owner)`. Never store a
  second module-wide policy choice or treat a generated support procedure as an
  adapter for a direct user operation.

### Stage 4 — Binding And Adapter Lowering

- [x] Reuse the separated Goal 1 binding/entrypoint boundary, but extend its
  planned actual kinds and mechanical lowering for the route-neutral
  `@native_call` projections that are currently realized only after entering
  the Fortran adapter. Do not create separate direct and adapted binding
  pipelines; both consume only binding and entrypoint facets without
  re-evaluating the mapping or signature.
- [x] Make binding lowering execute the planned entrypoint actual sequence for
  both direct and adapted operations, without parsing semantic decorators or
  consulting bridge slots. The binding may materialize only the local C
  temporaries selected by completed policy.
- [x] Make the binding lowerer the sole owner that realizes each planned C
  passing convention at the call site: emit a value expression, address,
  nullable pointer, descriptor pointer, handle, function-return assignment, or
  output-storage address exactly as recorded by the entrypoint plan. This rule
  applies equally when the target symbol is a generated Fortran adapter or the
  user's direct C ABI symbol.
- [x] Make binding lowering realize direct optional absence mechanically as the
  planned `NULL`, descriptor pointer, or declared presence actual. It must not
  generate a Fortran-style omission decision or treat every nullable C pointer
  as a native optional argument.
- [x] Generate a Fortran adapter procedure only for operations whose completed
  action selected it.
- [x] Make Fortran lowering consume only the optional adapter facet of each
  shared projected slot. It may convert an already supplied C-side actual and
  form the original Fortran invocation, but it must not reimplement
  `@native_call` ordering, source selection, literals, or hidden-storage
  materialization, or choose whether the binding-to-entrypoint call passes a
  value or reference. The Fortran compiler still applies the original dummy's
  calling convention when the adapter invokes the original procedure, but the
  adapter only follows its completed conversion and invocation facet. Direct
  Fortran entrypoints have no adapter facets.
- [x] Emit no generated Fortran source when both the selected adapter-operation
  set and the Fortran-owned support-procedure set are empty. When only the
  support set is nonempty, emit support-only source and no wrapper for a direct
  user operation.
- [x] Reuse existing binding-local extraction, conversion, validation,
  temporary-storage, writeback, cleanup, and Python-result paths for direct
  calls whenever their completed plans are identical.
- [x] Keep generic reusable CPython/NumPy conversion helpers in native support;
  keep operation-specific direct-call glue in the generated binding. Do not add
  a C adapter generator or native C input lowering in Goal 2.

#### Stages 2-4 Architectural Acceptance

- [x] Complete the `@native_call` and value/reference ownership relocation
  before enabling selective direct routing. Treat this relocation as an
  architectural change with unchanged feature behavior: retain and pass every
  feature-local policy, ABI, compilation, and end-to-end invariant, while
  removing only obsolete assertions about the former implementation owner.
- [x] Add or update only focused infrastructure tests for this ownership
  relocation, primarily under `tests/fortran/infrastructure/codegen/`. Prove
  that the shared entrypoint plan owns the ordered projections and completed
  passing conventions, that the C binding realizes their call-site actuals for
  an adapted target, and that Fortran lowering consumes only the remaining
  conversion/invocation facets.
- [x] Do not rewrite a feature behavior or ABI expectation merely to
  accommodate the relocation. If an existing feature test fails, identify and
  preserve the maintained invariant that it protects; remove or replace only
  an obsolete implementation-shape assertion. Later direct-route stages add
  their own feature evidence because they add observable support and artifact
  shapes. Goal 3 separately owns C adoption evidence.

### Stage 5 — Pipeline, Compilation, And Linking

- [x] Allow `GeneratedWrapper` to contain zero generated native sources while
  retaining one or more C binding sources and the generated header. Represent
  adapter and generated-support membership separately even if they share a
  physical Fortran source initially.
- [x] Materialize and compile only the native generated-code groups present in
  the result. Progress output, generated-file records, Makefiles, and saved
  build manifests must represent zero-generated-source, selective-adapter, and
  support-only builds factually.
- [x] Select the final link driver from all native and generated object
  languages and their runtime requirements, not from the presence of a
  Fortran adapter. An all-direct Fortran module can still require the Fortran
  linker and runtime.
- [x] Preserve native object and library ordering for source-driven and
  semantic-`.pyi` builds in all-direct and mixed routes.

### Stage 6 — Fortran Scalar Adoption Baseline

- [x] Add a Fortran all-direct fixture containing safely interoperable
  `bind(C)` scalar functions and subroutines, including a renamed native label.
  Its end-to-end build must emit, compile, import, and call successfully with
  no generated Fortran adapter source or object.
- [x] Add a mixed Fortran fixture containing direct `bind(C)` and ordinary
  procedures. Its end-to-end build must prove equivalent Python behavior and
  that the generated adapter contains only the ordinary procedures.
- [x] Add source, generated-`.pyi`, and source-free edited-`.pyi` parity for
  the ABI marker, renamed symbol, selected entrypoint, public NumPy scalar
  results, and Boolean exception.
- [x] Add direct and adapted Fortran projection fixtures covering reordered
  scalar arguments, `Addr` and `Value`, a hidden scalar result, and a typed
  hidden literal. Prove from generated artifacts and compiled runtime behavior
  that the binding executes the planned `@native_call` sequence without a
  generated adapter for the direct case, and passes the same binding-owned
  sequence through the adapter without reconstructing it for the adapted case.
- [x] Add a direct `bind(C)` non-`VALUE` optional scalar fixture proving omitted,
  explicit `None`, and present values produce the expected `present(...)`
  states with no adapter. Distinguish a nullable pointer in the direct C ABI
  signature from Fortran optionality, and prove that an optional Fortran
  `VALUE` dummy selects an adapter or a pre-generation blocker rather than a
  compiler-specific direct ABI.

### Stage 7 — Feature-Local Direct And Mixed Adoption

Adopt direct routing one feature at a time after the scalar baseline. Every
callable feature row that is claimed as direct must own both fixture shapes
below under its existing `tests/fortran/<feature>/end_to_end/fixtures/`
directory. Parser, semantic-IR, CLI, and infrastructure directories do not need
native fixtures merely because they exist under `tests/fortran/`.

- [x] Add `<feature>_direct_bind_c_f90.f90`, containing only user procedures
  whose completed contracts select direct C ABI entrypoints. Cover both a
  function and subroutine when the feature supports both. Prove that no direct
  user procedure appears in adapter membership. When the fixture has no
  Fortran-owned support procedures, prove that no generated Fortran source or
  object exists.
- [x] Add `<feature>_mixed_bind_c_f90.f90`, containing at least one directly
  callable `bind(C)` procedure and at least one ordinary or otherwise
  adapter-required procedure. Prove per-operation selection, equivalent Python
  behavior, and that generated adapter membership contains only the latter.
- [x] For features such as derived types, module state, ownership handles, and
  callbacks, allow the direct fixture to generate the accessors, lifecycle
  helpers, descriptor operations, or trampolines selected independently by
  their support-entrypoint plans. Prove that a resulting Fortran artifact is
  support-only with respect to direct user procedures; do not call the entire
  module adapter-backed merely because support code exists.
- [x] Reuse the owning feature's existing behavioral assertions and semantic
  `.pyi` replay route. Add the direct and mixed cases without replacing or
  weakening ordinary-procedure coverage, and keep source, generated-`.pyi`, and
  source-free edited-`.pyi` decisions equivalent where that feature supports
  those inputs.
- [x] Add the fixture pair only when completed policy supports the feature's
  direct ABI mechanism. Until then, keep the feature-matrix cell unchecked and
  retain a focused blocker test instead of adding a nominal `bind(C)` fixture
  that still relies on an unacknowledged adapter.

### Stage 8 — Direct-Entrypoint Performance Evidence

Add performance cases only after their correctness, route selection, generated
artifacts, and compiled runtime behavior pass outside the timer.

- [x] Add same-source `bind(C)` no-op, scalar-function, and scalar-subroutine
  workloads that isolate binding-to-native call overhead. The PRIK build must
  prove that none of those user procedures has a generated adapter wrapper.
- [x] Measure the equivalent ordinary-Fortran PRIK operations separately so the
  cost difference between PRIK's adapted and direct routes is visible without
  attributing native-kernel work to either route.
- [x] Build the f2py direct-call comparison with its documented
  [`--no-wrap-functions`](https://numpy.org/doc/stable/f2py/usage.html) mode for
  Fortran functions and
  `--skip-empty-wrappers` where applicable. Keep f2py's Python C/API binding;
  these flags concern generated Fortran wrapper procedures/files rather than
  removal of the Python binding.
- [x] Inspect the generated binding object, native object, linked extension,
  and generated-source membership with the pinned NumPy version before
  describing the maintained result. Prove that the binding refers directly to
  the three user labels and that both the native object and linked extension
  define them.
- [x] Keep the benchmark procedures' Fortran names and `bind(C)` labels equal so
  both tools consume the same source without a benchmark-only symbol rewrite.
  Test renamed native labels separately in the correctness suite, and use a
  standalone or module source shape only after artifact inspection proves the
  intended f2py native-call path.
- [x] Keep the existing default-interface PRIK/f2py results intact. Publish the
  direct-entrypoint cohort separately unless the benchmark methodology,
  paired-suite validation, labels, and geometric-mean population are
  deliberately revised and documented.
- [x] Use identical native operations, Python-visible inputs, numerical result
  values, optimization flags, GIL policy, process-order balancing, CPU
  affinity, and correctness checks for each cross-tool pair. Preserve and
  record each tool's natural result class instead of hiding PRIK's exact NumPy
  scalar and f2py's built-in scalar behind a normalization shim. Record route
  and wrapper-mode metadata so default, adapted, and direct results cannot be
  merged silently.
- [x] Add both runtime-call and clean small-build cases. The build case must
  report generated/compiled source membership so a missing PRIK adapter or an
  empty f2py wrapper file is an evidenced artifact fact, not an inference from
  elapsed time.
- [x] Update `benchmarks/README.md`, benchmark workflows, and tooling tests under
  `tests/tools/` for the separate direct-entrypoint cohort without changing the
  generated Performance page or its published snapshot.
- [x] After a complete paired run on the maintained benchmark runner, update
  the generated Performance-page methodology and published snapshot with the
  direct-entrypoint cohort.

## Goal 2 Fortran Feature Adoption Matrix

After the scalar baseline, adopt features by native ABI mechanism rather than
by copying the entire existing Fortran suite. A feature row is complete only
when it has policy, plan/lowering, generated-artifact, compiled runtime, and
semantic-`.pyi` parity evidence through the Stage 7 direct and mixed fixture
pair. Use the central scalar fixtures for cross-feature module and pipeline
invariants rather than duplicating those assertions in every feature.

| Feature boundary | Fortran direct and mixed evidence | Special acceptance concerns |
| --- | --- | --- |
| Numeric and Boolean scalars | [x] | Exact NumPy numeric results; Python Boolean results; `logical(c_bool)` direct storage versus ordinary Fortran logical adapter conversion. |
| Reference, input/output, and projected results | [x] | Address projection, mutation, writeback ordering, tuple results, and direct function returns. |
| Numeric and Boolean arrays | [x] | Dtype, rank, shape, order, alignment, mutability, copy/writeback, zero extents, and explicit Boolean-storage compatibility. |
| Strings and character buffers | [x] | Length source, terminators, encoding, embedded NUL, mutation, ownership, and returned-buffer lifetime. |
| Enumerations and constants | [x] | Underlying integer ABI, exported constants, and no invented Python enum layout. |
| Optional and nullable values | [x] | Fortran presence representation, null pointers, omitted Python arguments, and output projection. |
| Raw addresses and native pointers | [x] | Pointee type, nullability, ownership, target lifetime, and reassociation or writeback. |
| Structs, derived types, fields, and methods | [x] | By-value versus pointer ABI, opaque/accessor routes, construction, destruction, borrowing, and layout proof. `bind(C)` alone never authorizes direct aggregate layout. |
| Module variables and native global state | [x] | Direct exported storage versus generated accessor operations, mutability, saved state, and ownership. |
| Generics, overloads, and defined operations | [x] | Each candidate owns its entrypoint action; dispatch owns no shared adapter route. |
| Immediate callbacks | [x] | Function-pointer ABI, callback argument/result conversion, GIL entry, exception handling, and call-scoped lifetime. |
| Allocatable, pointer, and descriptor-backed storage | [x] | Descriptor ABI, allocation ownership, release responsibility, optional presence, nullable state, and runtime/compiler dependencies. |
| Error/status projection and GIL release | [x] | Call target remains independent of status checking, cleanup order, and GIL policy. |
| Standalone, multi-source, and external-library builds | [x] | Native symbol scope, object/library order, module dependencies, and final link-driver selection. |

## Goal 2 Required Evidence Owners

- Entrypoint completion and blockers: `tests/fortran/<feature>/policy/`.
- Canonical byte-for-byte ordinary non-`bind(C)` generated-output regression:
  one focused owner under `tests/fortran/infrastructure/codegen/`, covering the
  generated C binding, C header, and Fortran adapter without duplicating the
  snapshot across feature directories.
- Stages 2-4 projection-ownership relocation: focused
  `tests/fortran/infrastructure/codegen/` tests. Existing feature-local tests
  remain unchanged regression evidence and must pass.
- Selective adapter membership, direct binding call targets, and generated
  artifact sets introduced by later adoption stages: the owning
  `tests/fortran/<feature>/codegen/` and infrastructure owners for
  cross-feature artifact invariants.
- Direct and mixed compiled behavior for each adopted feature: its Stage 7
  fixtures and owning `tests/fortran/<feature>/end_to_end/` tests. A direct
  fixture with generated support operations proves support-only membership,
  while a fixture with neither adapters nor support proves complete generated
  Fortran source/object absence.
- Zero-adapter materialization, compile scheduling, link-driver selection,
  Makefiles, manifests, and progress records:
  `tests/fortran/infrastructure/building/pipeline/` and
  `tests/fortran/infrastructure/building/compiling/`.
- Compiled Fortran feature behavior: the owning
  `tests/fortran/<feature>/end_to_end/` directory. The scalar adoption starts by
  replacing the current assumption that every procedure in
  `tests/fortran/data_types/end_to_end/test_value_and_bind_c.py` appears in the
  generated adapter.
- Direct-entrypoint runtime and clean-build performance: benchmark correctness
  and artifact preflight outside timing, paired `pyperf` results, and benchmark
  tooling tests under `tests/tools/`. These supplement rather than replace
  feature-local correctness evidence.
- Generated and edited semantic-contract parity:
  `tests/fortran/infrastructure/semantic_pyi/` plus feature-local end-to-end fixtures.

Artifact assertions protect observable generated and build behavior: whether
an adapter source/object exists, which native operations it exports, which
symbol the binding calls, and which link driver is selected. Tests should not
freeze private class names, complete plan field inventories, or incidental
source formatting.

## Definition Of Goal 2 Fortran Readiness

Selective direct Fortran routing is ready to claim only when:

- [x] Stage 0 proves that binding lowering cannot read bridge facets and
  Fortran lowering cannot read binding facets for ordinary or generated
  support procedures;
- [x] Fortran source, generated `.pyi`, and source-free `.pyi` inputs preserve
  the `bind(C)` ABI fact, native symbol, and selected per-operation route;
- [x] all-direct and mixed Fortran routes pass through the shared plan and
  pipeline changes without changing ordinary-procedure behavior;
- [x] zero-adapter generated artifacts, compilation, linking, manifests,
  Makefiles, verbose output, and imports have focused evidence; and
- [x] each checked Goal 2 feature row has policy, codegen, artifact,
  compilation, runtime, and semantic-contract parity evidence.

Goal 2 completion does not claim that PRIK accepts native C inputs.

## Scalar Character Descriptor Lanes

Independent of Goal 3. Every `allocatable` and `pointer` scalar `character`
form is implemented. This section records the completed design.

### Current State (2026-08-19, updated after implementation)

The attribute, not the length, decides the lane. A dummy carrying `allocatable`
or `pointer` will not accept a plain temporary as its actual argument, so policy
completes the adapter local — attribute, length, and release — for each one.

| Form | Behavior |
| --- | --- |
| `allocatable`/`pointer`, `intent(in)` | Supported. The adapter builds the matching local from the binding byte buffer. |
| `allocatable`/`pointer`, `intent(out)` | Supported. Projected descriptor result with `c_malloc` storage and a length readback. |
| `allocatable`/`pointer`, `intent(inout)` | Supported. Call-local character-buffer input plus a projected descriptor result. |
| `allocatable` function result | Supported. Moved out through an allocatable dummy, so an unallocated result is `None` rather than a read of storage that was never established. |
| `pointer` function result | Supported. Copied out of the associated target. |

Declared length (`len=n`) and deferred length (`len=:`) both work in each row.
A descriptor local spells the declared length rather than the runtime one,
because neither side is deferred there and the standard requires them to agree.

A `pointer` local is storage the adapter allocated, so its release is a
completed decision: an `intent(in)` dummy cannot reassociate, so the adapter
always frees it; a mutable dummy is freed only while it still identifies that
allocation. A native procedure that reassociates or nullifies a mutable pointer
dummy therefore orphans the adapter's allocation — the alternative, freeing the
seed unconditionally, double-frees the ordinary "deallocate then reallocate"
idiom, so the leak is the deliberate choice.

The contract vocabulary now spells every character length in the first
subscription after `String`: `String[...]` assumed, `String[8]` explicit, and
`String[:]` deferred, with any array shape in a second subscription. That closed
a round-trip gap affecting every deferred-length *scalar*, including the
read-only lane that shipped first, whose generated contract previously said
plain `String` (assumed length) and failed to rebuild. It also replaced the
one-subscription array spellings (`String[::]`, `String[n]`), which the printer
emitted but the parser rejected or silently read as a scalar length.

The bridge fact is `ArgumentPolicy.character_local`, set by
`_character_local_policy` and projected onto `BridgeArgumentPlan`. The C ABI is
unchanged in every lane: the binding still passes a byte buffer and a length.

### Selected Design For `intent(inout)`

The dummy is a Python-visible **input argument** that also projects a
**descriptor-backed result**. Output transport belongs to the result facet and
to the bidirectional entrypoint, not to argument presence.

- [x] Complete one policy action for a deferred-length allocatable string
  update: the argument keeps a plain character-buffer input
  (`CALL_LOCAL_INPUT`, not `COPY_IN_OUT`), and a `ResultPolicy` carries the
  existing `ScalarDescriptorResultPolicy` unchanged.
- [x] Let a Python-visible argument produce a `ResultPolicy`. The gate in
  `_hidden_result_policies` stayed `python_visible=False`; instead the dummy
  owns **two** completed decisions, following the getter/setter precedent.
  `RESOLVED_UPDATE_RESULT_OWNERSHIP_POLICY_METADATA` holds the result facet,
  resolved from the same native-output context an `intent(out)` dummy uses, so
  every hidden-result validator keeps checking a real result contract instead of
  being relaxed against the argument's input decision. Hidden outputs and
  fixed-length replacements keep their current selection.
- [x] Let the entrypoint carry the descriptor output parameters it already
  produces for `intent(out)`. `ResultPolicy.updates_argument` names the fact
  through planning; the output group is named `<name>_output` (the suffix the
  existing required-descriptor copyout already uses) so it cannot collide with
  the input's own name and length parameters. No new `OptionalMode`.
- [x] Do not relax the `descriptor_boundary` equivalence with descriptor
  optional modes in `pipeline/wrapper.py`. The argument stays a non-descriptor
  `REQUIRED` input, so the invariant held exactly and was not touched.
- [x] Reuse the existing binding result path that builds a Python string from
  the returned pointer and length and releases the C storage. The C binding
  needed no change at all.
- [x] Prove the round trip end to end. `tests/fortran/strings/end_to_end/`
  compiles and imports the fixture: a reallocated dummy returns the new value,
  a deallocated dummy returns `None`, an unallocated optional returns `None`,
  and a zero-length value stays `''`.

The one genuinely new emitted-code mechanism is in the adapter: the descriptor
readback reads the argument's call-local allocatable rather than a result-local
of its own, since the native procedure reallocates that local in place.

### Rejected Alternatives

Both were attempted and reverted; the notes prevent re-deriving them.

- **Relaxing `descriptor_boundary ⟺ descriptor optional mode.** Makes the
  invariant conditional and removes its ability to catch inconsistencies.
- **A new `OptionalMode` for string updates.** `OptionalMode` describes argument
  presence. Setting `REQUIRED_DESCRIPTOR` also routes the C binding into
  `_lower_argument_required_descriptor`, which calls
  `PrimitiveScalarTypeRegistry.type_for` and rejects `String`.
- **One ownership decision for both facets.** Reusing the argument's
  `CALLER/CALL_LOCAL` input decision as the result's ownership forces
  `_scalar_descriptor_result_blockers` and the plan's hidden-result checks to be
  relaxed on owner, destruction, nullability, descriptor boundary, and Python
  action at once — exactly the checks that would otherwise catch a wrapper
  returning the pre-call value. The second decision keeps them enforcing.

## Goal 3 — Initial Direct-Only C Adoption

Start Goal 3 only after Goal 2 is complete. Goal 3 adds C as a native input
language by reusing the completed binding-to-entrypoint path. It does not add a
generated native C adapter: an operation is either directly supported or
blocked by completed policy before planning and source generation.

### Initial Scope And Readiness Boundary

Goal 3 is deliberately a primitive lane, not general C-wrapper support. Its
required positive scope is:

- externally linkable, non-variadic C functions using the ordinary C calling
  convention;
- modeled C arithmetic primitives passed by value and returned by value,
  together with `void` results;
- one-level pointers to those same primitives when an authoritative contract
  selects one supported scalar-reference, rank-zero storage, projected-output,
  or primitive-array interpretation; and
- renamed symbols and route-neutral `@native_call(...)` projections composed
  only from mechanisms already supported by the shared direct entrypoint.

“Primitive” means the complete modeled arithmetic set, not an unspecified
sample: C `_Bool`; plain, signed, and unsigned character and integer types;
`short`, `int`, `long`, and `long long` in both signednesses; `float`, `double`,
and `long double`; the corresponding standard C complex types; and resolved
standard scalar typedefs such as fixed-width integers and `size_t`. Target ABI
facts may map multiple C spellings to one semantic storage identity, but policy
and lowering must either preserve an exact compatible C ABI or reject the
spelling. They must never narrow, change signedness, or choose a nearby dtype.

Initial readiness does **not** include multi-level pointers, pointer-valued
results, strings or character buffers, nullable pointers, ownership transfer,
retained native pointers, structs or unions, global state, callbacks, variadic
functions, nonstandard calling conventions, `volatile` or atomic access, or
general C feature adoption. Those remain fail-closed follow-on work. A single
edited numeric `T *`-to-array path is required because it proves the contract
can resolve the central pointer ambiguity; it does not claim the complete C
array feature, returned arrays, `_Bool` array compatibility, or pointer
ownership support.

### Goal 3 Implementation Record (2026-08-21, audited 2026-08-21)

Goal 3 is implemented only for its documented direct-only primitive lane. C
implementation sources and source-free C-native semantic contracts use
explicit public inputs; policy either selects the user C symbol directly or
raises a stable diagnostic before target ABI probing, generated files, or
native build commands. Source preprocessing runs before parsing, exactly as it
does on the C inspection routes, so it is the one compiler invocation that
precedes that decision. The C scalar and one-level-pointer matrices have
source and authoritative-contract compiled evidence under the named C feature
owners.

This is not general C adoption. Callbacks, aggregates, variadics, unsupported
calling conventions, ownership/retention or nullable pointer contracts, raw
addresses, pointer results or reassociation, and Boolean array promotion stay
fail-closed. Later C forms remain in the post-goal backlog below.

The follow-up audit closed these defects, each with focused C evidence:

- module variables, enum constants, and aggregate type declarations of a C
  translation unit reached wrapper planning and generated a Fortran adapter
  module; they now fail with `C_DIRECT_NATIVE_GLOBAL_STATE`,
  `C_DIRECT_ENUM_CONSTANT`, `C_DIRECT_MACRO_CONSTANT`, and
  `C_DIRECT_AGGREGATE_TYPE` before planning;
- a declaration the C parser could not model was silently dropped from a
  wrapper build's public API and now raises `C_DIRECT_UNMODELED_DECLARATION`;
- `T[:] | None` and `T[()] | None` silently lost their nullable spelling and
  now raise `C_DIRECT_NULLABLE_POINTER`;
- a route-neutral reorder resolved each argument's Python conversion against
  the wrong declared type;
- the documented `Arg(i).shape[d]` array promotion was rejected, because a
  binding-owned extent producer was mistaken for the argument's own transport
  slot;
- an exact C declaration plan was built for Fortran `bind(C)` operations too,
  which broke every Goal 2 direct route carrying a string, derived object, or
  callback; and
- C wrapper builds did not preprocess their sources, so any directive other
  than `#include` was unparseable.

### Stage 0 — C Language And Contract Inputs

#### Current Stage 0 Status (2026-08-21)

Stage 0 is **implemented for the initial direct-only primitive lane**. The
public `build_c_extension()` accepts explicit C implementation sources and a
`preprocessing` configuration that defaults to the selected C compiler, so a
wrapped translation unit is expanded before parsing and its include provenance
decides what the wrapper may expose;
`build_pyi_extension(..., native_language="c", native_c_sources=...)` marks
source-free semantic contracts as C-native; and the CLI requires
`--language c` for that identity. Native language is retained in compilation
records, manifests, replay, verbose output, and Makefiles. C-only builds use a
C toolchain, while mixed language link selection uses all recorded object
languages. None of these routes infer C identity from a file suffix, compiler,
missing Fortran source, or `@native_abi("c")`.

C conversion preserves source language and C ABI provenance, including exact
spellings, qualifiers, pointer depth, result transport, symbols, variadic and
function-pointer facts. Starter contracts remain extraction output even when a
form is not wrappable; completed policy blocks that form only when a wrapper is
requested. C-owned policy, codegen, pipeline, and compiled end-to-end evidence
now live under `tests/c/primitive_scalars`, `tests/c/primitive_pointers`, and
`tests/c/infrastructure/building`.

- [x] Add C source conversion preserving `source_language = "c"` on semantic
  modules, declarations, and arguments.
- [x] Emit authoritative source-free C semantic contracts for the initial
  primitive lane. Function-pointer parameters currently serialize as the
  `CFunctionPointer` placeholder built by `prik/semantics/c2ir.py`, which
  `prik.contracts` does not export and the generated import line omits. Reject
  that operation with a documented out-of-scope diagnostic before wrapper
  planning; do not expand Goal 3 into callback adoption and do not leave a
  spelling that only PRIK's own `.pyi` parser accepts.
- [x] Preserve `source_language = "c"` on native inputs and build records.
  `build_pyi_extension(..., native_language="c", native_c_sources=...)`
  selects source-free C identity explicitly, with `input_c_compiler`; the CLI
  exposes the same explicit C inputs.
- [x] Treat a C procedure as C ABI by language identity. Do not require or
  synthesize `@native_abi("c")`; that decorator remains the source-free
  Fortran spelling for an original `bind(C)` procedure.
- [x] Preserve C symbols, `void` versus value returns, typedef-resolved scalar
  types, pointer depth, qualifiers, structs, and function-pointer facts needed
  by completed policy. Do not infer ownership, nullability, or aggregate layout
  merely from pointer or typedef syntax. Function-pointer facts are retained as
  origin provenance behind the placeholder named above.
- [x] Resolve each modeled arithmetic spelling to an exact target ABI fact and
  a supported lowering identity before policy. Preserve signedness, width,
  complex representation, original compatible declaration facts, and typedef
  provenance. A semantic dtype mapping alone must not authorize a direct call.
- [x] Classify linkability and callable ABI facts before policy: reject
  translation-unit-local symbols, variadic functions, and unsupported
  `volatile` or atomic access with named diagnostics. A declaration whose
  calling convention or other compiler attribute the parser cannot model is
  rejected as `C_DIRECT_UNMODELED_DECLARATION` rather than being accepted with
  the attribute discarded. An external name with no definition in any supplied
  native input is **not** rejected: declaring an API here and linking its
  implementation through `--native-objects` or `--native-library` is the
  supported multi-input workflow, so an unresolved symbol stays a link-time or
  import-time error.
- [x] Add language-owned parsing, semantic-contract, and diagnostic tests
  under `tests/c/` without importing Fortran-specific fixture helpers.

#### Conservative C Starter-Contract Defaults

A one-level pointer declaration cannot prove what its pointee count denotes.
`double *x` is equally a scalar passed by reference and a pointer to the first
element of an array, and no amount of effective-signature inspection
distinguishes them. Only the library's author knows, so the starter contract
commits to the least-assumptive reading —
**one scalar passed by reference** — and the user promotes it to an array by
editing the semantic `.pyi`. That edit is the intended workflow, not a
workaround: it is where the contract earns its place.

Everything the declaration *does* prove is preserved exactly. Conversion still
must not infer rank, shape, direction, nullability, ownership, or lifetime.

| C declaration | Default generated semantic `.pyi` | Preserved meaning |
| --- | --- | --- |
| `T value` | `value: T` | Primitive scalar passed by value. |
| `T *value` | `value: T` with `@native_call([Addr(Arg(i))])` | One scalar passed by reference. The user refines it to array storage in the contract. |
| `const T *value` | `value: T` with `@native_call([Addr(Arg(i))])`, with `const` retained in origin and policy facts | Same handoff as `T *`; `const` is recorded as provenance and does not by itself change the public contract. |
| `T **value` | `value: Addr[2](T)` | Two native pointer levels preserved for a stable unsupported diagnostic; initial Goal 3 blocks the operation. |
| return `T` | `-> T` | Direct primitive scalar result. |
| return `T *` | `-> Addr(T)` | Raw pointer result with no invented ownership, lifetime, NumPy storage, or destruction policy; initial Goal 3 blocks the operation. |

An authoritative semantic `.pyi` supplies the API meaning the declaration could
not. It may promote the by-reference scalar default to `T[n]` or `T[:]` for
proved array storage, keep `T[()]` for caller-provided rank-zero storage, or
restate `Addr(T)` deliberately as a raw address. `Addr(Arg(i))` requests the
address of call-local scalar storage. Mutation of that temporary is discarded
unless the contract instead exposes rank-zero mutable storage or projects an
output through `Returns["name", T]` and `Return(...)`.

For ordinary wrapper functions, direction is expressed by the visible call
shape, mutable storage, projected results, and `@native_call(...)`; `In(T)`,
`Out(T)`, and `InOut(T)` are reserved for exact `@prototype` declarations and
must not be recommended for this edit. Nullability would use an explicit
`| None`, but nullable pointers are outside initial Goal 3.

Promoting a pointer argument to an array is a coordinated contract edit, not
an annotation-only change. For a native operation whose effective arguments
are an element count followed by `double *values`, the conservative starter
contract is equivalent to:

```python
from prik.contracts import Addr, Arg, Float64, Int32, native_call

@native_call([Arg(0), Addr(Arg(1))])
def scale(n: Int32, values: Float64) -> None: ...
```

If the author knows that `values` addresses `n` elements, an edited contract
can expose only the array and derive the native extent from its shape:

```python
from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).shape[0], Arg(0)])
def scale(values: Float64[:]) -> None: ...
```

A derived `Arg(i).shape[d]` extent is a binding-owned producer with its own
completed `SizeT` identity, so this edit is exact only when the native count
parameter is `size_t`. A native `int` count keeps its exact ABI by staying a
visible argument — `def scale(values: Float64[n], n: Int32) -> None` — which is
the form to use when the declaration is not `size_t`. Policy must never narrow
or widen the extent to make one of these fit the other.

The edit changes `Float64` to shaped storage **and** replaces
`Addr(Arg(i))` with the array's ordinary `Arg(i)` data-pointer projection. It
also decides rank, shape, C-order validation, mutability, and whether an extent
remains visible or is derived. Keeping the scalar address projection after
changing the annotation must fail contract validation.

The by-reference scalar default is the only reading conversion may assume for a
source spelling of `T *`. It is a conservative starter interpretation, not
proof that calling the native function with one element is safe. Conversion
must not infer an array from an adjacent extent parameter, infer output behavior
from a parameter name, interpret non-`const` as input/output, or interpret
`char *` as a string. Source-driven builds use that scalar interpretation only
when it is correct for the native operation; an array API requires the edited
semantic contract above.

A parameter written with C array declarator syntax carries extra source
provenance even though its effective ABI type is still a pointer. Preserve that
syntax separately from the ABI. An ordinary bound such as `T values[10]` does
not by itself prove an exact ten-element runtime contract, while `static 10`
states a minimum rather than an exact shape. Stage 0 must therefore settle how
open arrays and minimum bounds are serialized without strengthening either into
an invented exact extent; until the semantic vocabulary can state the proven
constraint, require an author edit or fail closed.

Raw pointer contracts do not imply ownership transfer, native retention safety,
or automatic cleanup. Serialization alone does not make an operation eligible:
completed policy must block any pointer contract whose ownership, lifetime,
nullability, transfer, or result behavior remains unsafe or unsupported.

- [x] Settle the one-level pointer default (decided 2026-08-18). A C signature
  cannot distinguish a by-reference scalar from a pointer to a first array
  element, so conversion emits the by-reference scalar and the user promotes it
  to an array in the semantic `.pyi`. Current conversion output already matches
  every row of the table above; the table was corrected to record the decision.
- [x] Add fixture evidence for every row of the table above. The present
  round-trip check re-parses generated text with PRIK's own `.pyi` parser, so
  it accepts a contract that a user could not import, and its unknown-type
  guard matches only the literal `Unknown`. A pointer-default change must fail
  a focused test instead of silently rewriting every generated C contract.
- [x] Add focused array-declarator evidence distinguishing effective pointer
  ABI from written array provenance. Prove that `[]`, `[n]`, and `[static n]`
  do not silently become the same exact-shape Python contract.
- [x] Prove the promotion path end to end once C builds exist: one fixture
  where a `T *` parameter stays a by-reference scalar, and one where an edited
  contract promotes the same native procedure to a NumPy array argument. This
  pair must assert the `Addr(Arg(i))`-to-`Arg(i)` projection edit, validation of
  rank/shape/order, compiled mutation behavior, and generated direct prototype.
  It is the user-facing demonstration that the contract, not the effective C
  signature, owns the Python API.

### Stage 1 — Direct-Only C Policy

- [x] Reuse `NativeEntrypointAction.DIRECT_C_ABI` for supported C operations
  and complete eligibility before `WrapperPlanner` starts. Do not introduce a
  C-adapter action or fallback.
- [x] Replace the present Fortran-only route test with language-aware completed
  policy. An ineligible Fortran operation may select its generated Fortran
  adapter; an ineligible C operation must instead become unsupported with a
  named diagnostic. It must never inherit
  `GENERATED_FORTRAN_ADAPTER` merely because it lacks a Fortran `bind(C)` fact.
  This covers every wrapped surface of a C translation unit, not only its
  callables: module variables, enum and macro constants, and aggregate type
  declarations have no direct entrypoint, so they are rejected with named
  diagnostics rather than lowered through generated Fortran accessors.
- [x] Reuse the entrypoint passing conventions and route-neutral
  `@native_call` projections completed in Goal 2. A C operation that needs an
  unsupported conversion, ownership, lifetime, callback, aggregate, or result
  mechanism must fail with a documented policy diagnostic.
- [x] Complete the selected meaning of every one-level primitive pointer before
  planning: call-local scalar address, caller-provided rank-zero storage,
  hidden output storage, or shaped primitive-array data. Record passing,
  mutation visibility, writeback, result projection, rank/shape/order, and
  lifetime from the semantic contract; do not rediscover the choice from
  pointer depth or `const` in planning or binding generation.
- [x] Preserve `const` on the exact native entrypoint prototype and forbid
  output/writeback contracts that contradict it. A non-`const` pointer permits
  native writes but does not by itself make them Python-visible. The
  contradiction check reads preserved source declarations, so it applies to the
  C-source route; a source-free contract has no `const` fact to contradict and
  is authoritative on its own terms.
- [x] Keep C pointer nullability distinct from Fortran optional presence. A
  nullable C pointer may receive `NULL`, but it does not imply a hidden
  presence convention or omitted native argument. Initial Goal 3 blocks this
  form; the rule governs its later adoption.
- [x] Define C `_Bool` through the same public `Bool` contract: accept Python
  `bool` and `numpy.bool_`, return Python `bool`, and require an explicit safe
  mechanism before treating NumPy Boolean array storage as C `_Bool` array
  storage.
- [x] Complete all transfer, ownership, destruction, mutation, writeback,
  nullability, result projection, and release facts before planning, following
  the same policy boundary as Fortran.

### Stage 2 — Planning, Lowering, And Pipeline Reuse

- [x] Make supported C operations produce the same always-present entrypoint
  facet and no bridge facet. The C binding consumes only binding plus
  entrypoint and calls the user C symbol directly.
- [x] Carry an exact C declaration plan for every direct parameter and result.
  C binding generation must not reconstruct a user prototype from a
  Fortran-oriented scalar spelling or width alone. It must use the completed C
  ABI type, signedness, qualifiers, pointer depth, function-result transport,
  symbol, and calling convention selected before planning. Only a C-source
  operation carries this plan: a Fortran `bind(C)` procedure keeps its
  established backend-projected prototype, which remains the only direct route
  that can lower strings, derived objects, and callbacks. Policy records the
  preserved declaration text and resolved identity; the C binding generator
  owns the canonical spelling a source-free contract does not preserve, and
  emits the standard header a preserved typedef spelling needs.
- [x] Reuse Goal 2 binding-local extraction, validation, temporary storage,
  passing-convention lowering, writeback, cleanup, and Python-result paths
  whenever the completed plans are identical. Add a new lowering mechanism
  only when a genuinely new planned C ABI action requires it.
- [x] Generate no native C adapter source or object. Verify that an
  adapter-required C operation fails before files are written or compiler
  commands run.
- [x] Compile and link C inputs through language-aware native build records.
  Select the final link driver and runtime dependencies from all input and
  generated object languages rather than from adapter presence.
- [x] Define one public build input for C implementation sources and one way to
  mark a source-free semantic `.pyi` as C-native. Preserve that identity in
  saved manifests and rebuilds; do not infer it from a filename, compiler
  executable, absence of Fortran source, or `@native_abi("c")`.
- [x] Cover source-driven and source-free semantic-contract builds, saved
  generated artifacts, Makefiles, manifests, verbose output, and imports.

### Stage 3 — C Scalar Baseline

The scalar baseline is complete only when every row below has one exact target
mapping and the same semantic identity is accepted by policy, planning, C
prototype generation, binding conversion, and compiled runtime tests. The
“current gap” column records why existing C semantic conversion is not yet a
wrapper-support claim.

| C primitive family | Required semantic/lowering coverage | Current gap to close |
| --- | --- | --- |
| `_Bool` | `Bool`/measured Boolean storage; Python `bool` result | Direct C policy/build route is absent; `_Bool` arrays remain outside the baseline. |
| plain, signed, and unsigned `char` | Target-probed signedness and width; `Int8` or `UInt8` without guessing | Unsigned lowering is absent, and the generated C prototype must retain the compatible native character ABI. |
| signed `short`, `int`, `long`, `long long` | Exact measured `Int8`/`Int16`/`Int32`/`Int64` identity | C `int` deliberately retains public name `Int` while current first-lane policy accepts only fixed-width names; normalize the lowering identity without losing source spelling. |
| unsigned `short`, `int`, `long`, `long long` | Exact measured `UInt8`/`UInt16`/`UInt32`/`UInt64` identity | The semantic converter models these names, but shared primitive policy and binding lowering do not yet adopt them. |
| `float`, `double`, `long double` | Exact measured `Float32`/`Float64`/`Float128` identity | `Float32`/`Float64` have shared lowering; `long double` still needs an exact supported target mapping and backend path. |
| `float _Complex`, `double _Complex`, `long double _Complex` | Exact measured `Complex64`/`Complex128`/`Complex256` identity and C function-return ABI | The first two have shared scalar lowering; extended complex still lacks it, and all three need direct-C compiled evidence. |
| resolved standard scalar typedefs | Fixed-width integer aliases, `size_t`, and other probed arithmetic typedefs reuse the exact underlying ABI while retaining typedef provenance | `SizeT` has a backend spelling but is absent from current first-lane policy; unresolved or unsupported typedefs need pre-planning diagnostics. |
| `void` | Function result only, producing Python `None` | C semantic conversion preserves it, but no direct C build proves the result path. |

- [x] Close every row of the primitive matrix or narrow the documented goal by
  an explicit user decision. “Initially supported” must not hide an accidental
  intersection of converter and codegen registries.
- [x] Add C scalar fixtures and compiled end-to-end tests for every adopted
  arithmetic spelling: by-value inputs, direct value returns, `void` returns,
  `const T *` call-local scalar inputs, mutable `T *` rank-zero storage, and
  contract-projected scalar outputs. Source conversion must not infer the
  output forms; authoritative edited contracts select and prove them.
- [x] Check Python boundary behavior, not only native call success: accepted
  Python and NumPy scalar inputs, overflow/range diagnostics, exact NumPy
  numeric result dtype, Python `bool` Boolean results, complex values, and
  mutation visibility for each pointer contract.
- [x] Cover renamed symbols and route-neutral projections, including reordered
  arguments, `Addr`, `Value`, hidden result storage, and typed literals where
  the C contract supports them.
- [x] Prove from generated artifacts and build records that the binding calls
  the user symbol and no native C adapter source or object exists.
- [x] Add at least one parseable C operation whose unsupported ABI or transfer
  mechanism produces the documented pre-planning diagnostic.

### Stage 4 — Primitive Pointer Contracts And Array Promotion

This stage completes the promised one-level-pointer equivalent of the scalar
lane. It does not infer pointee count from the C ABI and does not turn Goal 3
into general pointer support.

- [x] For every adopted primitive, prove the generated `T *` default is a
  Python-visible scalar plus `Addr(Arg(i))`, with one call-local native element.
  Native mutation is not returned unless an edited contract requests it, and
  the generated docstring says so instead of promising an in-place update of
  caller storage that does not exist.
- [x] For every adopted primitive, prove an authoritative contract can expose
  caller-provided rank-zero storage with `T[()]` and can project a hidden scalar
  output with `Returns[...]`/`Return(...)`, with exact mutation and tuple-result
  behavior.
- [x] Preserve `const T *` in the generated C prototype and reject a
  contradictory mutable/output contract. Preserve `restrict` as provenance;
  it must not invent ownership or an array shape.
- [x] Prove both edited array spellings compile and call the same user symbol:
  a visible extent argument that keeps the native count's exact declared type,
  and a derived `Arg(i).shape[d]` extent whose native count is `size_t`.
- [x] Prove one native `T *` operation through both contract meanings: the
  conservative one-element scalar-reference form and an edited numeric NumPy
  array form. The array form must replace `Addr(Arg(i))` with `Arg(i)`, define
  rank/shape/C order and mutation, validate zero and nonzero extents, compile,
  call the same user symbol directly, and generate no C adapter.
- [x] Reject `T **`, returned `T *`, `T * | None`, retained pointers, raw owned
  addresses, pointer reassociation, and `_Bool *` array promotion with stable
  pre-planning diagnostics until their separate ownership, nullability,
  lifetime, or storage mechanisms are adopted.

### Post-Goal 3 C Feature Backlog

The rows below are later adoption work and do not block the narrowly defined
initial readiness above. Move a row into an implementation goal only with its
complete policy, planning, lowering, build, documentation, and compiled
evidence. Do not weaken a feature contract or silently generate a C adapter to
mark it complete.

| Feature boundary | Later C direct-only evidence | Special acceptance concerns |
| --- | --- | --- |
| Strings and character buffers | [ ] | Length source, terminators, encoding, embedded NUL, mutation, ownership, and returned-buffer lifetime. |
| Enumerations and constants | [ ] | Underlying integer ABI, exported constants, and no invented Python enum layout. |
| Nullable values | [ ] | Null-pointer policy, omitted Python arguments, and output projection without invented native optionality. |
| Raw addresses and native pointers | [ ] | Pointee type, pointer depth, qualifiers, nullability, ownership, target lifetime, and reassociation or writeback. |
| Complete numeric and Boolean arrays | [ ] | All element types, dtype, rank, shape, order, alignment, mutability, copy/writeback, zero extents, and explicit C `_Bool` storage handling beyond the one Goal 3 promotion proof. |
| Structs, fields, and methods | [ ] | By-value versus pointer ABI, opaque/accessor routes, construction, destruction, borrowing, and proven layout. |
| Native global state | [ ] | Direct exported storage versus generated accessors, mutability, lifetime, and ownership. |
| Overloads and generated dispatch | [ ] | Each selected C symbol owns an entrypoint action; dispatch owns no shared adapter route. |
| Immediate callbacks | [ ] | Function-pointer ABI, callback argument/result conversion, GIL entry, exception handling, and call-scoped lifetime. |
| Error/status projection and GIL release | [ ] | Call target remains independent of status checking, cleanup order, and GIL policy. |
| Multi-source and external-library builds | [ ] | Native symbol scope, object/library order, dependencies, runtime requirements, and final link-driver selection. Symbol scope includes ELF interposition: a direct call to a user symbol whose name is also exported by an already-loaded library (for example glibc's weak `step`) currently binds to that library, not to the wrapped definition. Deciding this needs a link-visibility policy that applies to both languages. |

### Goal 3 Required Evidence Owners

- Completed C policy and blockers: `tests/c/<feature>/policy/`.
- Direct call targets, signatures, and generated artifact sets:
  `tests/c/<feature>/codegen/` plus focused cross-language infrastructure
  owners where the pipeline invariant spans languages.
- Compiled behavior: `tests/c/<feature>/end_to_end/`, using C-owned fixtures
  and the same named public invariants as the corresponding Fortran feature.
- C parsing and semantic-contract parity: the language-owned parser and
  semantic-format tests under `tests/c/`.
- Zero-adapter materialization, compilation, linker selection, Makefiles,
  manifests, progress output, and imports: the relevant pipeline and compiling
  owners extended with C-native inputs.
- The initial lane should use named `primitive_scalars` and
  `primitive_pointers` feature owners. Semantic fixture parametrization covers
  every C spelling; policy and codegen parametrization covers every resolved
  lowering identity; compiled fixtures cover every ABI family and target-width
  case. None of those layers substitutes for the others.

## Definition Of Initial C Readiness

Initial direct-only C wrapper support is ready to claim only when:

- [x] every row in the Stage 3 primitive matrix has an exact supported ABI path
  or the goal was explicitly narrowed before implementation;
- [x] by-value scalars, value and `void` results, and the Stage 4 one-level
  pointer forms pass through C source and authoritative source-free C semantic
  contracts;
- [x] the same `T *` native signature has compiled scalar-reference and edited
  NumPy-array contract evidence, including the required projection change;
- [x] supported C operations call their user symbols without a native adapter;
- [x] unsupported adapter-required operations fail at completed policy with a
  documented diagnostic and no partial generated artifacts;
- [x] every out-of-scope pointer, callback, aggregate, variadic, calling
  convention, and unsupported scalar-ABI form named above fails before
  planning, files, or compiler execution;
- [x] zero-adapter compilation, linking, manifests, Makefiles, verbose output,
  and imports have focused evidence;
- [x] Goal 2 Fortran direct and adapted routes remain green after shared-path
  reuse; and
- [x] the user-facing language feature matrix lists only C rows proved by
  compiled runtime tests.
