---
title: Planning Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed policy
related: ../architecture.md, index.md, policy.md, codegen.md, ../codebase-map.md
status: maintained
publication: reviewed
---

# Planning Stage

## Purpose And Boundaries

`prik/planning/` mechanically projects policy-completed semantic IR into one
backend-neutral `ModulePlan`. It joins common transfer facts with explicit
binding, native-entrypoint, and bridge views, namespaces, stable native
symbols, lifecycle order, and build requirements. It may organize and validate
completed decisions; it may not reinterpret source declarations, choose
policy, or render text.

## Local Structure

```text
prik/planning/
├── __init__.py
├── models.py
└── planner.py
```

## What This Stage Receives And Produces

```text
policy-completed SemanticModule
  -> WrapperPlanner validates completed records and projects all three views
  -> editable ModulePlan
  -> freeze at WrapperGenerator boundary
  -> binding + entrypoint C generation
  -> entrypoint + bridge Fortran generation
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/planning/__init__.py`](../../../prik/planning/__init__.py) | Re-exports `WrapperPlanner` and the supported plan records. | A supported planning type or import path changes. |
| [`prik/planning/models.py`](../../../prik/planning/models.py) | `ModulePlan` and typed function, argument, result, bridge-call-slot, lifecycle, class, overload, binding, entrypoint, and bridge records form the editable plan tree. | Lowering needs a new *already completed* fact represented explicitly. |
| [`prik/planning/planner.py`](../../../prik/planning/planner.py) | `WrapperPlanner` validates policy, indexes declarations, allocates names, and projects deterministic binding, entrypoint, and bridge views; `_ClassPolicyCatalog` is a validated lookup. | A completed policy fact is projected or ordered incorrectly. |
| [`prik/planning/entrypoints.py`](../../../prik/planning/entrypoints.py) | Projects every auxiliary generated callable into the module entrypoint registry, including its implementation owner and structured C ABI. | An accessor, lifecycle, descriptor, origin, constructor, or callback operation changes its shared boundary. |

The private class-policy catalogue is a validated lookup, not another semantic
authority. The planner does not generate docstrings or source.

The stable plan tree keeps orchestration at module, namespace, and function
levels and confines datatype variation to transfers, results, lifecycle
actions, and module variables:

```text
ModulePlan
├── BindingModulePlan
├── NativeEntrypointModulePlan
│   └── NativeEntrypointOperationPlan
│       └── NativeEntrypointSignaturePlan
├── BridgeModulePlan
└── NamespacePlan (root and child namespaces)
    ├── FunctionPlan
    │   ├── ArgumentTransferPlan
    │   ├── ResultPlan
    │   ├── NativeEntrypointParameterPlan
    │   ├── BridgeCallSlotPlan
    │   └── LifecycleActionPlan
    └── ModuleVariablePlan
```

Each callable, argument, result, and module variable owns explicit binding,
entrypoint, and bridge views. Binding records own Python extraction and result
construction. Native-entrypoint records own the complete bidirectional C ABI:
the exported symbol, direct return, ordered parameter groups, value/address
projection, presence and length fields, descriptors, and hidden outputs.
Bridge records own adapter-local representation conversion and the invocation
of the original Fortran procedure.

`NativeEntrypointModulePlan.operations` is the authoritative registry for
externally linked generated helper callables that are not ordinary wrapped
functions. Each operation stores one collision-safe key and symbol plus a
structured signature of ordered ABI values. The registry covers constructors,
accessors, derived-origin transactions, destruction and holder helpers,
native-array operations, and callback trampolines. Each record also identifies
whether the binding or bridge implements the callable; the opposite side uses
the same record as its declaration/call contract. Static CPython helpers and
bridge-internal procedures are deliberately absent.

`NativeEntrypointFunctionPlan.results` includes public Python results and
binding-private outputs such as native status and message values. A public
`ResultPlan` shares its exact entrypoint-result object; a private output remains
available to C prototype, storage, and call lowering without exposing a bridge
call slot to the binding generator.

An argument or hidden result shares its `BridgeCallSlotPlan` with the
function-wide original-Fortran call ordering index. That slot is not the C ABI
parameter order: `NativeEntrypointParameterPlan` records the latter explicitly.
Function orchestration owns call, result, lifecycle, GIL, and status order
without becoming datatype policy.

`OverloadPlan` stores ordered candidates, exact match records, receiver
conventions, and one candidate ID per overload set. Generated dispatch chooses
an ID before making a native call, preserving first-match behavior for
overlapping optional domains without speculative calls.

## Module Algorithms

### `planner.py`: completed policy to namespace tree

`WrapperPlanner.build()` is the public boundary. It accepts one
policy-completed `SemanticModule` and dispatches it through the planner's
visitor. The completed-policy accessors used during projection reject missing
or blocked records, so planning cannot fill in a default.

For each module, the planner resets its derived-type and field indexes, then
assigns backend symbols, qualifying only genuinely colliding native type names.
It projects direct functions and variables, then uses `_ClassPolicyCatalog` to
join each public class to its completed derived-type, surface, method, and
overload policies. The catalogue is read-only: it maps existing owner paths to
their semantic declarations without deciding policy again.

The planner attaches class and overload callables to the function collections
that need their native entrypoints. It completes generated symbols, adds every
required parent namespace, and creates namespace plans in root-first path
order. Finally it collects headers selected by completed descriptor-handle
plans and returns one editable `ModulePlan`.

### `models.py`: shared plans and three lowering views

`models.py` defines editable `StageRecord` plans. `ModulePlan` is the root;
each `NamespacePlan` groups the public functions, variables, derived types,
classes, and overloads for one Python path. A `FunctionPlan` owns call-wide
ordering, while its transfers, results, entrypoint parameters, bridge call
slots, and lifecycle actions carry the datatype-specific details.

Binding, native-entrypoint, and bridge records are separate facets of the same
planned operation. For example, an `ArgumentTransferPlan` holds all three
views and shares its single `BridgeCallSlotPlan` with
`FunctionPlan.bridge_call_slots`. `FunctionPlan.entrypoint.parameters` is the
independent ordered C ABI index consumed by both generators. This prevents the
binding and adapter from carrying independent interpretations of their shared
boundary while keeping original-Fortran call details out of the binding.

`WrapperPlanner` constructs all three facets directly from completed upstream
facts. `WrapperGenerator` validates matching entrypoint roles, parameter
owners, and bridge-call references before freezing the graph. A generator may
not derive an entrypoint from a bridge record or split a two-part plan after
planning.

The plan remains editable only until `WrapperGenerator.generate()` validates
and freezes it. Add presentation details to code generation, not planning.

## Run The Workflows

`models.py` constructs the smallest complete plan directly: a no-argument
`ping()` export with a standalone native `PING` target.

```bash
python3 prik/planning/models.py
```

```text
Plan owner: demo
Python export: ping
Native procedure: PING
Bridge call slots: 0
```

The two names show the separate Python and native views carried by one plan.
Zero entrypoint parameters and zero bridge call slots are complete for a
no-argument subroutine; they are not omitted decisions.

`planner.py` follows the normal route. It constructs one `Float64` function,
completes its semantic policy, then asks `WrapperPlanner` to project the plan.

```bash
python3 prik/planning/planner.py
```

```text
Plan owner: planner_demo
Python export: double_value
Native target: DOUBLE_VALUE
Conversion order: ('planner_demo.double_value.value',)
```

The conversion-order owner path is the stable link between binding conversion
and the matching native call slot. It is copied from completed policy rather
than reconstructed by either backend.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Planner](../../../tests/fortran/infrastructure/codegen/test_planner.py) | Namespace grouping, exports, class lookup, array projection, and failure on missing, empty, or unsupported policy. |
| [Plan ownership and freezing](../../../tests/fortran/infrastructure/pipeline/test_wrapper_generator.py) | A plan is editable before generation; the generator validates and freezes it before backend and printer use. |
| [Overload dispatch plans](../../../tests/fortran/generic_interfaces/codegen/test_overload_dispatch_plan.py) | Candidate order, matching, and pre-call dispatch for supported generic interfaces. |
| [Native handle planning](../../../tests/fortran/memory_management/codegen/test_native_handle_planning.py) | Descriptor-handle state, operation sets, required headers, and central plan validation. |

## Change Routes

- Add a plan field only for an already completed fact needed by lowering.
- Change projection or indexing in `planner.py`.
- Change ownership, mutability, projection, setter exposure, or support in
  policy first.
- Change emitted temporaries or syntax downstream in codegen.

## Boundaries And Invariants

- Missing completed policy is an error, never a reason to infer a default.
- The C binding consumes only binding and entrypoint views; the Fortran bridge
  consumes entrypoint and bridge views.
- Neither generator may reconstruct the symbol, existence, parameter order, or
  result ABI of an auxiliary C-visible operation from a derived field, storage
  kind, array operation, lifecycle action, or callback record.
- Every current Fortran operation remains bridge-backed. Entrypoint separation
  does not select direct routing or make the adapter optional.
- Planning does not depend on presentation helpers such as docstring builders.
- Bridge call slots may interleave argument, result, literal, and helper
  positions; keep their original-Fortran call order distinct from entrypoint
  parameter order.
- Lifecycle actions stay explicit because cleanup and writeback order may span
  several transfers and differ on failure.

## Failure Boundary

Planning reports a missing, blocked, inconsistent, or unexported completed
policy; it also reports impossible plan relationships such as a missing native
slot or unsupported datatype family. It delegates semantic and support
decisions to `policy/`, and emitted syntax to `codegen/`. Start with the first
invalid policy or plan record, not a binding, bridge, or compiler symptom.
