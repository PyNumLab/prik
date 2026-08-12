---
title: Ownership Tracking
audience: maintainers
prerequisites: runtime layer, memory ownership model
related: runtime-layer.md, wrapper-generation-pipeline.md, ../../user/guide/memory-management.md
status: maintained
publication: draft
---

# Ownership Tracking

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

- `prik/semantics/ownership.py`: vocabulary, defaults, overrides, validation,
  and completed actions;
- `prik/semantics/policy_completion.py`: attachment of decisions to semantic
  variables, functions, fields, classes, and module state;
- `prik/semantics/wrapper_policy.py`: completed wrapper-policy records and
  cross-feature validation;
- `prik/codegen/planner.py`: projection into the immutable wrapper plan;
- `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py`: strict
  dispatch from planned actions into emitted mechanisms.

The enums documented on this page are the shared ownership vocabulary defined
in `ownership.py`. Feature-specific completed policies also define narrower
mechanical enums in `wrapper_policy.py`, such as derived-object owner
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
