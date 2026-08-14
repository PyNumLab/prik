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
binding and bridge views, namespaces, stable native symbols, lifecycle order,
and build requirements. It may organize and validate completed decisions; it
may not reinterpret source declarations, choose policy, or render text.

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
  -> WrapperPlanner validates completed records and projects views
  -> editable ModulePlan
  -> freeze at WrapperGenerator boundary
  -> binding and bridge node generation
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/planning/__init__.py`](../../../prik/planning/__init__.py) | Re-exports `WrapperPlanner` and the supported plan records. | A supported planning type or import path changes. |
| [`prik/planning/models.py`](../../../prik/planning/models.py) | `ModulePlan` and typed function, argument, result, slot, lifecycle, class, overload, binding, and bridge records form the editable plan tree. | Lowering needs a new *already completed* fact represented explicitly. |
| [`prik/planning/planner.py`](../../../prik/planning/planner.py) | `WrapperPlanner` validates policy, indexes declarations, allocates names, and projects deterministic binding and bridge views; `_ClassPolicyCatalog` is a validated lookup. | A completed policy fact is projected or ordered incorrectly. |

The private class-policy catalogue is a validated lookup, not another semantic
authority. The planner does not generate docstrings or source.

The stable plan tree keeps orchestration at module, namespace, and function
levels and confines datatype variation to transfers, results, lifecycle
actions, and module variables:

```text
ModulePlan
├── BindingModulePlan
├── BridgeModulePlan
└── NamespacePlan (root and child namespaces)
    ├── FunctionPlan
    │   ├── ArgumentTransferPlan
    │   ├── ResultPlan
    │   ├── NativeCallSlotPlan
    │   └── LifecycleActionPlan
    └── ModuleVariablePlan
```

Each argument or result owns explicit binding and bridge views. Its native-call
slot is the same record referenced from the transfer and the function-wide ABI
ordering index, not a duplicated policy fact. Function orchestration owns call,
result, lifecycle, GIL, and status order without becoming datatype policy.

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

### `models.py`: shared plans and backend views

`models.py` defines editable `StageRecord` plans. `ModulePlan` is the root;
each `NamespacePlan` groups the public functions, variables, derived types,
classes, and overloads for one Python path. A `FunctionPlan` owns call-wide
ordering, while its transfers, results, native slots, and lifecycle actions
carry the datatype-specific details.

Binding and bridge records are separate facets of the same planned operation.
For example, an `ArgumentTransferPlan` holds both backend views and shares its
single `NativeCallSlotPlan` with `FunctionPlan.native_call_slots`. This prevents
two backends from carrying independent interpretations of one ABI position.

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
Native slots: 0
```

The two names show the separate Python and native views carried by one plan.
Zero slots is complete for a no-argument subroutine; it is not an omitted
decision.

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
- Binding and bridge views may share one ABI contract without hiding their
  backend-specific lowering facts.
- Planning does not depend on presentation helpers such as docstring builders.
- Native slots may interleave argument, result, literal, and helper positions;
  keep their function-wide order explicit.
- Lifecycle actions stay explicit because cleanup and writeback order may span
  several transfers and differ on failure.

## Failure Boundary

Planning reports a missing, blocked, inconsistent, or unexported completed
policy; it also reports impossible plan relationships such as a missing native
slot or unsupported datatype family. It delegates semantic and support
decisions to `policy/`, and emitted syntax to `codegen/`. Start with the first
invalid policy or plan record, not a binding, bridge, or compiler symptom.
