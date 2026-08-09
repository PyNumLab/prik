---
title: Semantic .pyi Format
audience: users, advanced users, developers
prerequisites: semantic IR reference, wrapper build workflow
related: pyi_wrapper_checklist.md, reference/index.md
status: maintained
---

# Semantic `.pyi` Format

Semantic `.pyi` files are prik's editable wrapper contract. They are valid
Python stub files, but they are not meant to be clean static-type-checker stubs.
They preserve native type, storage, ownership, shape and visibility facts that a
wrapper generator needs. The implemented Fortran wrapper uses the same semantic
contract internally; the wrapper backend for user-supplied C inputs remains
future work.

The default wrapper workflow accepts Fortran source files. A `.pyi`-driven
wrapper workflow is also available for the implemented
subset: pass the semantic `.pyi` file as the wrapper input and provide native
object, archive, shared-library, module, include, and link inputs with the
native artifact flags. This path treats the `.pyi` as the source of truth for
the Python API and does not reparse native source to reconstruct the contract.

The full parity plan is tracked in
[Semantic `.pyi` wrapper checklist](pyi_wrapper_checklist.md).

Status terms used below:

- **Generated**: emitted today by `--pyi` or `codegen.printers.pyi_printer`.
- **Loaded**: accepted today by `prik.pyi_parser` and converted back to
  semantic IR.
- **Planning**: can be lowered once semantic policy is complete.
- **Build input**: accepted by the `.pyi` wrapper build for the implemented
  subset when the required native artifacts are supplied.
- **Roadmap**: design direction, not implemented wrapper behavior.

The scalar dtype mapping behind these names is documented in
[semantics.md](semantics.md). Wrapper-policy gaps are tracked in
[wrapper_design_notes.md](wrapper_design_notes.md).

## File Shape

Loaded files support imports, classes, enums, variables and stub functions:

```python
from types_mod import particle

answer: Final[Int32]

class particle:
    id: Int32
    mass: Float64

def scale(
    n: Addr(Int32),
    values: Float64[n],
) -> None: ...
```

Function and method bodies must be `...`. Positional-only, keyword-only,
`*args`, `**kwargs`, untyped parameters and ordinary Python statements are not
part of the semantic format. The generated keyword-only derived-type
constructor described below is the only keyword-only exception.

`pyi_paths_to_semantic_modules(...)` can load one file, several files, or a directory tree.
Directory loading derives dotted module names from relative `.pyi` paths and
reconciles imported external type references across the loaded set.

## Contract Bundles And Native Procedure Placement

> **Roadmap:** `@standalone`, generated contract bundles, `__init__.pyi` export
> lowering, `--root-contract`, and wrapper `--out` are the required contract
> described here, but are not implemented by the current `.pyi` build subset.

Wrapper generation must distinguish immutable native structure from editable
Python export policy. Module `.pyi` files describe where native declarations
actually live. A root export contract describes where those declarations appear
in Python. Export policy must never rewrite native module membership or ABI
facts.

### Contained Module Procedures

One Fortran module maps to one `.pyi` file named for that module. A procedure
declared without `@standalone` in that module contract is contained in the native
Fortran module:

```python
# module1.pyi
def update(value: Float64[()]) -> None: ...
```

The generated Fortran bridge imports the procedure from its retained native
scope, conceptually:

```fortran
use module1, only: update
```

The contract must retain the native module name even when Python export policy
later aliases or hides `update`. A modified module `.pyi` cannot move the
procedure to another module or reinterpret it as standalone.

### Standalone External Procedures

A procedure outside every Fortran module is marked explicitly with
`@standalone`:

```python
# externals/dgesv.pyi
@standalone
def dgesv(a: Float64[:, :], b: Float64[:, :]) -> Int32: ...
```

`@standalone` is immutable native-placement metadata. The bridge must generate a
matching explicit Fortran interface and call the external procedure without a
`use <module>` statement. The procedure therefore needs no Fortran `.mod` file,
but its defining object, archive, or shared library must be supplied to the
link.

Python-visible renaming is separate from placement. `@bind` retains the native
Fortran procedure name while the declaration uses a wrapper name:

```python
@standalone
@bind("dgesv")
def solve(a: Float64[:, :], b: Float64[:, :]) -> Int32: ...
```

Here the bridge calls the external native procedure `dgesv`; the root export
contract may expose the wrapper declaration as `solve`. `@bind` does not turn a
module procedure into an external procedure and `@standalone` does not rename a
symbol.

Every generated standalone declaration must carry `@standalone`. Handwritten
contracts must do the same. Missing or contradictory placement metadata must
fail during `.pyi` validation or wrapper planning, before bridge emission or native
compilation.

### Source-To-Contract Layout

The required generated layout depends on semantic contents, not only the source
suffix:

| Native input shape | Generated contract shape |
| --- | --- |
| One source containing one module | One `<module>.pyi` |
| One source containing several modules | One contract directory with `__init__.pyi` and one `.pyi` per module |
| Several sources containing modules | One contract directory with `__init__.pyi` and one `.pyi` per module |
| One fixed- or free-form source containing only standalone procedures | One root fragment with `@standalone` on every procedure |
| Several standalone-procedure sources, such as BLAS/LAPACK | One contract directory with `__init__.pyi` and organized external fragments |
| Mixed modules and standalone procedures | One contract directory containing module contracts, external fragments, and `__init__.pyi` |

A physical source file containing two modules generates two module `.pyi` files.
Conversely, a source file containing several standalone procedures may generate
one external fragment containing several `@standalone` declarations because those
procedures all contribute to the extension root rather than a native module
namespace.

For a LAPACK-style bundle, the generated layout may be:

```text
contracts/lapack/
├── __init__.pyi
└── externals/
    ├── dgesv.pyi
    ├── dgetrf.pyi
    └── dgetrs.pyi
```

The `externals/` directory organizes contract fragments; it is not automatically
a public runtime namespace.

### Native Artifacts And Link Resolution

Semantic contracts do not map to native artifacts by filename. prik must never
assume that `name.pyi` is implemented by `name.o`:

- one `.pyi` may require several objects and libraries;
- several `.pyi` files may be implemented by one object or archive;
- one shared library may implement an entire BLAS/LAPACK contract bundle; and
- module files, objects, archives, shared libraries, and transitive libraries
  may come from different directories or build systems.

Native inputs form one extension-level link plan. The generated bridge creates
native symbol uses from the immutable `.pyi` binding metadata, and the linker
resolves those symbols from caller-supplied artifacts. The `.pyi` filename is
never used to guess an object, archive, or shared-library name.

The current `.pyi` build subset accepts direct artifact paths through
`--native-objects`:

```bash
--native-objects build/module1.o build/module2.o \
  /opt/vendor/lib/libsupport.a \
  /opt/vendor/lib/libsolver.so
```

Named libraries use linker-style names and directories:

```bash
--native-library lapack \
--native-library blas \
--native-library-dir /opt/vendor/lib
```

This requests `-llapack -lblas`, adds the directory to the link search path, and
adds the supported runtime search path for the produced extension. A direct
shared-library path and a named `-l` library are alternate ways to identify a
shared dependency; neither is inferred from `.pyi`.

Fortran module procedures additionally need their compiler-produced `.mod`
files while the generated bridge is compiled:

```bash
--native-include-dir build/mod
```

Archives do not normally contain `.mod` files, so module directories remain
separate inputs. Standalone `@standalone` procedures require no `.mod` file
because the bridge emits their implicit external declaration or required
explicit interface from the semantic contract.

Required link cases are:

| Case | Native inputs |
| --- | --- |
| One contract, one object | one `.o` plus module directory when applicable |
| One contract, several dependencies | repeated objects/archives/shared libraries and named libraries |
| Several contracts, separate objects | all required `.o` files in dependency-safe link order |
| Several contracts, one archive | one `.a`; no contract-to-member mapping is inferred |
| Vendor shared implementation | direct `.so` path or `--native-library NAME` plus search directory |
| Mixed implementation | objects, archives, direct shared libraries, and named libraries in one ordered plan |
| Module procedures | native artifacts plus every required `.mod` search directory |
| Standalone procedures | native artifacts only; interfaces come from `@standalone` declarations |

Static link order is semantically significant: dependent objects precede the
archives or libraries that satisfy them, and dependent libraries precede their
providers. Cyclic static archives may require linker grouping or repeated
archives. The completed build interface must preserve caller order across all
native item kinds and provide an explicit ordered linker-argument mechanism for
groups, whole-archive policy, and platform-specific flags. The current first
slice runtime-verifies a single object only; it does not yet establish every
mixed or cyclic ordering case.

Directly linked objects and static archives must be position-independent when
the platform requires PIC. All artifacts must match the active compiler ABI,
architecture, Fortran kind/layout assumptions, and name-mangling convention.
Missing symbols, duplicate strong definitions, incompatible files, unavailable
dependent shared libraries, and missing `.mod` files must produce actionable
build or import diagnostics rather than triggering a source fallback.

### Root Export Contract

For multi-file contract sets, generated `__init__.pyi` is the default root
export contract. Native module boundaries remain preserved by default:

```python
from . import module1 as module1
from . import module2 as module2
```

With extension name `library`, this exposes
`library.module1.update` and `library.module2.update`. Identically named members
in different native modules do not collide.

Standalone procedures are explicitly re-exported at the extension root:

```python
from .externals.dgesv import dgesv as dgesv
from .externals.dgetrf import dgetrf as dgetrf
```

This exposes `library.dgesv` and `library.dgetrf`. Duplicate root names are an
error unless the root contract resolves them through an explicit alias or hides
one declaration.

Users may replace the generated export policy without changing leaf native
contracts. Selective aliasing is unambiguous:

```python
from .module1 import update as update_first
from .module2 import update as update_second
```

Explicit wildcard imports request flattening:

```python
from .module1 import *
from .module2 import *
```

Wildcard import order must not silently resolve collisions. If both modules
export `update`, semantic validation requires explicit aliases or exclusions.

### Root Selection And Extension Identity

Root export resolution follows this order:

1. an explicit `--root-contract PATH`;
2. otherwise `__init__.pyi` in the contract directory;
3. otherwise one supplied `.pyi` may act as an implicit root; and
4. several `.pyi` inputs without either root form fail as ambiguous.

When one module `.pyi` acts as the implicit root, the extension root represents
that sole native module. A multi-module bundle needs a separate root contract so
each native module can remain a distinct child namespace.

An arbitrary root file is allowed and uses normal stub import syntax without a
`.pyi` suffix:

```python
# api.pyi
from module1 import *
from module2 import *
```

The root filename does not choose the compiled extension name. Multi-module and
standalone-only contract sets can use wrapper `--out`, which controls the
extension filename, `PyInit_<name>` symbol, and Python import name. Source,
generated-contract, and modified-contract parity builds use the same explicit
extension name.

Target CLI shapes are:

```bash
python3 -m prik contracts/library \
  --out library \
  --native-objects native.a
```

```bash
python3 -m prik module1.pyi module2.pyi \
  --root-contract api.pyi \
  --out library \
  --native-library native \
  --native-library-dir /path/to/libs
```

For a single standalone fragment, no `__init__.pyi` is required:

```bash
python3 -m prik dgesv.pyi \
  --out lapack_dgesv \
  --native-objects dgesv.o
```

These future commands still treat native artifacts as link inputs only. They do
not permit fallback parsing of unavailable Fortran source.

## Semantic Type Names

The public annotations use semantic names, not raw C or Fortran spellings:

| Family | Names |
| --- | --- |
| Booleans and generic values | `Bool`, `Any` |
| Signed integers | `Int`, `Int8`, `Int16`, `Int32`, `Int64` |
| Unsigned integers | `UInt8`, `UInt16`, `UInt32`, `UInt64`, `SizeT` |
| Reals | `Float32`, `Float64`, `Float128` |
| Complex | `Complex64`, `Complex128`, `Complex256` |
| Text | `String` |
| User types | class names and imported type names |
| Callback prototypes | named `@prototype` declarations referenced by name |

`Unknown` is intentionally rejected in `.pyi` annotations. Generated stubs must
resolve or block unsupported source types instead of emitting unknown contracts.
Current C callback placeholders such as `CFunctionPointer` can appear in
generated stubs when source callback policy is incomplete; replace them with a
complete named prototype before building a wrapper.

## Storage Contracts

Bare types are direct values:

```python
def dot(a: Float64, b: Float64) -> Float64: ...
```

`T[()]` represents caller-provided rank-zero NumPy scalar storage:

```python
def update(value: Float64[()]) -> None: ...
def inspect(value: Int32[()]) -> None: ...
```

`Addr(T)` represents a raw address supplied by the caller:

```python
def update_raw(value: Addr(Float64)) -> None: ...
def inspect_raw(value: Addr(Int32)) -> None: ...
```

`T` marks the wrapped value or storage read-only. For `Addr(T)`
this means a read-only pointee. For `T[()]` it means readable rank-zero
storage. For an array it means read-only array storage.

Pointer depth is explicit for low-level pointer graphs:

```python
handle: Addr[2](OpaqueHandle)
argv: Addr[3](Int8)
```

`Addr[1](T)` is invalid; use `Addr(T)`.

Array storage uses NumPy-style subscriptions:

```python
vector: Float64[:]
fixed: Float64[3]
matrix: Float64[n, m]
strided: Float64[::]
rank_polymorphic: Float64[...]
```

Dimension entries have the following meaning:

| Form | Meaning |
| --- | --- |
| `:` | unconstrained extent for that axis |
| `n`, `3`, `n + 1` | required extent expression |
| `lower:upper` | range-like storage expression |
| `::` | axis accepts runtime stride |
| `0:n:` | range plus stride-aware axis |
| `...` | rank-polymorphic storage |

Qualified names such as `foo.bar` are not accepted as dimension expressions.
Use local constants or generated `Final[...]` names for shape symbols.

## Metadata With `Annotated`

`Annotated[...]` carries storage metadata and semantic constraints:

```python
def fill(
    a: Annotated[Float64[:, :], ORDER_F],
    out: Float64[()],
) -> None: ...
```

Generated canonical metadata:

| Metadata | Meaning |
| --- | --- |
| `ORDER_F` | multidimensional Fortran-oriented storage |
| `ORDER_ANY` | edited contract accepts either C or Fortran orientation |
| `Allocatable` | Fortran allocatable array storage |
| `Pointer` | Fortran pointer array storage |
| `PointerAssociation("runtime")` | pointer association is a runtime state rather than a declaration-time constant |
| `SourceName("native-name")` | source name cannot be represented directly as the Python target name |
| `FortranCharacterLength("n")` | Fortran character storage length for `String` contracts |
| `FortranAllocatable` | Fortran scalar character storage is allocatable |
| `Aliased` | native storage may be exposed across the Python boundary as an alias |
| `Ownership("python" | "native" | "wrapper" | "caller" | "temporary" | "unknown")` | explicit owner override for the wrapper ownership policy |
| `Transfer("copy_return" | "snapshot_copy" | "borrowed_view" | "call_local" | "in_place" | "by_value" | "wrapper_instance" | "blocked")` | explicit boundary transfer override for the wrapper ownership policy |
| `Destruction("python_refcount" | "wrapper_dealloc" | "native_owner" | "caller" | "call_local" | "none" | "blocked")` | explicit destruction override for the wrapper ownership policy |
| `PointerPolicy(...)` | complete pointer policy: `nullable`, `transfer`, `target_owner`, `lifetime`, `deallocation`, `shape_source`, `contiguity`, `reassociation`, `aliasing`, and `mutability` |

Loaded compatibility metadata:

| Metadata | Meaning |
| --- | --- |
| `ORDER_C` | explicit C-oriented storage in a Fortran contract |
| `Contiguous` | source provenance says the array is contiguous |
| `ArrayCategory("...")` | source array category provenance |
| `SourceDims(...)` | source declaration dimensions |
| `LowerBounds(...)`, `UpperBounds(...)` | source bound provenance |

Other positional `Annotated` helpers are preserved as semantic constraints:

```python
value: Annotated[Int32, Bounded(1, 8), Finite]
```

Ownership metadata is consumed by the centralized wrapper ownership policy. Use
it only when the native source facts are more precise than the generated default.
`PointerPolicy` is keyword-only and requires all ten keys. Its string values are
preserved verbatim so project-specific owner and release names can be expressed;
the backend still validates whether the requested transfer is implemented.

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
For example, a pointer array can be made a Python-owned snapshot only when the
stub also supplies enough shape, nullability, lifetime, and release facts for
the backend path being enabled.

`Final[T]` is the only public constant spelling. Do not use
`Annotated[T, Constant]` or `T[Constant]`.

## Constants And Enums

Constants use `Final[T]`. Literal values are optional unless the value is needed
as a compile-time expression or enumerator initializer:

```python
nmax: Final[Int32]
answer: Final[Int32] = 42
```

C and Fortran enumerators are plain integer constants. Do not declare or expect
Python `Enum`/`IntEnum` classes or semantic enum datatypes:

```python
STATUS_OK: Final[Int] = 0
STATUS_RETRY: Final[Int] = STATUS_OK + 1
```

The listed names are documentation and convenience constants. Procedure
arguments and returns that use native enum types are emitted as the underlying
integer type.

## Classes And Native Type Markers

Fortran derived types and ordinary semantic classes use normal class syntax:

```python
class particle:
    id: Int32
    position: Float64[3]
```

C aggregate identity is explicit through base markers:

```python
class packet(CStruct):
    tag: UInt32

class scalar(CUnion):
    i: Int32
    x: Float64

class context(CStruct, Opaque):
    pass
```

| Marker | Meaning |
| --- | --- |
| `CStruct` | native C `struct` |
| `CUnion` | native C `union` |
| `CAnonymous` | generated nested anonymous C aggregate type |
| `Opaque` | type identity is known, but fields/layout are intentionally hidden |

Anonymous C aggregate members are represented as nested classes plus a generated
field that marks the anonymous member:

```python
class flags(CStruct):
    class anonymous_union_0_type(CUnion, CAnonymous):
        integer: Int
        real: Float32

    _anonymous_union_0: Annotated[anonymous_union_0_type, CAnonymousMember]
    tag: Int
```

The generated field preserves that the anonymous union is a real C member even
though C exposes its fields through the containing aggregate.

External opaque types can live in separate owner stubs:

```python
# types_mod.pyi
class particle(Opaque):
    pass

# physics.pyi
from types_mod import particle

def move(p: Addr(particle)) -> None: ...
```

If the owner stub is later edited to include fields, the import is reconciled as
a wrapped external type without changing the importing file.

## Functions, Methods And Returns

Generated C and Fortran stubs describe native interfaces without guessing
ownership. Scalar values may be Python-visible values with an `@native_call`
address projection, caller-provided rank-zero storage, or explicit raw address
contracts.

Fortran scalar dummy arguments are generated as:

| Source dummy shape | Generated semantic form |
| --- | --- |
| no `value`, read-only reference | visible `T` plus `Addr(Arg(i))` in `@native_call` |
| no `value`, output reference | `T[()]` for caller storage, or projected `Returns[...]` |
| no `value`, writable reference | `T[()]` for caller storage, or visible `T` plus projected replacement `Returns[...]` |
| `value` | direct `T` |
| function result | direct return annotation |

Loaded return forms:

```python
def f() -> None: ...
def g(x: Float64) -> Float64: ...
def split(x: Float64) -> tuple[Float64, Int32]: ...
def projected(x: Float64) -> Returns["x", Float64]: ...
def maybe_projected(x: Float64) -> Returns["x", Float64] | None: ...
```

`Returns["name", T]` records an output value associated with an argument name.
Use `Returns["name", T] | None` when that named output can be absent. Plain
tuple return components after the first are converted to generated output arguments.
When the name matches an existing Python-visible argument, the argument remains
an input and the return item represents replacement-style writable-reference
behavior for immutable public values such as Python `str`.

Class methods use the same stub form. An untyped leading `self` is allowed in a
method and is not treated as a native argument.

## Generic Procedure Overloads

The prik semantic `.pyi` format uses `@overload("specific_name")` to link one
Python-visible declaration to an ordinary concrete procedure declaration. This
decorator is prik metadata; it is not `typing.overload` and must not be imported
from `typing`.

```python
@private
def convert_integer(value: Addr(Int32)) -> Int32: ...

@private
def convert_real(value: Addr(Float64)) -> Float64: ...

@overload("convert_integer")
def convert(value: Addr(Int32)) -> Int32: ...

@overload("convert_real")
def convert(value: Addr(Float64)) -> Float64: ...

class accumulator:
    @overload("accumulator_add_integer")
    def add(self, value: Addr(Int32)) -> None: ...

    @overload("accumulator_add_real")
    def add(self, value: Addr(Float64)) -> None: ...
```

Concrete specifics that remain in a stub are ordinary functions with their
native names. Ordinary source-private Fortran declarations are not emitted as
standalone generated `.pyi` items. A private overload specific may remain only
when it is needed to resolve a public overload declaration from the standalone
`.pyi`. `@private` is reserved for a user-imposed contract on a declaration
that is otherwise part of the wrapper input.
`@native_call` is not emitted merely to restate an unchanged native function
name.

The loader resolves only the decorator string. It never guesses a target by
signature. The target must exist exactly once, each target may occur only once
in one overload set, and the public declaration must agree with the concrete
call signature and return type. Missing, duplicate, ambiguous, and incompatible
links are deterministic errors.

Python method names recover the native generic for ordinary operators. When
two distinct Fortran generics share one Python method, the decorator carries
the otherwise unrecoverable spelling:

```python
@overload("equivalent_values", generic="operator(.eqv.)")
def __eq__(self, other: value) -> Bool: ...
```

The optional `generic=` argument is restricted to a compatible operator or
assignment generic. It is currently emitted for `.eqv.` and `.neqv.`, which
would otherwise be indistinguishable from `operator(==)` and `operator(/=)`.

The generated C extension exposes one callable for each generic name. It
dispatches before conversion using the wrapped scalar dtype, array element
dtype and rank, or wrapped derived-type class. It does not use implicit numeric
coercion to choose an overload. Array shape, bounds, and layout are validated
by the selected concrete wrapper, but they do not distinguish overloads;
overloads that differ only in those properties are rejected during generation.

All specifics must have one compatible Python call shape. Parameter names and
keyword parsing use the first specific procedure's signature. A call that
matches no specific raises `TypeError`; duplicate dtype/rank signatures are a
deterministic generation error.

Wrapped derived types dispatch by their generated extension class. Fortran
`extends` relationships are preserved semantically but do not currently create
Python C-type inheritance, so a base-type overload is not a fallback for a
derived wrapper. Each accepted wrapped derived type needs an explicit specific
procedure. User-defined Python subclasses are not part of this runtime
contract.

## Defined Operators And Assignment

Defined operators use the same explicit link. The concrete function keeps its
full Fortran operand list, while the class declaration describes the Python
method call:

```python
@private
def add_vector_real(left: Addr(vector), right: Addr(Float64)) -> vector: ...

@private
def add_real_vector(left: Addr(Float64), right: Addr(vector)) -> vector: ...

class vector:
    @overload("add_vector_real")
    def __add__(self, right: Addr(Float64)) -> vector: ...

    @overload("add_real_vector")
    def __radd__(self, left: Addr(Float64)) -> vector: ...
```

Operand positions are fixed:

| Python method | Native operands |
| --- | --- |
| non-reflected binary method | `self` is operand 1; `other` is operand 2 |
| reflected binary method | `other` is operand 1; `self` is operand 2 |
| unary method | `self` is the only operand |
| comparison method | `self` is the Python left operand; reflected comparison metadata restores native order |

Return annotations must equal the concrete procedure result. The generated C
extension dispatches the Python slot before conversion by dtype, rank, and
wrapped extension class. Operator slots also accept a native Python scalar when
there is exactly one candidate precision in that integer, real, or complex
family; this is needed when CPython or NumPy invokes a reflected slot with a
built-in scalar. No match raises `TypeError`, and indistinguishable candidates
fail during generation. Three-argument `pow(value, exponent, modulus)` is not a
Fortran operator form and raises `TypeError`.

Mappings:

| Fortran generic | Python methods |
| --- | --- |
| binary `operator(+)` | `__add__`, `__radd__` |
| unary `operator(+)` | `__pos__` |
| binary `operator(-)` | `__sub__`, `__rsub__` |
| unary `operator(-)` | `__neg__` |
| `operator(*)`, `operator(/)`, `operator(**)` | `__mul__`/`__rmul__`, `__truediv__`/`__rtruediv__`, `__pow__`/`__rpow__` |
| `operator(==)`, `operator(/=)` | `__eq__`, `__ne__` |
| `operator(<)`, `operator(<=)`, `operator(>)`, `operator(>=)` | `__lt__`, `__le__`, `__gt__`, `__ge__` with reflected comparison routing |
| `operator(.and.)`, `operator(.or.)`, `operator(.not.)` | `__and__`/`__rand__`, `__or__`/`__ror__`, `__invert__` |
| `operator(.eqv.)`, `operator(.neqv.)` | `__eq__`, `__ne__` |

prik does not infer in-place methods such as `__iadd__`. Python's fallback
therefore applies: an expression such as `value += other` may replace the
Python reference with the ordinary operator result rather than invoking
Fortran defined assignment.

A named operator `.custom.` is exposed as `operator_custom(self, other)`. If
the wrapped class is native operand 2, the method is
`r_operator_custom(self, other)`. These are normal methods because Python has
no syntax or data-model slot for arbitrary Fortran operator names.

Python assignment cannot be intercepted. Fortran `assignment(=)` is exposed as
explicit mutation:

```python
@private
def assign_vector_real(
    left: Addr(vector),
    right: Addr(Float64),
) -> None: ...

class vector:
    @overload("assign_vector_real")
    def assign(self, right: Addr(Float64)) -> None: ...
```

`lhs.assign(rhs)` invokes native `lhs = rhs`, mutates the existing wrapped
object, preserves Python object identity, and returns `None`. It never replaces
the Python variable. Assigning an object to itself is a no-op. A supported
specific must be a two-argument subroutine whose wrapped derived-type LHS is
writable and whose RHS is read-only. Unsafe or unsupported forms are wrapper-planning
blockers.

## Allocatable Borrowed Views

Supported Fortran allocatable module arrays and derived-type array fields are
exposed as zero-copy NumPy views over native storage. The NumPy array does not
own the memory. For derived-type fields, NumPy's `base` object is the containing
Python wrapper, so the wrapper cannot be destroyed while the view exists.
For module variables, the Fortran module owns the storage for the process
lifetime.

Unallocated allocatable arrays return `None`. A fresh getter call after native
deallocation also returns `None`. Existing views are not invalidated, detached,
or tracked. If a wrapped Fortran procedure reallocates or deallocates the native
storage while Python still holds an old view, that old view is stale; reading or
writing it is unsupported and may crash the process. Users who need independent
lifetime must copy explicitly:

```python
x = obj.values        # borrowed zero-copy NumPy view, or None
y = obj.values.copy() # independent NumPy-owned storage
obj.reset_values()    # may invalidate x; y remains valid
```

Derived-type allocatable fields remain fields in `.pyi`:

```python
class buffer:
    values: Annotated[Float64[:], Allocatable]
```

Python cannot directly replace or reallocate such fields. Assigning a new array
to the field raises `AttributeError`; explicit wrapped Fortran procedures must
perform allocation, reallocation, and deallocation.

Fortran classes with public rank-0 numeric, logical, or complex components
emit a generated keyword-only constructor in generated stubs. Every constructor
keyword is optional: omitted components keep the native allocation state,
including any Fortran default component initializer.

```python
class state:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
```

An edited stub controls whether that generated constructor remains part of the
Python surface. If the generated `__init__(self, *, ...)` declaration is
removed, wrapper generation must not recreate the keyword constructor. A class
left without any `__init__` keeps only native allocation and has no Python
initializer arguments.

An edited stub may instead replace the generated field-keyword constructor by
binding `__init__` to one concrete class method with
`@bind("specific_name")`. The target string must name another method declared in
the same class, with the same Python-call signature and return type. The target
method may be public, exposing both `state.init_state(...)` and `state(...)`, or
marked `@private`, exposing only construction. A private target is still emitted
in the `.pyi` because the `.pyi` must be sufficient to generate a wrapper
without the original Fortran source. The target method represents the native
initializer that keeps the native class argument; the Python `__init__`
declaration omits that argument because Python supplies the newly allocated
instance.

```python
class state:
    @private
    def init_state(
        self,
        seed: Addr(Int32),
        scale: Addr(Float64) = ...
    ) -> None: ...

    @bind("init_state")
    def __init__(
        self,
        seed: Addr(Int32),
        scale: Addr(Float64) = ...
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
```

The generated keyword-only shape remains reserved: if undecorated `__init__`
keeps the `self, *, ...` form and every keyword has a default, the loader treats
it as the generated field constructor metadata. Constructor overload
declarations may still be used only when the generated field constructor is
present; overloaded `tp_init` runtime lowering is not implemented yet and code
generation reports an explicit blocker for that form.

Module allocatable arrays are emitted as explicit getter functions so
unallocated storage can be represented as `None`:

```python
@module_variable("module_values")
def get_module_values() -> Annotated[Float64[:], Allocatable, Aliased] | None: ...
```

`@module_variable("name")` is prik metadata linking the getter to the native
module variable. The getter must take no arguments and must return an
allocatable array type unioned with `None`. `Aliased` marks native storage
that may be exposed as a borrowed view. Plain module allocatable arrays are
returned as read-only Python-owned snapshots.

Public scalar Fortran module variables use explicit accessors. The getter reads
current native storage; the setter writes through to the Fortran module
variable. The variable itself is not added as a mutable Python module
attribute.

```python
def get_counter() -> Int32: ...

def set_counter(value: Int32) -> None: ...
```

Fortran `parameter` declarations are emitted as `Final[...]` constants when
their literal value can be represented in `.pyi`:

```python
nmax: Final[Int32] = 12
```

No setter is generated for parameters. Python module namespaces remain ordinary
Python module namespaces, so assigning to `mod.nmax` can rebind that Python name
without modifying native Fortran state.

Allocatable array function results and allocatable output array arguments
use a copy-return policy. The generated bridge copies allocated Fortran storage
into C memory that becomes owned by the returned NumPy array, then deallocates
the Fortran allocatable. If the Fortran value remains unallocated, Python
receives `None`.

Allocatable writable arguments remain blocked. They need a replacement policy
for the caller-visible object before prik can safely expose them.

## Pointer Procedure Snapshot Subset

Fortran pointer array facts are emitted and loaded with `Pointer` metadata:

```python
def sum_values(values: Annotated[Float64[:], Pointer]) -> Float64: ...
def choose_values(flag: Int32) -> Annotated[Float64[:], Pointer] | None: ...
```

The supported runtime subset is procedure-local and copy-based:

- A pointer array read-only dummy is associated with the Python-owned NumPy
  buffer only for the duration of the native call. The wrapper does not expose
  or preserve pointer association identity after the call.
- A pointer array function result is copied into a new Python-owned NumPy
  array. If the Fortran result is unassociated, Python receives `None`.
- Pointer array output and writable dummy arguments remain blocked unless future
  policy metadata supplies ownership, lifetime, shape, contiguity,
  reassociation, and deallocation behavior.

The returned NumPy array from a pointer function result is a snapshot. Mutating
it does not mutate the original Fortran target. Borrowed views for module
pointer variables and derived-type pointer fields are not part of this subset.

## Visibility And Names

`@private` marks classes, functions and methods private:

```python
@private
def helper(x: Int32) -> None: ...
```

`private[T]` marks a variable or argument private:

```python
hidden_value: private[Float64]
def consume(value: private[Int32]) -> None: ...
```

Generated `.pyi` files omit ordinary declarations that are private in the
original Fortran source. Privacy written in an edited `.pyi` is different: it
is a user contract applied to a declaration that was otherwise available to the
wrapper, so the declaration remains printed and loadable as wrapper input.

Names that are not valid Python identifiers are represented with `var[...]` for
data declarations, or with `Annotated[..., SourceName("native-name")]` for callable
arguments:

```python
var["class"]: Int32
def f(class_: Annotated[Int32, SourceName("class")]) -> None: ...
```

## Projection Metadata

`@native_call` is loaded and printed as projection metadata for edited stubs
whose Python-visible signature intentionally differs from the exact native
signature:

```python
@native_call([Arg(0), Arg(0).shape[0], Return("result", 0)])
def normalize(values: Float64[:]) -> Float64: ...
```

Loaded projection entries:

| Entry | Meaning |
| --- | --- |
| `Arg(i)` | native argument is Python argument `i` |
| `Return(i)` | native argument is supplied by projected return slot `i` |
| `Return("name", i)` | named native argument is supplied by projected return slot `i` |
| `value` | hidden native literal |
| `Len(Arg(i))`, `Len(Return(i))`, `Len(Work("name"))` | hidden native length metadata |
| `Arg(i).shape[d]`, `Return(i).shape[d]`, `Work("name").shape[d]` | hidden native shape metadata |
| `IsPresent(Arg(i))` | hidden native optional-presence metadata |
| `Work("name")` | hidden workspace value |

This syntax is metadata today. Runtime lowering, allocation, copy-back,
validation, coercions and ownership behavior are roadmap work unless a backend
explicitly implements them.

## Current Generated Coverage

Generated `.pyi` currently covers these exact-contract areas:

| Area | Generated behavior |
| --- | --- |
| Fortran intrinsic scalars | compiler-aware semantic dtype names |
| C primitive scalars | compiler-probed semantic dtype names when a target report is supplied |
| Functions/subroutines | exact native argument order and direct return type |
| Fortran scalar storage | `T`, `T[()]`, `Addr(Arg(...))`, `Returns[...]` |
| Arrays | shaped storage with extents and strided axes; multidimensional order defaults from the selected native language |
| Allocatable borrowed views | derived-type fields and target-backed module arrays, with `None` for unallocated storage |
| Constants | `Final[T]` module variables |
| C and Fortran enums | module-level `Final[...]` integer constants |
| Fortran derived types | classes with fields and methods when resolvable |
| Fortran generic interfaces | explicit `@overload("specific")` links with C-extension dtype/rank dispatch |
| Fortran defined operators | Python data-model methods plus explicit named-operator methods |
| Fortran defined assignment | explicit mutating `assign(...)` overloads |
| C structs/unions | `CStruct` and `CUnion` classes |
| C anonymous aggregate members | nested `CAnonymous` classes plus `CAnonymousMember` fields |
| Opaque types | `Opaque` classes and owner-module dependency stubs |
| Imports | `import ...` and `from ... import ...` with aliases |
| Incomplete C callbacks | placeholder type that wrapper planning reports as incomplete |

Loaded but usually not generated from source today:

| Area | Loaded behavior |
| --- | --- |
| named `@prototype` | complete callback/procedure signature metadata |
| `Addr[n](T)` for `n > 1` | direct low-level pointer topology |
| `ORDER_ANY` | edited orientation-independent array contract |
| generic `Annotated` constraints | preserved semantic constraints |
| `@native_call` and `Returns[...]` | projection metadata |
| source-provenance array helpers | compatibility loading for older or edited stubs |

## Rejected Or Not Yet Supported

The loader intentionally rejects syntax that would be ambiguous or stale:

- `Unknown` semantic types.
- `Constant` or `Shape` as `Annotated` metadata.
- non-dimensional subscriptions such as `Float64[ORDER_F]`.
- `Addr[1](T)`.
- untyped callable parameters.
- positional-only, keyword-only, vararg or kwarg function parameters, except
  for the generated derived-type constructor shape.
- nested enum declarations.
- ordinary function bodies instead of `...`.
- unsupported decorators other than `@private`, `@native_call`,
  `@module_variable("native_name")`,
  `@overload("specific")`, its documented `generic=` form, and
  `@staticmethod`.
- bare `@overload` or `typing.overload`; overload links require one concrete
  procedure name.

## Roadmap

Near-term format work:

1. Make C and Fortran callbacks/procedure pointers first-class by preserving
   complete named prototypes from source.
2. Add explicit pointer ownership, borrow, nullability, output-buffer and
   copy/readback policy so pointer-heavy C APIs can move beyond blockers.
3. Strengthen Fortran `character(len=...)` with length, kind, hidden-length ABI
   and `bind(c)` byte-string metadata.
4. Expand aggregate layout metadata for C bitfields, C attributes, Fortran
   `bind(c)`, `sequence`, and by-value aggregate ABI checks.
5. Represent Fortran polymorphic `class(...)` and procedure bindings without
   losing dynamic-type or dispatch information.

Projection/runtime roadmap:

1. Lower `@native_call` mappings into executable wrapper calls.
2. Add validation and coercion contracts for dtype, rank, shape, order,
   strides, alignment, mutability and aliasing.
3. Add ownership and lifetime contracts for opaque handles, pointer returns,
   allocatable/pointer reassociation, callbacks and work buffers.
4. Decide how to emit clean IDE/type-checker stubs from semantic `.pyi` files
   without losing the native wrapper contract.
