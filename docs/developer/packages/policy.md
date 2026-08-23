---
title: Policy Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, semantic IR
related: ../architecture.md, index.md, semantics.md, planning.md, runtime.md, ../../user/guide/memory-management.md
status: maintained
publication: reviewed
---

# Policy Stage

## Purpose And Boundaries

`prik/policy/` is the final semantic authority before planning. It turns raw
semantic facts and metadata into complete, immutable interoperability
decisions: public exports, object kind, owner, transfer, destruction, storage,
mutability, writeback, nullability, projection, lifecycle, descriptor
operations, setter behavior, and support blockers.

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
  -> entry-export filtering and Python export completion
  -> ownership, accessor, and per-operation native-entrypoint decisions
  -> class, callable, result, overload, and descriptor policy construction
  -> immutable completed policies attached to semantic IR
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
| [`prik/policy/native_array_handles.py`](../../../prik/policy/native_array_handles.py) | `NativeArrayHandlePolicy`, ABI selectors and dispatchers, and `native_array_handle_build_requirements()` describe already-completed descriptor handles and their build requirements. | Descriptor-backed array ABI selection, allowed operations, dispatch, or build headers change. |

`completion.py` shows the dependency order. `ownership.py` and
`construction.py` contain the focused decision rules; `models.py` is the
durable output vocabulary that planning reads.

## Module Algorithms

### `completion.py`: one ordered completion pass

`complete_semantic_policies()` accepts one `SemanticModule` or an iterable,
updates each module in place, and returns the same modules in input order. It
first limits declarations to explicit entry exports when that metadata is
present, then completes collision-checked Python export names.

The remaining order is intentional. It resolves local derived-type identities,
then persistent module variables and their accessors. It completes classes,
their derived-type graph, surfaces, methods, and overloads before building
module-variable policies. Finally it completes direct functions, overload
candidates, and module overload tables, then marks the module prepared for
planning. Later steps depend on records attached by earlier ones.

### `ownership.py`: lifetime facts to lowering-ready decisions

`OwnershipPolicyResolver` is the primitive used during completion. For one
semantic type and its context—argument, result, field, getter, setter, or
module variable—it derives storage facts, selects a default for the object
kind, applies declared ownership and pointer requests, and validates alias,
pointer, immutability, projection, and lifetime combinations.

Only after that validation does it attach boundary storage and the Python,
native, and code-generation actions. An unsupported combination remains a
blocked `OwnershipDecision` with its reason; no later stage chooses a
substitute. `decide_semantic_variable()`, `decide_semantic_getter()`, and
`decide_semantic_setter()` apply the same rule to their specific locations.

### `construction.py`: decisions to wrapper-facing records

The construction helpers combine completed decisions into immutable records
for functions, results, native call slots, module variables, derived types,
classes, overloads, callbacks, transformations, lifecycles, and native
entrypoints.

For a function, `build_function_wrapper_policy()` fixes native-slot order,
projects visible arguments, completes each binding-owned projection and C
passing convention, completes result and declaration-callable records, binds
declaration extents, records writeback and cleanup, and then selects exactly
one `NativeEntrypointAction`. A Fortran procedure without the retained C ABI
fact selects `GENERATED_FORTRAN_ADAPTER`. A `bind(C)` procedure selects
`DIRECT_C_ABI` only when every argument, result, optional-presence,
representation, ownership, lifecycle, and invocation fact is directly
interoperable; otherwise it keeps the adapter route. Optional non-`VALUE`
interoperable dummies use a nullable C pointer, while optional `VALUE` dummies
remain adapter-backed.

A C-source or explicitly C-native `.pyi` operation instead selects
`DIRECT_C_ABI` only when completed direct-C policy supports its ABI and
contract. The policy carries the native declaration identity, transport, and
user symbol required downstream. An ineligible C operation raises its stable
diagnostic before `WrapperPlanner` runs and never falls back to
`GENERATED_FORTRAN_ADAPTER`.

An immediate callback is directly interoperable only when both the containing
procedure and its named callback prototype retain the Fortran C ABI marker,
and every callback argument/result has a supported scalar C value or reference
ABI. The binding then passes its binding-owned trampoline as the planned
function-pointer actual. Array, string, derived, optional, and non-`bind(C)`
callback interfaces retain the generated Fortran adapter route.

An allocatable or pointer array argument may use the direct route only when
completed native-array policy supplies a persistent standard C descriptor and
the original `bind(C)` dummy accepts that descriptor. Optional descriptor
arguments use the standard three states: a null descriptor pointer is absent,
a non-null empty descriptor is present but unallocated or unassociated, and a
non-null populated descriptor is present with storage. Fact-packed call-local
descriptors and owned descriptor results remain adapter-backed.

A `character(c_char)` scalar or explicit/assumed-size array is directly
interoperable only when its completed element length is one. Policy selects a
C value for a scalar `VALUE` dummy and a character pointer for reference or
array storage; longer or runtime-length character storage remains
adapter-backed. The lowerer does not infer this choice from a C spelling.

`EntrypointPassingConvention` describes value, reference, nullable pointer,
C-descriptor, runtime-handle, C-return, and output-storage transport.
`EntrypointOptionalityAction` remains independent from the Python default and
nullable surface. `EntrypointProjectionAction` records how the binding
materializes every ordered `@native_call` item. Adapter data actions describe
only representation or original-invocation work after the shared C boundary;
they do not choose the call source, ordering, or C passing convention.

The resulting `FunctionWrapperPolicy` is the planner's complete description of
the wrapper mechanism;
`completed_function_wrapper_policy()` rejects absent or blocked records at
that boundary.

### `exports.py` and `native_array_handles.py`: focused completion products

`complete_python_export_policy()` writes one collision-checked Python name for
each public declaration in its namespace. `completed_python_exports()` reads
those names as immutable `PythonExportPolicy` records while assembling a
wrapper policy.

`completion.py` creates native-array handle policies for descriptor-backed
arrays. `native_array_handles.py` carries those records through the rest of
the build: `array_interop_policy()` selects ordinary data-buffer or descriptor
ABI, dispatchers select the preplanned handler, and
`native_array_handle_build_requirements()` collects required generated-code
headers from completed modules.

### `models.py`: the durable vocabulary

`models.py` groups frozen records and enums by what later stages must know:
argument/result and native-slot handoff, array and descriptor handling,
lifecycle and transformations, callbacks, derived types and class surfaces,
overloads, module variables, and native status errors. It defines the data
shape of a completed decision; it does not choose one.

## Completed Decision Vocabulary

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

## Run The Workflows

Completed record immutability:

```bash
python3 prik/policy/models.py
```

```text
Array policy: rank=2, shape=('rows', 'columns'), order=F
Lifecycle policy: copy_out writeback via copy_in_out
Completed record mutation rejected: True
```

The script creates completed array and lifecycle records, then attempts to
change one field. `True` confirms that completed policy is immutable once a
decision is ready for planning.

Ownership resolution:

```bash
python3 prik/policy/ownership.py
```

```text
before: math.scale(value): Float64 semantic IR
after: scalar/caller/call_local; scalar_value -> pass_value
```

It gives the resolver one raw scalar argument context. The `after` line names
the selected object kind, owner, transfer, and the Python-to-native mechanism
that later stages must consume unchanged.

Public export completion:

```bash
python3 prik/policy/exports.py
```

```text
Native semantic owner: math.SCALE_VALUE
Python export: linear_algebra.scale_value
Completed policy type: PythonExportPolicy
```

The script adds one export request to a semantic function and completes it.
The output separates the native owner from the public Python path and confirms
that the path is now a completed policy record.

Feature-policy construction:

```bash
python3 prik/policy/construction.py
```

```text
before: math.scale(value): Float64 semantic IR
after: direct_transfer; result=native_scalar; native=pass_value
```

This example supplies already resolved scalar ownership for one argument and
result, then builds only the function policy. Its output shows the resulting
bridge transfer, result ABI, and native call action—not generated source.

Full ordered completion:

```bash
python3 prik/policy/completion.py
```

```text
before: math.scale(value): Float64 semantic IR
after: math.scale(value): scalar_value -> pass_value
```

Here the script starts with raw semantic IR and invokes the full completion
sequence. The final conversion pair shows the exact completed actions that the
planner will project into both backend views.

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

The script marks a pointer array as a native handle and supplies its completed
handle policy. The result links its allowed Python operations and alias storage
to the descriptor ABI and build header required downstream.

The outputs move from raw semantic facts to immutable decisions. They do not
generate source; that begins only after planning.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Policy completion](../../../tests/fortran/infrastructure/policy/test_policy_completion.py) | Completion precedes lowering; accessor, projection, and missing-conversion failures remain explicit. |
| [Wrapper policy](../../../tests/fortran/infrastructure/policy/test_wrapper_policy.py) | Function, result, call-slot, array, export, status, and support policies are complete before planning. |
| [Ownership policy](../../../tests/fortran/memory_management/policy/test_memory_ownership_policy.py) | Contradictory explicit ownership contracts fail before lowering. |
| [Descriptor handle policy](../../../tests/fortran/allocatables/policy/test_allocatable_handle_policy.py) | Allocatable descriptor-handle decisions, ownership, access, and support blockers. |
| [Planner boundary](../../../tests/fortran/infrastructure/codegen/test_planner.py) | Planning rejects a missing completed wrapper policy instead of filling it in. |

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

## Boundaries And Invariants

- Completion order stays explicit; do not replace it with an opaque pass
  registry.
- Raw semantic ownership metadata is a request, not an `OwnershipDecision`.
- Hidden output projection is separate from ABI transport.
- Ordinary NumPy buffer handoff and a persistent native descriptor handoff
  are distinct ABI choices.
- A valid source declaration or `.pyi` annotation is not proof of safe
  wrapper support.
- If a generator needs a decision, make it explicit in policy completion and
  add focused policy evidence before changing lowering.

## Failure Boundary

This stage reports incomplete, contradictory, or unsupported interoperability
contracts, including missing ownership, unsafe lifetime combinations, invalid
projection, unavailable accessor behavior, and unsupported wrapper mechanisms.
It delegates parser and semantic facts to earlier stages, and it delegates
planning, rendering, and native compilation to later stages. Diagnose the first
incorrect completed policy or blocker, not a later generated-code symptom.
