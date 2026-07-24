---
title: Native Array Handle Checklist
audience: maintainers
prerequisites: semantic .pyi format, ownership policy, allocatables, pointers
related: index.md, ../../user/reference/semantic-pyi-format.md, ../../user/guide/allocatables.md, ../../user/guide/pointers.md
status: active-roadmap
publication: draft
---

# Native Array Handle Checklist

This is the implementation and verification checklist for native Fortran array
descriptor handles:

- `Allocatable[T[...]]`
- `Pointer[T[...]]`

Use this page as the canonical checklist for this feature. The original prompts
are consolidated here; future implementation should use this page instead of
re-reading those prompts.

The intended implementation is one shared native-array handle path with
descriptor-specific operations layered on top. Keep Allocatable and Pointer as
separate public contract types, but do not build two unrelated parser, policy,
runtime, bridge, or binding stacks.

Scalar allocatable and pointer procedure projections are not part of this array
handle work. Scalars continue to use ordinary nullable Python values plus
`@native_call` descriptor projections such as `Allocatable(Arg(i))`,
`Pointer(Arg(i))`, `Allocatable(Return(...))`, and `Pointer(Return(...))`.
For scalar descriptor inputs, explicit `None` means a present but unallocated
allocatable descriptor or a present but unassociated pointer descriptor. Native
optional scalar descriptor dummies use the three-state scalar bridge path:
omission means `present(...)` false, explicit `None` means a present descriptor
with absent value state, and a value means a present descriptor with scalar
storage. Array handles keep a different rule: `Allocatable[T[...]] | None` and
`Pointer[T[...]] | None` mean optional absent handle only.

## Core Contract Decisions

- [x] `Allocatable[T[...]]` means a Python handle to a native allocatable array
  descriptor.
- [x] `Pointer[T[...]]` means a Python handle to a native pointer array
  descriptor.
- [x] `Allocatable[T[...]]` and `Pointer[T[...]]` are handles, not NumPy arrays.
- [x] `T[...]` remains the ordinary array data-buffer contract.
- [x] Passing a handle to an `Allocatable[T[...]]` or `Pointer[T[...]]`
  parameter uses descriptor semantics.
- [x] Passing a handle to a `T[...]` parameter uses normal array-actual
  semantics in the shared runtime handoff path. For native wrapper calls, pass
  the handle's native array actual to the normal Fortran array dummy instead of
  implicitly calling `.to_numpy()`; generated wrapper parameter integration is
  tracked separately below.
- [x] Normal `T[...]` parameters require a valid array actual: allocatable
  handles must be allocated, pointer handles must be associated, and
  allocated/associated zero-length arrays remain valid.
- [x] Unallocated allocatable handles and unassociated pointer handles are
  accepted only by descriptor-handle parameters such as `Allocatable[T[...]]`
  and `Pointer[T[...]]`, where that state belongs inside the handle.
- [x] Plain NumPy arrays are rejected by the shared runtime descriptor-parameter
  handoff for `Allocatable[T[...]]` and `Pointer[T[...]]` descriptor
  parameters; generated wrapper parameter integration is tracked separately
  below.
- [x] `| None` on a handle means the handle object itself may be absent for a
  native optional dummy, not that a present handle is unallocated or
  unassociated.
- [x] Unallocated allocatable state lives inside the allocatable handle:
  `h.allocated is False` and `h.to_numpy() is None`.
- [x] Unassociated pointer state lives inside the pointer handle:
  `p.associated is False` and `p.to_numpy() is None`.
- [x] `Annotated[T[...], Allocatable]` is not an active public allocatable-array
  spelling after migration.
- [x] `Annotated[T[...], Pointer]` is not an active public pointer-array
  spelling after migration.
- [x] `Snapshot[T]` is not an allocatable- or pointer-array extraction mode and
  is no longer an active public contract.
- [x] Live native-array views, explicit user-requested NumPy copies, live
  derived objects, and descriptor handles remain distinct concepts in docs,
  diagnostics, runtime names, and tests.

## Public `.pyi` Examples

### Allocatable Handles

```python
from x2py.contracts import Allocatable, Float64, Int32

values: Allocatable[Float64[:]]

class box:
    values: Allocatable[Float64[:]]

def resize(values: Allocatable[Float64[:]], n: Int32) -> None: ...

def make_values(n: Int32) -> Allocatable[Float64[:]]: ...

def maybe_optional(
    values: Allocatable[Float64[:]] | None = ...,
) -> None: ...

def scale(values: Float64[:]) -> None: ...
```

`scale()` is ordinary array-data semantics. It may accept an allocated
`Allocatable[Float64[:]]` at runtime by passing the handle's native array actual
to the normal Fortran array dummy. It does not receive an allocatable dummy
descriptor.

### Pointer Handles

```python
from x2py.contracts import Float64, Int32, Pointer

values: Pointer[Float64[:]]

class box:
    values: Pointer[Float64[:]]

def reassociate(
    values: Pointer[Float64[:]],
    target: Pointer[Float64[:]],
) -> None: ...

def maybe_optional(
    values: Pointer[Float64[:]] | None = ...,
) -> None: ...

def scale(values: Float64[:]) -> None: ...
```

`scale()` is ordinary array-data semantics. It may accept an associated
`Pointer[Float64[:]]` at runtime by passing the handle's native array actual to
the normal Fortran array dummy. It does not receive a pointer dummy descriptor.

## Call Compatibility Model

For a normal array data signature:

```python
from x2py.contracts import Allocatable, Float64, Pointer

def f(x: Float64[:]) -> None: ...

plain: Float64[:]
allocatable: Allocatable[Float64[:]]
pointer: Pointer[Float64[:]]

f(plain)
f(allocatable)
f(pointer)
```

all three calls are valid when the runtime value can provide usable
`Float64[:]` data:

- `f(plain)` passes the NumPy/data-buffer value directly;
- `f(allocatable)` verifies that the handle is allocated and compatible, then
  passes the wrapped native allocatable array actual to the normal Fortran array
  dummy;
- `f(pointer)` verifies that the handle is associated and compatible, then
  passes the wrapped native pointer array actual to the normal Fortran array
  dummy.

This mirrors Fortran argument association: a non-allocatable array dummy can be
called with ordinary, allocatable, or pointer actual arrays when the actual
array is present/associated and otherwise valid. At the Python boundary this is
not allocatable-or-pointer dummy descriptor semantics; the callee sees a normal
array dummy. It also is not an implicit `.to_numpy()` conversion.

If the user writes `f(allocatable.to_numpy())` or `f(pointer.to_numpy())`, that
is the explicit public extraction path. The result is treated like any other
ordinary array argument and must pass the normal validation rules, including
non-`None` state and any mutability requirements.

For descriptor signatures:

```python
def g(x: Allocatable[Float64[:]]) -> None: ...

def h(x: Pointer[Float64[:]]) -> None: ...
```

`g()` requires an allocatable handle and `h()` requires a pointer handle. A
plain NumPy array is rejected because it has no native allocatable or pointer
descriptor to pass.

Internally, model this as a handle with an array-data facet plus descriptor
facts, not as a global rewrite of the base array type. For example, an
`Allocatable[Float64[:]]` value should expose or carry:

- array data type: `Float64[:]`;
- descriptor kind: `allocatable`;
- descriptor operations: allocation state, descriptor passing, deallocate, and
  resize.

A `Pointer[Float64[:]]` value should expose or carry:

- array data type: `Float64[:]`;
- descriptor kind: `pointer`;
- descriptor operations: association state, descriptor passing, nullify, and
  any policy-gated allocation/deallocation operations.
- default handle mode: `Pointer[T[...]]` must be usable without
  `PointerPolicy(...)` for conservative handle creation, association
  inspection, descriptor handoff, `nullify()` where legal, and supported
  extraction operations.
- explicit policy mode: `PointerPolicy(...)` enables or requests behavior that
  needs otherwise unprovable facts, such as allocation, deallocation,
  reassociation, target lifetime, or unsafe ownership transfer.

The implementation may use predicates or metadata equivalent to
`is_allocatable` and `is_pointer` on the specific handle semantic type, but
plain `Float64[:]` itself remains the data-buffer contract. Do not make a
normal array parameter infer descriptor semantics merely because a handle is
accepted as an array-like runtime value.

## Recommended Implementation Order

### 1. Documentation And Contract Sync

Update the public docs first so the intended behavior is explicit before code
changes.

- [x] Update `docs/user/guide/allocatables.md`.
- [x] Update `docs/user/guide/pointers.md`.
- [x] Update `docs/user/reference/semantic-pyi-format.md`.
- [x] Update memory-management or language-support pages if they describe
  allocatable or pointer arrays as NumPy arrays, `ndarray | None`, metadata
  annotations, or `Snapshot[T]`.
- [x] Document that `Allocatable[T[...]]` is a handle, not an ndarray.
- [x] Document that `Pointer[T[...]]` is a handle to pointer association state,
  not an ndarray.
- [x] Document that `h.to_numpy()` returns a live view of the current allocation
  or `None`, never an automatic detached copy.
- [x] Document that `p.to_numpy()` returns the current target view or `None`,
  and can expose strided pointer targets when descriptor support is available.
- [x] Document that passing a handle to a handle parameter is descriptor
  passing, while passing a handle to `T[...]` uses normal array-actual
  semantics through the handle's native array-data facet.
- [x] Document call compatibility for `def f(x: T[...])`: ordinary arrays,
  allocated allocatable handles, and associated pointer handles are accepted
  as array actuals without implicit `.to_numpy()` conversion.
- [x] Document that normal `T[...]` parameters reject unallocated allocatable
  handles and unassociated pointer handles because there is no valid array
  actual to pass. Allocated or associated zero-length arrays are still valid.
- [x] Document that explicit `f(h.to_numpy())` is a separate user-requested
  ndarray path and follows ordinary ndarray validation.
- [x] Document that parameters annotated as `Allocatable[T[...]]` or
  `Pointer[T[...]]` pass native descriptors, so they require the corresponding
  handle object. Ordinary arrays are accepted only by normal `T[...]`
  parameters.
- [x] Document that plain ndarray inputs are rejected for descriptor-handle
  parameters.
- [x] Document that module allocatables and pointer arrays expose handles, not
  `ndarray | None` module attributes.
- [x] Document that derived allocatable and pointer fields expose handles.
- [x] Document that allocatable function results can return owned handles only
  when x2py creates stable owner storage.
- [x] Document that pointer handles do not imply target ownership.
- [x] Document that pointer `nullify()` is default, while pointer
  `allocate()`, `deallocate()`, and `resize()` require explicit policy.
- [x] Document stale-view hazards after descriptor-changing operations,
  reassociation, nullification, deallocation, or reallocation.
- [x] Remove active public examples of `Annotated[T[...], Allocatable]` and
  `Annotated[T[...], Pointer]` for this feature.

### 2. Public Contract Symbols, Parser, And Printer

Implement the public contract wrappers once and parameterize by descriptor kind.

- [x] Add `Allocatable[...]` as a real array-handle contract wrapper.
- [x] Add `Pointer[...]` as a real array-handle contract wrapper.
- [x] Parse `Allocatable[T[...]]` into a semantic representation for a native
  allocatable array handle.
- [x] Parse `Pointer[T[...]]` into a semantic representation for a native
  pointer array handle.
- [x] Parse optional absent callable-argument handles as
  `Allocatable[T[...]] | None = ...` and `Pointer[T[...]] | None = ...`.
- [x] Reject `Allocatable[T[...]] | None` and `Pointer[T[...]] | None` outside
  optional callable arguments.
- [x] Reject optional/defaulted callable-argument handles that omit the
  explicit `| None` spelling.
- [x] Preserve normal `T[...]` type identity as array data semantics, not
  descriptor semantics.
- [x] Do not interpret `Snapshot[T]` as a native-array descriptor wrapper.
- [x] Remove the obsolete public `Snapshot` contract, its semantic `.pyi`
  parsing/printing, generated contracts, and recursive derived-object lowering.
- [x] Reject or fully migrate `Annotated[T[...], Allocatable]` from active
  public contracts.
- [x] Reject or fully migrate `Annotated[T[...], Pointer]` from active public
  contracts.
- [x] Keep metadata-only allocatable or pointer facts only as temporary internal
  migration facts, not as accepted public syntax.
- [x] Print generated module allocatables as `Allocatable[T[...]]`.
- [x] Print generated derived allocatable fields as `Allocatable[T[...]]`.
- [x] Print allocatable descriptor arguments and supported handle results as
  `Allocatable[T[...]]`.
- [x] Print generated module pointer arrays as `Pointer[T[...]]`.
- [x] Print generated derived pointer fields as `Pointer[T[...]]`.
- [x] Print pointer descriptor arguments and supported handle results as
  `Pointer[T[...]]`.

### 3. Semantic IR Representation

Create one semantic representation family for native array handles with a
descriptor-kind field rather than separate unrelated models.

- [x] Represent common native-array handle facts:
  - descriptor kind: allocatable or pointer;
  - element semantic type;
  - dtype;
  - rank;
  - shape metadata when statically known;
  - array data type/facet used when a handle is passed to a normal `T[...]`
    parameter;
  - string element length metadata when applicable;
  - optional-absent handle state;
  - source origin: module variable, derived field, argument, or result;
  - native access path.
- [x] Keep handle semantic types distinct from normal array semantic types.
- [x] Store allocatable/pointer descriptor facts on the handle semantic type,
  not as a global mutation of the plain array type.
- [x] Permit shared predicates or metadata equivalent to `is_allocatable` and
  `is_pointer` on handle semantic types when that helps policy dispatch.
- [x] Keep each handle's base array data type available for ordinary `T[...]`
  call compatibility.
- [x] Keep scalar descriptor projection metadata on the existing scalar
  nullable-value path, not on array handle types.
- [x] Preserve `T[...]` arguments/results as normal array data in semantic IR
  even when runtime may later accept a handle through data coercion.
- [x] Verify `Snapshot[T]` is absent from active semantic IR and remains
  unrelated to native-array-handle extraction.

### 4. Post-IR Policy Completion

Complete every semantic decision before wrapper planning. Bridge and binding
generators must dispatch from these decisions rather than inferring policy from
datatype, intent, origin, dotted access shape, alias metadata, or local memory
checks.

The completed decision is recorded as `NativeArrayHandlePolicy` metadata on
each handle declaration or result type. That policy records the descriptor kind,
handle origin/kind, owner retention, borrowed-vs-owned descriptor status,
getter/setter behavior, native assignment behavior, release responsibility,
target lifetime, generated destroy behavior, storage mode, optional
absent-handle state, `.to_numpy()` extraction policy, and descriptor operation
permissions. It also records whether the selected path requires pointer C
descriptor interop or owned-allocatable CFI storage, so build integration can
gate `ISO_Fortran_binding.h` from completed policy instead of raw datatype
checks. Wrapper planning must fail before lowering a native array handle that
is missing this completed policy.

For pointer handles, plain `Pointer[T[...]]` gets a default conservative
operation table for descriptor association, `nullify()`, and unavailable
extraction reporting. `PointerPolicy(...)` adds facts for behavior that needs
an explicit contract. `allocate(shape)` requires an explicit reassociation
value that allows allocation, `deallocate()` requires an explicit deallocation
value, and `resize(shape)` requires both sides to opt into resize. When an
explicit pointer policy selects descriptor-view extraction, the completed policy
records the `pointer_c_descriptor` interop requirement even if another planning
blocker still prevents wrapper lowering.

- [x] Add one completed native-array-handle policy decision shared by
  Allocatable and Pointer.
- [x] Complete descriptor kind before lowering: allocatable or pointer.
- [x] Complete handle kind before lowering:
  - `borrowed_module_descriptor`;
  - `borrowed_field_descriptor`;
  - `argument_descriptor`;
  - `owned_result_descriptor`;
  - `optional_absent_handle`;
  - `unsupported`.
- [x] Complete ownership and lifetime retention before lowering.
- [x] Complete whether the Python handle is borrowed or owned before lowering.
- [x] Complete getter behavior before lowering.
- [x] Complete Python setter exposure, if any, before lowering.
- [x] Complete native setter assignment behavior, if any, before lowering.
- [x] Complete output projection/readback behavior before lowering.
- [x] Complete release responsibility and generated destroy behavior before
  lowering.
- [x] Complete `.to_numpy()` policy before lowering:
  - `borrowed_view`;
  - `descriptor_view`;
  - `contiguous_view`;
  - `unsupported`.
- [x] Complete standard C-descriptor interop requirement before lowering:
  `none`, `module_allocatable_c_descriptor`, or `pointer_c_descriptor`.
- [x] Complete nullability and optional-absent-handle behavior before lowering.
- [x] Complete contract-value storage mode before lowering: `stack`, `heap`, or
  `alias`.
- [x] Keep descriptor-argument and optional-absent-handle policies semantically
  complete before lowering; generated bridge descriptor pass-through dispatches
  from this completed policy.
- [x] Fail wrapper planning with a clear diagnostic when descriptor ownership, target
  lifetime, shape, addressability, release responsibility, or extraction policy
  is incomplete.

#### Allocatable Policy Items

- [x] Complete allocated-state support.
- [x] Complete live-view mechanism independently from `Aliased`: direct
  borrowed access where legal, otherwise standard descriptor access.
- [x] Give plain and `Aliased` module allocatable handles the same native-owned
  borrowed lifetime, mutability, and live-view-or-`None` public behavior.
- [x] Block unsupported descriptor extraction explicitly instead of copying.
- [x] Complete `deallocate()` permission.
- [x] Complete `resize(shape)` permission.
- [x] Complete function-result ownership as wrapper-owned stable descriptor
  storage.
- [x] Mark unsupported allocatable array forms as wrapper-planning errors rather than
  silently falling back to NumPy-array copy behavior.

#### Pointer Policy Items

- [x] Complete association-state support.
- [x] Complete target lifetime policy.
- [x] Complete `to_numpy()` extraction policy:
  - descriptor view;
  - contiguous view;
  - unsupported.
- [x] Select pointer `to_numpy()` policy from completed `PointerPolicy(...)`
  facts before lowering: contiguous targets use `contiguous_view`, and
  strided/general targets use `descriptor_view`. A copy-oriented pointer policy
  may retain unrelated meaning, but must not make extraction copy.
- [x] Complete `nullify()` permission as the default pointer descriptor
  operation.
- [x] Complete a default conservative handle profile for plain
  `Pointer[T[...]]` without requiring `PointerPolicy(...)`.
- [x] Complete `allocate(shape)` permission only when explicit pointer policy
  allows allocation through this pointer.
- [x] Complete `deallocate()` permission only when explicit pointer policy
  allows deallocation through this pointer.
- [x] Add an explicit unsafe/user-responsibility deallocation policy value,
  `unsafe_deallocate`, for callers who knowingly request deallocation without
  x2py-proven target ownership.
- [x] Complete `resize(shape)` permission only when explicit pointer policy
  allows resize through this pointer.
- [x] Do not expose pointer `allocate()`, `deallocate()`, or `resize()` when
  policy disallows those operations.
- [x] Treat pointer handle ownership as descriptor/association access by
  default, not target ownership.
- [x] For pointer results, support `owned_result_descriptor` only when stable
  owner storage and target lifetime are explicit; otherwise stop wrapper planning.

### 5. Shared Runtime Handle Foundation

Add or reuse one internal runtime base for both public handle classes.

- [x] Implement or reuse `NativeArrayHandleBase`.
- [x] Put shared dtype metadata on the base.
- [x] Put shared rank metadata on the base.
- [x] Put shared shape-query dispatch on the base.
- [x] Put shared `to_numpy()` dispatch on the base.
- [x] Put shared owner/lifetime retention on the base.
- [x] Put shared generated ops table/accessor storage on the base.
- [x] Validate generated operation table names and callables when a runtime
  handle is constructed.
- [x] Require generated runtime handles to provide the shared `shape` operation
  at construction time.
- [x] Require generated runtime handles to provide an internal `array_actual`
  operation for normal `T[...]` native array-actual handoff, distinct from
  explicit public `to_numpy()` extraction.
- [x] Require generated runtime handles to provide an internal `descriptor`
  operation for `Allocatable[T[...]]` and `Pointer[T[...]]` descriptor-parameter
  handoff.
- [x] Reject generated `array_actual` or `descriptor` handoff operations that
  return `None`, so present handles cannot collapse into optional absent-handle
  state.
- [x] Require generated `array_actual` operations to return the internal typed
  native-array handoff object carrying a non-null native data address.
- [x] Require generated `descriptor` operations to return either decoded
  standard descriptor fields or a contiguous native data address that the
  shared runtime normalizes into those fields. An unallocated or unassociated
  descriptor may carry a null `base_addr`; that state remains distinct from an
  absent optional handle.
- [x] Put shared borrowed-vs-owned descriptor kind on the base.
- [x] Validate shared runtime descriptor kind at handle construction, so
  generated handles can only use `allocatable` or `pointer` descriptor tags.
- [x] Put shared owned-handle release state and finalizer dispatch on the base,
  so generated owner-storage handles can call a generated `destroy` operation
  exactly once.
- [x] Require generated owned-handle operation tables to provide a callable
  `destroy` operation at construction time.
- [x] Run owned-handle destroy operations before marking the handle closed, so
  generated destroy accessors can still read descriptor or owner state.
- [x] Mark owned handles closed after a generated destroy attempt even when
  destroy reports an error, so finalizers cannot retry the same native release.
- [x] Leave room for optional generation or stale-view tracking later.
- [x] Add an internal runtime array-actual validation and handoff hook for
  future normal `T[...]` handle inputs, without calling `to_numpy()`.
- [x] Add an internal runtime normal-array argument dispatcher that keeps
  ordinary ndarray validation and native-handle array-actual handoff as
  separate paths while sharing dtype, rank, shape, layout, and writeability
  checks.
- [x] Add an internal runtime normal-array argument ABI packer that returns the
  generated Bind-C array tuple fields from either an ndarray data pointer or a
  native handle `array_actual` handoff: pointer address, optional runtime rank,
  optional item size, extents, and optional upper bounds plus unit strides.
- [x] Normalize runtime layout validation for handle array-actual handoff with
  the same supported `C` and `F` layout expectations used by the ndarray path.
- [x] Normalize runtime handle shapes as non-negative extents, rejecting
  negative dimensions while preserving zero-length arrays as valid array
  actuals.
- [x] Let the internal runtime normal-array argument dispatcher enforce native
  byte order and alignment when generated binding policy requests those checks.
- [x] Add an internal runtime descriptor-parameter validation and handoff hook
  for future `Allocatable[T[...]]` and `Pointer[T[...]]` binding inputs,
  including optional absent-handle `None` mapping.
- [x] Validate descriptor-parameter handoff kind before mapping optional
  absent-handle `None`, so unsupported descriptor kinds cannot silently pass.
- [x] Add an internal runtime descriptor-argument field packer that returns
  validated `base_addr`, `elem_len`, `rank`, and per-dimension lower-bound,
  extent, and stride-multiplier facts. Generated C uses those facts to establish
  call-local `CFI_CDESC_T(rank)` storage for non-projected descriptor calls;
  Python never supplies compiler-private descriptor storage.
- [x] Add a distinct direct standard-C-descriptor handoff for projected writable
  handles. Owned allocatable handles pass their persistent `CFI_cdesc_t*` so
  native allocation, deallocation, and shape changes update the same caller
  handle instead of a discarded call-local descriptor copy.
- [x] Use a dedicated non-null runtime presence token for present optional
  handle arguments, rather than reusing the descriptor handoff object as the
  presence field.
- [x] Pack optional descriptor arguments with the same validated descriptor
  facts plus a distinct presence token. Optional absent handles produce null
  fact fields and a null presence token; present unallocated or unassociated
  handles produce present descriptor facts whose `base_addr` may be null.
- [x] Carry the completed `.to_numpy()` extraction policy on the runtime
  handle.
- [x] Remove detached-copy dispatch from the runtime handle; extraction-enabled
  operations must supply live storage or standard descriptor facts.
- [x] Validate generated `.to_numpy()` operations return either a NumPy array or
  `None` before applying borrowed-view, descriptor-view, or contiguous-view
  policy.
- [x] Validate non-`None` `.to_numpy()` results against the handle's declared
  dtype and rank before returning them to Python.
- [x] Short-circuit absent descriptor state before generated extraction, so an
  unallocated allocatable handle or unassociated pointer handle returns `None`
  from `to_numpy()` without relying on backend extraction code.
- [x] Reject generated `.to_numpy()` results that report `None` after the
  handle has reported present descriptor state, so backend extraction cannot
  collapse allocated or associated handles into absent state.
- [x] Require generated runtime handles with an extraction-enabled
  `to_numpy_policy` to provide the generated `to_numpy` operation at
  construction time; handles without extraction support must use
  `to_numpy_policy="unsupported"`.
- [x] Enforce live contiguous-view and descriptor-view `.to_numpy()` policies
  in the shared runtime handle without a copy fallback.
- [x] Implement `AllocatableArray` as a descriptor-specific subclass.
- [x] Require allocatable runtime handles to provide the generated `allocated`
  operation at construction time.
- [x] Implement `PointerArray` as a descriptor-specific subclass.
- [x] Require pointer runtime handles to provide generated `associated` and
  default `nullify` operations at construction time.

Runtime handle support means the shared Python class enforces the completed
policy once generated operations provide access to current native storage.
Bridge generation for module variables, fields, arguments, results, and C
descriptor extraction remains tracked in the codegen and integration sections
below.

#### Allocatable Runtime API

- [x] `h.allocated -> bool`
- [x] `h.shape -> tuple[int, ...] | None`
- [x] `h.to_numpy() -> ndarray | None`
- [x] `h.deallocate()`
- [x] `h.resize(shape)`
- [x] `h.to_numpy()` returns `None` when unallocated.
- [x] `h.to_numpy()` returns a live mutable view for every supported allocated
  handle, using direct or descriptor access as selected by completed policy.
- [x] Users can call `.copy()` on the returned NumPy array when they need
  independent lifetime.
- [x] Existing views may become stale after descriptor-changing operations;
  accessing stale views is unsupported and may crash.

#### Pointer Runtime API

- [x] `p.associated -> bool`
- [x] `p.shape -> tuple[int, ...] | None`
- [x] `p.to_numpy() -> ndarray | None`
- [x] `p.nullify()`
- [x] Optional, policy-gated `p.allocate(shape)`
- [x] Optional, policy-gated `p.deallocate()`
- [x] Optional, policy-gated `p.resize(shape)`
- [x] `p.to_numpy()` returns `None` when unassociated.
- [x] `p.to_numpy()` returns a live borrowed NumPy view when associated and
  descriptor extraction is supported.
- [x] `p.to_numpy()` supports strided views when descriptor support is
  available.
- [x] `p.to_numpy()` raises a clear error when descriptor extraction is
  unavailable and no fallback is supported.
- [x] Old borrowed views are documented as stale after native code nullifies,
  reassociates, deallocates, or otherwise changes the pointer target.

### 6. IR-to-AST And Codegen Model

Lower only completed policy decisions into named implementation methods.

- [x] Use one completed array interop policy object for array-like bridge and
  binding decisions. The policy selects a named ABI lane:
  `data_buffer` for ordinary `T[...]` NumPy/data-pointer semantics, or
  `descriptor` for `Allocatable[T[...]]` and `Pointer[T[...]]` descriptor
  semantics.
- [x] Keep the generated implementation methods separate under that dispatcher:
  the data-buffer lane emits the existing pointer/shape/stride ABI for normal
  arrays, while the descriptor lane emits descriptor-handle ABI operations and
  any gated TS 29113 reader code.
- [x] Add codegen model nodes or metadata for native-array handle creation.
- [x] Add codegen model nodes or metadata for generated native-array handle ops.
- [x] Route Allocatable and Pointer handles through the same lowering path with
  descriptor-kind-specific operations.
- [x] Keep `@native_call Addr(Arg(i))` as data-address projection only.
- [x] Add native-array-handle bridge/binding dispatchers keyed by completed
  descriptor kind and handle kind.
- [x] Route native-array module-variable bridge generation through completed
  handle policy before ordinary module-variable array dispatch.
- [x] Route native-array derived-field bridge and binding generation through
  completed handle policy before ordinary field array dispatch.
- [x] Route native-array function-result bridge and binding generation through
  completed handle policy before ordinary array result dispatch.
- [x] Select descriptor passing from `Allocatable[T[...]]` or
  `Pointer[T[...]]` plus completed policy, not from `Addr`.
- [x] Lower unsupported policy decisions to planning/codegen errors, not
  fallback behavior.

### 7. Bridge Generation

Generate descriptor-access routines through the shared handle-ops shape, then
specialize operation bodies by descriptor kind.

- [x] Block generated descriptor-handle accessors with explicit native-array
  codegen blockers until the descriptor-access routines below exist.
- [x] Add the shared Bind-C/binding/runtime construction substrate for
  generated handle objects: explicit operation-name maps, module-owner
  retention, runtime factory creation, and pointer-address handoff wrapping.
- [x] Generate module allocatable handles as borrowed descriptor handles.
- [x] Create module allocatable handle objects at module initialization.
- [x] Store complete generated operation pointers/accessors for module
  allocatable variables, including portable descriptor handoff and generated
  `resize(shape)` operations. The operation table covers state, shape,
  array-actual and descriptor-fact handoff, `.to_numpy()`, `deallocate()`, and
  `resize(shape)` without exposing a compiler-private descriptor layout.
- [x] Do not move ownership out of the Fortran module for ordinary module
  allocatable attribute reads.
- [x] Generate derived-field allocatable handles as borrowed descriptor handles.
- [x] Keep the parent wrapper object alive for derived-field allocatable
  handles.
- [x] Generate field operations that access `parent%field`.
- [x] Generate owned allocatable function-result handles when policy supports
  stable owner storage.
- [x] Use wrapper-owned standard C descriptor storage for allocatable results:
  allocate persistent rank-specific `CFI_CDESC_T(rank)` storage and establish
  it with allocatable attribute. Numeric function results populate a local
  allocatable once, then transfer that allocation with `move_alloc`; generated
  shape-changing operations use `CFI_allocate`.
- [x] Assign a supported numeric direct allocatable function result once into a
  bridge-local allocatable, then `move_alloc` that allocation into the
  allocatable `intent(out)` dummy backed by persistent CFI storage. Do not
  generate a collector or a second intrinsic assignment. Rank-one, matrix, and
  higher-rank results preserve allocated, zero-sized, and unallocated state.
- [x] Return a native pointer to owner storage for owned allocatable handles.
- [x] Generate destroy routines called by the Python handle finalizer for owned
  allocatable handles.
- [x] Generate module pointer handles as borrowed descriptor handles.
- [x] Create module pointer handle objects at module initialization.
- [x] Store complete generated operation pointers/accessors for module pointer
  variables, including portable descriptor handoff and policy-gated
  `allocate(shape)`, `deallocate()`, and `resize(shape)` operations. The current
  generated module operation table covers association state, shape,
  pointer-address handoff wrappers, `nullify()`, and the policy-gated
  shape-changing operations when completed policy enables them. Descriptor
  handoff uses standard C descriptor facts rather than guessing a compiler
  descriptor layout.
- [x] Do not transfer ownership of pointer targets for module pointer handles.
- [x] Generate derived-field pointer handles as borrowed descriptor handles.
- [x] Keep the parent wrapper object alive for derived-field pointer handles.
- [x] Generate field operations that access `parent%field`.
- [x] Route pointer descriptor-argument bridge and binding generation through
  completed handle policy before ordinary array argument dispatch.
- [x] Model native descriptor-handle argument handoff as a dedicated Bind-C
  descriptor tuple selected by bridge and binding descriptor-argument handlers
  through completed output-projection policy. Non-projected calls establish
  standard call-local descriptor storage from validated runtime facts.
  Projected writable calls pass persistent standard C descriptor storage
  directly so descriptor mutation remains attached to the caller handle. Both
  paths add an explicit presence token only for optional absent handles.
- [x] Generate pointer descriptor-argument handoff for `Pointer[T[...]]`
  parameters.
- [x] Route allocatable descriptor-argument bridge and binding generation
  through completed handle policy before ordinary array argument dispatch.
- [x] Generate allocatable descriptor-argument handoff for
  `Allocatable[T[...]]` parameters.
- [x] Do not guess compiler-specific descriptor layouts. Descriptor-based
  interop must use the TS 29113 / Fortran 2018 C descriptor path or fail
  wrapper planning with an explicit diagnostic.

#### Pointer Descriptor Extraction

This path is feature-gated. It may use TS 29113 / Fortran 2018 C descriptors
only when descriptor-view interop is selected, and it must not add a global
`ISO_Fortran_binding.h` requirement to wrappers that do not need descriptor
decoding.

- [x] Use TS 29113 / Fortran 2018 C descriptors for general pointer-array
  `to_numpy()` when this path is enabled.
- [x] Use `ISO_Fortran_binding.h` only for descriptor-based pointer interop
  paths.
- [x] Do not require `ISO_Fortran_binding.h` globally.
- [x] In the shared runtime helper, build NumPy shape from decoded descriptor
  `dim[i].extent` fields supplied by generated descriptor-interoperability
  code.
- [x] In the shared runtime helper, build NumPy strides from decoded descriptor
  `dim[i].sm` fields supplied by generated descriptor-interoperability code.
- [x] Let pointer `descriptor_view` extraction operations return decoded
  descriptor fields as mappings or field-record objects, with the shared
  runtime converting those fields into the NumPy view instead of requiring
  every generated operation to call the helper.
- [x] Validate decoded pointer descriptor rank against the handle's declared
  rank before constructing the NumPy view.
- [x] Reject decoded pointer descriptors with null `base_addr` after the handle
  has reported associated state.
- [x] Support positive and negative descriptor stride multipliers in the shared
  runtime descriptor-view helper by computing the full buffer window before
  constructing the NumPy view.
- [x] In the shared runtime helper, read and validate decoded descriptor
  `base_addr`, `elem_len`, `rank`, `dim[i].lower_bound`, `dim[i].extent`, and
  `dim[i].sm` fields for pointer views.
- [x] Add a shared generated C/CPython descriptor-reader primitive that decodes
  a `CFI_cdesc_t*` into the runtime descriptor-view mapping shape, without
  exposing TS 29113 layout details in public Python APIs.
- [x] Generate code that reads TS 29113 descriptor `base_addr`, `elem_len`,
  `rank`, `dim[i].lower_bound`, `dim[i].extent`, and `dim[i].sm` for pointer
  descriptor-view operations in private generated CPython operation wrappers.
- [x] Support strided pointer targets, including negative strides, in the shared
  runtime once generated descriptor-interoperability code supplies decoded
  descriptor fields.
- [x] If descriptor support is unavailable, choose one explicit policy:
  contiguous-only pointer views when shape/address are safely available,
  explicitly implemented copy fallback, or a wrapper-planning failure with a
  clear diagnostic. There is no deferred blocker payload.

### 8. Python Binding Generation

Keep descriptor-handle argument conversion separate from normal array data
conversion. For normal `T[...]` parameters, support both ordinary ndarray inputs
and native handle inputs, but do not implement handle inputs by implicitly
calling `.to_numpy()`. The handle path should route to a native array-actual
handoff when the wrapped call is native.

- [x] Accept `AllocatableArray` objects for `Allocatable[T[...]]` parameters.
- [x] Reject plain NumPy arrays for `Allocatable[T[...]]` parameters.
- [x] Accept `PointerArray` objects for `Pointer[T[...]]` parameters.
- [x] Reject plain NumPy arrays for `Pointer[T[...]]` parameters.
- [x] Accept `None` for optional-absent handle parameters only when the `.pyi`
  annotation includes `| None`.
- [x] Convert `None` optional handles into native absent optional dummies, not
  into unallocated or unassociated handle objects.
  The CPython binding layer now packs required and optional descriptor-handle
  arguments through the runtime descriptor-argument helper, and bridge
  generation passes descriptor dummies through the Bind-C descriptor tuple.
- [x] For normal `T[...]` parameters, accept ndarray inputs through the existing
  array data path.
- [x] For concrete-rank numeric normal `T[...]` parameters in generated Bind-C
  wrapper calls, accept allocated allocatable handles only by validating the
  handle state and passing the wrapped native allocatable array actual to the
  normal native array dummy.
- [x] For concrete-rank numeric normal `T[...]` parameters in generated Bind-C
  wrapper calls, accept associated pointer handles only by validating the
  handle state and passing the wrapped native pointer array actual to the normal
  native array dummy.
- [x] Share dtype, rank, shape, layout, and mutability validation policy between
  ndarray inputs and handle inputs for concrete-rank numeric `T[...]`, while
  keeping the existing ndarray pointer/shape handoff and native-handle
  array-actual handoff as separate generated implementation branches.
- [x] Treat explicit `h.to_numpy()` or `p.to_numpy()` results that are NumPy
  arrays as ordinary ndarray input through the existing array-storage path.
- [x] Reject read-only arrays returned by explicit `h.to_numpy()` or
  `p.to_numpy()` when the native dummy requires writable storage, reusing the
  existing writable ndarray validation.
- [x] Add direct wrapper coverage showing explicit `h.to_numpy()` or
  `p.to_numpy()` returning `None` is rejected as an ordinary ndarray argument
  for non-nullable `T[...]` dummies.
- [x] Reject unallocated allocatable handles for concrete-rank numeric `T[...]`
  unless nullable data-buffer behavior is explicitly implemented.
- [x] Reject unassociated pointer handles for concrete-rank numeric `T[...]`
  unless nullable data-buffer behavior is explicitly implemented.
- [x] Reject unallocated allocatable handles for optional, assumed-rank, and
  character `T[...]` unless nullable
  data-buffer behavior is explicitly implemented.
- [x] Reject unassociated pointer handles for optional, assumed-rank, and
  character `T[...]` unless nullable
  data-buffer behavior is explicitly implemented.

### 9. Compilation And Build Gating

- [x] Require descriptor interop support only when a generated wrapper uses the
  pointer C-descriptor path or persistent CFI owner storage for an allocatable
  result.
- [x] Do not require `ISO_Fortran_binding.h` for allocatable-only builds that
  contain no owned allocatable result handles.
- [x] Require `ISO_Fortran_binding.h` locally when owned allocatable result
  handles use persistent `CFI_CDESC_T` storage.
- [x] Do not require `ISO_Fortran_binding.h` for pointer builds that do not use
  descriptor-based pointer interop.
- [x] Collect native-array build requirements from completed handle policy
  metadata, not from raw `Allocatable[...]` or `Pointer[...]` syntax.
- [x] Record native-array build requirements in replayable `.pyi` wrapper build
  manifests.
- [x] Emit a clear planning or build diagnostic when pointer descriptor interop
  is required but unavailable.

## Test Checklist

### Parser And Printer Tests

- [x] Parse and print `Allocatable[Float64[:]]`.
- [x] Parse and print `Allocatable[String[:][:]]`.
- [x] Parse and print `Allocatable[Float64[:, :]]`.
- [x] Parse and print `Allocatable[Float64[:]] | None = ...`.
- [x] Reject `Allocatable[Float64[:]] | None` on non-argument declarations.
- [x] Parse and print `Pointer[Float64[:]]`.
- [x] Parse and print `Pointer[Float64[:, :]]`.
- [x] Parse and print `Pointer[String[8][:]]` if string arrays are supported.
- [x] Parse and print `Pointer[Float64[:]] | None = ...`.
- [x] Reject `Pointer[Float64[:]] | None` on non-argument declarations.
- [x] Verify normal `T[...]` type identity remains array data semantics even
  when runtime can accept handles by data coercion.
- [x] Verify `Allocatable[T[...]]` and `Pointer[T[...]]` retain a base array
  data type that matches the wrapped `T[...]` annotation.
- [x] Reject `Snapshot[T]` in active contracts.
- [x] Reject or migrate `Annotated[T[...], Allocatable]`.
- [x] Reject or migrate `Annotated[T[...], Pointer]`.
- [x] Verify no generated `.pyi` uses `Snapshot[T]`.
- [x] Verify no generated active `.pyi` uses public
  `Annotated[T[...], Allocatable]` or `Annotated[T[...], Pointer]` for array
  descriptor handles.

### Semantic IR And Policy Tests

- [x] Verify Allocatable and Pointer handles use the same semantic handle
  representation family with distinct descriptor kinds.
- [x] Verify handle types are distinct from normal array data types.
- [x] Verify handle semantic types carry descriptor facts without mutating the
  plain array semantic type.
- [x] Verify handle semantic types expose the base array data type used for
  `T[...]` call compatibility.
- [x] Verify module-variable, derived-field, argument, result, and optional
  absent handle origins complete policy before lowering.
- [x] Verify native array handle policy carries owner retention, target
  lifetime, and generated destroy behavior before lowering.
- [x] Verify bridge/binding layers dispatch from completed policy decisions.
- [x] Verify incomplete ownership, lifetime, release, addressability, or
  descriptor-extraction facts produce wrapper-planning errors.
- [x] Verify descriptor-handle arguments stop wrapper planning until generated handle
  handoff exists instead of falling back to NumPy-array conversion.
- [x] Verify plain `Pointer[T[...]]` generates the default conservative handle
  profile without requiring `PointerPolicy(...)`.
- [x] Verify missing owner/release facts block only ownership-changing pointer
  operations, not association inspection, handle passing, or other safe default
  handle operations.
- [x] Verify `Addr(Arg(i))` rejects `Allocatable[T[...]]` and
  `Pointer[T[...]]` descriptor handles instead of acting as descriptor passing.
- [x] Verify pointer allocation/deallocation/resize permissions are absent or
  blocked unless explicit pointer policy allows them.
- [x] Verify unsafe/user-responsibility deallocation is available only through
  the explicit policy value and never by default.
- [x] Verify completed `PointerPolicy(...)` facts select `contiguous_view` or
  `descriptor_view` before lowering, never an extraction-only copy action, and
  only descriptor-view paths request pointer C-descriptor interop.
- [x] Verify pointer C-descriptor interop requirements produce an explicit
  wrapper-planning error while that interop path is unavailable.

### Shared Runtime Handle Tests

- [x] Verify `AllocatableArray` and `PointerArray` use the same common
  `to_numpy()`, `shape`, dtype, rank, owner-retention, and ops-table path.
- [x] Verify common shape metadata is reported consistently.
- [x] Verify common dtype metadata is reported consistently.
- [x] Verify handles keep required module, parent object, or owner storage alive.
- [x] Verify invalid generated operation tables fail at handle construction
  before descriptor state or native handoff is queried.
- [x] Verify handles without the shared generated `shape`, `array_actual`, or
  `descriptor` operations fail at construction.
- [x] Verify generated `array_actual` and `descriptor` handoff operations cannot
  return `None`; optional absent handles are the only runtime path that maps to
  absent descriptor fact fields.
- [x] Verify generated array-actual operations must return the internal typed
  native-array handoff object with a non-null pointer address, rejecting
  booleans, non-integers, zero addresses, negative addresses, and arbitrary
  Python objects before generated bridge handoff.
- [x] Verify descriptor operations accept validated decoded standard descriptor
  fields or a contiguous data address, preserve null `base_addr` as present
  unallocated/unassociated state, and reject malformed field records.
- [x] Verify shared runtime handles reject unsupported descriptor-kind tags
  before any generated operations are used.
- [x] Verify owned handles call generated destroy ops exactly once when closed
  or finalized, and borrowed handles do not destroy native owner storage.
- [x] Verify owned handles without generated `destroy` operations fail at
  construction instead of leaking through a suppressed finalizer error.
- [x] Verify owned-handle destroy operations can inspect live handle state
  before the handle is marked closed.
- [x] Verify owned handles are marked closed after a failing destroy attempt,
  preventing finalizer retries of the same generated release operation.
- [x] Verify generated `.to_numpy()` operations cannot return non-NumPy objects
  from borrowed-view or contiguous-view policies, and cannot return non-NumPy
  objects from descriptor-view policy unless the value is a decoded pointer
  descriptor field mapping or field-record object.
- [x] Verify generated `.to_numpy()` arrays and decoded pointer descriptor
  views must match the handle's declared dtype and rank.
- [x] Verify `to_numpy()` returns `None` for unallocated allocatable handles and
  unassociated pointer handles before generated extraction or unsupported-policy
  errors are reached.
- [x] Verify generated extraction cannot return `None`, or a decoded pointer
  descriptor with null `base_addr`, after the handle has reported present
  descriptor state.
- [x] Verify extraction-enabled handles without generated `to_numpy` fail at
  construction, while unsupported extraction raises the completed-policy error.
- [x] Verify contiguous-view policy rejects non-contiguous arrays and never
  copies; descriptor-view policy preserves validated shape and strides.
- [x] Verify the internal runtime array-actual hook rejects absent descriptor
  state and uses generated handoff ops instead of `to_numpy()`.
- [x] Verify the internal runtime array-actual hook validates expected dtype,
  rank, shape, layout, and writeability before generated handoff.
- [x] Verify handle array-actual layout validation normalizes `C` and `F`
  expectations consistently with ndarray validation and rejects unsupported
  layout names before generated handoff.
- [x] Verify the internal runtime normal-array argument dispatcher accepts
  ordinary ndarrays through an ndarray path, accepts allocated/associated
  handles through native array-actual handoff, and rejects unallocated or
  unassociated handles without calling `to_numpy()`.
- [x] Verify the internal runtime normal-array argument ABI packer emits the
  generated Bind-C array tuple shape for ndarray inputs and for
  allocated/associated handle inputs without calling `to_numpy()`.
- [x] Verify the internal runtime normal-array argument dispatcher preserves
  zero-length array actuals and rejects handle shapes with negative extents.
- [x] Verify the internal runtime normal-array argument dispatcher rejects
  byte-swapped or unaligned ndarray inputs when generated binding policy
  requests native byte order or alignment.
- [x] Verify the internal runtime descriptor-parameter hook accepts only the
  matching handle class/kind, rejects ordinary arrays, validates expected dtype,
  rank, and shape, and maps optional `None` to an absent native handle.
- [x] Verify optional absent-handle `None` still rejects unsupported descriptor
  kinds before returning the native absent-handle sentinel.
- [x] Verify the internal runtime descriptor-argument field packer returns
  `base_addr`, `elem_len`, `rank`, and each dimension's lower bound, extent, and
  stride multiplier; maps optional absent-handle `None` to null fact fields;
  and uses a distinct non-null presence token for present optional handles.
- [x] Verify projected writable handle arguments require a typed direct
  standard-descriptor handoff and reject fact-only descriptors before native
  mutation can detach the caller's handle state.
- [x] Verify CPython binding generation packs required and optional
  descriptor-handle arguments through the runtime helper, dispatches
  non-projected calls to standard call-local CFI storage, dispatches projected
  writable calls to persistent descriptor storage, and passes the selected
  descriptor pointer through the completed Bind-C tuple shape.
- [x] Verify allocatable handles without generated `allocated` fail at
  construction.
- [x] Verify pointer handles without generated `associated` or `nullify` fail
  at construction.

### Allocatable Runtime Tests

- [x] Module allocatable attribute is a handle object.
- [x] `h.allocated` updates after allocate, deallocate, and resize.
- [x] `h.shape` updates after allocate, deallocate, and resize.
- [x] `h.to_numpy()` returns `None` when unallocated.
- [x] Plain and `Aliased` allocated module handles both return mutable live
  views, and mutating either view updates native module storage.
- [x] A fresh extraction follows allocation, deallocation, resize, and
  reallocation state; an explicit `.copy()` remains independent.
- [x] Tests state the stale-view contract without dereferencing deliberately
  stale storage.
- [x] Derived allocatable field is a handle object.
- [x] Derived-field handle keeps the parent wrapper alive.
- [x] Derived-field `deallocate()` operates on `parent%field`.
- [x] Derived-field `resize(shape)` operates on `parent%field`.
- [x] Allocatable function result returns an owned handle.
- [x] Owned result handle finalizer deallocates native owner storage.
- [x] Owned result handle `to_numpy()` works after the bridge returns.
- [x] `Allocatable[T[...]]` parameter accepts allocatable handles.
- [x] `Allocatable[T[...]]` parameter rejects plain ndarray.
- [x] `T[...]` parameter accepts ndarray.
- [x] Concrete-rank numeric `T[...]` parameter accepts allocated allocatable handle through native
  array-actual handoff, without implicitly calling `h.to_numpy()`.
- [x] Concrete-rank numeric `T[...]` parameter applies the same dtype, rank, shape, layout, and
  mutability validation policy to ndarray inputs and allocated allocatable
  handles.
- [x] Explicit `T[...]` calls with `h.to_numpy()` follow the ordinary ndarray
  path and reject `None` or read-only arrays when writable storage is required.
- [x] Concrete-rank numeric `T[...]` parameter rejects unallocated allocatable handle unless nullable
  data-buffer behavior is explicitly supported.

### Pointer Runtime Tests

- [x] Module pointer attribute is a handle object.
- [x] `p.associated` reflects association state.
- [x] `p.shape` reflects association state and target shape.
- [x] `p.to_numpy()` returns `None` when unassociated.
- [x] `p.to_numpy()` returns a borrowed view when associated and supported.
- [x] `p.nullify()` disassociates the native pointer descriptor.
- [x] Derived pointer field is a handle object.
- [x] Derived-field pointer handle keeps the parent wrapper alive.
- [x] Derived-field pointer operations access `parent%field`.
- [x] Pointer associated with a slice returns a NumPy view with expected shape
  and strides when C descriptors are available.
- [x] Runtime pointer handles raise a clear unavailable-operation error when
  no descriptor-extraction `to_numpy()` operation is generated.
- [x] Runtime pointer descriptor-view extraction validates required decoded
  TS29113 fields before constructing a NumPy view.
- [x] If C descriptors are unavailable, test the selected explicit behavior:
  contiguous live view or clear wrapper-planning diagnostic, never a copy fallback.
- [x] Pointer `deallocate()` and `resize()` are absent or raise when policy
  disallows them.
- [x] Pointer `allocate()`, `deallocate()`, and `resize()` work only when
  explicit pointer policy allows them.
- [x] `Pointer[T[...]]` parameter accepts pointer handles.
- [x] `Pointer[T[...]]` parameter rejects plain ndarray.
- [x] Concrete-rank numeric `T[...]` parameter accepts an associated pointer
  handle through native array-actual handoff when the target is contiguous,
  without implicitly calling `p.to_numpy()`.
- [x] Concrete-rank numeric `T[...]` parameter applies the same dtype, rank, shape, layout, and
  mutability validation policy to ndarray inputs and associated pointer
  handles.
- [x] Reject noncontiguous pointer targets from the pointer/shape array-actual
  handoff instead of silently treating their elements as contiguous.
- [x] Explicit `T[...]` calls with `p.to_numpy()` follow the ordinary ndarray
  path and reject `None` or read-only arrays when writable storage is required.
- [x] Concrete-rank numeric `T[...]` parameter rejects unassociated pointer handle unless nullable
  data-buffer behavior is explicitly supported.

### Build Gating Tests

- [x] Pointer descriptor interop includes or requires `ISO_Fortran_binding.h`
  only when descriptor-based pointer interop is used.
- [x] Borrowed/argument-only allocatable builds do not require
  `ISO_Fortran_binding.h`; owned allocatable result builds include it for their
  persistent CFI storage path.
- [x] Builds that need unavailable pointer descriptor interop fail with a clear
  diagnostic rather than guessing descriptor layout.

### Documentation Regression Tests

- [x] Public docs show `Allocatable[T[...]]` for allocatable array handles.
- [x] Public docs show `Pointer[T[...]]` for pointer array handles.
- [x] Public docs do not show `Annotated[T[...], Allocatable]` as the active
  public spelling.
- [x] Public docs do not show `Annotated[T[...], Pointer]` as the active public
  spelling.
- [x] Public docs do not show `Snapshot[T]` as an active array descriptor
  contract.
- [x] Public docs explain `to_numpy()` as the explicit user-facing extraction
  operation for both handle types, not the required internal implementation of
  handle-to-native calls.

## Completion Criteria

The feature is complete only when all of these are true:

- [x] Allocatable and Pointer array handles share one internal handle
  foundation.
- [x] Public contract syntax is `Allocatable[T[...]]` and `Pointer[T[...]]`.
- [x] Active parser/printer paths reject or remove the old annotation and
  snapshot forms.
- [x] Post-IR policy completes every handle decision before wrapper planning.
- [x] Bridge and binding generation dispatch from completed policy only.
- [x] Runtime handles expose the documented APIs and state transitions.
- [x] Pointer descriptor extraction never guesses compiler-specific descriptor
  layout.
- [x] Build gating keeps descriptor interop requirements local to the paths that
  need them.
- [x] Runtime tests cover module variables, derived fields, arguments, data
  coercion, owned allocatable results, pointer association, pointer nullify, and
  pointer policy gating.
- [x] Documentation and generated `.pyi` fixtures no longer present old public
  forms as active contracts.
