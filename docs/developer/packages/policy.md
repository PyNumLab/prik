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

`prik/policy/` is the final semantic authority before planning. It resolves
public exports, object kind, owner, transfer, destruction, mutability,
writeback, nullability, storage, projections, lifecycle actions, descriptor
operations, setter behavior, and support blockers. Planning and generation may
dispatch from these immutable decisions but may not replace them.

## Local Structure

```text
prik/policy/
├── models.py
├── ownership.py
├── exports.py
├── construction.py
├── completion.py
└── native_array_handles.py
```

## Internal Workflow

```text
complete SemanticModule + normalized raw metadata
  -> export and graph completion
  -> ownership and feature-policy construction
  -> complete_semantic_policies()
  -> immutable policies attached to semantic IR
  -> WrapperPlanner
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `models.py` | `FunctionWrapperPolicy`, argument/result/call-slot/lifecycle/class/callback/array records | Defines immutable backend-neutral completed policy. |
| `ownership.py` | `OwnershipDecision` and ownership vocabulary | Resolves object kind, lifetime triple, storage, and strict lowering actions. |
| `exports.py` | `PythonExportPolicy` | Completes collision-checked Python placement. |
| `construction.py` | `_FunctionPolicyContext` and feature constructors | Builds coherent function, result, native-slot, callback, and class policies. |
| `completion.py` | `complete_semantic_policies()` | Runs completion in explicit dependency order and attaches its results. |
| `native_array_handles.py` | `NativeArrayHandlePolicy` and ABI dispatch records | Completes descriptor operations, array ABI, and selected build requirements. |

## Execution Examples

```bash
python3 prik/policy/models.py
```

```text
Array policy: rank=2, shape=('rows', 'columns'), order=F
Lifecycle policy: copy_out writeback via copy_in_out
Completed record mutation rejected: True
```

```bash
python3 prik/policy/ownership.py
```

```text
before: math.scale(value): Float64 semantic IR
after: scalar/caller/call_local; scalar_value -> pass_value
```

```bash
python3 prik/policy/exports.py
```

```text
Native semantic owner: math.SCALE_VALUE
Python export: linear_algebra.scale_value
Completed policy type: PythonExportPolicy
```

```bash
python3 prik/policy/construction.py
```

```text
before: math.scale(value): Float64 semantic IR
after: direct_transfer; result=native_scalar; native=pass_value
```

```bash
python3 prik/policy/completion.py
```

```text
before: math.scale(value): Float64 semantic IR
after: math.scale(value): scalar_value -> pass_value
```

```bash
python3 prik/policy/native_array_handles.py
```

```text
Handle policy: pointer/pointer, storage=alias
Allowed operations: to_numpy, nullify
Array ABI: descriptor
Selected build header: ISO_Fortran_binding.h
```

These exact outputs show completed immutable decisions rather than generated source.
The completion entrypoint is mandatory for normal planning; individual example
builders exist only to expose their focused ownership boundaries.

## Tests

- [Policy infrastructure](../../../tests/fortran/infrastructure/semantics/)
- [Native handle policy](../../../tests/fortran/infrastructure/semantics/test_native_array_handles.py)
- [Feature-local policy suites](../../../tests/fortran/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Put reusable immutable output vocabulary in `models.py`.
- Start a new semantic decision in completion and its focused resolver or
  constructor.
- Extend strict descriptor dispatch/build selection in
  `native_array_handles.py`.
- If a generator guesses policy from datatype, intent, aliases, or local
  memory checks, remove the guess and complete the decision here.

## Invariants And Common Mistakes

- Completion order remains visible and explicit; do not replace it with an
  opaque pass registry.
- Blocked policies keep their owner path and reason.
- Shared policy models remain independent of construction implementation.

## Orthogonal Selector Vocabulary

Completed policy keeps separate questions separate:

| Selector | Question |
| --- | --- |
| `ObjectKind` | What kind of value follows this route? |
| result source kind | Is a result direct or projected from a hidden output? |
| `PythonBarrierAction` | How does the binding validate or extract the Python object? |
| `NativeBarrierAction` | What transport crosses the native ABI boundary? |
| `CodegenAction` | What ownership or transfer operation occurs? |
| bridge data action | What representation operation occurs in the bridge? |
| writeback phase | When does mutation, copy-out, cleanup, or release happen? |

Hiddenness is not an ownership action. Ordinary NumPy buffer handoff and
persistent native descriptor handoff are also distinct ABI choices; neither
backend may substitute one for the other. A datatype family may select an
element spelling only after object-kind/action dispatch. It must never be used
to rediscover whether the overall transfer is scalar, string, array, or native
handle.

Native source `intent` may seed a generated default Python signature during
source conversion, but the editable signature, `Returns[...]` projection, and
ordered native-call mapping become authoritative. An explicit native-call list
is exhaustive for native dummy positions. Transport overrides such as
primitive `Addr(Arg(i))` or derived `Value(Arg(i))` select ABI transport;
`Returns[...]` selects Python projection and writeback expectation, not the
transport itself.

## Ownership Resolution Reference

PRIK represents ownership as a completed semantic contract, not as one label
such as "owned" or "borrowed." A value is lowering-ready only after policy
completion answers separate questions about its representation, storage owner,
boundary transfer, release responsibility, storage form, and generated actions.

This separation is deliberate. A NumPy view may be a Python object while its
buffer remains native-owned; a generated Python object may control a
wrapper-owned native instance; and a caller-owned array may be mutated in
place without transferring ownership. Combining those cases under one boolean
would make cleanup and alias behavior ambiguous.

The canonical pipeline is:

```text
semantic type + semantic use context + explicit metadata
    -> OwnershipPolicyResolver
    -> immutable OwnershipDecision
    -> post-IR policy validation
    -> wrapper plan
    -> binding and bridge lowering
```

The binding and bridge generators consume completed actions. They must not
reconstruct ownership from datatype, source `intent`, rank, allocation flags,
or local memory checks.

## The Three Lifetime Questions

Read the central lifetime triple from left to right:

1. `OwnershipOwner` says who owns the represented storage.
2. `TransferMode` says how the value or storage relationship crosses the
   Python/native boundary.
3. `DestructionPolicy` says who releases any owned resource.

For example:

```text
PYTHON + COPY_RETURN + PYTHON_REFCOUNT
```

means that native output is copied into independent Python-owned storage and
that ordinary Python or NumPy lifetime releases that copy. In contrast:

```text
NATIVE + BORROWED_VIEW + NATIVE_OWNER
```

means that Python observes live native storage without owning or releasing it.
The resolver accepts only implemented triples and converts contradictory or
unsupported combinations into an explicit blocked decision.

## Completed Policy Vocabulary

### Object kind

`ObjectKind` selects the Python-facing representation family before lifetime
or lowering actions are chosen.

| Value | Meaning |
| --- | --- |
| `SCALAR` | An ordinary scalar Python value or scalar storage cell. |
| `STRING` | A Python string value or mutable native character storage. |
| `NUMPY_ARRAY` | NumPy-compatible array storage, including descriptor-backed arrays. |
| `DERIVED_TYPE` | An opaque native object represented through a generated wrapper. |

### Storage owner

| Value | Meaning |
| --- | --- |
| `PYTHON` | Python, NumPy, or a Python-owned capsule owns the represented value or buffer. |
| `CALLER` | The caller supplied the object and retains ownership across the call. |
| `NATIVE` | A Fortran module or another native owner keeps the storage alive and releases it. |
| `WRAPPER` | A generated wrapper or handle owns or controls the native resource. |
| `TEMPORARY` | Generated call-local storage exists only for the current invocation. |
| `UNKNOWN` | No safe owner is known; this is used by fail-closed decisions. |

### Boundary transfer

| Value | Meaning |
| --- | --- |
| `BY_VALUE` | An independent scalar-like value crosses the boundary. |
| `IN_PLACE` | Native code reads or writes caller-visible storage without replacement. |
| `COPY_RETURN` | Native output is copied or converted into a fresh Python result. |
| `SNAPSHOT_COPY` | Python receives a detached copy of current native state. |
| `BORROWED_VIEW` | Python observes storage owned elsewhere without taking ownership. |
| `CALL_LOCAL` | Storage or an association exists only for one wrapped call. |
| `WRAPPER_INSTANCE` | Python receives an object that owns or controls a native instance. |
| `BLOCKED` | No supported safe transfer exists; generation must stop. |

### Destruction responsibility

| Value | Meaning |
| --- | --- |
| `PYTHON_REFCOUNT` | Python, NumPy, or a Python-owned capsule releases the resource. |
| `CALLER` | The caller retains release responsibility; PRIK must not destroy the object. |
| `WRAPPER_DEALLOC` | A generated wrapper or handle deallocator releases the native resource. |
| `NATIVE_OWNER` | The independent native owner releases the storage. |
| `CALL_LOCAL` | Generated cleanup releases a temporary before the wrapper call ends. |
| `NONE` | This boundary value creates no resource that PRIK must release. |
| `BLOCKED` | Release responsibility is unsafe, contradictory, or unimplemented. |

`NONE` does not mean that the value has no storage. It means that this wrapper
boundary did not create an owned resource requiring a release action. For
example, a wrapper-owned derived input can use `CALL_LOCAL + NONE` because the
existing wrapper remains responsible for its instance.

### Contract and boundary storage

`StorageMode` describes where PRIK keeps the contract value and, separately,
its ABI boundary representation.

| Value | Meaning |
| --- | --- |
| `STACK` | Direct or call-frame storage with no persistent heap allocation. |
| `HEAP` | Storage whose lifetime extends beyond a native stack value. |
| `ALIAS` | A reference to existing storage; no independent value is owned here. |

Pointers always use alias storage, allocatables use heap storage, and borrowed
array views use alias storage. Those are storage invariants, not backend
guesses.

### General lowering action

| Value | Meaning |
| --- | --- |
| `DIRECT_VALUE` | Convert or return a direct independent value. |
| `CALL_LOCAL_INPUT` | Prepare input storage valid only during the call. |
| `IN_PLACE_ARGUMENT` | Pass mutable caller-visible storage through to native code. |
| `IDENTITY_OUTPUT` | Mutate and project the same supplied object rather than replacing it. |
| `COPY_IN_OUT` | Copy immutable Python input into mutable call storage and return its final value. |
| `COPY_OUT` | Materialize native output as a new Python result. |
| `SNAPSHOT_COPY` | Materialize a detached snapshot of persistent native state. |
| `BORROWED_VIEW` | Expose existing owner-controlled storage. |
| `WRAPPER_INSTANCE` | Construct or return a generated native-object wrapper. |
| `BLOCKED` | Reject lowering because the completed policy is unsupported. |

### Python-to-wrapper barrier

| Value | Meaning |
| --- | --- |
| `SCALAR_VALUE` | Read an ordinary Python scalar value. |
| `SCALAR_STORAGE` | Read or create addressable scalar storage. |
| `ARRAY_STORAGE` | Validate and use NumPy-compatible array storage. |
| `STRING_VALUE` | Read an immutable Python string value. |
| `STRING_STORAGE` | Use mutable addressable character storage. |
| `RAW_ADDRESS` | Accept an explicit raw-address contract. |
| `WRAPPER_INSTANCE` | Extract an opaque native instance or descriptor from a wrapper. |
| `NONE` | No Python argument crosses this boundary. |
| `BLOCKED` | Reject Python-boundary lowering. |

### Wrapper-to-native barrier

| Value | Meaning |
| --- | --- |
| `PASS_VALUE` | Pass the converted value directly. |
| `PASS_CALL_LOCAL_ADDRESS` | Pass the address of wrapper-created call-local storage. |
| `PASS_STORAGE_ADDRESS` | Pass the address of existing mutable storage. |
| `PASS_RAW_ADDRESS` | Forward the explicitly supplied raw address. |
| `PASS_ARRAY_BUFFER` | Pass a validated array data buffer. |
| `PASS_NATIVE_DESCRIPTOR` | Pass a native allocatable or pointer descriptor. |
| `PASS_WRAPPER_ADDRESS` | Pass the opaque address held by a generated object wrapper. |
| `NONE` | No native argument is required for this value. |
| `BLOCKED` | Reject native-boundary lowering. |

### Assignment and setter actions

| Axis | Value | Meaning |
| --- | --- | --- |
| `AssignmentMode` | `NONE` | No native assignment is generated. |
| `AssignmentMode` | `VALUE_COPY` | Copy the incoming value into existing native storage. |
| `AssignmentMode` | `ALIAS` | Associate the destination with existing storage. |
| `SetterAction` | `WRITE_THROUGH` | Expose a Python setter that updates native state. |
| `SetterAction` | `REJECT_REPLACEMENT` | Keep the property readable but reject replacing its storage. |
| `SetterAction` | `OMIT` | Do not expose a Python setter. |

## Supported Triples

The resolver's validated triples are the authoritative combinations:

| Owner + transfer + destruction | Typical use |
| --- | --- |
| `PYTHON + BY_VALUE + PYTHON_REFCOUNT` | Scalar result. |
| `PYTHON + COPY_RETURN + PYTHON_REFCOUNT` | Array or string copied into a Python result. |
| `PYTHON + SNAPSHOT_COPY + PYTHON_REFCOUNT` | Detached view of current native state. |
| `CALLER + CALL_LOCAL + NONE` | Read-only caller value used only during the call. |
| `CALLER + CALL_LOCAL + CALL_LOCAL` | Caller-classified value with wrapper-created call storage that needs local cleanup. |
| `CALLER + IN_PLACE + CALLER` | Caller array mutated without ownership transfer. |
| `NATIVE + BORROWED_VIEW + NATIVE_OWNER` | Live module-state view. |
| `WRAPPER + CALL_LOCAL + NONE` | Existing wrapper instance used for one call without creating a resource. |
| `WRAPPER + IN_PLACE + WRAPPER_DEALLOC` | Existing wrapper-controlled storage mutated in place. |
| `WRAPPER + BORROWED_VIEW + WRAPPER_DEALLOC` | Field storage retained by its parent wrapper. |
| `WRAPPER + WRAPPER_INSTANCE + WRAPPER_DEALLOC` | Generated object or owned descriptor handle. |
| `TEMPORARY + CALL_LOCAL + CALL_LOCAL` | Generated bridge temporary. |

Not every syntactically possible triple is meaningful. Adding a new triple is
a semantic feature: update the resolver validation, completed wrapper policy,
planner validation, backend lowering, documentation, and focused runtime tests
together.

## Explicit Overrides and Pointer Policy

`Ownership(...)`, `Transfer(...)`, and `Destruction(...)` override the general
lifetime triple. The resolver normalizes the metadata, applies storage
invariants, and then validates the resulting combination. An override never
bypasses the normal safety gates.

`PointerPolicy(...)` is a separate descriptor/target contract with ten fields:

| Field | Question answered |
| --- | --- |
| `nullable` | May the descriptor be unassociated? |
| `transfer` | How is the pointer or target relationship used at the boundary? |
| `target_owner` | Who owns the target allocation? |
| `lifetime` | What proves the target outlives the Python use? |
| `deallocation` | Which target-release operations are permitted? |
| `shape_source` | Where are rank and extents obtained? |
| `contiguity` | What storage-layout guarantee is available? |
| `reassociation` | Which association-changing operations are permitted? |
| `aliasing` | Is the result a live alias, descriptor, or independent copy? |
| `mutability` | May Python or native code modify the target through this path? |

The strings are retained so contracts can describe project-specific facts;
policy completion still accepts only mechanisms the current wrapper runtime
can implement. Pointer-array module variables, fields, arguments, and results
are descriptor containers. Their container ownership is fixed by their native
location, so `PointerPolicy` governs extraction and descriptor operations
rather than silently replacing that ownership with the general override.

## Resolution and Validation Order

`OwnershipPolicyResolver.decide_semantic_type()` performs these stages in
order:

1. Normalize the semantic type into immutable storage facts.
2. Select a default decision for the object kind and semantic use context.
3. Apply explicit ownership or pointer metadata.
4. Reject unsupported pointer lifetimes and reassociation.
5. Complete immutable-value policy and validate result projection.
6. Validate the owner/transfer/destruction triple.
7. Derive general, Python-barrier, and native-barrier lowering actions.

This order prevents an explicit annotation from bypassing a later safety
check, and prevents a backend from selecting an easier but semantically
different implementation.

## Change and Test Routes

The main source owners are:

- `prik/policy/ownership.py`: vocabulary, defaults, overrides, validation,
  and completed actions;
- `prik/policy/completion.py`: attachment of decisions to semantic
  variables, functions, fields, classes, and module state;
- `prik/policy/construction.py`: completed wrapper-policy records and
  cross-feature validation;
- `prik/policy/models.py`: immutable feature-specific completed-policy records;
- `prik/planning/planner.py`: projection into the editable wrapper plan;
- `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py`: strict
  dispatch from planned actions into emitted mechanisms.

The enums documented on this page are the shared ownership vocabulary defined
in `ownership.py`. Feature-specific completed policies also define narrower
mechanical enums in `models.py`, such as derived-object owner
retention/release and native-array descriptor ownership/release. Those values
refine an already completed ownership decision for one implementation family;
they do not form another competing ownership system.

Start focused verification in
`tests/fortran/infrastructure/semantics/test_ownership.py`. Add feature-specific
policy and runtime evidence under the owning `tests/fortran/<feature>/`
directory whenever a decision gains a new observable mechanism. The user-facing
lifetime and stale-view rules remain in
[Memory Management](../../user/guide/memory-management.md).

## Safety Boundary

Completed ownership policy makes release responsibility explicit; it does not
make every live view memory-safe. Native deallocation, allocatable
reallocation, pointer reassociation, or owner destruction can invalidate an
existing NumPy view. The generated runtime cannot revoke every previously
exported view, so users must copy data that needs to outlive such a native
change and request a fresh view afterward.
