---
title: Wrapper Design Notes
audience: advanced users, developers, maintainers
prerequisites: Fortran wrapper guide, semantic IR reference
related: design/overall-architecture.md, internal-architecture/wrapper-generation-pipeline.md
status: design
---

# Wrapper Design Notes

This file records policy decisions that are not settled by the implemented
Fortran wrapper contract. The parser and semantic layers should keep collecting
source facts, emitting blockers where policy is missing, and leaving runtime
behavior to the owning wrapper backend. User-supplied C inputs do not yet have a
runtime backend; the generated C binding used by the Fortran path does not
change that boundary.

Reference details live in:

- `docs/c_parser.md`
- `docs/fortran_parser.md`
- `docs/fortran_wrapper.md`
- `docs/semantics.md`

## Known Semantic Gaps To Track

These are source-language concepts that the parser or semantic layer can often
see today, but that still need a stronger `.pyi`, semantic, or wrapper policy
before generated wrappers should treat them as supported behavior.

### C Gaps

| Gap | Current risk | Proposed direction |
| --- | --- | --- |
| Function pointers and callbacks | The parser can capture function-pointer shape, but some C callback declarations still lack a complete wrapper policy. | Round-trip callback signatures as named `@prototype` declarations and make wrapper planning fail until lifetime, threading, exception, context-pointer, and unregister policy is supplied. |
| Pointer ownership and array extents | Raw pointers, pointer-to-pointer values, unknown extents, output buffers, and arrays of pointers are ambiguous without user policy. | Keep exact pointer topology in semantic IR. Require explicit `.pyi` ownership, borrow, output, shape, nullability, and copy/readback policy before projecting to Python containers or NumPy arrays. |
| Unions | `CUnion` identifies the native type, but it does not say which member is active or whether by-value union ABI is safe. | Continue representing named and anonymous unions explicitly with `CUnion`; require active-member/discriminant policy for high-level access. Prefer a compiled shim or target layout proof for by-value union calls; otherwise make wrapper planning fail. |
| Bitfields | Bit width is parser-visible, but Python field access needs target layout, signedness, padding, and read/write rules. | Preserve bit width, declared base type, containing aggregate, and layout-sensitive attributes. Generate access through a compiled C shim or target layout probe; block direct field projection when layout cannot be proven. |
| ABI and layout attributes | Attributes such as `packed`, `aligned`, `vector_size`, `stdcall`, `ms_abi`, asm labels, and compiler-specific qualifiers can change layout or calls. | Normalize ABI facts into semantic metadata on functions, fields, and classes. Let wrappers accept only the default ABI directly; use generated shims or explicit target support for non-default calling conventions and layout-sensitive attributes. |
| `volatile`, `_Atomic`, and extended scalar types | These require memory-order, side-effect, or target-specific scalar policy that ordinary scalar mapping cannot express. | Add explicit semantic wrappers or metadata for volatile and atomic access, defaulting to a wrapper-planning error. Extend compiler probing for target scalar spellings such as `_BitInt`, `__int128`, and `_Float128` before assigning stable dtypes. |

### Fortran Gaps

| Gap | Current risk | Proposed direction |
| --- | --- | --- |
| Procedure pointers and dummy procedures | A broad `Procedure` type loses enough signature and lifetime information that wrappers cannot safely call or receive callbacks. | Resolve abstract interface signatures into a first-class semantic callable form. Preserve procedure pointer, optional, pass-through, and callback lifetime facts; block wrapper generation until call direction and ownership policy are explicit. |
| `character(len=...)` and character ABI | Mapping all character forms to `String` loses length, kind, hidden length arguments, fixed buffers, and `bind(c)` byte-string behavior. | Represent character storage with length expression, kind, assumed-length status, array shape, and C-interoperability metadata. Require explicit encoding, termination, copy, and hidden-length ABI handling in wrapper policy. |
| Polymorphic `class(...)` and unlimited polymorphism | Static extension-type inheritance is represented by Python C-type inheritance. Scalar `class(base), intent(in)` dummies are safe when the accepted dynamic types are the closed set of known wrapped base/descendant classes, but replacement, allocation, pointer association, results, and unlimited polymorphism still need stronger contracts. | Preserve the `class(...)` source fact. Allow concrete type-bound passed-object arguments. For scalar `class(base), intent(in)` arguments, generate concrete dispatch candidates through the normal overload dispatcher, ordered from descendants to base. Block polymorphic results, arrays, `intent(out)`/`intent(inout)`, allocatable scalars, pointer scalars, and `class(*)` until wrapper policy defines accepted dynamic types, allocation behavior, and ownership. Keep `class(*)` under the assumed-type descriptor blocker. |
| Advanced type-bound procedure details | Default `pass`, explicit `pass(name)`, `nopass`, concrete type-bound generics, concrete type-bound operators, and concrete overrides are preserved and wrapped. Finalizers and deferred bindings still need stronger contracts. | Preserve complete binding metadata on semantic classes. Type-bound generics and operators use explicit `.pyi` `@overload("specific")` links and generated C-extension dispatch; unresolved or deferred targets fail at semantic conversion or wrapper planning. |
| Derived-type layout and interoperability | `sequence`, `bind(c)`, common ABI expectations, and component layout are wrapper-critical but not yet a complete runtime contract. | Add explicit Fortran derived-type markers and metadata for `bind(c)`, `sequence`, component order, and interoperable layout. Use compiler layout probes or generated Fortran/C shims before passing derived types by value or exposing memory views. |
| Pointer and allocatable ownership | Borrowed zero-copy views are supported for allocatable derived-type fields and target-backed module arrays. Allocatable array results, `intent(out)` dummies, and `intent(inout)` replacement dummies use copy-return NumPy-owned storage. Pointer arrays have no intrinsic owner, so results, module variables, and derived-type fields use snapshot-copy behavior only when association, shape, dtype, nullability, contiguity, target owner, and deallocation obligations are known; otherwise they remain blocked. | Keep pointer/allocatable, rank, bounds, `intent`, `target`, and contiguity facts in semantic IR. Expose allocatable fields/module arrays as borrowed views returning `None` when unallocated. Copy allocatable array results and allocatable output/replacement dummies before returning to Python. Expose pointer arrays only as Python-owned snapshots or block them until explicit borrowed-view, replacement, deallocation, aliasing, and stale-view policy is defined. Block allocatable scalar derived-type replacement until ownership and destruction policy is defined. |
| Assumed-rank, assumed-type, and optional descriptor-heavy arguments | Descriptors such as `dimension(..)` and `type(*)` can accept many native shapes that Python cannot infer safely. | Represent descriptor category, rank constraints, element type availability, optional presence, and contiguity. Generate wrappers only for explicit accepted rank/dtype policies or through backend shims that validate descriptors. |
| Generic interfaces and operators | Named generics, defined operators, named operators, and defined assignment now preserve explicit concrete-target links. Python cannot intercept `=`, arbitrary named operators, or infer safe in-place mutation. Static extension-type inheritance is represented in Python, and scalar polymorphic input dispatch reuses the same generated overload selection path. | Use Python data-model slots for intrinsic operators, `operator_name`/`r_operator_name` methods for named operators, and mutating `assign` methods for defined assignment. Keep exact dtype/rank/extension-class dispatch and reject indistinguishable signatures during generation. |
| Coarrays, teams, events, and directive-driven device/offload behavior | These introduce parallel runtime or device-memory semantics outside normal host wrappers. | Treat as out of the initial wrapper scope. Preserve diagnostics where detected and require a separate runtime design before claiming support. |

## Settled Scope

The C frontend is a declaration and signature parser for wrapper-relevant
interfaces. It does not need to become a full compiler-grade C implementation.
The supported target is the API surface needed to produce or validate wrappers:
functions, variables, structs, enums, typedefs, constants, arrays, pointers,
callbacks, and the metadata needed for completed policy decisions.

Generated CPython extension builds copy their bundled C/Python support header
into a `binding_support/` directory inside the build output. The generated C
extension includes `binding_support/prik_binding.h`. This header is an
implementation detail of the generated extension, but its name is intentionally
prik-specific so it does not look like user source or a generic C wrapper.

The support header is header-only: each helper has internal linkage and is
eligible for inlining when the generated binding translation unit is compiled.
There is no separately compiled or linked support object. It exposes a
deliberately small `prik_*` mechanical API: scalar type matching, scalar
unpacking, scalar creation as a Python or NumPy object, and release of a
bridge-owned allocation. The generated binding passes the completed NumPy type,
layout, ownership, and mutation decisions into those operations. Native support
must not infer a layout, accept a different dtype, or choose ownership behavior
from a value at runtime; those are completed wrapper-plan decisions.

Generated CPython extensions should expose useful NumPy-style docstrings on the
Python-visible API. The CPython wrapper layer owns this generation because it has
the final callable signatures, hidden projection decisions, class/property
layout, and return conversion policy. These docstrings are for Python users and
should stay compact. Use NumPy-style sections with short type headers such as
`x : ndarray[float64]` and `result : ndarray[float64] or None`. Put only the
facts that are known and useful: rank for arrays, shape only when constrained or
known, layout for rank greater than one as `F-contiguous` or `C-contiguous`,
intent for arguments, mutation for `intent(out)`/`intent(inout)`, ownership
when it matters using `Ownership: Python-owned` or `Ownership: Native-owned`,
and when `None` can be returned. Do not emit placeholder unknowns such as
runtime-determined shape or scalar rank. Avoid long
wrapper-internal explanations. Class docstrings should
summarize fields and methods. Get/set descriptor docstrings should describe
class attributes, including borrowed view lifetimes for allocatable arrays and
snapshot-copy behavior for pointer-backed arrays. Module variables exposed
through getter functions should document the getter, since CPython modules do
not provide a portable per-variable descriptor docstring for plain module
attributes.

Verbose wrapper builds should print the exact compiler command lines they run,
not only the source or target being compiled. The printed command should be
shell-quoted so users can copy it to reproduce object compilation, generated
wrapper compilation (including its header-only native binding support), and
final shared-library linking.

Normal C parsing uses a real compiler preprocessor first. Macro expansion,
conditional compilation, token paste, stringify, and include resolution belong
to that compiler preprocessing step. The parser should consume the resulting C
translation unit and preserve provenance where useful.

Raw macro-generated declarations are not a separate parser target. If a macro
creates a declaration, that declaration should be visible after preprocessing:

```c
#define DECLARE_SCALE(T) void scale_##T(T *values, int n)

DECLARE_SCALE(double);
```

After preprocessing, the parser should see the expanded declaration and does not
need to understand `DECLARE_SCALE` itself.

C compiler extensions are supported when they appear in C declarations that we
need for wrappers. Unsupported or policy-sensitive extension semantics can still
be represented as diagnostics or wrapper-planning errors. C++ is a separate frontend
problem; C-compatible declarations that survive C preprocessing remain C work.

## Wrapper Decisions To Revisit

### ABI Boundary

We already collect wrapper-relevant declaration facts. The open wrapper-phase
question is how much exact ABI behavior the generated wrapper must model itself
versus delegate to a compiled shim or backend compiler.

Example:

```c
struct Packet {
    unsigned tag : 3;
    unsigned flags : 5;
    double payload;
} __attribute__((packed));

void send_packet(struct Packet packet);
```

The parser can preserve struct members, bitfield facts, attributes, and the
function signature. The wrapper phase must decide whether this can be passed
directly, needs a generated C shim, or should be blocked because exact layout or
calling convention is not safe enough.

### Pointer Ownership And Lifetime

The wrapper must not infer ownership silently. A pointer can mean borrowed
storage, owned allocation, mutable in-place data, read-only data, optional data,
or a sentinel-terminated buffer. The user must provide the missing policy in the
wrapper contract.

Example:

```c
double *make_values(size_t n);
void free_values(double *values);
void scale(double *values, size_t n);
const double *borrow_values(void);
```

These signatures alone do not prove who owns the memory, how long it lives, or
whether Python should copy, borrow, mutate, or free it. The wrapper design
should make that explicit in `.pyi` or another policy layer.

### Pointer, Size, And Output Projections

Explicit projections are allowed. Automatic hidden projection is not. If a C API
uses pointer/size pairs or output buffers, the wrapper can expose a Pythonic
shape only when the user supplies the projection policy, such as through
`@native_call`.

Example:

```c
int read_samples(double *out, size_t capacity, size_t *written);
```

The exact native contract is `out`, `capacity`, and `written`. A wrapper could
project this to `list[float]` or `np.ndarray`, but only after the user says how
large the output should be, who allocates it, how errors are handled, and whether
the result is copied or shared.

### Callback Policy

Callback wrappers need more than the function pointer type. The wrapper must
know whether the native library stores the callback, which Python object keeps it
alive, whether callbacks may happen on native threads, how exceptions propagate,
how `void *ctx` pairs with the callback, and how registration/unregistration
works.

Example:

```c
typedef void (*event_callback)(int code, void *ctx);

void register_callback(event_callback callback, void *ctx);
void unregister_callback(event_callback callback, void *ctx);
```

The parser can record the callback signature. The wrapper phase must decide the
lifetime, context pairing, threading, exception, and unregistration behavior
before generating a Python API.

### Fortran Allocatable And Pointer Reassociation

Fortran allocatable and pointer dummy arguments can replace the storage visible
to the caller. The parser and semantic IR should preserve allocatable/pointer
facts, but wrapper generation must decide Python replacement and lifetime
behavior.

Example:

```fortran
subroutine build_grid(x, n)
  integer, intent(in) :: n
  real, allocatable, intent(out) :: x(:)
end subroutine
```

The Fortran procedure may allocate or reallocate `x`. For allocatable array
dummy arguments, prik uses copy-return ownership: the bridge copies allocated
native storage into NumPy-owned memory, deallocates the temporary Fortran
allocation, and returns the new Python object. `None` represents an unallocated
dummy.

Array transfer policy is based on the native storage category and owner, not on
whether an array appears as a top-level result, module variable, or derived-type
field:

- Allocatable dummy arguments and function results are temporary replacement
  values at the Python boundary. They use copy-return storage and become
  Python-owned NumPy arrays or `None`.
- Allocatable derived-type fields are owned by the containing native instance.
  A field getter returns `None` or a borrowed NumPy view whose base keeps the
  containing Python wrapper alive.
- Target-backed allocatable module arrays are owned by the Fortran module for
  the process lifetime. Explicit getters may return `None` or borrowed NumPy
  views.
- Pointer arrays do not have intrinsic ownership. A pointer target may be a
  callee allocation, a module variable, a derived-type field, a dummy argument,
  a section, or external state. Therefore pointer array results, module
  variables, and derived-type fields must not become borrowed views or
  snapshot-copy values unless an explicit policy identifies the target owner,
  lifetime, deallocation rules, association replacement behavior, aliasing,
  mutability, shape, and contiguity.

The safe first behavior for exposed pointer arrays, when those policy facts are
known, is a snapshot copy: associated pointer targets are copied into
Python-owned NumPy arrays, and unassociated pointers become `None`. Mutating
that returned array does not mutate the native pointer target, and repeated
property access may produce a new snapshot. If the wrapper cannot prove
association state, shape, dtype, contiguity, nullability, and deallocation
obligations, wrapper planning must block the pointer array instead of returning a view,
leaking a callee allocation, double-freeing a borrowed target, or inventing
ownership.

This means a returned derived-type wrapper owns the native instance itself, but
does not automatically own targets reachable through pointer components. Putting
a pointer array inside an `intent(out)` derived type does not change the pointer
array policy: the object may be returned, but the pointer component is either a
documented snapshot-copy property with known owner/deallocation behavior or
remains unavailable until explicit pointer policy exists.

Returned derived-type wrappers own the native instance they wrap. If a
procedure produces the value through a Fortran temporary, the bridge must move
or copy that value into wrapper-owned native storage before the temporary goes
out of scope. Python/C must not deallocate allocatable components directly.
Instead, the wrapper object's `tp_dealloc` path should call a generated
Fortran-aware destroy helper for owned instances. That helper releases
allocatable components and invokes the supported Fortran finalization behavior.
Borrowed child wrappers and borrowed
array views keep the owning wrapper alive and never destroy native storage
themselves. Pointer component targets are not owned by the containing derived
type unless explicit pointer policy says so, so destroying the wrapper must not
deallocate those targets by default.

Allocatable borrowed views keep their containing derived-type wrapper alive, but
prik does not track views or invalidate them when native code reallocates or
deallocates the storage. Users must call `.copy()` when they need independent
lifetime. Allocatable `intent(inout)` array dummies are detached from the
caller: an input array is copied into a temporary native allocation, Fortran may
replace it, and Python receives a new NumPy-owned array or `None`; the original
array is not mutated. Module allocatable arrays require the native `target`
attribute because the bridge uses `c_loc`; otherwise wrapper planning reports a
blocker rather than generating a copying fallback. Allocatable scalar
derived-type replacement remains blocked until construction, replacement, and
destruction policy is explicit.

Pointer reassociation has similar policy questions:

```fortran
subroutine attach_view(x)
  real, pointer, intent(out) :: x(:)
end subroutine
```

The wrapper must define whether `x` becomes a borrowed view, an owned Python
object, or a blocked interface unless the user supplies more policy. Until
that policy exists, Fortran pointer `intent(out)` and `intent(inout)` dummy
arguments should remain blocked by default. A final associated pointer does not
prove whether the target was allocated for this return, borrowed from module
storage, borrowed from a derived-type field, associated with another dummy
argument, or kept alive elsewhere by native code.

The narrow first contract for procedure pointer arrays is implemented as:

- Pointer `intent(in)` dummy arrays may be call-local associations to
  Python-owned storage. Reassociation or saving the pointer beyond the call is
  unsupported unless an explicit policy says otherwise.
- Pointer array function results are copied into Python-owned values when
  association, shape, dtype, and contiguity are known. An unassociated result
  maps to `None`.
- Pointer `intent(out)` and `intent(inout)` dummy arguments require explicit
  policy metadata before they can be projected to Python returns or mutable
  Python-visible arguments.
- Module pointer variables and derived-type pointer fields use the same
  pointer ownership rule. They may be exposed only as documented snapshot
  copies when the wrapper can prove the required array facts. Borrowed pointer
  views require owner tracking and stale-view rules, so they are not the
  default field or module-variable behavior.

Scalar pointer `intent(in)` dummies use a call-local wrapper temporary. The
generated bridge associates the native pointer with that temporary only for the
call, so Python never receives a native address and does not observe writes or
reassociation. Scalar pointer function results use the same detached snapshot
rule as arrays: the bridge copies an associated value into wrapper-owned
temporary storage and returns an ordinary Python scalar, while an unassociated
result returns `None`.

Future `.pyi` pointer policy should make each missing fact explicit:

| Policy fact | Why the wrapper needs it |
| --- | --- |
| Nullability | Defines whether an unassociated pointer is valid and whether Python should receive `None` or raise an error. |
| Transfer mode | Distinguishes snapshot copy, borrowed NumPy view, native-owned capsule, Python-owned input storage, and blocked exact-native pointer passing. |
| Target owner | Identifies who owns the storage: a Python argument, a containing wrapper instance, a module variable, a callee allocation, an external library, or unknown native state. |
| Lifetime | States how long a borrowed target remains valid: call only, owner object lifetime, module lifetime, explicit release, or unknown. |
| Deallocation policy | Says whether the wrapper must never deallocate, should deallocate after copying, should attach a destructor capsule, or must call a named native release routine. This is the main missing fact for pointer outputs. |
| Shape source | Provides extents for array pointers, such as explicit `.pyi` dimensions, companion size arguments, descriptor bounds, or source pointer bounds. |
| Contiguity and strides | Decides whether only contiguous targets are supported, whether strided sections may become NumPy views, or whether non-contiguous targets must be copied or rejected. |
| Reassociation behavior | Defines what happens when Fortran points the dummy somewhere else: ignore the original Python input, return the final association as a snapshot, write back association state, invalidate old views, or block. |
| Aliasing | States whether two returned pointers may share one target and whether Python must preserve that identity or may return independent copies. |
| Mutability | Declares whether Python may write through a borrowed view and whether native code may write while Python holds it. |

These facts are policy, not parser facts. The parser and semantic IR should
preserve the native pointer, target, rank, bounds, intent, and contiguity
information they can observe, but wrapper planning should keep reporting a
blocker when the user-supplied policy is not strong enough for the requested
Python behavior.

Semantic `.pyi` expresses these facts in one keyword-only annotation:

```python
value: Annotated[
    Float64[:],
    Pointer,
    PointerPolicy(
        nullable=True,
        transfer="snapshot_copy",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="snapshot_final",
        aliasing="independent_copy",
        mutability="copy",
    ),
]
```

All ten keys round-trip through semantic IR. Metadata is descriptive policy,
not permission to bypass backend safety checks. In particular,
`transfer="borrowed_view"` remains blocked until the generated Python object
can retain the native owner and stale views can be invalidated after
reassociation or reallocation.

### Fortran Assumed-Rank Wrappers

Assumed-rank numeric array arguments use a fixed generated bridge policy. The
Python layer accepts NumPy array ranks 1 through 15, records the runtime rank
and descriptor metadata, and rejects rank 0 scalars or higher-rank arrays before
entering the bridge. The Fortran bridge then dispatches on each assumed-rank
argument's runtime rank, creates a rank-specific Fortran pointer view with
`c_f_pointer`, and calls the native procedure with fixed-rank actual arguments.

Example:

```fortran
subroutine inspect(x)
  real, intent(in) :: x(..)
end subroutine
```

The generated wrapper exposes one Python entrypoint for `inspect(x)`. Passing a
rank-3 `float64` Fortran-contiguous array selects the bridge case for rank 3 and
the native routine still receives the original assumed-rank dummy through a
rank-3 pointer view. Procedures with more than one assumed-rank argument use
nested bridge dispatch so each argument is viewed at its own runtime rank.

This support is intentionally limited to typed numeric arrays. Assumed-type
`type(*)` and unlimited polymorphic `class(*)` arguments remain blocked because
the wrapper cannot infer the element dtype, layout, or descriptor contract from
the source declaration alone; that information must come from a later `.pyi`
policy.

### Fortran Numeric Array Wrapper Subset

The settled numeric array subset uses validation and copy rules instead of
implicit conversion:

- Numeric array function results are copy-return values. Explicit-shape and
  automatic-shape results are copied out of the Fortran temporary into
  Python-owned C storage. Allocatable function results use the same copy-return
  policy and return `None` only when the Fortran result is unallocated.
  Zero-sized allocated results remain zero-sized NumPy arrays.
- Pointer array function results use the procedure snapshot policy: associated
  results are copied into Python-owned NumPy arrays, and unassociated results
  return `None`.
- Multidimensional Fortran results and arguments preserve Fortran order.
- The maximum supported wrapper rank is 15. Higher ranks are rejected before
  wrapper generation. Numeric assumed-rank `dimension(..)` dummy arguments use
  generated Fortran rank dispatch for actual NumPy array ranks 1 through 15.
  Rank 0 scalars are not accepted by the automatic assumed-rank policy.
- Python supplies full storage for assumed-size dummy arguments. The wrapper
  validates the declared extents it can express from literals, constants, and
  scalar argument names. The omitted final extent remains the caller's
  responsibility.
- `intent(in)` arrays may be read-only. `intent(out)` and `intent(inout)` arrays
  must be writeable.
- NumPy inputs must be native-endian and aligned. The wrapper does not perform
  unsafe casts, byte swaps, or alignment-fixing copies.
- Overlapping Python-visible arrays are not copied or de-aliased by prik; the
  call is forwarded to Fortran, so the native routine's aliasing contract still
  governs behavior.

Assumed-type `type(*)`, character arrays, and derived-type arrays remain
blocked until explicit dtype, descriptor, ABI, layout, construction, and
ownership policies are supplied.
