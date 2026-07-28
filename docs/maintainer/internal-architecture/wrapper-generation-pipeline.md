---
title: Wrapper Generation Pipeline
audience: maintainers
prerequisites: semantic passes, code generation design
related: runtime-layer.md, ownership-tracking.md, ../roadmap/wrapper-plan-migration-checklist.md
status: maintained
publication: draft
---

# Wrapper Generation Pipeline

This page describes the canonical wrapper-plan generation route. It covers the
completed scalar, string, array, native-handle, derived-type, class, callback,
module-state, generic, and build surfaces.

## Architectural Boundary

All semantic policy must be complete before wrapper planning begins. Post-IR
policy completion owns
object kind, ownership, transfer, destruction, mutability, writeback,
nullability, output projection, release responsibility, storage mode, getter
behavior, native setter assignment, and Python setter exposure.

Planning projects those completed decisions into one editable `ModulePlan`.
Validation checks that the projections agree. Binding and bridge generation
then dispatch only from completed selectors into small named lowering methods;
they do not reconstruct policy from datatype, `intent`, shape, alias flags, or
local memory checks.

Native-source `intent` may be consumed while importing a source declaration to
propose default Python argument/result positions. It is not retained in the
semantic `.pyi` or post-IR ownership context. The editable Python signature,
`Returns[...]` projection, and ordered native-call mapping are authoritative.
Bridge entry dummies omit `intent`, leaving their storage permissive; that
contract controls wrapper copy-in, copy-back, and returned values, while the
compiled native procedure's own interface controls native access.

Within that contract, an explicit native-call list is exhaustive for native
dummy positions. Matching named `Returns[...]` items attach result positions to
visible `Arg(i)` entries automatically; direct function results remain the first
ordinary Python return item, while hidden native output dummies require explicit
`Return(...)` entries. Descriptor reassociation follows the same rule:
`Pointer(Arg(i))` without a projected return uses a call-local adapter and
discards reassociation, while a matching projected return requires storage that
can preserve association writeback.

Native transport overrides also live on that mapping. Primitive `Arg(i)` is a
value handoff and `Addr(Arg(i))` selects call-local address handoff. Wrapped
derived `Arg(i)` is a typed reference handoff and `Value(Arg(i))` selects exact
typed value handoff. `Returns[...]` never selects either ABI; it only assigns a
Python result position and writeback expectation. A derived `Value(...)` slot
does not expose aggregate layout at the C boundary: C still supplies an opaque
address, the bridge reconstructs the exact native type, and the Fortran compiler
applies the explicit interface's `VALUE` semantics at the typed call.

Standalone legacy externals use a completed declaration mode. Procedures whose
ABI is valid with an implicit interface, including classic BLAS/LAPACK
subroutines and scalar functions, lower to `external` declarations; optional,
descriptor-rich, polymorphic, or array-result procedures retain explicit
interfaces. The bridge dispatches this completed mode and does not reclassify
the signature.

The public direct-generation boundary is:

```python
complete_semantic_policies(module)
plan = WrapperPlanner().build(module)
artifacts = WrapperCodeGenerator().generate(plan)
```

`WrapperCodeGenerator.generate()` freezes the plan, runs the shared validator,
runs both backend preflight checks, lowers recursively to C and Fortran syntax
nodes, and asks the source printers to render those nodes. Build integration
compiles the rendered sources; it does not own datatype transfer policy.
Wrapper C/Fortran source printers and the semantic `.pyi` printer share
`x2py/wrapper_codegen/printers/`; no compatibility printer remains under the
legacy codegen package.

Wrapper builds have no legacy route or fallback. An unsupported completed plan
fails with its exact owner path before either backend emits source.

## Stable Tree and Datatype-Varying Records

The shared plan has stable module, namespace, and function orchestration:

```text
ModulePlan
  binding: BindingModulePlan
  bridge: BridgeModulePlan
  namespaces: NamespacePlan ...
    functions: FunctionPlan ...
      binding: BindingFunctionPlan
      bridge: BridgeFunctionPlan
      arguments: ArgumentTransferPlan ...
        binding: BindingArgumentPlan
        bridge: BridgeArgumentPlan
        native_call_slot: NativeCallSlotPlan
      results: ResultPlan ...
        binding: BindingResultPlan
        bridge: BridgeResultPlan
        native_call_slot: NativeCallSlotPlan | None
      native_call_slots: NativeCallSlotPlan ...
      lifecycle actions: LifecycleActionPlan ...
    variables: ModuleVariablePlan ...
```

Most datatype-specific work belongs to `ArgumentTransferPlan` and
`ResultPlan`. Each is one transfer with explicit binding and bridge views.
`ModuleVariablePlan` is the other intentionally datatype-sensitive surface,
because getter, setter, and native assignment behavior depend on the stored
value.

`FunctionPlan`, `NamespacePlan`, and `ModulePlan` remain orchestration records.
They own export names, call order, result order, runtime/GIL envelopes, and
aggregation, but not datatype policy.

Python-facing documentation is also a plan projection. The shared docstring
builder consumes completed namespace, module-variable, class, overload,
argument, result, and lifecycle records and stores the rendered text on the
owning plan nodes. C method-table emission and generated Python class assembly
only attach that text; neither backend infers signatures, ownership, mutation,
nullability, or exception behavior while rendering source.

`NativeCallSlotPlan` and `LifecycleActionPlan` are subordinate transfer
details. Native slots stay indexed on `FunctionPlan` because native ABI order
can interleave argument slots, result slots, literals, and helpers. Lifecycle
actions stay indexed there because copy-out, cleanup, and release order may
span several arguments and results or differ on failure. Argument and hidden
result slots are the same mutable records referenced from both their transfer
owner and the function-wide index; they are not duplicated policy.

## One Repeatable Transfer Algorithm

Use this sequence for scalars, strings, arrays, and future datatype families:

1. Post-IR policy completion classifies the value with `ObjectKind` and
   completes ownership, transfer, storage, nullability, mutability, projection,
   barrier actions, data action, and any justified copy reason.
2. Wrapper policy records the backend-neutral transfer and the ordered native
   slot. It must report a blocker instead of leaving a semantic choice for a
   backend.
3. `WrapperPlanner` mechanically projects one `ArgumentTransferPlan` or
   `ResultPlan`, adds symbolic handoff roles, and shares the corresponding
   `NativeCallSlotPlan` reference.
4. The shared validator checks graph consistency and common invariants, then
   dispatches by the completed `object_kind` to scalar, string, or ordinary-
   array validation.
5. Backend preflight dispatches by the same completed kind and action selectors
   and rejects combinations it cannot lower.
6. The binding lowers Python extraction or result construction. The bridge
   lowers ABI declarations, representation conversion, the ordered native
   call, and native result production. Both communicate through planned
   symbolic roles.
7. Function-level orchestration applies status handling and ordered lifecycle
   actions, aggregates Python results, and returns. Printers and build
   integration remain generic.

When adding a datatype, first extend semantic policy and its transfer record,
then add one named validator and one named lowering method per affected
backend. Do not add a parallel plan hierarchy or datatype branches to module,
namespace, or function traversal. Add a new typed action only when the existing
selectors cannot express a genuine semantic choice.

## Selector Vocabulary

The action axes are deliberately orthogonal:

| Selector | Question answered | Examples |
| --- | --- | --- |
| `ObjectKind` | What kind of object follows this route? | `SCALAR`, `STRING`, `NUMPY_ARRAY` |
| `source_kind` | Where is a result produced? | `direct_return`, `hidden_output` |
| `PythonBarrierAction` | How does the binding cross the Python boundary? | `SCALAR_VALUE`, `STRING_VALUE`, `ARRAY_STORAGE` |
| `NativeBarrierAction` | What native ABI transport is used? | `PASS_VALUE`, `PASS_CALL_LOCAL_ADDRESS`, `PASS_ARRAY_BUFFER` |
| `CodegenAction` | What ownership or transfer operation occurs? | `DIRECT_VALUE`, `CALL_LOCAL_INPUT`, `COPY_IN_OUT`, `COPY_OUT` |
| `BridgeDataAction` | What happens to the representation in the bridge? | `DIRECT_TRANSFER`, `ASSOCIATE_VIEW`, `COPY_REPRESENTATION` |
| `WritebackPhase` | When does a lifecycle operation run? | native mutation, copy-out, cleanup, release |

Hiddenness is not a transfer operation. A hidden scalar result therefore uses
`source_kind="hidden_output"` with `CodegenAction.DIRECT_VALUE`; hidden strings
and ordinary arrays use the same source kind with `CodegenAction.COPY_OUT`.

`NativeBarrierAction.PASS_ARRAY_BUFFER` identifies the Phase 6 ordinary-array
data-buffer ABI. Its handoff plan carries data, rank, extents, strides, and
itemsize. `PASS_NATIVE_DESCRIPTOR` is reserved for Phase 7 persistent native
descriptors and handles. Neither backend may substitute one for the other.
Array handoff shapes are completed bridge extents; native source bounds are
temporary import facts and must not appear in semantic `.pyi` or become extent
dependencies. A source dimension such as `0:LDB-1` therefore completes to
extent `LDB`, while the native procedure keeps control of its own indexing
bounds. When `PASS_NATIVE_DESCRIPTOR` also carries
optional absence, the completed optional mode lowers a valid call-local
placeholder descriptor plus a separate presence role. This keeps the bridge
entry ABI valid while presence dispatch omits the native dummy.

`DatatypeFamily` remains useful after object-kind dispatch for primitive
element spelling and conversion, such as integer versus real scalar types or
the element type of an ordinary array. It must not be used to rediscover
whether the transfer itself is a scalar, string, or array.

## Maintainer Inspection and Acceptance

Inspect the real records directly with normal Python prints. The primary path
is `complete_semantic_policies()` -> `WrapperPlanner.build()` ->
`WrapperCodeGenerator.generate()`. Generated artifacts from real passing
`tests/wrapper` cases are the behavioral oracle; plan unit tests cover action
and graph invariants. Production source and semantic-`.pyi` builds both use
this one path; unsupported completed policy is an error before lowering, not a
request to retry a legacy generator.

A wrapper-generation change is acceptable when:

- semantic decisions are complete before planning;
- datatype variation is confined to transfer, result, lifecycle, or
  module-variable records and their named handlers;
- scalar, string, and array routes use the same planning and validation
  sequence;
- binding and bridge consume the same shared roles and native-slot records;
- no backend infers policy or silently falls back to another action;
- focused plan tests, relevant wrapper runtime tests, documentation checks, and
  static analysis pass.
