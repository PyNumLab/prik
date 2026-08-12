---
title: Policy Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, semantic IR
related: ../architecture.md, index.md, semantics.md, planning.md, runtime.md, ../../user/guide/memory-management.md
status: maintained
publication: draft
---

# Policy Package

## Purpose And Boundaries

`prik/policy/` is the final semantic authority before planning. It turns raw
semantic facts and metadata into complete immutable interoperability decisions:
public exports, object kind, owner, transfer, destruction, storage, mutability,
writeback, nullability, projection, lifecycle, descriptor operations, setter
behavior, and support blockers.

Planning, binding, bridge, and runtime code consume these decisions. They may
validate and dispatch from them, but may not infer an alternative answer from
datatype, source `intent`, dotted-variable shape, `is_alias`, or local memory
checks.

## Local Structure

```text
prik/policy/
├── __init__.py
├── models.py
├── ownership.py
├── exports.py
├── construction.py
├── completion.py
└── native_array_handles.py
```

## What This Stage Receives And Produces

```text
SemanticModule + normalized raw metadata
  -> export completion and semantic graph completion
  -> ownership, callable, class, result, and descriptor-policy construction
  -> complete_semantic_policies()
  -> immutable completed policy attached to semantic IR
  -> WrapperPlanner
```

Completion is ordered because later decisions depend on earlier facts. A
blocked decision records its owner path and reason; it is never replaced by a
downstream fallback.

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/policy/__init__.py`](../../../prik/policy/__init__.py) | Re-exports `complete_semantic_policies()` as the normal policy-stage entrypoint. | The supported policy import surface changes. |
| [`prik/policy/models.py`](../../../prik/policy/models.py) | Immutable records and enums for function, argument, result, slot, lifecycle, class, overload, callback, array, descriptor, status, and transformation policy. | A completed decision needs a durable backend-neutral representation. |
| [`prik/policy/ownership.py`](../../../prik/policy/ownership.py) | Ownership vocabulary, `OwnershipContext`, `OwnershipDecision`, `OwnershipPolicyResolver`, and action dispatchers resolve lifetime triples and fail-closed lowering actions. | Object kind, owner, transfer, destruction, storage, barrier, assignment, or setter selection changes. |
| [`prik/policy/exports.py`](../../../prik/policy/exports.py) | `PythonExportPolicy`, `complete_python_export_policy()`, and `completed_python_exports()` create collision-checked Python placement. | Export namespace, visibility, or collision behavior changes. |
| [`prik/policy/construction.py`](../../../prik/policy/construction.py) | Feature constructors build coherent function, result, native-slot, callback, class, overload, and module-variable policies from completed ownership decisions. | A supported feature needs different completed policy composition. |
| [`prik/policy/completion.py`](../../../prik/policy/completion.py) | `complete_semantic_policies()` runs the dependency-ordered completion pass, attaches outcomes, and validates blockers. | Completion order, cross-declaration completion, or the stage boundary changes. |
| [`prik/policy/native_array_handles.py`](../../../prik/policy/native_array_handles.py) | `NativeArrayHandlePolicy`, interop/handle/projection dispatchers, and build-requirement records complete descriptor operations and selected ABI/build requirements. | Descriptor-backed array behavior, ABI selection, allowed operations, or build headers change. |

Start with `completion.py` to see the order, follow its call into the focused
resolver or constructor, and finish in `models.py` to confirm the durable
output. Do not begin in code generation when the question is semantic.

## How To Read A Completed Decision

Policy keeps related questions separate. This makes aliases, copies, views,
and cleanup auditable instead of encoding them in one overloaded `owned`
flag.

| Question | Main vocabulary | Example answer |
| --- | --- | --- |
| What Python-facing family is this? | `ObjectKind` | `SCALAR`, `STRING`, `NUMPY_ARRAY`, `DERIVED_TYPE` |
| Who owns the represented storage? | `OwnershipOwner` | `CALLER`, `NATIVE`, `WRAPPER`, `TEMPORARY` |
| How does value or storage cross the boundary? | `TransferMode` | `BY_VALUE`, `IN_PLACE`, `COPY_RETURN`, `BORROWED_VIEW` |
| Who releases a resource? | `DestructionPolicy` | `CALLER`, `NATIVE_OWNER`, `WRAPPER_DEALLOC`, `CALL_LOCAL` |
| Where is the contract value stored? | `StorageMode` | `STACK`, `HEAP`, `ALIAS` |
| What does each boundary do? | `PythonBarrierAction`, `NativeBarrierAction`, `CodegenAction` | extract storage, pass a descriptor, copy out, construct a wrapper |
| How may native storage be assigned or exposed? | `AssignmentMode`, `SetterAction` | value copy, alias, write-through, omit setter |

Read the lifetime triple left to right. For example,
`NATIVE + BORROWED_VIEW + NATIVE_OWNER` means Python observes live native
storage but does not own or release it. `PYTHON + COPY_RETURN +
PYTHON_REFCOUNT` means that PRIK creates an independent Python-owned result.
Only supported combinations are lowered; contradictory or unimplemented
combinations become explicit blockers.

For every lowering-ready value, policy completion must answer all of the
following before `WrapperPlanner.build()`:

1. Object kind and public projection.
2. Owner, transfer, destruction, and contract storage mode.
3. Python and native barrier actions, including ordered native call slots.
4. Mutability, writeback, nullability, lifecycle, release responsibility,
   getter behavior, native setter assignment, and Python setter exposure.
5. Supported mechanism or an explicit blocked diagnostic.

The binding and bridge may create local temporary variables inside a selected
implementation method, but those are emitted-code details. They are not a
license to choose a new semantic policy.

## Execution Examples

Completed record immutability:

```bash
python3 prik/policy/models.py
```

```text
Array policy: rank=2, shape=('rows', 'columns'), order=F
Lifecycle policy: copy_out writeback via copy_in_out
Completed record mutation rejected: True
```

Ownership resolution:

```bash
python3 prik/policy/ownership.py
```

```text
before: math.scale(value): Float64 semantic IR
after: scalar/caller/call_local; scalar_value -> pass_value
```

Public export completion:

```bash
python3 prik/policy/exports.py
```

```text
Native semantic owner: math.SCALE_VALUE
Python export: linear_algebra.scale_value
Completed policy type: PythonExportPolicy
```

Feature-policy construction:

```bash
python3 prik/policy/construction.py
```

```text
before: math.scale(value): Float64 semantic IR
after: direct_transfer; result=native_scalar; native=pass_value
```

Full ordered completion:

```bash
python3 prik/policy/completion.py
```

```text
before: math.scale(value): Float64 semantic IR
after: math.scale(value): scalar_value -> pass_value
```

Descriptor-backed array completion:

```bash
python3 prik/policy/native_array_handles.py
```

```text
Handle policy: pointer/pointer, storage=alias
Allowed operations: to_numpy, nullify
Array ABI: descriptor
Selected build header: ISO_Fortran_binding.h
```

The outputs move from raw semantic facts to immutable decisions. They do not
generate source; that begins only after planning.

## Tests And What They Prove

- [Policy infrastructure](../../../tests/fortran/infrastructure/semantics/) covers policy records, completion order, and general semantic-policy rules.
- [Native handle policy](../../../tests/fortran/infrastructure/semantics/test_native_array_handles.py) covers descriptor policy, allowed operations, and ABI requirements.
- [Feature-local policy suites](../../../tests/fortran/) cover ownership and projection decisions for the supported wrapper features.
- [Planner tests](../../../tests/fortran/infrastructure/codegen/test_planner.py) prove that planning rejects incomplete policy instead of filling it in.
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py) fixes the six demonstrations above.

## Change Routes

- Add reusable immutable output vocabulary in `models.py` only when it is a
  semantic decision that more than one lower stage must consume.
- Change one lifetime or barrier decision in `ownership.py`; retain a blocked
  result when no safe supported combination exists.
- Change Python placement in `exports.py`.
- Change the coherent composition of a supported function, class, overload,
  callback, result, or module-variable policy in `construction.py`.
- Change dependency order and attachment in `completion.py`.
- Change descriptor operations, ABI, or build requirements in
  `native_array_handles.py`.
- Project an already completed fact in planning; lower an already selected
  mechanism in codegen. Neither is a replacement policy owner.

## Invariants And Common Mistakes

- Completion order stays explicit; do not replace it with an opaque pass
  registry.
- Raw semantic ownership metadata is a request, not an `OwnershipDecision`.
- Hidden output projection is separate from ABI transport.
- Ordinary NumPy buffer handoff and a persistent native descriptor handoff
  are distinct ABI choices.
- A valid source declaration or `.pyi` annotation is not proof of safe
  wrapper support.
- If a generator guesses a decision, move that decision into policy completion
  and add the focused policy test before changing lowering.
