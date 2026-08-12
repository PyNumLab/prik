---
title: Planning Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed policy
related: ../architecture.md, index.md, policy.md, codegen.md, ../source-map.md
status: maintained
publication: draft
---

# Planning Package

## Purpose And Boundaries

`prik/planning/` mechanically projects policy-completed semantic IR into one
backend-neutral `ModulePlan`. It joins common transfer facts with explicit
binding and bridge views, namespaces, stable native symbols, lifecycle order,
and build requirements. It may organize and validate completed decisions; it
may not reinterpret source declarations, choose policy, or render text.

## Local Structure

```text
prik/planning/
├── models.py
└── planner.py
```

## Internal Workflow

```text
policy-completed SemanticModule
  -> WrapperPlanner validation and projection
  -> editable ModulePlan
  -> freeze at WrapperGenerator boundary
  -> backend node generation
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `models.py` | `ModulePlan`, function, argument, result, slot, lifecycle, class, overload, binding, and bridge plan records | Defines the typed editable plan tree. |
| `planner.py` | `WrapperPlanner`, `_ClassPolicyCatalog` | Validates completed policy, creates indexes and symbols, and projects the plan deterministically. |

The private class-policy catalogue is a validated lookup, not another semantic
authority. The planner does not generate docstrings or source.

The stable plan tree keeps orchestration at module, namespace, and function
levels and confines datatype variation to transfers, results, lifecycle
actions, and module variables:

```text
ModulePlan
  -> binding and bridge module views
  -> NamespacePlan
       -> FunctionPlan
            -> ArgumentTransferPlan
            -> ResultPlan
            -> NativeCallSlotPlan
            -> LifecycleActionPlan
       -> ModuleVariablePlan
```

Each argument or result owns explicit binding and bridge views. Its native-call
slot is the same record referenced from the transfer and the function-wide ABI
ordering index, not a duplicated policy fact. Function orchestration owns call,
result, lifecycle, GIL, and status order without becoming datatype policy.

`OverloadPlan` stores ordered candidates, exact match records, receiver
conventions, and one candidate ID per overload set. Generated dispatch chooses
an ID before making a native call, preserving first-match behavior for
overlapping optional domains without speculative calls.

## Execution Examples

```bash
python3 prik/planning/models.py
```

```text
Plan owner: demo
Python export: ping
Native procedure: PING
Native slots: 0
```

```bash
python3 prik/planning/planner.py
```

```text
Plan owner: planner_demo
Python export: double_value
Native target: DOUBLE_VALUE
Conversion order: ('planner_demo.double_value.value',)
```

The model example demonstrates representation. The planner example follows
the real sequence—semantic IR, policy completion, then planning—and shows the
stable role connecting binding conversion to the native call slot.

## Tests

- [Plan model tests](../../../tests/fortran/infrastructure/codegen/test_plan.py)
- [Planner tests](../../../tests/fortran/infrastructure/codegen/test_planner.py)
- [Feature-local codegen stages](../../../tests/fortran/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Add a plan field only for an already completed fact needed by lowering.
- Change projection or indexing in `planner.py`.
- Change ownership, mutability, projection, setter exposure, or support in
  policy first.
- Change emitted temporaries or syntax downstream in codegen.

## Invariants And Common Mistakes

- Missing completed policy is an error, never a reason to infer a default.
- Binding and bridge views may share one ABI contract without hiding their
  backend-specific lowering facts.
- Planning does not depend on presentation helpers such as docstring builders.
- Native slots may interleave argument, result, literal, and helper positions;
  keep their function-wide order explicit.
- Lifecycle actions stay explicit because cleanup and writeback order may span
  several transfers and differ on failure.
