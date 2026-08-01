---
title: Wrapper Design Notes
audience: maintainers
prerequisites: Fortran wrapper reference, semantic IR reference
related: overall-architecture.md, ../internal-architecture/wrapper-generation-pipeline.md
status: design
publication: draft
---

# Wrapper Design Notes

<!-- X2PY_C_DOCS_START
This file records policy decisions that are not settled by the implemented
Fortran wrapper contract. The parser and semantic layers should keep collecting
source facts, emitting blockers where policy is missing, and leaving runtime
behavior to the owning wrapper backend. User-supplied C inputs do not yet have a
runtime backend; the generated C binding used by the Fortran path does not
change that boundary.
X2PY_C_DOCS_END -->

Reference details live in:

- `docs/developer/fortran-parser-reference.md`
- `docs/user/reference/fortran-wrapper.md`
- `docs/user/reference/semantic-ir.md`

<!-- X2PY_C_DOCS_START
- `docs/developer/c-parser-reference.md`
X2PY_C_DOCS_END -->

## Known Semantic Gaps To Track

These are source-language concepts that the parser or semantic layer can often
see today, but that still need a stronger `.pyi`, semantic, or wrapper policy
before generated wrappers should treat them as supported behavior.

<!-- X2PY_C_DOCS_START
### C Gaps
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
| Gap | Current risk | Proposed direction |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| Function pointers and callbacks | The parser can capture function-pointer shape, but some C callback declarations still lack a complete wrapper policy. | Round-trip callback signatures as named `@prototype` declarations and make wrapper planning fail until lifetime, threading, exception, context-pointer, and unregister policy is supplied. |
| Pointer ownership and array extents | Raw pointers, pointer-to-pointer values, unknown extents, output buffers, and arrays of pointers are ambiguous without user policy. | Keep exact pointer topology in semantic IR. Require explicit `.pyi` ownership, borrow, output, shape, nullability, descriptor handoff, and copy/readback policy before projecting to Python containers, handles, or NumPy arrays. |
| Unions | `CUnion` identifies the native type, but it does not say which member is active or whether by-value union ABI is safe. | Continue representing named and anonymous unions explicitly with `CUnion`; require active-member/discriminant policy for high-level access. Prefer a compiled shim or target layout proof for by-value union calls; otherwise make wrapper planning fail. |
| Bitfields | Bit width is parser-visible, but Python field access needs target layout, signedness, padding, and read/write rules. | Preserve bit width, declared base type, containing aggregate, and layout-sensitive attributes. Generate access through a compiled C shim or target layout probe; block direct field projection when layout cannot be proven. |
| ABI and layout attributes | Attributes such as `packed`, `aligned`, `vector_size`, `stdcall`, `ms_abi`, asm labels, and compiler-specific qualifiers can change layout or calls. | Normalize ABI facts into semantic metadata on functions, fields, and classes. Let wrappers accept only the default ABI directly; use generated shims or explicit target support for non-default calling conventions and layout-sensitive attributes. |
| `volatile`, `_Atomic`, and extended scalar types | These require memory-order, side-effect, or target-specific scalar policy that ordinary scalar mapping cannot express. | Add explicit semantic wrappers or metadata for volatile and atomic access, defaulting to a wrapper-planning error. Extend compiler probing for target scalar spellings such as `_BitInt`, `__int128`, and `_Float128` before assigning stable dtypes. |
X2PY_C_DOCS_END -->

### Fortran Gaps

| Gap | Current risk | Proposed direction |
| --- | --- | --- |
| Procedure pointers and dummy procedures | A broad `Procedure` type loses enough signature and lifetime information that wrappers cannot safely call or receive callbacks. | Resolve abstract interface signatures into a first-class semantic callable form. Preserve procedure pointer, optional, pass-through, and callback lifetime facts; block wrapper generation until call direction and ownership policy are explicit. |
| Pointer and allocatable ownership | Allocatable and pointer arrays use explicit descriptor handles. Module and derived-field handles borrow their native owner; owned allocatable results retain persistent wrapper-owned descriptor storage. An unallocated or unassociated descriptor remains a present handle whose `to_numpy()` result is `None`; otherwise `to_numpy()` returns a current live view and callers use `.copy()` explicitly for independent storage. Allocatable `intent(inout)` descriptor arguments accept handles and project the same caller handle, while ordinary arrays and ordinary array results keep NumPy data-buffer semantics. Rank-zero derived module allocatables/pointers use nullable live member proxies. Wrapper-owned allocatable and pointer derived results use persistent typed holders. Module allocatable dummies use reversible `move_alloc` holder transactions; module pointer dummies use typed association transactions and exact restoration. C transports opaque holder addresses and typed operation pointers, never descriptors. A pointer holder owns its association container, not an unknown native target. | Complete descriptor kind, handle/storage kind, actual declaration, dummy form, owner retention, live extraction or member mechanism, mutation/writeback, release, transaction cleanup, and operation permissions in post-IR policy before lowering. Route module, field, argument, and result generation through named policy dispatch. Keep contiguous-view, descriptor-view, scoped-reference, module-transaction, and typed-holder mechanisms distinct; never fall back from incomplete policy to a copy, fabricated address, or compiler-private descriptor. |
| Assumed-rank, assumed-type, and optional descriptor-heavy arguments | Descriptors such as `dimension(..)` and `type(*)` can accept many native shapes that Python cannot infer safely. | Represent descriptor category, rank constraints, element type availability, optional presence, and contiguity. Generate wrappers only for explicit accepted rank/dtype policies or through backend shims that validate descriptors. |
| Generic interfaces and operators | Named generics, defined operators, named operators, and defined assignment now preserve explicit concrete-target links. Python cannot intercept `=`, arbitrary named operators, or infer safe in-place mutation. Static extension-type inheritance is represented in Python, and scalar polymorphic input dispatch reuses the same generated overload selection path. | Use Python data-model slots for intrinsic operators, `operator_name`/`r_operator_name` methods for named operators, and mutating `assign` methods for defined assignment. Keep exact dtype/rank/extension-class dispatch and reject indistinguishable signatures during generation. |
| Coarrays, teams, events, and directive-driven device/offload behavior | These introduce parallel runtime or device-memory semantics outside normal host wrappers. | Treat as out of the initial wrapper scope. Preserve diagnostics where detected and require a separate runtime design before claiming support. |

<!-- X2PY_C_DOCS_START
| `character(len=...)` and character ABI | Mapping all character forms to `String` loses length, kind, hidden length arguments, fixed buffers, and `bind(c)` byte-string behavior. | Represent character storage with length expression, kind, assumed-length status, array shape, and C-interoperability metadata. Require explicit encoding, termination, copy, and hidden-length ABI handling in wrapper policy. |
| Polymorphic `class(...)` and unlimited polymorphism | Static extension-type inheritance is represented by Python C-type inheritance. Scalar `class(base), intent(in)` dummies are safe when the accepted dynamic types are the closed set of known wrapped base/descendant classes, but replacement, allocation, pointer association, results, and unlimited polymorphism still need stronger contracts. | Preserve the `class(...)` source fact for ordinary arguments. Infer it for the passed-object dummy of a resolved type-bound binding so generated `.pyi` does not repeat `Polymorphic` there. For scalar `class(base), intent(in)` arguments, generate concrete dispatch candidates through the normal overload dispatcher, ordered from descendants to base. Block polymorphic results, arrays, `intent(out)`/`intent(inout)`, allocatable scalars, pointer scalars, and `class(*)` until wrapper policy defines accepted dynamic types, allocation behavior, and ownership. Keep `class(*)` under the assumed-type descriptor blocker. |
| Advanced type-bound procedure details | Default `pass`, explicit `pass(name)`, `nopass`, concrete type-bound generics, concrete type-bound operators, and concrete overrides are preserved and wrapped. Finalizers and deferred bindings still need stronger contracts. | Preserve complete binding metadata on semantic classes. Type-bound generics and operators use explicit `.pyi` `@overload("specific")` links and generated C-extension dispatch; unresolved or deferred targets fail at semantic conversion or wrapper planning. |
| Derived-type layout and interoperability | `sequence`, `bind(c)`, component order, and layout remain semantic facts, but all Python wrappers are opaque. Exact monomorphic by-value dummies are called by typed Fortran bridge code; the C boundary never mirrors or byte-copies the aggregate. | Preserve the exact qualified native type and by-value fact before lowering. Keep component access in typed Fortran operations. Require compiler-proved layout only for a future direct C view, never for the opaque typed-value path. |
X2PY_C_DOCS_END -->

## Settled Scope

<!-- X2PY_C_DOCS_START
The C frontend is a declaration and signature parser for wrapper-relevant
interfaces. It does not need to become a full compiler-grade C implementation.
The supported target is the API surface needed to produce or validate wrappers:
functions, variables, structs, enums, typedefs, constants, arrays, pointers,
callbacks, and the metadata needed for completed policy decisions.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Generated CPython extension builds copy their bundled C/Python support header
into a `binding_support/` directory inside the build output. The generated C
extension includes `binding_support/x2py_binding.h`. This header is an
implementation detail of the generated extension, but its name is intentionally
x2py-specific so it does not look like user source or a generic C wrapper.

The support header is header-only and there is no separately compiled or linked
support object. Small scalar helpers have internal linkage and are eligible for
inlining when the generated binding translation unit is compiled. They are
specialized by the completed scalar dtype instead of accepting a runtime dtype
selector. Exact scalar inputs use one fused validation-and-unpack operation;
the distinct coercive unpack operation is reserved for a completed boundary
that permits Python scalar conversion, such as a callback result.

The normal-array native-handle fallback is emitted once through this header and
remains out of line within each generated translation unit. Each call site
supplies the completed dtype, rank, shape, layout, mutability, flattening, and
ABI-field selectors and receives one mechanical data/extent/stride result. This
avoids copying runtime imports, reference cleanup, and tuple unpacking for every
array argument while keeping the ordinary NumPy path independent of the slow
fallback.

Helper linkage follows execution frequency rather than size alone. Small
operations on the successful NumPy and scalar paths may remain `static inline`
so the compiler can specialize completed dtype, rank, layout, and mutability
selectors without an extra C call. Error construction, cleanup, and native
handle fallback operations may be non-inlined because normal successful calls
do not execute them. Substantial stride or flattening helpers require measured
call-time and build-time evidence before moving out of line; reducing generated
source size is not sufficient if the normal Python-call boundary regresses.

Ordinary NumPy-array validation uses one compact `static inline` support
helper. Each wrapper supplies its completed dtype, rank bounds, layout,
contiguity, and writeability selectors; the helper performs the repeated type,
access, and layout checks, including the positive-stride contract. Concrete
shape expressions and ABI-field extraction remain in the wrapper because they
refer to call-local symbolic roles. Constant selectors allow the compiler to
specialize the successful path without requiring a separate helper call.

Procedure-only modules with at least 128 Python-call wrappers split them across
multiple generated binding translation units. The module-initialization unit
owns NumPy C-API import and the CPython method tables; worker units contain
stable, balanced groups of externally linked wrapper functions and reuse the
generated binding header. A 128-wrapper module begins with four worker units;
larger modules add workers around a target of 32 wrappers each. Sharding is
automatic only for the mechanically independent
function surface: module variables, classes, overload dispatch, callbacks,
derived runtime state, and persistent native-array handles retain one binding
translation unit. This is a compilation mechanism, not semantic policy, and
does not alter the completed call plan or the inlining of hot support helpers.

Together these helpers expose a deliberately small `x2py_*` mechanical API:
typed scalar unpacking, scalar creation as a Python or NumPy object, native
array-actual extraction, and release of a bridge-owned allocation. Native
support must not infer a layout, accept a different dtype, or choose ownership
behavior from a value at runtime; those are completed wrapper-plan decisions.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Generated CPython extensions should expose useful NumPy-style docstrings on the
Python-visible API. The CPython wrapper layer owns this generation because it has
the final callable signatures, hidden projection decisions, class/property
layout, and return conversion policy. These docstrings are for Python users and
should stay compact. One plan-side docstring builder must consume completed
wrapper-plan records; binding and bridge lowering must not reconstruct
documentation from native declarations or generated source. Use NumPy-style
sections with short type headers such as
`x : ndarray[float64]` and `result : ndarray[float64] or None`. Put only the
facts that are known and useful: rank for arrays, shape only when constrained or
known, layout for rank greater than one as `F-contiguous` or `C-contiguous`,
native mutation for writable arguments, ownership
when it matters using `Ownership: Python-owned` or `Ownership: Native-owned`,
and when `None` can be returned. Do not emit placeholder unknowns such as
runtime-determined shape or scalar rank. Avoid long
wrapper-internal explanations.

Every public surface must participate. Namespace docstrings list functions,
module attributes, and classes without empty headings. Function and method
docstrings show the public signature, parameters, ordered returns, optional
omission versus present-`None` behavior, and planned exceptions. Overload
docstrings list their accepted public signatures without exposing private
candidate names. Class docstrings summarize the public constructor, fields,
methods, and overloads. Constructor and method descriptors carry their own
docstrings so `help(Type.method)` is useful. Property docstrings describe the
public type, whether replacement assignment is supported, and relevant borrowed
or descriptor-handle lifetime. Because CPython modules do not provide portable
per-variable descriptors, module-variable documentation belongs in the
namespace docstring.
X2PY_C_DOCS_END -->

Verbose wrapper builds should print the exact compiler command lines they run,
not only the source or target being compiled. The printed command should be
shell-quoted so users can copy it to reproduce object compilation, generated
wrapper compilation (including its header-only native binding support), and
final shared-library linking.

<!-- X2PY_C_DOCS_START
Normal C parsing uses a real compiler preprocessor first. Macro expansion,
conditional compilation, token paste, stringify, and include resolution belong
to that compiler preprocessing step. The parser should consume the resulting C
translation unit and preserve provenance where useful.
X2PY_C_DOCS_END -->

Raw macro-generated declarations are not a separate parser target. If a macro
creates a declaration, that declaration should be visible after preprocessing:

<!-- X2PY_C_DOCS_START
```c
#define DECLARE_SCALE(T) void scale_##T(T *values, int n)

DECLARE_SCALE(double);
```
X2PY_C_DOCS_END -->

After preprocessing, the parser should see the expanded declaration and does not
need to understand `DECLARE_SCALE` itself.

<!-- X2PY_C_DOCS_START
C compiler extensions are supported when they appear in C declarations that we
need for wrappers. Unsupported or policy-sensitive extension semantics can still
be represented as diagnostics or wrapper-planning errors. C++ is a separate frontend
problem; C-compatible declarations that survive C preprocessing remain C work.
X2PY_C_DOCS_END -->

## Wrapper Decisions To Revisit

### ABI Boundary

We already collect wrapper-relevant declaration facts. The open wrapper-phase
question is how much exact ABI behavior the generated wrapper must model itself
versus delegate to a compiled shim or backend compiler.

Example:

<!-- X2PY_C_DOCS_START
```c
struct Packet {
    unsigned tag : 3;
    unsigned flags : 5;
    double payload;
} __attribute__((packed));

void send_packet(struct Packet packet);
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
The parser can preserve struct members, bitfield facts, attributes, and the
function signature. The wrapper phase must decide whether this can be passed
directly, needs a generated C shim, or should be blocked because exact layout or
calling convention is not safe enough.
X2PY_C_DOCS_END -->

### Pointer Ownership And Lifetime

The wrapper must not infer ownership silently. A pointer can mean borrowed
storage, owned allocation, mutable in-place data, read-only data, optional data,
or a sentinel-terminated buffer. The user must provide the missing policy in the
wrapper contract.

Example:

<!-- X2PY_C_DOCS_START
```c
double *make_values(size_t n);
void free_values(double *values);
void scale(double *values, size_t n);
const double *borrow_values(void);
```
X2PY_C_DOCS_END -->

These signatures alone do not prove who owns the memory, how long it lives, or
whether Python should copy, borrow, mutate, or free it. The wrapper design
should make that explicit in `.pyi` or another policy layer.

### Pointer, Size, And Output Projections

<!-- X2PY_C_DOCS_START
Explicit projections are allowed. Automatic hidden projection is not. If a C API
uses pointer/size pairs or output buffers, the wrapper can expose a Pythonic
shape only when the user supplies the projection policy, such as through
`@native_call`.
X2PY_C_DOCS_END -->

Example:

<!-- X2PY_C_DOCS_START
```c
int read_samples(double *out, size_t capacity, size_t *written);
```
X2PY_C_DOCS_END -->

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

<!-- X2PY_C_DOCS_START
```c
typedef void (*event_callback)(int code, void *ctx);

void register_callback(event_callback callback, void *ctx);
void unregister_callback(event_callback callback, void *ctx);
```
X2PY_C_DOCS_END -->

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
dummy arguments, x2py uses copy-return ownership: the bridge copies allocated
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
  detached-copy values unless an explicit policy identifies the target owner,
  lifetime, deallocation rules, association replacement behavior, aliasing,
  mutability, shape, and contiguity.

The current safe policy behavior for exposed pointer fields and module
variables is a conservative descriptor-handle profile: association inspection
and `nullify()` are distinct from target ownership, and allocation,
deallocation, and resize remain opt-in. Pointer-array descriptor arguments need
generated handle handoff before they can be accepted, and pointer-array results
need stable owner storage, target lifetime, descriptor extraction, and destroy
behavior before they can return handles. Until generated handle accessors exist,
wrapper planning must stop generation instead of returning a view, leaking a
callee allocation, double-freeing a borrowed target, or inventing ownership.

This means a returned derived-type wrapper owns the native instance itself, but
does not automatically own targets reachable through pointer components. Putting
a pointer array inside an `intent(out)` derived type does not change the pointer
array policy: the object may be returned, but the pointer component remains
unavailable until explicit descriptor extraction, target lifetime, and release
policy exists.

<!-- X2PY_C_DOCS_START
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
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Allocatable borrowed views keep their containing derived-type wrapper alive, but
x2py does not track views or invalidate them when native code reallocates or
deallocates the storage. Users must call `.copy()` when they need independent
lifetime. Allocatable `intent(inout)` array dummies are detached from the
caller: an input array is copied into a temporary native allocation, Fortran may
replace it, and Python receives a new NumPy-owned array or `None`; the original
array is not mutated. Module allocatable arrays require the native `target`
attribute because the bridge uses `c_loc`; otherwise wrapper planning reports a
blocker rather than generating a copying fallback. Allocatable scalar
derived-type replacement remains blocked until construction, replacement, and
destruction policy is explicit.
X2PY_C_DOCS_END -->

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

The narrow current contract for procedure pointer arrays is:

- Pointer-array descriptor arguments are represented in semantic policy but
  block wrapper lowering until generated handle handoff is implemented.
- Pointer array function results block wrapper lowering until stable owner
  storage, target lifetime, descriptor extraction, and generated destroy
  behavior are implemented.
- Pointer `intent(out)` and `intent(inout)` dummy arguments require explicit
  policy metadata before they can be projected to Python returns or mutable
  Python-visible arguments.
- Module pointer variables and derived-type pointer fields use the default
  conservative handle policy. Generated accessors remain blocked until
  descriptor-handle code generation is implemented; ownership-changing
  operations still require explicit policy.

Scalar pointer `intent(in)` dummies use a call-local wrapper temporary. The
generated bridge associates the native pointer with that temporary only for the
call, so Python never receives a native address and does not observe writes or
reassociation. Scalar pointer function results use copied-value projection: the
bridge copies an associated value into wrapper-owned temporary storage and
returns an ordinary Python scalar, while an unassociated result returns `None`.

Future `.pyi` pointer policy should make each missing fact explicit:

| Policy fact | Why the wrapper needs it |
| --- | --- |
| Nullability | Defines whether an unassociated pointer is valid and whether Python should receive `None` or raise an error. |
| Transfer mode | Distinguishes detached copy, borrowed NumPy view, native-owned capsule, Python-owned input storage, and blocked exact-native pointer passing. |
| Target owner | Identifies who owns the storage: a Python argument, a containing wrapper instance, a module variable, a callee allocation, an external library, or unknown native state. |
| Lifetime | States how long a borrowed target remains valid: call only, owner object lifetime, module lifetime, explicit release, or unknown. |
| Deallocation policy | Says whether the wrapper must never deallocate, should deallocate after copying, should attach a destructor capsule, or must call a named native release routine. This is the main missing fact for pointer outputs. |
| Shape source | Provides extents for array pointers, such as explicit `.pyi` dimensions, companion size arguments, descriptor bounds, or source pointer bounds. |
| Contiguity and strides | Decides whether only contiguous targets are supported, whether strided sections may become NumPy views, or whether non-contiguous targets must be copied or rejected. |
| Reassociation behavior | Defines what happens when Fortran points the dummy somewhere else: ignore the original Python input, return the final association as a detached copy, write back association state, invalidate old views, or block. |
| Aliasing | States whether two returned pointers may share one target and whether Python must preserve that identity or may return independent copies. |
| Mutability | Declares whether Python may write through a borrowed view and whether native code may write while Python holds it. |

These facts are policy, not parser facts. The parser and semantic IR should
preserve the native pointer, target, rank, bounds, intent, and contiguity
information they can observe, but wrapper planning should keep reporting a
blocker when the user-supplied policy is not strong enough for the requested
Python behavior.

Semantic `.pyi` expresses these facts in one keyword-only annotation:

```python
from x2py.contracts import Annotated, Float64, Pointer, PointerPolicy

value: Annotated[
    Pointer[Float64[:]],
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

<!-- X2PY_C_DOCS_START
Assumed-rank numeric array arguments use a fixed generated bridge policy. The
Python layer accepts NumPy array ranks 1 through 15, records the runtime rank
and descriptor metadata, and rejects rank 0 scalars or higher-rank arrays before
entering the bridge. The Fortran bridge then dispatches on each assumed-rank
argument's runtime rank, creates a rank-specific Fortran pointer view with
`c_f_pointer`, and calls the native procedure with fixed-rank actual arguments.
X2PY_C_DOCS_END -->

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

- Pointer array function results remain blocked until returned-handle owner
  storage, target lifetime, descriptor extraction, and destroy behavior are
  implemented.
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
- Overlapping Python-visible arrays are not copied or de-aliased by x2py; the
  call is forwarded to Fortran, so the native routine's aliasing contract still
  governs behavior.

<!-- X2PY_C_DOCS_START
- Numeric array function results are copy-return values. Explicit-shape and
  automatic-shape results are copied out of the Fortran temporary into
  Python-owned C storage. Allocatable function results use the same copy-return
  policy and return `None` only when the Fortran result is unallocated.
  Zero-sized allocated results remain zero-sized NumPy arrays.
X2PY_C_DOCS_END -->

Assumed-type `type(*)`, character arrays, and derived-type arrays remain
blocked until explicit dtype, descriptor, ABI, layout, construction, and
ownership policies are supplied.
