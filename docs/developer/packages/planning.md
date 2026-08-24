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
├── entrypoints.py
├── models.py
└── planner.py
```

## What This Stage Receives And Produces

```text
policy-completed SemanticModule
  -> WrapperPlanner projects binding + entrypoint views
     plus an adapter view only where completed policy selected one
  -> editable ModulePlan
  -> freeze at WrapperGenerator boundary
  -> binding + entrypoint C generation
  -> optional entrypoint + bridge Fortran generation
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/planning/__init__.py`](../../../prik/planning/__init__.py) | Re-exports `WrapperPlanner` and the supported plan records. | A supported planning type or import path changes. |
| [`prik/planning/models.py`](../../../prik/planning/models.py) | `ModulePlan` and typed function, argument, result, bridge-call-slot, lifecycle, class, overload, binding, entrypoint, and bridge records form the editable plan tree. | Lowering needs a new *already completed* fact represented explicitly. |
| [`prik/planning/planner.py`](../../../prik/planning/planner.py) | `WrapperPlanner` validates policy, indexes declarations, allocates names, and projects deterministic binding, entrypoint, and bridge views; `_ClassPolicyCatalog` is a validated lookup. | A completed policy fact is projected or ordered incorrectly. |
| [`prik/planning/entrypoints.py`](../../../prik/planning/entrypoints.py) | Projects every generated support procedure entrypoint into the module registry, including its implementation owner and structured C ABI. | An accessor, lifecycle, descriptor, origin, constructor, or callback operation changes its shared boundary. |

The private class-policy catalogue is a validated lookup, not another semantic
authority. The planner does not generate docstrings or source.

The stable plan tree keeps orchestration at module, namespace, and function
levels and confines datatype variation to transfers, results, lifecycle
actions, and module variables:

```text
ModulePlan
├── BindingModulePlan
├── NativeEntrypointModulePlan
│   └── GeneratedSupportProcedureEntrypointPlan
│       └── NativeEntrypointSignaturePlan
├── NativeGeneratedCodeGroupPlan (zero or more)
├── BridgeModulePlan (optional; Fortran-local holder inventories)
└── NamespacePlan (root and child namespaces)
    ├── FunctionPlan
    │   ├── ArgumentTransferPlan
    │   ├── ResultPlan
    │   ├── NativeEntrypointParameterPlan
    │   ├── NativeEntrypointProjectedSlotPlan
    │   │   └── BridgeCallSlotPlan (optional adapter facet)
    │   └── LifecycleActionPlan
    └── ModuleVariablePlan
```

Each callable, argument, and result always owns binding and entrypoint views;
an adapter-backed callable additionally owns a bridge view. Binding records own Python extraction and result
construction. Native-entrypoint records own the complete bidirectional C ABI:
the exported symbol, direct return, ordered parameter groups, value/address
projection, presence and length fields, descriptors, and hidden outputs.
Bridge records own adapter-local representation conversion and the invocation
of the original Fortran procedure.

`NativeEntrypointModulePlan.support_procedures` is the authoritative registry for
externally linked generated helper callables that are not ordinary wrapped
functions. Each operation stores one collision-safe key and symbol plus a
structured signature of ordered ABI values. The registry covers constructors,
accessors, derived-origin transactions, destruction and holder helpers,
native-array operations, and callback trampolines. Each record also identifies
whether the binding or bridge implements the callable; the opposite side uses
the same record as its declaration/call contract. Static CPython helpers and
bridge-internal procedures are deliberately absent.

`BindingModulePlan` separately records which derived-type owners need
binding-local capsule and holder surfaces. Those static CPython helpers are not
entrypoints, but their membership is still planned rather than rediscovered by
C lowering. `BridgeModulePlan` likewise records the broad typed-holder
definitions required by adapter calls and the narrower holder field-support
inventories. Planning derives both backend-local inventories and the external
support-procedure registry together. Validation requires every planned local
helper that calls native support to resolve an entrypoint with the matching
owner and role.

`ModulePlan.native_generated_code_groups` records generated native membership
without using the presence of a physical source file as policy: adapter groups
hold user operations selected for a generated Fortran adapter, support groups
hold Fortran-owned support-procedure keys, and empty groups are omitted.

`NativeEntrypointFunctionPlan.results` includes public Python results and
binding-private outputs such as native status and message values. A public
`ResultPlan` shares its exact entrypoint-result object; a private output remains
available to C prototype, storage, and call lowering without exposing a bridge
call slot to the binding generator.

An argument or hidden result shares one authoritative
`NativeEntrypointProjectedSlotPlan` with the function-wide binding projection
sequence. It owns source mapping, ordering, passing, optionality, and the C ABI
actual. Adapter-backed operations attach a narrow `BridgeCallSlotPlan`; direct
operations do not. `NativeEntrypointParameterPlan` independently groups the
resulting C declaration fields.
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

For each module, the planner first collects top-level and nested semantic
classes into one depth-first, source-ordered tuple. That same collection feeds
derived-type name indexing, backend-symbol allocation, and
`_ClassPolicyCatalog`, so a nested class cannot reach projection without its
symbol being registered. It projects direct functions and variables, then uses
the catalogue to join each public class to its completed derived-type, surface,
method, and overload policies. The catalogue is read-only: it maps existing
owner paths to their semantic declarations without deciding policy again.

The planner attaches class and overload callables to the function collections
that need their native entrypoints. It completes generated symbols, adds every
required parent namespace, and creates namespace plans in root-first path
order. Finally it collects headers selected by completed descriptor-handle
plans and returns one editable `ModulePlan`.

### `models.py`: shared plans and three lowering views

`models.py` defines editable `StageRecord` plans. `ModulePlan` is the root;
each `NamespacePlan` groups the public functions, variables, derived types,
classes, and overloads for one Python path. A `FunctionPlan` owns call-wide
ordering, while its transfers, results, entrypoint parameters, projected call
slots, optional adapter facets, and lifecycle actions carry the
datatype-specific details.

Binding, native-entrypoint, and optional bridge records are separate facets of
the same planned operation. For example, an `ArgumentTransferPlan` shares its
projected entrypoint slot with `FunctionPlan.entrypoint.projected_slots`; only
an adapted route also references that slot's adapter facet.
`FunctionPlan.entrypoint.parameters` is the ordered C ABI grouping consumed by
lowering. This keeps the binding projection authoritative while leaving
original-Fortran invocation details out of direct routes and C lowering.

`WrapperPlanner` constructs the selected facets directly from completed upstream
facts. `WrapperGenerator` validates matching entrypoint roles, parameter
owners, and projected-slot references before freezing the graph. A generator may
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
Projected call slots: 0
```

The two names show the separate Python and native views carried by one plan.
Zero entrypoint parameters and zero projected call slots are complete for a
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
  result ABI of a generated support procedure from a derived field, storage
  kind, array operation, lifecycle action, or callback record.
- C lowering may map a planned binding-local derived owner back to its
  `DerivedTypePlan` for names and fields, but it may not walk results,
  arguments, module variables, constructors, releases, or storage kinds to
  rediscover capsule or holder membership.
- Fortran lowering may perform the same mechanical owner-to-type join for its
  planned holder definitions and holder field bodies. It may not walk result
  storage or argument call cases to reconstruct either module inventory.
- Direct Fortran operations have no bridge facet. Adapter and Fortran-support
  membership are separate generated-code groups even when they share a
  physical source.
- Planning does not depend on presentation helpers such as docstring builders.
- Shared projected slots own argument, result, literal, and helper ordering.
  An adapted slot may add only its Fortran-local conversion and invocation
  facet; it does not own a second projection order.
- Lifecycle actions stay explicit because cleanup and writeback order may span
  several transfers and differ on failure.

## Failure Boundary

Planning reports a missing, blocked, inconsistent, or unexported completed
policy; it also reports impossible plan relationships such as a missing native
slot or unsupported datatype family. It delegates semantic and support
decisions to `policy/`, and emitted syntax to `codegen/`. Start with the first
invalid policy or plan record, not a binding, bridge, or compiler symptom.
