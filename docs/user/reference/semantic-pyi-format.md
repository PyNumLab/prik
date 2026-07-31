---
title: Semantic .pyi Format
audience: users, advanced users, developers
prerequisites: semantic IR reference, wrapper build workflow
related: index.md, semantic-ir.md
status: maintained
publication: draft
---

# Semantic `.pyi` Format

For the supported edit workflow and runtime consequences of changing a
contract, including ownership and destruction examples, see
[Editing `.pyi` contracts](pyi-contracts/index.md).

<!-- X2PY_C_DOCS_START
Semantic `.pyi` files are x2py's editable wrapper contract. They are valid
Python stub files, but they are not meant to be clean static-type-checker stubs.
They preserve native type, storage, ownership, shape and visibility facts that a
wrapper generator needs. The implemented Fortran wrapper uses the same semantic
contract internally; the wrapper backend for user-supplied C inputs remains
future work.
X2PY_C_DOCS_END -->

The normal wrapper workflow accepts recognizable Fortran source without a
stage flag. A `.pyi`-driven wrapper workflow is also available for the
implemented subset: pass the semantic `.pyi` file as the wrapper input and
provide native object, archive, shared-library, module, include, and link
inputs with the native artifact flags. The `.pyi` input selects the wrapper
stage automatically and remains the source of truth for the Python API; native
source is not reparsed to reconstruct the contract.

The implemented subset and remaining parity limits are stated in this
reference and summarized later in Language Support.

Status terms used below:

- **Generated**: emitted today by `--pyi` or
  `wrapper_codegen.printers.pyi_printer`.
- **Loaded**: accepted today by `x2py.parsers.pyi` and converted back to
  semantic IR.
- **Planning**: can be lowered by the implemented wrapper planner once its
  semantic policy is complete.
- **Build input**: accepted by the `.pyi` wrapper build for the implemented
  subset when the required native artifacts are supplied.
- **Roadmap**: design direction, not implemented wrapper behavior.

Parser-related pull requests that change `x2py/parsers/pyi/` or its focused
loading tests must update this reference. The parser-reference guard checks
that contract independently from the language parser references.

## Contract Imports

Every semantic `.pyi` control name is imported from `x2py.contracts`. This
single namespace also re-exports the typing forms used by the contract:

```python
from x2py.contracts import Addr, Arg, Final, Flat, Float64, Int32, native_call

max_colors: Final[Int32] = 256

@native_call([Addr(Arg(0))])
def inspect(values: Float64[Flat]) -> None: ...
```

The loader follows each import binding, including arbitrary `as` aliases,
instead of matching the final spelling. For example, importing
`Flat as LayoutFlat` makes `LayoutFlat` the contract marker. An unimported
`Flat`, `Arg`, or `Float64` is therefore a user symbol. When a user declaration
has the same name, generated contracts alias only the imported control name:

```python
from x2py.contracts import Final, Flat as LayoutFlat, Float64, Int32

Flat: Final[Int32] = 10
values: Float64[LayoutFlat]
```

The alias spelling in generated files is an implementation detail; edited
contracts may use any non-conflicting local alias imported from
`x2py.contracts`.

Bare-name compatibility is not part of the format. Contract files must import
every x2py or re-exported typing form they use.

The user-facing Fortran, semantic `.pyi`, Python, and NumPy mapping is documented
in [Data Types](../guide/data-types.md). The underlying semantic model is
documented in [Semantic IR reference](semantic-ir.md).

## Misuse, Diagnostics And Risk

Semantic `.pyi` files are ordinary Python syntax, so a user can write many
things that are syntactically valid but not meaningful to x2py. The wrapper
build accepts only the documented semantic subset. Unsupported syntax, unknown
metadata, missing native facts, contradictory projection metadata, and unsupported
runtime policy must never be ignored and must never trigger a hidden fallback to
native-source parsing.

Failures should happen at the earliest layer that has enough information:

- **Stub-shape errors** fail while loading the `.pyi`: unsupported decorators,
  ordinary function bodies, untyped parameters, invalid `Annotated` metadata,
  unknown semantic types, missing relative imports, import cycles, or conflicting
  exports.
- **Structural contract errors** fail during semantic validation:
  incomplete `@native_call` mappings, duplicate native argument positions,
  missing or incompatible `@bind` / `@overload` targets, public declarations that
  expose private types, or native-placement facts that contradict the contract
  file shape.
- **Unsupported policy** fails during wrapper planning or lowering: ownership,
  lifetime, replacement, pointer reassociation, callback lifetime, coercion, or
  allocation behavior that x2py cannot yet express safely.
- **Native artifact mismatches** fail during compile, link, import, or runtime
  execution. x2py can validate the `.pyi` contract structure; it cannot prove
  that an arbitrary caller-supplied object, archive, or shared library implements
  the declared ABI.

Actionable diagnostics should name the contract path when available, the
declaration or import being processed, the invalid fact, and the expected
documented form. When x2py can continue only by guessing, it should report an
error instead of guessing.

When a `.pyi` file is converted from disk, syntax diagnostics use Python's
filename field and semantic pipeline diagnostics prefix the message with the
contract path. Inline helper calls such as `pyi_text_to_semantic_module(...)`
do not invent a path; pass a `filename=` when inline syntax diagnostics need
source provenance.

Some edited contracts intentionally request a lower-level native identity call.
Those are not misuse if they are structurally complete, but the Python behavior
is exactly the behavior declared in the `.pyi`. For example, an identity
fixed-length `String[n]` writable argument can return `None`; if the caller
passed an ordinary Python `str`, native mutation happened in temporary native
storage and is not observable in Python. To request Python-visible replacement
behavior, write a projected return contract such as
`Returns["name", String[n]]`.

Future unsafe, coercion, or copy/readback modes must be explicit `.pyi` metadata.
x2py must not infer them from malformed syntax or from a declaration that merely
looks risky.

`Immutable` marks a Python-visible value as replace-only: native code may write a
temporary representation, but the caller's Python object must not be mutated in
place. `Transfer("borrowed_view")` requests no-copy shared storage. Combining
`Immutable` with a writable borrowed view is contradictory and fails while
loading the `.pyi` contract:

```python
from x2py.contracts import Annotated, Float64, Immutable, Transfer

def normalize(
    values: Annotated[Float64[:], Immutable, Transfer("borrowed_view")]
) -> None: ...
```

The diagnostic tells the user to choose one contract: remove `Immutable` for an
in-place no-copy view, or keep `Immutable` and use a projected replacement return
such as `Returns["values", Float64[:]]`.

`Immutable` is a post-IR policy input, not a bridge heuristic. For writable
native storage, policy completion must choose either copy-in/copy-out replacement
or an explicit call-local copy whose native mutation is discarded. A replacement
requires a projected return such as `Returns["values", Float64[:]]`; the bridge
and binding then emit the already-selected action without reconsidering the
datatype, mutability, ownership, or storage mode. Unsupported combinations block
before wrapper planning and direct lowering.

`@native_call(...)` and `Returns[...]` describe projection and native placement;
they do not ask the backend to rediscover conversion policy. After `.pyi`
loading, policy completion records two barrier actions for each argument. The
Python barrier defines how the generated Python extension consumes the Python object
(`T`, `T[()]`, arrays, strings, raw addresses, or wrapper instances). The native
barrier defines how the bridge passes the extracted value onward (value,
call-local address, caller storage address, raw address, array descriptor, or
wrapper address). Code generation dispatches from those recorded actions and
fails closed for missing handlers.

## File Shape

Loaded files support imports, classes, enums, variables and stub functions:

```python
from x2py.contracts import Addr, Arg, Final, Float64, Int32, native_call

from types_mod import particle

answer: Final[Int32]

class particle:
    id: Int32
    mass: Float64

@native_call([Addr(Arg(0)), Arg(1)])
def scale(
    n: Int32,
    values: Float64[n],
) -> None: ...
```

Function and method bodies must be `...`. Positional-only, keyword-only,
`*args`, `**kwargs`, untyped parameters and ordinary Python statements are not
part of the semantic format. The generated keyword-only derived-type
constructor described below is the only keyword-only exception.

Wrapper commands accept exactly one entry `.pyi`. Relative imports from that
entry recursively discover the remaining contract files and reconcile imported
type references across the discovered project. Low-level semantic loading may
still operate on the resulting file set internally; users do not pass that set
as separate wrapper inputs.

## Imported Derived-Type Identity

Fortran `use` statements at module scope may still generate flattened `.pyi`
imports when that is unambiguous:

```fortran
module physics
  use types_mod, only: particle
contains
  subroutine move(p)
    type(particle), intent(inout) :: p
  end subroutine move
end module physics
```

```python
from types_mod import particle

def move(p: particle) -> None: ...
```

A procedure-local `use` that appears in the public API is represented by the
imported module namespace instead. The public datatype spelling is the origin
module plus the original exported type name:

```fortran
module physics
contains
  subroutine move(p)
    use types_mod, only: local_particle => particle
    type(local_particle), intent(inout) :: p
  end subroutine move
end module physics
```

```python
from . import types_mod

def move(p: types_mod.particle) -> None: ...
```

The Fortran rename `local_particle` is a procedure-local convenience and is not
preserved as the public datatype spelling. Two modules that both export
`state` therefore remain distinct as `a_types.state` and `b_types.state`.
Generated procedure-local namespace imports are not aliased; if the generated
module already has a public declaration or another import named `a_types`,
contract generation fails instead of inventing a replacement alias.

## Contract Files And Native Procedure Placement

Wrapper generation must distinguish immutable native structure from editable
Python export policy. Module `.pyi` files describe where native declarations
actually live. A root export contract describes where those declarations appear
in Python. Export policy must never rewrite native module membership or ABI
facts.

Every contained Fortran module is emitted as a leaf named after that module:

```text
solver_mod.pyi
```

The leaf filename is the native module identity. Renaming the leaf changes the
module selected by generated bridge code. Module procedures need no placement
or kind decorator: a declaration returning `None` is a subroutine; an
unprojected return is a function result; returns named by `@native_call` are
native output arguments.

The ordinary module-procedure form is intentionally small when the Python
signature already describes the native argument order:

```python
from x2py.contracts import Float64

def update(value: Float64[()]) -> None: ...
```

Only standalone procedures carry `@external`:

```python
from x2py.contracts import Float64, external

@external
def update(value: Float64[()]) -> None: ...
```

`@bind("native_name")` remains necessary only when the Python declaration name
differs from the native symbol. `@native_call` remains necessary only when the
Python signature hides, inserts, or reorders native arguments. `Pass()` marks
the implicit class instance. This is a method receiver or a newly allocated
constructor object.

Ordinary semantic types are the native type contract. `Int32`, `Float64`,
`Addr`, scalar storage rank `()`, array rank, shape, and focused metadata such
as `Allocatable` are not duplicated with source-language spellings.
Write the Python boundary shape directly as `T`, `T[()]`, `T[:]`, `Addr(T)`,
or `WrappedType`.
`Final[T]` remains the module-variable and constant spelling. `@native_type(...)`
is emitted only when a derived type has irreducible attributes or finalizers.

These facts are structurally validated before `.pyi` wrapper code generation.
They are declarations about the supplied native artifacts, not binary
introspection: x2py cannot prove that an arbitrary opaque binary actually uses
the declared ABI.

### Contained Module Procedures

One Fortran module maps to one `.pyi` file named for that module. A procedure
declared without `@external` in that module contract is contained in the native
Fortran module:

```python
from x2py.contracts import Float64

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
`@external`:

```python
from x2py.contracts import Float64, Int32, external

# externals/dgesv.pyi
@external
def dgesv(a: Float64[:, :], b: Float64[:, :]) -> Int32: ...
```

`@external` is immutable native-placement metadata. The bridge calls the
external procedure without a `use <module>` statement. Classic
implicit-interface-compatible procedures use a compact `external` declaration;
features that require an explicit interface retain one. The procedure needs no
Fortran `.mod` file, but its defining object, archive, or shared library must be
supplied to the link.

Python-visible renaming is separate from placement. `@bind` retains the native
Fortran procedure name while the declaration uses a wrapper name:

```python
from x2py.contracts import Float64, Int32, bind, external

@external
@bind("dgesv")
def solve(a: Float64[:, :], b: Float64[:, :]) -> Int32: ...
```

Here the bridge calls the external native procedure `dgesv`; the root export
contract may expose the wrapper declaration as `solve`. `@bind` does not turn a
module procedure into an external procedure and `@external` does not rename a
symbol.

Every generated standalone declaration must carry `@external`. Handwritten
contracts must do the same. Missing or contradictory placement metadata must
fail during `.pyi` validation or wrapper planning, before bridge emission or native
compilation.

### Source-To-Contract Layout

For Fortran `--pyi --out PATH`, `PATH` is the generated contract package
directory. The package entry is `PATH/__init__.pyi`. Native Fortran module
contracts are flat leaves named `<fortran-module>.pyi` directly under `PATH`;
the generator does not add per-source directories.

| Native input shape | Generated contract shape |
| --- | --- |
| One source containing one module | `__init__.pyi` plus one `<module>.pyi` leaf |
| One source containing several modules | `__init__.pyi` plus one flat leaf per native module |
| Several ordered sources containing modules | one combined package with one `__init__.pyi` and one flat leaf per native module across all sources |
| One fixed- or free-form source containing only standalone procedures | one `__init__.pyi` entry with `@external` on every procedure |
| Several standalone-procedure sources, such as BLAS/LAPACK | one compact `__init__.pyi` entry containing all generated `@external` declarations |
| Mixed modules and standalone procedures | one entry contract containing standalone declarations and importing module leaves |

For example, explicit output for `basic_subroutine.f90` containing module `m1`
emits:

```text
contracts/basic_subroutine/
├── __init__.pyi  # entry contract: from . import m1
└── m1.pyi        # declarations for native module m1
```

The entry file is the only wrapper input. It recursively discovers its native
leaves:

```bash
python3 -m x2py contracts/basic_subroutine/__init__.pyi \
  --native-objects basic_subroutine.o
```

For `__init__.pyi`, the package directory name supplies the extension name
unless wrapper `--out NAME` is provided. The runtime follows the entry's import
policy: `from . import m1` exposes `basic_subroutine.m1`, while
`from .m1 import *` explicitly flattens `m1` into the extension root.
Passing a leaf such as `m1.pyi` directly builds a flat extension named `m1`
unless `--out NAME` overrides it, so the same declaration is exposed as
`m1.update(...)` instead of under a package child namespace.

A mixed source keeps standalone procedures in the entry contract and marks each
one with `@external`:

```python
from x2py.contracts import Float64, external

from . import m1

@external
def func(value: Float64[()]) -> None: ...
```

This exposes `basic_subroutine.func` and `basic_subroutine.m1.add1`. The
standalone marker remains necessary because the bridge must distinguish an
external call from `use m1, only: add1`.

For several ordered sources, the requested output directory is still the package
itself. If two sources each define two modules, then:

```bash
python3 -m x2py generate --pyi first_api.f90 second_api.f90 --out contracts
```

emits exactly this shape when no extra dependency stubs are needed:

```text
contracts/
├── __init__.pyi
├── first_math.pyi
├── shared_types.pyi
├── second_math.pyi
└── box_ops.pyi
```

The entry imports module leaves in source order. Native source order and native
link order remain build-plan facts; the `.pyi` package records the Python API
and native module topology.

For a BLAS/LAPACK-style folder containing only standalone procedures, generated
output stays compact. Even when the native implementation remains split across
several source files, explicit `--pyi --out contracts` emits one entry
contract:

```text
contracts/
└── __init__.pyi  # @external dgesv, @external dgetrf, @external dgetrs
```

The entry is still the sole wrapper input. The native build plan remains
separate: each original Fortran source may compile to its own object, or the
procedures may come from one archive or shared library. This compact generated
shape applies only to standalone `@external` procedures. If a bundle also
contains native modules, those modules still generate one flat module leaf per
native module and the entry imports those leaves.

For legacy BLAS/LAPACK-style assumed-size arrays such as `DX(*)`, generated
contracts use `Flat`:

```python
from x2py.contracts import Addr, Flat, Float64, Int32, external

@external
def DAXPY(
    N: Addr(Int32),
    DA: Addr(Float64),
    DX: Float64[Flat],
    INCX: Addr(Int32),
    DY: Float64[Flat],
    INCY: Addr(Int32),
) -> None: ...
```

`Float64[Flat]` maps to rank-one assumed-size storage such as `real :: a(*)`.
The Python argument may be any contiguous NumPy array with rank 1 through 15;
the wrapper passes the contiguous element sequence as a rank-one native view.

`Float64[3, Flat]` maps to `real :: a(3, *)`, and
`Float64[3, 4, Flat]` maps to `real :: a(3, 4, *)`. Those multidimensional
forms are flat-edge contracts: the wrapper validates the fixed prefix axes, then
collapses all remaining contiguous Python axes into the final native assumed-size
extent. `Float64[:, Flat]` follows the same rule but reads the prefix extent
from the Python actual. Because `real :: a(:, *)` is not a legal Fortran
assumed-size declaration, source-generated contracts use declared prefix
extents such as `Float64[n, Flat]`; edited contracts may use `:` when the Python
actual should provide that prefix extent.

<!-- X2PY_C_DOCS_START
C-order flat storage can be expressed for native routines that consume a raw
flat buffer while the Python contract validates a multidimensional C-contiguous
view:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```python

from x2py.contracts import Addr, Annotated, Flat, Float64, Int32, ORDER_C, external

@external
def row_sums(
    n: Addr(Int32),
    values: Annotated[Float64[Flat, 3], ORDER_C],
    result: Float64[Flat],
) -> None: ...
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Here `values` is not a literal Fortran dummy declaration such as `real ::
values(*, 3)`, which Fortran does not allow. It is a Python storage contract:
the wrapper validates a C-contiguous `(n, 3)` view, constructs the corresponding
rank-2 Fortran bridge view over the same storage, and passes it to the native
assumed-size dummy. The native routine's `values(*)` dummy receives the
flattened element sequence and interprets the elements in row-major order.
X2PY_C_DOCS_END -->

### Native Artifacts And Link Resolution

Semantic contracts do not map to native artifacts by filename. x2py must never
assume that `name.pyi` is implemented by `name.o`:

- one entry `.pyi` may require several objects and libraries;
- several imported `.pyi` files may be implemented by one object or archive;
- one shared library may implement an entire BLAS/LAPACK contract bundle; and
- module files, objects, archives, shared libraries, and transitive libraries
  may come from different directories or build systems.

Native inputs form one extension-level link plan. The generated bridge creates
native symbol uses from the immutable `.pyi` binding metadata, and the linker
resolves those symbols from caller-supplied artifacts. The `.pyi` filename is
never used to guess an object, archive, or shared-library name.

Build results expose that plan as `WrapperBuildResult.native_build_plan`, not
as a flattened string list. `sources` records the semantic entry contract and
its recursively imported `.pyi` files. The native plan separately records
compiled native source units, produced objects, prebuilt objects/archives/shared
libraries, module/include directories, library directories, and ordered
`link_items`. Link items can represent `object`, `archive`, `shared_library`,
`named_library`, and `linker_argument` entries, so the model can preserve order
without pretending every item is the same kind of input.

The current `.pyi` build subset accepts direct artifact paths through
`--native-objects`:

```bash
--native-objects build/module1.o build/module2.o \
  /opt/vendor/lib/libsupport.a \
  /opt/vendor/lib/libsolver.so
```

Named libraries use linker-style names and directories:

```bash
--native-library lapack blas \
--native-library-dir /opt/vendor/lib
```

This requests `-llapack -lblas`, adds the directory to the link search path, and
adds the supported runtime search path for the produced extension. A direct
shared-library path and a named `-l` library are alternate ways to identify a
shared dependency; neither is inferred from `.pyi`.

Fortran module procedures additionally need their compiler-produced `.mod`
files while the generated bridge is compiled:

```bash
-I build/mod
```

Archives do not normally contain `.mod` files, so module directories remain
separate inputs. Standalone `@external` procedures require no `.mod` file because
the semantic contract supplies either their implicit external declaration or
their required explicit interface.

Required link cases are:

| Case | Native inputs |
| --- | --- |
| One contract, one object | one `.o` plus module directory when applicable |
| One contract, several dependencies | ordered objects/archives/shared libraries and named libraries |
| Imported contracts, separate objects | all required `.o` files in dependency-safe link order |
| Imported contracts, one archive | one `.a`; no contract-to-member mapping is inferred |
| Vendor shared implementation | direct `.so` path or `--native-library NAME` plus search directory |
| Mixed implementation | objects, archives, direct shared libraries, and named libraries in one ordered plan |
| Module procedures | native artifacts plus every required `.mod` search directory |
| Standalone procedures | native artifacts only; declaration mode comes from the completed `@external` contract |

Static link order is semantically significant: dependent objects precede the
archives or libraries that satisfy them, and dependent libraries precede their
providers. Cyclic static archives may require linker grouping or repeated
archives. The completed build interface must preserve caller order across all
native item kinds and provide an explicit ordered linker-argument mechanism for
groups, whole-archive policy, and platform-specific flags. The maintained
GNU/Linux runtime evidence covers mixed objects, archives, direct shared
libraries, named libraries, transitive providers, and explicit archive groups
for cyclic dependencies. These cases prove that the ordered plan is preserved;
they do not imply that every linker accepts the same platform-specific control
arguments.

Directly linked objects and static archives must be position-independent when
the platform requires PIC. All artifacts must match the active compiler ABI,
architecture, Fortran kind/layout assumptions, and name-mangling convention.
Missing symbols, duplicate strong definitions, incompatible files, unavailable
dependent shared libraries, and missing `.mod` files must produce actionable
build or import diagnostics rather than triggering a source fallback.

### Root Export Contract

For multi-file contract projects, one entry file defines the export contract.
Native module boundaries remain preserved by default:

```python
from . import module1 as module1
from . import module2 as module2
```

With extension name `library`, this exposes
`library.module1.update` and `library.module2.update`. Identically named members
in different native modules do not collide.

Aliases change only the Python export tree. They never change native placement:

```python
from . import module1 as solver
from .module2 import update as update_second
```

This exposes `library.solver` and `library.update_second`, not
`library.module1` or `library.update`. The bridge still imports native module
`module1` and still calls native procedure `module2.update`.

An alias creates another public Python binding to the same native declaration;
it does not promise Python object identity between exported names. For module
variables, every exported name routes to the same native storage, so writes
through one name are visible through the others, but each read may return a new
Python object. For functions, each exported name calls the same native
procedure; introspection such as `__name__` and `repr()` may report the public
alias name.

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

### Entry Contract And Extension Identity

Every `.pyi` wrapper build takes exactly one entry contract. A module leaf may
itself be the entry; in that case its declarations appear at the extension root.
A multi-module project uses an entry containing relative imports so each native
module remains a distinct child namespace unless explicitly re-exported.

An arbitrary root file is allowed and uses normal stub import syntax without a
`.pyi` suffix:

```python
# api.pyi
from .module1 import *
from .module2 import *
```

The entry filename chooses the compiled extension and shared-library name by
default. For `__init__.pyi`, the resolved containing directory name is used;
calling x2py as either `foo/__init__.pyi` or `__init__.pyi` from inside `foo/`
therefore selects `foo`. Wrapper `--out NAME`
overrides that inference and controls the extension filename,
`PyInit_<name>` symbol, and Python import name.

Target CLI shapes are:

```bash
python3 -m x2py contracts/library/__init__.pyi \
  --out library \
  --native-objects native.a
```

```bash
python3 -m x2py api.pyi \
  --out library \
  --native-library native \
  --native-library-dir /path/to/libs
```

For a single standalone fragment, no `__init__.pyi` is required:

```bash
python3 -m x2py dgesv.pyi \
  --out lapack_dgesv \
  --native-objects dgesv.o
```

These commands treat native artifacts as link inputs only. They do not permit
fallback parsing of unavailable Fortran source. The entry recursively resolves
its relative imports; imported contracts must not also appear as positional
arguments.

### Contract Import Graph

x2py parses the entry as a restricted semantic stub; it does not execute Python
code. Every relative import is resolved recursively to a sibling `.pyi` or a
package `__init__.pyi`, producing the complete transitive contract graph before
wrapper planning or code generation. Files that both declare native objects and import
other contracts contribute both roles.

The resolver preserves normal explicit export choices:

```python
from . import m1 as m2
from .m1 import func as f
from .m1 import *
```

The first form creates child namespace `m2`, the second exports only `f`, and
the third explicitly flattens all public names. Repeating the same export is
idempotent, and the same declaration may be exported under its original name and
one or more aliases when each export is requested explicitly. These aliases
share the same native target or storage, but `is` identity between Python
attributes is not part of the contract. Missing relative imports,
relative-import cycles, and conflicting exports fail before code generation and
identify the participating contract paths.

For wrapper builds, the entry export policy also defines the generated Python
extension binding surface. Declarations in imported leaf files that are not
reachable from that policy do not get standalone public wrapper bindings; they
remain native contract facts only when an exported declaration depends on them.

Absolute support imports such as `from x2py.contracts import prototype` or
`from types import SimpleNamespace` may support annotation parsing, but they are
not contract graph edges and never create runtime exports. Generated references
to declarations in another contract package file use relative imports.

Source-driven wrapping applies the same export construction internally. A
source `foo.f90` containing module `m1` therefore exposes `foo.m1`, while
standalone procedures remain directly below `foo`; source and generated-contract
builds must not disagree about namespace placement.

## Semantic Type Names

<!-- X2PY_C_DOCS_START
The public annotations use semantic names, not raw C or Fortran spellings:
X2PY_C_DOCS_END -->

| Family | Names |
| --- | --- |
| Booleans and generic values | `Bool`, `Any` |
| Signed integers | `Int`, `Int8`, `Int16`, `Int32`, `Int64` |
| Unsigned integers | `UInt8`, `UInt16`, `UInt32`, `UInt64`, `SizeT` |
| Reals | `Float32`, `Float64`, `Float128` |
| Complex | `Complex64`, `Complex128`, `Complex256` |
| Text | `String` |
| User types | class names and imported type names |
| Named callable prototypes | `@prototype` function declarations referenced by name |
| Prototype primitive reference | `Addr(T)` inside a `@prototype` declaration |
| Prototype non-primitive value override | `Value(T)` inside a `@prototype` declaration |

<!-- X2PY_C_DOCS_START
`Unknown` is intentionally rejected in `.pyi` annotations. Generated stubs must
resolve or block unsupported source types instead of emitting unknown contracts.
Current C callback placeholders such as `CFunctionPointer` can appear in
generated stubs when source callback policy is incomplete; replace them with a
named prototype before building a wrapper. A prototype records the
transport facts required by the generated adapter: native argument order,
type, rank, shape, character length, result shape, and value/reference passing.
It does not repeat native callback direction:

```python
from x2py.contracts import Addr, Float64, Int32, prototype

@prototype
def update_values(count: Addr(Int32), scale: Float64, values: Float64[:]) -> None: ...

def apply_update(callback: update_values) -> None: ...
```

Bare primitive callback arguments use native value passing, matching ordinary
wrapper signatures. Use `Addr(T)` when a primitive callback dummy is passed by
reference; Python still receives an independent NumPy scalar value. Arrays
become writable NumPy views, fixed-length character references become mutable
rank-zero bytes storage, and wrapped objects retain their native reference.
`Value(T)` is reserved for supported non-primitive scalar value dummies, such
as derived types declared with the Fortran `value` attribute.

Prototype declarations are not runtime functions and are not exported from the
generated Python module. They may be referenced from another semantic contract
module through a relative import:

```python
from .callback_shapes import transform

def apply_transform(callback: transform) -> None: ...
```

Post-IR policy completes each prototype reference as an implicit external or a
named explicit declaration. The named form is selected whenever the prototype
contains an explicit-interface-only characteristic such as an optional or
descriptor dummy, polymorphism, or an array/pointer/allocatable
result. The backend imports that real interface from the prototype's native
module, including its native direction attributes; the semantic `.pyi` does not
duplicate them. Primitive `Addr(...)` or non-primitive `Value(...)` alone may
still use a typed external declaration when no other characteristic requires
the explicit interface.

Optional callback dummies and allocatable, pointer, or polymorphic callback
dummies and results are currently rejected during policy completion.

Before wrapper planning, x2py completes these declarations into explicit
callback ABI, primitive-scalar value projection, non-scalar reference
writeback, result, context-lifecycle, thread/GIL, cleanup,
and fatal-error actions. The generated C trampoline and Fortran adapter consume
that completed record directly.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Character annotations have two axes. The first `String[...]` subscription is
the character length, and any second subscription is scalar-storage or array
shape:

- `String`: scalar string with assumed, deferred, or otherwise non-fixed length.
- `String[8]`: scalar fixed-length string with length 8.
- `String[:][:]`: rank-one array of non-fixed-length strings.
- `String[8][:]`: rank-one array of fixed-length strings.
- `String[8][()]`: mutable scalar fixed-length string storage.

Bare `String[:]` is invalid because it omits the shape axis and is ambiguous:
use `String` for a scalar non-fixed string, `String[:][:]` for an array of
non-fixed strings, or `String[n]` for a scalar fixed-length string. Source kind
names are already resolved into semantic dtypes, so generated contracts do not
import `iso_c_binding`, `iso_fortran_env`, or their kind constants.
X2PY_C_DOCS_END -->

## Python And Native Boundaries

Semantic `.pyi` annotations describe two related but separate boundaries:

- the Python boundary: what the caller passes to the generated wrapper;
- the native boundary: how x2py lowers that value into the native call.

Some types have one normal native representation. Array storage, scalar storage,
and scalar character values are always lowered as storage addresses. Bare numeric
scalars have two native representations: value by default, or address of
call-local storage when `@native_call([Addr(Arg(i))])` asks for that projection.

Use `@native_call` only when the native argument order, hidden outputs, inserted
arguments, or scalar by-address projection differs from the default lowering.

| Contract | Python boundary | Default native boundary |
| --- | --- | --- |
| `Float64` | `np.float64(...)` | scalar value |
| `@native_call([Addr(Arg(i))])` with `Float64` | `np.float64(...)` | address of x2py's call-local native scalar slot |
| `Float64[()]` | rank-zero NumPy array with dtype `np.float64` | storage address |
| `Float64[n]`, `Float64[:]`, `Float64[:, :]` | NumPy array storage | data address |
| `String[n]` | Python `str` whose encoded length is exactly `n` | address of x2py's call-local fixed-width character storage |
| `String[n][:]`, `String[:][:]` | NumPy bytes array storage | character array descriptor/data contract |
| `String[n][()]` | rank-zero NumPy bytes array with dtype `S<n>` | fixed-width character storage copied back into the NumPy array when native code mutates it |
| `Addr(Float64)`, `Addr(Float64[n])`, `Addr(String[n])` | integer raw address such as `array.ctypes.data` or a `ctypes` buffer address | that raw address |
| `WrappedType` | generated wrapper instance | wrapped object's native handle/address |

`Arg(i)` in `@native_call` means "use argument `i`'s default native
representation." For arrays, scalar storage, strings, and raw-address arguments,
that representation is already address/storage based. `Addr(Arg(i))` is reserved
for bare numeric scalar values that would otherwise be passed by value.
`Return(...)` entries always name hidden writable native output storage. The
wrapper passes that storage by address because a native output argument cannot
be written by value; `Addr(Return(...))` is redundant and invalid. Do not use
`Return(...)` for optional native outputs when the caller must control
`present(...)`; keep the output visible instead, using `T[()]` for scalar
storage and visible optional array storage for arrays.

## Storage Contracts

Bare scalar types are direct values:

```python
from x2py.contracts import Float64

def dot(a: Float64, b: Float64) -> Float64: ...
```

`T[()]` represents rank-zero NumPy storage. For arguments, the caller passes an
addressable rank-0 NumPy array with the declared dtype; x2py validates the
object and uses its data storage for the native call. For direct or projected
results, x2py returns a rank-0 NumPy array instead of collapsing the contract to
a scalar value:

```python
from x2py.contracts import Float64, Int32

def update_storage(value: Float64[()]) -> None: ...
def inspect_storage(value: Int32[()]) -> None: ...
def current_storage() -> Float64[()]: ...
```

The caller writes:

```python
value = np.array(3.0, dtype=np.float64)
update_storage(value)
```

Array annotations such as `T[n]`, `T[:]`, and `T[:, :]` represent
caller-provided NumPy storage. Character arrays use the same second-axis shape
rule: `String[8][:]` is an array of fixed-length strings, while `String[:][:]`
is an array whose element length is not fixed in the public contract. The native
boundary is always the array data address; `@native_call([Addr(Arg(i))])` is
redundant for these arguments.

Array dimensions in the public type are bridge extents, not native lower and
upper bounds. For example, a native dimension `0:LDB-1` has public extent
`LDB`, so an assumed-size contract is written `T[LDB, Flat]`. The bridge may
construct its local view with any lower bound while passing the same base
address and extent; the compiled native procedure applies its own declared
bounds. Native lower bounds, upper bounds, and source-dimension spellings are
not part of the semantic `.pyi` format.

`String[n]` represents a Python `str` at the Python boundary. Its encoded byte
length must be exactly `n`; x2py does not pad or truncate the public value. x2py
converts it to call-local fixed-width character storage and passes that storage
address to native code. If a returned `Returns["name", String[n]]` item is
present, native mutation is copied back into a replacement Python `str`;
otherwise the mutation is discarded.

`String[n][()]` represents caller-provided mutable scalar character storage. The
caller passes a rank-zero NumPy fixed-width bytes array:

```python
from x2py.contracts import String

def rewrite_label(label: String[8][()]) -> None: ...

label = np.array("abcdefgh", dtype="S8")
rewrite_label(label)
```

The public object is NumPy bytes storage, so reads such as `label[()]` produce a
bytes value. The dtype itemsize must match `n`; Python Unicode arrays and object
arrays are rejected.

Type-level `Addr(T)` represents an integer raw address supplied by the Python
caller. It is valid only for a primitive scalar pointee, a fixed-length
`String[n]`, or an array whose rank and every extent are resolved by literals
or visible scalar arguments. It is an advanced unsafe contract: x2py casts the
address according to the declared pointee type, but it cannot prove the address
lifetime, true dtype, alignment, length, or ownership. The pointer value itself
does not carry string length or array shape. Integer zero becomes a null
pointer without a conversion error, negative integers are forwarded through
the platform pointer conversion, and an out-of-range integer raises
`OverflowError`. x2py likewise resolves raw-array extent expressions without a
positivity check. Calling native code with an invalid address or pointee shape
is the caller's responsibility and may crash the process:

```python
from x2py.contracts import Addr, Float64, Int32, String

def update_raw(value: Addr(Float64)) -> None: ...
def inspect_raw(value: Addr(Int32)) -> None: ...
def raw_values(n: Int32, values: Addr(Float64[n])) -> None: ...
def raw_label(label: Addr(String[8])) -> None: ...
```

The caller passes an address value, usually from NumPy:

```python
value = np.array(3.0, dtype=np.float64)
update_raw(value.ctypes.data)
```

`Addr(WrappedType)`, `Addr(String)`, and unresolved array forms such as
`Addr(Float64[:])` are invalid Python-visible raw-address contracts. Wrapped
classes use `WrappedType` at the Python boundary, and their default `Arg(i)`
representation already supplies the wrapped native handle/address. Post-IR
policy completion rejects these invalid forms before wrapper planning or wrapper
lowering. `Addr(...)` remains a Python-visible raw-address contract and is not a
Fortran callback argument wrapper.

There is no type-level read-only wrapper. `T[()]`, arrays, raw addresses, and
wrapped objects are storage boundaries. Source-language read/write facts may
guide policy while converting source, but generated and edited `.pyi` contracts
do not store argument direction. Projected replacement and output behavior is
expressed with `Returns[...]`; ownership and transfer behavior is expressed
with explicit policy metadata. When a `.pyi` contract is loaded directly,
ordinary visible array and raw address storage is treated as writable caller
storage. Pointer array storage remains in the supported input subset unless
projected output policy is added.

Pointer depth is explicit for low-level pointer graphs:

```python
from x2py.contracts import Addr, Int8, OpaqueHandle

handle: Addr[2](OpaqueHandle)
argv: Addr[3](Int8)
```

`Addr[1](T)` is invalid; use `Addr(T)`.

Array storage uses NumPy-style subscriptions:

<!-- X2PY_C_DOCS_START
```python
from x2py.contracts import Annotated, Flat, Float64, ORDER_C

vector: Float64[:]
fixed: Float64[3]
matrix: Float64[n, m]
strided: Float64[::]
flat: Float64[Flat]
flat_matrix: Float64[3, Flat]
c_flat_matrix: Annotated[Float64[Flat, 3], ORDER_C]
rank_polymorphic: Float64[...]
```
X2PY_C_DOCS_END -->

Dimension entries have the following meaning:

| Form | Meaning |
| --- | --- |
| `:` | unconstrained extent for that axis |
| `n`, `3`, `n + 1` | required extent expression |
| `lower:upper` | range-like storage expression |
| `::` | axis accepts runtime stride |
| `0:n:` | range plus stride-aware axis |
| `Flat` | edge-position flat contiguous storage dimension |
| `...` | rank-polymorphic storage |

Generated `.pyi` prints `::` and bounded forms such as `0:n:` for stride-aware
axes. Edited contracts may still use the explicit `::Strided` and
`0:n:Strided` spellings; they load to the same semantic array contract.
Wrapper planning uses the structured array contract to distinguish layout dimensions
from extent expressions. Names such as `Strided` and `Flat` remain ordinary
symbols when they occur in native extent expressions. Called Fortran shape
intrinsics such as `size(v)` are recognized only after visible symbols are
resolved; the referenced value `v` must still be visible in the interface.

<!-- X2PY_C_DOCS_START
`Flat` must appear exactly once at either edge of a concrete-rank array.
`Float64[Flat]` is the rank-one assumed-size storage contract: the Python side
accepts any contiguous rank from 1 through 15 and flattens that storage sequence
to the rank-one native view. Final `Flat` in a multidimensional contract is
Fortran-oriented flat storage: `Float64[3, Flat]` corresponds to `real ::
a(3, *)`, accepts any Fortran-contiguous Python rank from 2 through 15 with
first extent `3`, and passes native extents `[3, product(rest)]`.

Leading `Flat` is C-oriented flat storage and should be spelled with explicit
`ORDER_C` in Fortran-facing contracts:
`Annotated[Float64[Flat, 3], ORDER_C]`. It validates any C-contiguous Python
rank from 2 through 15 with final extent `3`, flattens the leading Python axes,
and passes binding extents `[product(leading), 3]`. It does not imply an
invalid Fortran declaration such as `real :: a(*, 3)`.

Array dimensions are always written in Python logical-axis order. Consequently
the symmetric multidimensional forms are `Float64[rows, Flat]` for
Fortran-contiguous storage and
`Annotated[Float64[Flat, columns], ORDER_C]` for C-contiguous storage. The
bridge reverses the latter's extents to construct its Fortran storage view.
X2PY_C_DOCS_END -->

The Python argument may provide more storage than the declared explicit
dimensions describe, but the wrapper passes it to native code without a stride
descriptor. Non-contiguous arrays in the required native layout must be rejected
or copied into a contiguous temporary.

Qualified names such as `foo.bar` are not accepted as dimension expressions.
Use local constants or generated `Final[...]` names for shape symbols.

## Metadata With `Annotated`

`Annotated[...]` carries storage and call-boundary metadata. It does not carry
source-language argument direction or per-call value/reference selection. The
Fortran semantic pipeline supplies `ORDER_F` as the default multidimensional
layout. Generated contracts omit that default. Write explicit layout metadata
only when the Python-visible storage deliberately differs from that Fortran
representation, such as a row-major input accepted by a Fortran wrapper.
Native call transport belongs to `@native_call`: a wrapped derived
object uses its normal reference handoff with `Arg(i)` and exact typed value
handoff with `Value(Arg(i))`. The Python API accepts the same opaque wrapper
object in both cases; the generated Fortran bridge performs the typed call, and
the binding never exposes or guesses aggregate layout.

```python
from x2py.contracts import Annotated, COPY_F, Float64, ORDER_C

def fill(
    a: Float64[:, :],
    c_input: Annotated[Float64[:, :], ORDER_C, COPY_F],
    out: Float64[()],
) -> None: ...
```

Generated canonical metadata:

| Metadata | Meaning |
| --- | --- |
| `COPY_F` | accept the declared C-contiguous Python layout, create an F-contiguous temporary with the same logical axes, and copy back after visible native mutation |
| `PointerAssociation("runtime")` | pointer association is a runtime state rather than a declaration-time constant |
| `SourceName("native-name")` | source name cannot be represented directly as the Python target name |
| `Aliased` | native storage may be exposed across the Python boundary as an alias |
| `Immutable` | Python-visible value must not be mutated in place; this is a use-site boundary policy rather than an intrinsic datatype property, and writable native calls require a completed copy-in/copy-out replacement policy or an explicit call-local discarded-mutation policy |
| `Polymorphic` | an ordinary derived argument is a native polymorphic `class(T)` dummy; the passed-object dummy of a type-bound procedure omits this metadata because the binding already proves it |
| `Ownership("python" | "native" | "wrapper" | "caller" | "temporary" | "unknown")` | explicit owner override for the wrapper ownership policy |
| `Transfer("copy_return" | "snapshot_copy" | "borrowed_view" | "call_local" | "in_place" | "by_value" | "wrapper_instance" | "blocked")` | explicit boundary transfer override for the wrapper ownership policy |
| `Destruction("python_refcount" | "wrapper_dealloc" | "native_owner" | "caller" | "call_local" | "none" | "blocked")` | explicit destruction override for the wrapper ownership policy |
| `PointerPolicy(...)` | complete pointer policy: `nullable`, `transfer`, `target_owner`, `lifetime`, `deallocation`, `shape_source`, `contiguity`, `reassociation`, `aliasing`, and `mutability` |

<!-- X2PY_C_DOCS_START
| `ORDER_ANY` | edited contract accepts either C or Fortran orientation |
X2PY_C_DOCS_END -->

Loaded compatibility metadata:

| Metadata | Meaning |
| --- | --- |
| `Contiguous` | source provenance says the array is contiguous |
| `ArrayCategory("...")` | source array category provenance |
| `FortranAllocatable` | older scalar character allocatable metadata; generated contracts use `Allocatable[String]` |

<!-- X2PY_C_DOCS_START
| `ORDER_F` | explicit Fortran-oriented storage in a C contract |
| `ORDER_C` | explicit C-oriented storage in a Fortran contract |
Plain multidimensional C contracts default to `ORDER_C`; generated contracts
omit that marker and retain only an intentional alternate layout.
X2PY_C_DOCS_END -->

Without `COPY_F`, `ORDER_C` is zero-copy and native Fortran observes the
reversed-axis storage view. With `COPY_F`, the binding performs both copy-in and
any required copy-out; the bridge receives an ordinary F-order buffer and does
not know that a representation conversion occurred. `COPY_F` is initially
limited to required, concrete-rank, dense numeric ndarray arguments. It does
not apply to `Flat`, assumed-rank or strided arrays, optional arrays, character
arrays, native descriptor arguments, or handle actuals.

Semantic `.pyi` types never repeat the native procedure's `intent`. Native
source conversion may use the source declaration once to propose default
Python argument/result positions. The emitted Python signature, `Returns[...]`
items, and ordered `@native_call` mapping are the editable, authoritative
contract; users may retain the native positions or choose a different Python
projection. Wrapper policy is completed from that contract and does not retain
or re-infer native `intent`.

Bridge entry dummies use the permissive omitted-`intent` default. The binding
may therefore use mutable call-local storage and perform completed copy-back
even when the native procedure has a more restrictive dummy. The compiled
native procedure's own explicit interface remains authoritative when the
bridge calls it. When an argument is projected with `Returns`, Python receives
the original C-order object after copy-back.

Persistent native descriptors use wrapper type syntax instead of descriptor
metadata inside `Annotated[...]`:

```python
from x2py.contracts import Allocatable, Float64, Int32, Pointer

scratch: Allocatable[Float64]
current: Pointer[Int32]
values: Allocatable[Float64[:]]
target: Pointer[Float64[:]]
```

`Allocatable[T]` means a persistent native allocatable scalar descriptor and
`Pointer[T]` means a persistent native pointer scalar descriptor. Use those
type wrappers for module variables and derived-type fields.

`Allocatable[T[...]]` means a Python handle to a native allocatable array
descriptor. `Pointer[T[...]]` means a Python handle to native pointer
association state. Both are handles, not NumPy arrays. Extra metadata wraps the
handle, for example `Annotated[Allocatable[Float64[:]], Aliased]` or
`Annotated[Pointer[Float64[:]], PointerAssociation("runtime")]`.

At runtime, the same annotation can create a present empty descriptor handle:
`Allocatable[Float64[:]]()` starts unallocated, while
`Pointer[Float64[:]]()` starts unassociated. The element annotation and array
rank are required. Ordinary array annotations such as `Float64[:]` and scalar
descriptor annotations such as `Allocatable[Float64]` are not constructors.

`Allocatable[T[...]] | None` and `Pointer[T[...]] | None` are valid only on
optional callable arguments, where `None` or omission maps to native
`present(...)` false. Module variables, derived-type fields, and function results
use the handle type without `| None`; unallocated or unassociated state lives
inside the present handle.

For this optional-descriptor ABI, the binding always supplies the bridge with a
valid standard descriptor. For an omitted Python value it establishes a local
unallocated or unassociated placeholder descriptor, while a separate completed
presence action selects a native call that omits the native dummy. The bridge
never forwards or inspects placeholder storage as a present native argument.

Procedure boundaries keep the Python value type in the annotation and put the
native descriptor conversion in `@native_call`. Both scalar descriptor kinds
are nullable: Python passes `T | None`, where `None` creates a present but
unallocated allocatable descriptor or a present but unassociated pointer
descriptor for the call. An unallocated or unassociated projected result returns
`None`.

```python
from x2py.contracts import Allocatable, Arg, Float64, Pointer, Return, Returns, native_call

@native_call(
    [
        Allocatable(Arg(0)),
        Allocatable(Return("normalized", 0)),
        Pointer(Return("selected", 2)),
    ],
)
def normalize(
    value: Float64 | None,
) -> tuple[
    Float64 | None,
    Returns["value", Float64] | None,
    Returns["selected", Float64] | None,
]: ...
```

`Allocatable(Arg(i))` and `Pointer(Arg(i))` initialize an `intent(in)` or
`intent(inout)` descriptor from Python argument `i`. For `intent(inout)`, a
matching `Returns["name", T] | None` item requests readback from the same native
dummy. `Allocatable(Return("name", j))` and `Pointer(Return("name", j))`
create hidden `intent(out)` descriptor dummies projected into Python result slot
`j`. The `result=...` keyword describes the single native Fortran function
result; its nested `Return(j)` selects that result's position among all Python
results. Other Python results come from projected `intent(out)` and
`intent(inout)` dummies.

Use hidden descriptor outputs for nullable rank-zero results that must preserve
`None`: `Allocatable(Return("name", j))` or `Pointer(Return("name", j))`.
Direct rank-zero allocatable function results are blocked because the bridge
cannot safely preserve the unallocated function-result state across supported
Fortran compilers.
Direct allocatable array function results use wrapper-owned descriptor handles
and preserve allocated, zero-sized, and unallocated state for rank one and
higher.

Descriptor projection uses calls, not type subscriptions. Write
`Allocatable(Arg(0))`, not `Allocatable[Arg(0)]`. This is distinct from
`Addr(Arg(0))`: a scalar allocatable or pointer is a native descriptor, not just
the address of a scalar slot.

Defaulted scalar descriptor arguments carry native optional-dummy absence:

```python
@native_call([Allocatable(Arg(0))])
def update(value: Float64 | None = ...) -> None: ...
```

The native optional-dummy behavior has three states: `update()` means native
`present(value)` is false, `update(None)` means the dummy is present with an
unallocated or unassociated descriptor, and `update(1.0)` means the dummy is
present with a value. This scalar rule is separate from array handles:
`Allocatable[T[...]] | None` and `Pointer[T[...]] | None` are only the optional
absent-handle form, while unallocated or unassociated array state remains inside
a present handle.

Reads of scalar descriptor variables or derived-type components are different
because they expose persistent native state. Attribute reads copy the current
scalar value into Python and return `None` when the allocatable is unallocated
or the pointer is unassociated. No scalar handle object is exposed, so these
values do not provide `.to_numpy()`, `.view()`, `.get()`, `.value`,
allocation, deallocation, nullification, or resize APIs.

Plain nullable Python projections are separate from native descriptors:

```python
from x2py.contracts import Float64

maybe_value: Float64 | None
```

`Float64 | None` does not imply a native allocatable or pointer descriptor.
For array descriptors, use `Allocatable[T[...]]` and `Pointer[T[...]]`.
`Annotated[T[...], Allocatable]` and `Annotated[T[...], Pointer]` are not
active public descriptor spellings. Derived module objects remain live objects;
there is no public whole-object snapshot annotation.

### Ownership, Transfer, And Destruction Policies

Ownership metadata is consumed by the centralized wrapper ownership policy.
These annotations are the editable contract for how a value crosses the Python
boundary and who eventually releases the storage:

- `Ownership("...")` says who owns the value or native storage.
- `Transfer("...")` says how that value crosses the Python/native boundary.
- `Destruction("...")` says where the owned storage is released.

`Transfer(...)` is intentionally the canonical spelling for borrowed views. A
borrowed view is one transfer mode among copies, call-local temporaries, in-place
mutation, wrapper-owned instances, and explicit blockers. Grouping them under
`Transfer(...)` keeps mutually exclusive boundary behaviors visible in the same
place instead of hiding them behind unrelated helper names.

These annotations are policy requests, not permission to skip validation. The
backend still verifies that the requested owner, transfer mode, lifetime, shape,
and destruction policy are implemented for the object kind and native context.
Unsupported or contradictory policy must fail before bridge lowering instead of
falling back to source-derived behavior.

Transfer modes:

| Transfer mode | Meaning | Usual destruction policy | Example |
| --- | --- | --- | --- |
| `Transfer("by_value")` | A scalar value crosses as a Python value; no shared native storage is exposed. | `Destruction("python_refcount")` for the returned Python object. | `def count() -> Annotated[Int32, Ownership("python"), Transfer("by_value"), Destruction("python_refcount")]: ...` |
| `Transfer("call_local")` | The wrapper creates or associates storage only for one native call. Python does not receive persistent native storage. | `Destruction("call_local")` for bridge temporaries, or `Destruction("none")` when no generated storage is owned. | `def use_value(value: Annotated[Float64, Ownership("temporary"), Transfer("call_local"), Destruction("call_local")]) -> None: ...` |
| `Transfer("in_place")` | Native code writes through caller-provided mutable Python storage. The same Python object observes the mutation. | `Destruction("caller")`; x2py must not free caller storage. | `def scale(values: Annotated[Float64[:], Ownership("caller"), Transfer("in_place"), Destruction("caller")]) -> None: ...` |
| `Transfer("copy_return")` | Native output is copied or read back into a fresh Python-visible return value. The original Python object is not mutated unless separately declared. | `Destruction("python_refcount")` after Python owns the copy. | `def read_values() -> Annotated[Float64[:], Ownership("python"), Transfer("copy_return"), Destruction("python_refcount")]: ...` |
| `Transfer("snapshot_copy")` | Python receives a detached copy of current native state. Later native changes do not update it, and Python writes do not mutate native storage. This transfer name does not by itself make a returned NumPy array read-only. | `Destruction("python_refcount")` for the detached copy. | `def read_values() -> Annotated[Float64[:], Ownership("python"), Transfer("snapshot_copy"), Destruction("python_refcount")]: ...` |
| `Transfer("borrowed_view")` | Python receives a no-copy view of storage owned somewhere else. Writes may mutate that storage when the value is mutable and the backend supports writable views. | Usually `Destruction("native_owner")` or `Destruction("wrapper_dealloc")`; Python does not free the borrowed target. | `module_values: Annotated[Allocatable[Float64[:]], Aliased, Ownership("native"), Transfer("borrowed_view"), Destruction("native_owner")]` |
| `Transfer("wrapper_instance")` | Python receives a wrapper object that owns or controls a native instance. | `Destruction("wrapper_dealloc")`. | `def make_state() -> Annotated[state, Ownership("wrapper"), Transfer("wrapper_instance"), Destruction("wrapper_dealloc")]: ...` |
| `Transfer("blocked")` | The contract intentionally has no safe lowering with the current policy facts. Wrapper generation must stop. | `Destruction("blocked")`. | `def reassociate(values: Annotated[Pointer[Float64[:]], Ownership("unknown"), Transfer("blocked"), Destruction("blocked")]) -> None: ...` |

Destruction policies:

| Destruction policy | Where storage is released |
| --- | --- |
| `Destruction("python_refcount")` | Python, NumPy, or a generated base capsule releases the Python-owned copy when references are gone. |
| `Destruction("wrapper_dealloc")` | The generated wrapper deallocator releases the native instance or storage owned by that wrapper. |
| `Destruction("native_owner")` | Native module state or an external native owner releases the storage; Python only borrows it. |
| `Destruction("caller")` | The Python caller owns the object passed into the wrapper; x2py may mutate it but must not destroy it. |
| `Destruction("call_local")` | The generated bridge releases the temporary before the wrapped call returns. |
| `Destruction("none")` | No persistent owned storage is created by x2py for this boundary value. This is not a claim that no native storage exists. |
| `Destruction("blocked")` | Release ownership is unknown, contradictory, or unimplemented, so wrapper generation must stop. |

Contradictions are contract errors, not implementation choices. For example,
`Immutable` says the Python-visible value must not be mutated in place, while
`Transfer("borrowed_view")` says Python sees shared no-copy storage. Combining
them for a writable native argument is invalid because the wrapper cannot both
preserve immutability and expose a writable shared view. The user must choose one
contract: remove `Immutable` for in-place borrowed mutation, or keep `Immutable`
and request an explicit replacement return such as `Returns["values",
Float64[:]]`.

`PointerPolicy` is keyword-only and requires all ten keys. Its string values are
preserved verbatim so project-specific owner and release names can be expressed;
the backend still validates whether the requested transfer and destruction path
are implemented.

For native pointer-array handles, `associate(other)` and `nullify()` are always
available. `allocate(shape)` is permitted only when `reassociation` is
`allocate`, `allocate_resize`, `reallocate`, or `reassociate_allocate`.
`deallocate()` is permitted only when `deallocation` is
`deallocate`, `deallocate_resize`, `owner_deallocate`,
`unsafe_deallocate`, or `wrapper_dealloc`.
Use `unsafe_deallocate` only when the contract intentionally makes the caller
responsible for requesting deallocation without x2py-proven target ownership.
`resize(shape)` is permitted only when the policy opts into resize through both
reassociation and deallocation, using `resize`, `allocate_resize`, or
`deallocate_resize` as appropriate. Other values keep those operations absent
from the completed handle policy.

Pointer-array extraction policy is selected from completed descriptor and
layout facts before wrapper lowering. A contiguous target selects
`contiguous_view`. A strided or otherwise general target selects
`descriptor_view`, which requires standard descriptor interop support. Copy-
oriented `PointerPolicy(...)` values may retain unrelated call/ownership
meaning, but they do not request a copied `to_numpy()` result. If those facts
cannot support a live view, extraction is unsupported rather than copied. When
generated descriptor interop supplies decoded descriptor fields as mappings or
field-record objects, the shared runtime can build live NumPy views for positive
or negative descriptor stride multipliers.

```python
from x2py.contracts import Annotated, Float64, Pointer, PointerPolicy

value: Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]
```
For module and derived-field pointer-array handles, a completed contiguous
policy enables `contiguous_view` extraction and checks the target's current
contiguity before reading it. General strided extraction still requires the
descriptor-view path. Pointer-array function results and nonoptional
`intent(out)` outputs use wrapper-owned standard pointer descriptors. Their
handles release descriptor storage on `close()` or finalization without
implicitly deallocating the target.

Derived module objects use the normal generated class in both plain and
`Aliased` declarations:

```python
from x2py.contracts import Aliased, Allocatable, Annotated, Float64

class box:
    values: Allocatable[Float64[:]]

live_current: Annotated[box, Aliased]
plain_current: box
```

Both reads return live native-owned objects. `Aliased` remains a
language-neutral addressability fact: it permits an address-backed borrow, but
does not make a native-array handle copy. A plain derived module declaration
uses typed module-specific bridge operations and must not be lowered by
fabricating a native address.

`Final[T]` is the only public constant spelling. Do not use
`Annotated[T, Constant]` or `T[Constant]`.

## Constants And Enums

Constants use `Final[T]`. Literal values are optional unless the value is needed
as a compile-time expression or enumerator initializer:

```python
from x2py.contracts import Final, Int32

nmax: Final[Int32]
answer: Final[Int32] = 42
```

Fortran enumerators are plain integer constants. Do not declare or expect
Python `Enum`/`IntEnum` classes or semantic enum datatypes:

```python
from x2py.contracts import Final, Int

STATUS_OK: Final[Int] = 0
STATUS_RETRY: Final[Int] = STATUS_OK + 1
```

The listed names are documentation and convenience constants. Procedure
arguments and returns that use native enum types are emitted as the underlying
integer type.

<!-- X2PY_C_DOCS_START
C enumerators use the same integer-constant contract.
X2PY_C_DOCS_END -->

## Classes And Native Type Markers

Fortran derived types and ordinary semantic classes use normal class syntax:

```python
from x2py.contracts import Float64, Int32

class particle:
    id: Int32
    position: Float64[3]
```

<!-- X2PY_C_DOCS_START
C aggregate identity is explicit through base markers:
X2PY_C_DOCS_END -->

```python
from x2py.contracts import CStruct, CUnion, Float64, Int32, Opaque, UInt32

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
| `Opaque` | type identity is known, but fields/layout are intentionally hidden |

<!-- X2PY_C_DOCS_START
| `CStruct` | native C `struct` |
| `CUnion` | native C `union` |
| `CAnonymous` | generated nested anonymous C aggregate type |
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Anonymous C aggregate members are represented as nested classes plus a generated
field that marks the anonymous member:
X2PY_C_DOCS_END -->

```python
from x2py.contracts import Annotated, CAnonymous, CAnonymousMember, CStruct, CUnion, Float32, Int

class flags(CStruct):
    class anonymous_union_0_type(CUnion, CAnonymous):
        integer: Int
        real: Float32

    _anonymous_union_0: Annotated[anonymous_union_0_type, CAnonymousMember]
    tag: Int
```

<!-- X2PY_C_DOCS_START
The generated field preserves that the anonymous union is a real C member even
though C exposes its fields through the containing aggregate.
X2PY_C_DOCS_END -->

External opaque types can live in separate owner stubs:

```python
from x2py.contracts import Opaque

# types_mod.pyi
class particle(Opaque):
    pass

# physics.pyi
from types_mod import particle

def move(p: particle) -> None: ...
```

If the owner stub is later edited to include fields, the import is reconciled as
a wrapped external type without changing the importing file.

## Functions, Methods And Returns

Generated Fortran stubs present the documented Python call while retaining the
exact native argument topology. An identity call needs no `@native_call`.
Whenever the Python signature hides, inserts, or reorders a native argument,
the generated declaration includes `@native_call`.

Edited contracts may also choose the identity native call directly. When every
native dummy argument remains visible in native order, output scalar dummies are
ordinary writable arguments instead of projected Python returns, and the
declaration does not need `@native_call`. Callers pass mutable storage, such as
a 0-D NumPy array with the declared dtype, for scalar output slots.
If a caller chooses identity form for a fixed-length `String[n]` argument while
passing an ordinary Python `str`, any native mutation is made to a temporary
native buffer and is not observable after a `None` return.

Fortran scalar dummy arguments are represented with explicit value, storage, or
address contracts:

| Source dummy shape | Generated semantic form |
| --- | --- |
| no `value`, read-only reference | visible `T` plus `@native_call([Addr(Arg(i))])` |
| no `value`, output reference | `T[()]` for identity storage, or a projected `Returns["name", T]` |
| no `value`, writable reference | `T[()]` for caller storage, or visible `T` plus projected `Returns["name", T]` |
| `value` | direct `T` |
| function result | direct return annotation |

Visible non-allocatable array output buffers are compact by default. They are
still passed to native code as writable arrays and projected with
`Returns["name", T]`; the native procedure owns the source-level
discard-initial-value semantics.

Loaded return forms:

```python
from x2py.contracts import Float64, Int32, Returns

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

With an explicit `@native_call`, a matching `Returns["name", T]` item
automatically assigns that visible `Arg(i)` its Python result position; it does
not require a duplicate `Return(...)` entry. The first ordinary return item is
the native function result. A native output dummy with no visible Python
argument must instead appear explicitly as `Return("name", position)` in the
native argument list. The list itself is exhaustive: once `@native_call` is
present, every native dummy position must have exactly one entry in native
order; native arguments are never inferred from leftovers.

For bare numeric scalar values, `Addr(Arg(i))` means x2py first converts the
Python argument to its native scalar representation and then passes the address
of that native slot. It does not mean the user passed a reference.

```python
from x2py.contracts import Addr, Arg, Float64, Returns, native_call

@native_call([Addr(Arg(0))])
def read_ref(x: Float64) -> None: ...

@native_call([Addr(Arg(0))])
def update_value(x: Float64) -> Returns["x", Float64]: ...
```

`read_ref` creates call-local native scalar storage initialized from `x` and
passes its address with no readback. `update_value` creates mutable native scalar
storage initialized from `x`, passes its address, then returns the updated value.
The caller writes `x = update_value(x)`.

When an existing native signature has writable scalar-reference behavior but no
projected replacement result, use scalar storage to expose an addressable Python
object:

```python
from x2py.contracts import Float64

def legacy_update(x: Float64[()]) -> None: ...
```

The wrapper uses the caller-supplied rank-zero storage, so native mutation is
observable through that storage after the call.

Inside `@native_call`, `Addr` wraps a projection rather than a type.
`Addr(Arg(i))` is valid only for a primitive scalar Python value whose native
parameter requires the address of call-local scalar storage. Do not use it for
`T[()]`, arrays, strings, wrapped objects, or raw `Addr(...)` arguments. Their
default `Arg(i)` representation is already the native storage, handle, or raw
address representation. Address projections of `Return(...)` and `Work(...)`
are also rejected; native outputs and workspaces already name their storage.

`Value(Arg(i))` is the inverse override for an exact rank-zero monomorphic
wrapped derived object. Plain `Arg(i)` passes that object by reference;
`Value(Arg(i))` asks the typed bridge to pass the exact native object by value.
Primitive scalars already use value passing with plain `Arg(i)`, while arrays,
strings, raw addresses, and descriptor handles keep their normal storage ABI and
do not accept `Value(...)`. The foreign binding boundary still carries an opaque object
address: `Value(...)` records the native Fortran dummy contract, and the Fortran
compiler performs any required copy when the typed bridge makes the call. It
never asks the binding to pass aggregate bytes through the foreign ABI.

```python
from x2py.contracts import Returns, String

def string_inout(label: String[8]) -> Returns["label", String[8]]: ...
```

The caller passes a Python `str`; x2py creates fixed-width character storage,
passes its address, and returns a replacement string because the signature asks
for one.

For example, a native subroutine ordered as `(a, status, b)` with hidden scalar
`status` output is represented as:

```python
from x2py.contracts import Addr, Arg, Float64, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("status", 0), Addr(Arg(1))])
def solve(
    a: Float64,
    b: Float64,
) -> Int32: ...
```

`@native_call` preserves native argument order. The return annotation preserves
Python result order and the hidden output's native name and type. A function
result is Python result slot zero; projected output arguments follow it in
native argument order. Each `Return(...)` entry is hidden writable storage passed
to the native procedure by address. The optional `result=` keyword records a
native scalar descriptor function result, for example
`result=Allocatable(Return(0))` or `result=Pointer(Return(0))`.

For nullable rank-zero values, prefer a hidden output dummy:
`Allocatable(Return("name", 0))` or `Pointer(Return("name", 0))`. Direct
rank-zero allocatable function results are rejected when the wrapper would need
to preserve an unallocated result as Python `None`.
Direct allocatable array function results use wrapper-owned descriptor handles
and are supported for matrices and higher-rank arrays.

For descriptor projections, `Pointer(Arg(i))` without a matching
`Returns["name", T]` creates a permissive call-local pointer adapter and
discards any native reassociation after the call. Adding the matching projected
return requests association writeback instead; scalar-derived values then
require persistent pointer storage. This choice belongs to the Python contract,
not native `intent`.

The same native routine can be edited into an identity call without projection:

```python
from x2py.contracts import Addr, Float64, Int32

def solve(
    a: Addr(Float64),
    status: Int32[()],
    b: Addr(Float64),
) -> None: ...
```

This form exposes the native argument order directly. Python callers allocate
`status` as a rank-0 NumPy array and inspect it after the call; x2py does not
synthesize a return value for that output slot. The raw `Addr(Float64)`
arguments require callers to pass addresses directly; use visible `T`
plus `@native_call([Addr(Arg(i))])` when callers should pass ordinary scalar
values instead.

Class methods use the same stub form. An untyped leading `self` is allowed in a
method and is not treated as a native argument.

A declared module procedure may also be projected as an instance method.
`Pass()` places `self` in its native argument list. The module function and
method remain independent Python exports, even when they have the same name.
Matching names select the same native procedure without `@bind`. A different
Python method name requires `@bind("native_name")`.

## Generic Procedure Overloads

The x2py semantic `.pyi` format uses `@overload("specific_name")` to link one
Python-visible declaration to an ordinary concrete procedure declaration. This
decorator is x2py metadata; it is not `typing.overload` and must not be imported
from `typing`.

```python
from x2py.contracts import Addr, Arg, Float64, Int32, Pass, bind, native_call, overload, private

@private
@native_call([Addr(Arg(0))])
def convert_integer(value: Int32) -> Int32: ...

@private
@native_call([Addr(Arg(0))])
def convert_real(value: Float64) -> Float64: ...

@bind("convert")
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_real")
def convert(value: Float64) -> Float64: ...

class accumulator:
    @bind("add")
    @overload("accumulator_add_integer")
    def add(self, value: Int32) -> None: ...

    @bind("add")
    @overload("accumulator_add_real")
    def add(self, value: Float64) -> None: ...
```

Concrete specifics that remain in a stub are ordinary functions with their
native names. Ordinary source-private Fortran declarations are not emitted as
standalone generated `.pyi` items. A private overload specific may remain only
when it is needed to resolve a public overload declaration from the standalone
`.pyi`. `@private` is reserved for a user-imposed contract on a declaration
that is otherwise part of the wrapper input.
`@native_call` is not emitted merely to restate an unchanged native function
name.
An overload declaration is a Python dispatch link. It must not also carry
`@native_call`; the linked concrete procedure owns argument reordering,
`Pass()`, hidden values, and projected returns. An overload-level `@bind`
changes only the final native call target.

The same rule applies to class overloads. Their concrete link may describe a
private specific while `@bind("public_generic")` selects the callable
type-bound generic.

The loader resolves only the decorator string. It never guesses a target by
signature. The target must exist exactly once, each target may occur only once
in one overload set, and the public declaration must agree with the concrete
call signature and return type. Missing, duplicate, ambiguous, and incompatible
links are deterministic errors.

Without overload-level `@bind`, a module candidate calls the linked procedure's
resolved native name. With `@bind`, it calls the named native symbol instead.
This is required when a public generic is the only native entry point for a
private specific:

```python
from x2py.contracts import Int32, bind, overload, private

@private
def convert_integer(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_integer")
def convert_number(value: Int32) -> Int32: ...
```

`@private` controls Python visibility only. For edited standalone contracts,
x2py cannot infer whether the linked native procedure is accessible. A direct
call to a Fortran-private specific therefore fails during the native build.

Python method names recover the native generic for ordinary operators. When
two distinct Fortran generics share one Python method, the decorator also
carries the otherwise unrecoverable operator spelling:

```python
from x2py.contracts import Bool, overload

@overload("equivalent_values", generic="operator(.eqv.)")
def __eq__(self, other: value) -> Bool: ...
```

For class methods, `generic=` is restricted to a compatible operator or
assignment generic. It is emitted for `.eqv.` and `.neqv.`, which would
otherwise be indistinguishable from `operator(==)` and `operator(/=)`.

<!-- X2PY_C_DOCS_START
The generated C extension exposes one callable for each generic name. It
dispatches before conversion using the wrapped scalar dtype, array element
dtype and rank, or wrapped derived-type class. It does not use implicit numeric
coercion to choose an overload. Array shape, bounds, and layout are validated
by the selected concrete wrapper, but they do not distinguish overloads;
overloads that differ only in those properties are rejected during generation.
X2PY_C_DOCS_END -->

Each specific keeps its declared Python call shape. The generated dispatcher
normalizes positional and keyword arguments against each candidate, then uses
the candidate's exact typed predicates. A call that matches no specific raises
`TypeError`; duplicate runtime dtype/rank/class signatures are a deterministic
generation error.

<!-- X2PY_C_DOCS_START
Wrapped derived types dispatch by their generated extension class. Fortran
`extends` relationships create the corresponding Python extension-type
inheritance graph. Ordinary overload predicates remain exact-class predicates;
closed scalar `class(base), intent(in)` dispatch separately enumerates the
supported descendants most-derived first. User-defined Python subclasses are
not part of this runtime contract.
X2PY_C_DOCS_END -->

## Defined Operators And Assignment

Defined operators use the same explicit link. The concrete function keeps its
full Fortran operand list, while the class declaration describes the Python
method call:

```python
from x2py.contracts import Addr, Arg, Float64, Pass, native_call, overload, private

@private
@native_call([Arg(0), Addr(Arg(1))])
def add_vector_real(left: vector, right: Float64) -> vector: ...

@private
@native_call([Addr(Arg(0)), Arg(1)])
def add_real_vector(left: Float64, right: vector) -> vector: ...

class vector:
    @overload("add_vector_real")
    def __add__(self, right: Float64) -> vector: ...

    @overload("add_real_vector")
    def __radd__(self, left: Float64) -> vector: ...
```

Operand positions are fixed:

| Python method | Native operands |
| --- | --- |
| non-reflected binary method | `self` is operand 1; `other` is operand 2 |
| reflected binary method | `other` is operand 1; `self` is operand 2 |
| unary method | `self` is the only operand |
| comparison method | `self` is the Python left operand; reflected comparison metadata restores native order |

<!-- X2PY_C_DOCS_START
Return annotations must equal the concrete procedure result. The generated C
extension dispatches the Python slot before conversion by dtype, rank, and
wrapped extension class. Operator slots also accept a native Python scalar when
there is exactly one candidate precision in that integer, real, or complex
family; this is needed when Python or NumPy invokes a reflected slot with a
built-in scalar. No match raises `TypeError`, and indistinguishable candidates
fail during generation. Three-argument `pow(value, exponent, modulus)` is not a
Fortran operator form and raises `TypeError`.
X2PY_C_DOCS_END -->

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

x2py does not infer in-place methods such as `__iadd__`. Python's fallback
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
from x2py.contracts import Addr, Arg, Float64, Pass, Returns, native_call, overload, private

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_real(
    left: vector,
    right: Float64,
) -> Returns["left", vector]: ...

class vector:
    @overload("assign_vector_real")
    def assign(self, right: Float64) -> vector: ...
```

`lhs.assign(rhs)` invokes native `lhs = rhs`, mutates the existing wrapped
object, preserves Python object identity, and returns the same object. Both
`lhs.assign(rhs)` and `lhs = lhs.assign(rhs)` are therefore valid. Assigning an
object to itself is a no-op that returns the existing object. A supported
specific must be a two-argument subroutine whose wrapped derived-type LHS is
writable and whose RHS is read-only. Unsafe or unsupported forms are wrapper-planning
blockers.

## Allocatable Array Handles

Supported Fortran allocatable module arrays and derived-type array fields are
exposed as `Allocatable[T[...]]` handles. The handle carries allocation state
and descriptor operations. It is not a NumPy array, and unallocated state lives
inside the handle.

`h.to_numpy()` returns `None` when the descriptor is unallocated. Otherwise it
returns a live NumPy view over the current native storage and never an automatic
detached copy. For derived-type fields, the extracted view retains the field
handle and the field handle retains the containing Python wrapper. For module
variables, the handle retains the generated module owner while the native
module controls allocation.

Existing views are not invalidated, detached, or tracked. If a wrapped Fortran
procedure reallocates or deallocates native storage while Python still holds an
old view, that old view is stale; reading or writing it is unsupported and may
crash the process. Users who need independent lifetime must copy explicitly:

```python
x = obj.values.to_numpy()        # live view or None
y = None if x is None else x.copy()
obj.reset_values()               # may invalidate x; y remains valid
```

Derived-type allocatable fields remain fields in `.pyi`:

```python
from x2py.contracts import Allocatable, Float64

class buffer:
    values: Allocatable[Float64[:]]
```

Python cannot directly replace or reallocate such fields. Assigning a new array
to the field raises `AttributeError`; explicit wrapped Fortran procedures must
perform allocation, reallocation, and deallocation.

Fortran classes with public rank-0 numeric, logical, or complex components
emit a generated keyword-only constructor in generated stubs. Every constructor
keyword is optional: omitted components keep the native allocation state,
including any Fortran default component initializer.

```python
from x2py.contracts import Float64, Int32

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

If a generated class has fields but none can be constructor keywords, the stub
emits the self-only form `def __init__(self) -> None: ...`. This declaration
keeps native default construction explicit in the editable contract; arrays,
allocatables, pointers, characters, and derived-type fields still do not become
constructor arguments.

An edited stub controls whether that generated constructor remains part of the
Python surface. If either generated `__init__` form is removed, wrapper
generation must not recreate it. A class left without any `__init__` has no
public Python constructor; native allocation remains an internal wrapper
operation only.

An edited stub may replace the generated field-keyword constructor with one
native initializer. `@bind("native_name")` selects the procedure. Exactly one
`Pass()` in `@native_call(...)` selects the newly allocated object. Its native
position is explicit, so other arguments of the same derived type remain
unambiguous. The selected native dummy must accept the constructed type. The
original module-level declaration may remain public or be marked `@private`.
It may also be removed when only construction should expose the initializer.
The `__init__` declaration remains sufficient to generate the native call.

```python
from x2py.contracts import Addr, Arg, Float64, Int32, Pass, bind, native_call

class state:
    @bind("init_state")
    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def __init__(
        self,
        seed: Int32,
        scale: Float64 = ...
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
```

The generated keyword-only shape remains reserved: if undecorated `__init__`
keeps the `self, *, ...` form and every keyword has a default, the loader treats
it as the generated field constructor metadata. Constructor overload
declarations replace runtime field initialization with an exact constructor
overload set linked to concrete same-class targets. The direct wrapper allocates
one native owner, dispatches without candidate trial calls, and releases an
uncommitted owner on failure. Missing, incompatible, or indistinguishable
candidates are rejected before source emission.

A constructor overload may also route through a public type-bound generic:

```python
class accumulator:
    @bind("add")
    @overload("accumulator_add_integer")
    def __init__(self, value: Int32) -> None: ...
```

The wrapper allocates `self` first. The overload link supplies the concrete
argument contract; `@bind("add")` supplies the native call target.

Module variables are declarations in the semantic contract. Allocatable array
module variables expose handles; unallocated state is represented by the handle,
not by making the module attribute `None`:

```python
from x2py.contracts import Aliased, Allocatable, Annotated, Float64

module_values: Annotated[Allocatable[Float64[:]], Aliased]
plain_values: Allocatable[Float64[:]]
```

Both declarations expose a stable native-owned handle whose `to_numpy()` call
returns a current live view or `None`. `Aliased` does not select view versus
copy extraction. It remains a language-neutral fact that native storage may be
externally aliased or addressed. Fortran source declarations with `target` are
printed as `Aliased` because they supply that native fact.

`Aliased` also records addressability used by borrowed access to an existing
derived-type module object. Plain derived module objects remain live but use a
different bridge mechanism:

```python
from x2py.contracts import Aliased, Allocatable, Annotated, Float64

class box:
    values: Allocatable[Float64[:]]

live_current: Annotated[box, Aliased]
plain_current: box
```

The annotation belongs to the module variable, not to `box`. An x2py-created
`box()` is addressable because its generated constructor allocates
pointer-backed native storage. A native module declaration is a different object
origin. `Annotated[box, Aliased]` lets the wrapper retain that object's native
address and return a live borrowed `box` wrapper. A plain `box` module variable
returns the same public wrapper type, backed by typed module-specific bridge
operations. Unsupported live lifetime or module-access policy stops wrapper planning;
the backend must not fall back to a detached object or an invented address.

Public scalar Fortran module variables are emitted directly with their resolved
semantic type:

```python
from x2py.contracts import Int32, String

counter: Int32
label: String[8]
```

Scalar allocatable and pointer module variables keep their descriptor spelling
in the contract while reads expose copied Python values or `None`:

```python
from x2py.contracts import Allocatable, Float64, Pointer

optional_scale: Allocatable[Float64]
selected_scale: Pointer[Float64]
```

Wrapper generation may synthesize native getter and setter bridge functions to
implement Python attribute reads and writes. Those functions are internal: they
are absent from the `.pyi` and are not exported as Python-callable procedures.
The post-IR policy stage separately decides the getter result policy, native
setter assignment mode, and Python setter exposure before wrapper planning. A
native value-copy setter can therefore exist for ABI use while Python
replacement is explicitly rejected, as for allocatable or derived fields.
Bridge and binding generation only dispatch those completed accessor decisions.

A mutable scalar module variable may include a literal default in an edited
`.pyi` contract:

```python
from x2py.contracts import Int32

counter: Int32 = 41
```

The default is an import-time native initializer, not a `Final` constant. When
the extension module is imported, x2py applies the value through the completed
native setter policy. Later reads and writes still use the current native module
storage. This initializer form is only for scalar module variables with a
write-through setter; non-scalar or read-only declarations remain explicit
wrapper-planning or code-generation errors instead of falling back to a copied Python
value.

Fortran `parameter` declarations are emitted as `Final[...]` constants when
their literal value can be represented in `.pyi`:

```python
from x2py.contracts import Final, Int32

nmax: Final[Int32] = 12
```

If a Fortran `parameter` initializer is an expression, generated `.pyi` emits a
default only after x2py has resolved that expression to a literal. Unresolved
native expressions are kept out of the active `.pyi` default:

```fortran
real, parameter :: c = cos(0.0)
```

```python
from x2py.contracts import Final, Float32

c: Final[Float32]
```

The source expression may remain available as native provenance metadata, but it
does not become an executable Python default unless a literal value is known.

No setter is generated for parameters. Python module namespaces remain ordinary
Python module namespaces, so assigning to `mod.nmax` can rebind that Python name
without modifying native Fortran state.

A derived-type `parameter` remains a `Final[DerivedType]` constant rather than
mutable module storage. When its fields have a complete value-copy policy, the
wrapper materializes a wrapper-owned copy from the native parameter and exposes
no native setter. Mutating that Python wrapper cannot modify the Fortran
parameter. Derived constants whose fields cannot be copied safely fail policy
completion explicitly instead of being treated as `Aliased` module variables.

<!-- X2PY_C_DOCS_START
Allocatable array function results and non-optional allocatable output array
arguments use owned-handle policy. The generated binding transfers the native
result into persistent standard C descriptor storage and the handle releases
that storage on `close()` or finalization; it does not return or copy a
compiler-private Fortran descriptor record. Optional allocatable output dummies
remain visible so the caller can omit them and make native `present(...)`
false.
X2PY_C_DOCS_END -->

Supported top-level allocatable writable descriptor arguments use
`Allocatable[T[...]]` handle policy. `| None` on the annotation means the handle
object itself may be absent for an optional native dummy. That spelling is only
valid on optional callable arguments. Passing a handle to a normal `T[...]`
argument is separate: the wrapper validates that the handle is allocated and
hands off the native array actual, without implicitly calling `h.to_numpy()`.

## Pointer Array Handles

Fortran pointer array facts are emitted and loaded with `Pointer[T[...]]`
handles:

```python
from x2py.contracts import Float64, Int32, Pointer

def sum_values(values: Pointer[Float64[:]]) -> Float64: ...
def choose_values(flag: Int32) -> Pointer[Float64[:]]: ...
```

The handle carries association state and descriptor operations:

- `p.associated` reports whether the pointer currently has a target.
- `p.to_numpy()` returns the current target view or `None`.
- `p.associate(other)` copies `other`'s association without copying data.
- `p.nullify()` is the default descriptor operation.
- `allocate(shape)`, `deallocate()`, and `resize(shape)` are exposed only when
  completed pointer policy allows them.

Direct pointer-array function results and nonoptional pointer-array
`intent(out)` outputs return owned `PointerArray` descriptor handles. Optional
outputs remain visible to preserve native absence, and `intent(inout)` remains
visible because its incoming association is part of the call.

When descriptor-backed extraction is enabled, `to_numpy()` builds NumPy shape and
strides from descriptor metadata and can expose strided pointer targets. If that
path is unavailable, the completed policy must choose a contiguous live view or
an explicit wrapper-planning diagnostic. It must not fall back to a copy. Pointer
handle ownership is descriptor or association access by default, not target
ownership.
The generated descriptor-view path establishes portable descriptor storage,
associates an `intent(out)` pointer dummy with the live target, and decodes the
descriptor synchronously. It does not inspect a compiler-private Fortran
descriptor layout.

## Visibility And Names

`@private` marks classes, functions and methods private:

```python
from x2py.contracts import Int32, private

@private
def helper(x: Int32) -> None: ...
```

`private[T]` marks a variable or argument private:

```python
from x2py.contracts import Float64, Int32, private

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
from x2py.contracts import Annotated, Int32, SourceName

var["class"]: Int32
def f(class_: Annotated[Int32, SourceName("class")]) -> None: ...
```

## Projection Metadata

`@native_call` is loaded and printed whenever the Python-visible signature
differs from the exact native signature, whether the projection was generated
from native projected-output behavior or written by the user:

```python
from x2py.contracts import Arg, Float64, Return, native_call

@native_call([Arg(0), Arg(0).shape[0], Return("result", 0)])
def normalize(values: Float64[:]) -> Float64: ...
```

Scalar address inputs use a Python-visible value type and an explicit native
address projection:

```python
from x2py.contracts import Addr, Arg, Int32, native_call

@native_call([Addr(Arg(0))])
def add_one(value: Int32) -> Int32: ...
```

Loaded projection entries:

| Entry | Meaning |
| --- | --- |
| `Arg(i)` | native argument is Python argument `i`'s default native representation |
| `Addr(Arg(i))` | native argument is the address of Python argument `i`'s call-local native scalar representation |
| `Value(Arg(i))` | exact rank-zero monomorphic wrapped derived object is passed to the native value dummy by the typed bridge |
| `Allocatable(Arg(i))`, `Pointer(Arg(i))` | native argument is a nullable call-local scalar descriptor initialized from Python argument `i`; `None` means present but unallocated or unassociated |
| `Return(i)` | native argument is supplied by projected return slot `i` as hidden writable storage passed by address |
| `Return("name", i)` | named native argument is supplied by projected return slot `i` as hidden writable storage passed by address |
| `Allocatable(Return(...))`, `Pointer(Return(...))` | native output dummy is a nullable scalar descriptor copied to the selected Python result slot |
| `Pass()` | implicit class instance: a method receiver or newly allocated constructor object |
| `Int32(1)`, `Float64(0.5)`, `Bool(False)`, `String[1]("N")` | hidden native literal with an explicit ABI type |
| `Len(Arg(i))`, `Len(Return(i))`, `Len(Work("name"))` | hidden native length metadata |
| `Arg(i).shape[d]`, `Return(i).shape[d]`, `Work("name").shape[d]` | hidden native shape metadata |
| `IsPresent(Arg(i))` | hidden native optional-presence metadata |
| `Work("name")` | hidden workspace value |

Hidden native literals must be typed call expressions inside `@native_call`.
`native_call` accepts one native-argument list and, when required, one
`result=Allocatable(Return(i))` or `result=Pointer(Return(i))` keyword. The
`result=` mapping describes the native function result and is not another native
dummy argument.
For nullable rank-zero outputs, use `Allocatable(Return("name", i))` or
`Pointer(Return("name", i))` in the native-argument list instead of a direct
allocatable function result.
Allocatable array function results can be direct returns or hidden output
dummies; both forms preserve unallocated handle state.
Bare literals such as `1` or `"N"` are rejected because they do not declare the
native ABI type. Fixed-length string literals must include their length, for
example `String[1]("N")`; plain `String("N")` is not enough.

Generated hidden-output mappings and existing backend-supported projection
entries are lowered into runtime calls. General allocation, coercion,
validation, and ownership transformations remain unsupported unless the
relevant backend explicitly implements them.

## Current Generated Coverage

Generated `.pyi` currently covers these exact-contract areas:

| Area | Generated behavior |
| --- | --- |
| Fortran intrinsic scalars | compiler-aware semantic dtype names |
| Native scope | module-leaf filename, or `@external` for standalone procedures |
| Functions/subroutines | declaration return shape, optional native rename, ABI argument order, and direct result |
| Hidden Fortran outputs | Python returns plus generated `@native_call` in native argument order |
| Scalar address inputs | Python-visible `T` plus `Addr(Arg(...))` native-call projection |
| Writable scalar storage | `T[()]`, or visible `T` plus projected replacement `Returns["name", T]` |
| Arrays | shaped storage with extents and strided axes; multidimensional order defaults from the selected native language |
| Module variables | direct module-level annotations; native accessors remain internal |
| Native array descriptor handles | `Allocatable[T[...]]` and `Pointer[T[...]]` handles for module variables, supported fields, and descriptor arguments; owned allocatable result handles; unallocated or unassociated state remains inside the handle |
| Constants | `Final[T]` module variables |
| Fortran derived types | classes with fields and methods; `@native_type` only for irreducible attributes or finalizers |
| Fortran defined operators | Python data-model methods plus explicit named-operator methods |
| Fortran defined assignment | explicit mutating `assign(...)` overloads |
| Opaque types | `Opaque` classes and owner-module dependency stubs |
| Imports | retained contract dependencies with aliases; source kind modules are omitted after dtype resolution |
| Callbacks | named `@prototype` declarations when source interfaces resolve |

<!-- X2PY_C_DOCS_START
| C primitive scalars | compiler-probed semantic dtype names when a target report is supplied |
| C and Fortran enums | module-level `Final[...]` integer constants |
| Fortran generic interfaces | explicit `@overload("specific")` links with C-extension dtype/rank dispatch |
| C structs/unions | `CStruct` and `CUnion` classes |
| C anonymous aggregate members | nested `CAnonymous` classes plus `CAnonymousMember` fields |
| Incomplete C callbacks | placeholder type that wrapper planning reports as incomplete |
X2PY_C_DOCS_END -->

Loaded but usually not generated from source today:

| Area | Loaded behavior |
| --- | --- |
| `Addr[n](T)` for `n > 1` | direct low-level pointer topology |
| `ORDER_ANY` | edited orientation-independent array contract |
| additional `@native_call` and `Returns[...]` edits | projection metadata beyond generated output mappings |
| source-provenance array helpers | compatibility loading for older or edited stubs |

## Rejected Or Not Yet Supported

The parser or post-IR policy-completion stage rejects contracts that would be
ambiguous, unsafe, or stale before wrapper lowering:

- `Unknown` semantic types.
- `Constant` or `Shape` as `Annotated` metadata.
- non-dimensional subscriptions such as `Float64[ORDER_F]`.
- `Addr[1](T)`.
- callable `Addr[n](T)` for `n > 1`; deeper pointer topology remains limited to
  low-level data declarations.
- callable `Addr(WrappedType)`, `Addr(String)`, or raw arrays with unresolved
  extents.
- `Addr(Arg(i))` for anything except a primitive scalar value, and all
  `Addr(Return(i))` or `Addr(Work("name"))` projections.
- untyped callable parameters.
- positional-only, keyword-only, vararg or kwarg function parameters, except
  for the generated derived-type constructor shape.
- nested enum declarations.
- ordinary function bodies instead of `...`.
- unsupported decorators other than `@private`, `@bind`, `@external`,
  `@native_call`, `@native_type`,
  `@overload("specific")`, the class-operator `generic=` form, `@raises`,
  `@hold_gil`, and `@staticmethod`.
- bare `@overload` or `typing.overload`; overload links require one concrete
  procedure name.
- `@overload(...)` combined with `@native_call(...)`; the linked concrete
  procedure owns native projection metadata.

## Remaining Format And Runtime Work

Ordered `@native_call` lowering, typed hidden outputs, array validation, and
completed ownership/action dispatch are implemented parts of the current
Fortran wrapper path. They are not future roadmap items.

Remaining public gaps include broader polymorphic `class(...)` representation,
pointer-return lifetime cases that still lack a provable owner, and clean
IDE/type-checker stubs that do not lose the semantic wrapper contract. The
[language feature matrix](../language-support/feature-matrix.md) is the
authoritative current support summary.

<!-- X2PY_C_DOCS_START
1. Make C and Fortran callbacks/procedure pointers first-class by preserving
   complete named prototypes from source.
2. Add explicit pointer ownership, borrow, nullability, output-buffer and
   copy/readback policy so pointer-heavy C APIs can move beyond blockers.
3. Strengthen Fortran character kind, hidden-length ABI, and `bind(c)`
   byte-string metadata beyond the existing `String[n]` fixed-length contract.
4. Expand aggregate layout metadata for C bitfields, C attributes, Fortran
   `bind(c)`, `sequence`, and by-value aggregate ABI checks.
X2PY_C_DOCS_END -->
