---
title: .pyi Format
audience: users, advanced users, developers
prerequisites: wrapper build workflow
related: index.md, pyi-contracts/index.md, ../language-support/fortran-support.md, ../language-support/c-support.md
status: maintained
publication: reviewed
---

# `.pyi` Format

A PRIK `.pyi` project is the editable contract between a native library and its
generated Python extension. It describes the Python namespace, native names,
types, storage, calls, ownership, and results. Both Fortran and C use this
format; language-specific forms are identified below.

The files use a checked subset of Python stub syntax. They are valid Python
syntax, but they carry native-wrapper information that ordinary type checkers
do not understand. Generate a starting contract instead of writing one from an
empty file:

```bash
python3 -m prik generate --pyi path/to/source.f90 --out contracts/source
python3 -m prik generate --pyi --language c path/to/api.h --out api.pyi
```

Then edit the generated contract and build from its entry file. The
[editing guide](pyi-contracts/index.md) explains the workflow; this page defines
the language.

Three support terms matter:

- **Accepted** means the `.pyi` loader understands the syntax.
- **Generated** means source conversion can write it.
- **Buildable** means current wrapper policy and lowering can implement it.

Accepted or generated syntax is not automatically buildable. Use [Fortran
Support](../language-support/fortran-support.md), [C
Support](../language-support/c-support.md), and the [feature
matrix](../language-support/feature-matrix.md) for the runtime boundary.

On a first read, follow the page from project structure through metadata. For
later lookup, jump to [Fortran and C forms](#fortran-and-c-forms-at-a-glance)
or the [complete keyword index](#complete-prikcontracts-index).

## Contract Project Structure

Start with the files PRIK generates. Fortran uses a contract package because
native modules and standalone procedures have different placement. C has no
native module scope, so C contract generation writes one `.pyi` file.

### Source-To-Contract Layout

**Fortran.** Suppose `solver.f90` contains one module procedure and one
standalone procedure, with their bodies omitted here:

```fortran
module solver_mod
contains
  subroutine solve()
  end subroutine
end module

subroutine reset()
end subroutine
```

Generate the contract package:

```bash
python3 -m prik generate --pyi solver.f90 --out contracts/solver
```

PRIK preserves the native placement:

```text
contracts/solver/
├── __init__.pyi      # imports solver_mod and declares @standalone reset
└── solver_mod.pyi    # declares the module procedure solve
```

With only standalone procedures, the package contains only `__init__.pyi`.
With only modules, `__init__.pyi` imports their leaf files and contains no
procedure declarations itself.

**C.** Suppose `api.h` contains two external function declarations:

```c
void solve(void);
void reset(void);
```

Generate one contract file:

```bash
python3 -m prik generate --pyi --language c api.h --out api.pyi
```

The result is:

```text
api.pyi               # declares solve and reset
```

C functions need no `@standalone`: they are already external symbols. The
filename organizes the contract and does not introduce a native C module.

The generated forms therefore have these responsibilities:

| Form | Responsibility |
| --- | --- |
| Fortran `__init__.pyi` | Package entry, public Python namespace, and standalone declarations. |
| Fortran `<module>.pyi` | Declarations contained by that native Fortran module. |
| C `<name>.pyi` | Selected C declarations in one directly buildable contract file. |

A contract build receives one entry `.pyi`: the package `__init__.pyi` for the
Fortran layout above, or the C file itself. Relative imports from a package
entry discover its leaf files.

### Entry Contract And Extension Identity

For a package entry, the directory name is the default extension name. This
entry:

```python
from . import solver_mod
from .types_mod import particle
```

produces a default extension named `solver`, with the public names
`solver.solver_mod` and `solver.particle`. `--out NAME` overrides the extension
name without changing native ownership recorded by the leaf files.

A single file can also be the entry:

```text
contracts/
└── api.pyi
```

Building `api.pyi` directly exposes its declarations at the extension root and
uses `api` as the default extension name.

Use the entry, not every imported leaf, on the command line:

```bash
python3 -m prik contracts/solver/__init__.pyi \
  --native-objects build/solver.o
```

A source-free C contract also needs its native language selected explicitly:

```bash
python3 -m prik --language c contracts/api.pyi \
  --native-c-sources native/api.c
```

### Root Export Contract

`__init__.pyi` uses ordinary relative-import forms to define the generated
Python namespace:

| Entry statement | Public effect for extension `solver` |
| --- | --- |
| `from . import solver_mod` | Exposes `solver.solver_mod`. |
| `from . import solver_mod as core` | Exposes the module as `solver.core`. |
| `from .solver_mod import solve` | Exposes `solver.solve`. |
| `from .solver_mod import solve as run` | Exposes `solver.run`. |
| `from .solver_mod import *` | Flattens all public names from that leaf. |

Aliases change the Python API only. They do not rename native modules, types,
or symbols. Conflicting wildcard exports are rejected; resolve them with
explicit imports and aliases.

### Contract Import Graph

PRIK parses contract files without executing them. Relative imports recursively
load sibling `.pyi` files or package `__init__.pyi` files. Missing files,
cycles, and conflicting exports fail before wrapper planning.

Absolute imports serve a different purpose:

- `from prik.contracts import ...` imports contract vocabulary.
- `from typing import ...` or another support import may help annotations.
- neither kind creates a contract-project edge or a Python extension export.

Every `prik.contracts` name must be imported explicitly. Wildcard imports from
`prik.contracts` are rejected. Aliases are supported:

```python
from prik.contracts import Flat as LayoutFlat, Float64

values: Float64[LayoutFlat]
```

### Contract Files And Native Procedure Placement

Fortran module leaves have native meaning: `solver_mod.pyi` describes native
module `solver_mod`. Renaming that leaf changes the module the generated bridge
imports. A declaration in the leaf is a contained module procedure unless it
has `@standalone`.

C has no Fortran-style module scope. In a C-native build, a file organizes the
contract and Python namespace; the declaration name or `@bind(...)` selects the
external C symbol. Use `--language c` to establish the C array defaults and ABI
policy.

Python export aliases never change either language's native placement.

### Contained Module Procedures

A Fortran procedure inside `solver_mod.pyi` is contained in native module
`solver_mod`:

```python
from prik.contracts import Float64

def update(value: Float64[()]) -> None: ...
```

The leaf filename supplies the native module. No placement decorator is needed.

### Standalone Procedures

A Fortran procedure outside every module uses `@standalone`:

```python
from prik.contracts import Float64, Int32, standalone

@standalone
def dgesv(a: Float64[:, :], b: Float64[:, :]) -> Int32: ...
```

`@standalone` changes native placement, not the Python name. Combine it with
`@bind("native_name")` when the declaration and native symbol names differ.
It is a Fortran form; C functions are already external C symbols.

### Imported Derived-Type Identity

Relative imports retain the owner of a wrapped or opaque type:

```python
from . import types_mod

def move(item: types_mod.particle) -> None: ...
```

`a_types.state` and `b_types.state` remain different native types even when
their final names match. An alias changes only the local Python spelling.

### Native Artifacts And Link Resolution

Contract filenames never imply object or library filenames. One entry may need
several objects and libraries, and one library may implement several contract
files. Supply native sources, objects, archives, shared libraries, module
directories, and ordered link items explicitly.

The [Build Manifests and Makefiles](configuration-files.md) reference explains
the persisted build plan. The [CLI reference](cli-commands.md#wrapper-builds)
lists the native artifact flags.

## File Shape

Inside a leaf, read from top to bottom: imports, module variables and constants,
classes, then functions and prototypes. This complete small leaf demonstrates
the normal shape:

```python
from prik.contracts import Final, Float64, Int32

MAX_STEPS: Final[Int32] = 100
iterations: Int32

class state:
    value: Float64

def advance(item: state, step: Float64) -> None: ...
```

The loader accepts these top-level statements:

- `import` and `from ... import ...`;
- annotated module variables and `Final[...]` constants;
- classes with annotated fields, nested classes, and stub methods;
- stub functions and exact `@prototype` declarations.

Function and method bodies must be exactly `...`. Ordinary statements,
executable assignments, enum classes, untyped parameters, `*args`, and
`**kwargs` are outside the format. The generated field constructor is the one
special keyword-only function shape documented below.

## Contract Imports

Every PRIK keyword used by a file comes from `prik.contracts`:

```python
from prik.contracts import Annotated, Float64, Immutable

value: Annotated[Float64, Immutable]
```

The loader follows the imported binding, so an alias remains a contract keyword
and an unimported same-named declaration remains a user symbol. Unknown or
unimported contract names are rejected instead of being interpreted by spelling.

## Module Variables

An annotated assignment declares native module state:

```python
from prik.contracts import Float64, Int32

counter: Int32
scale: Float64 = 2.0
```

Fortran module variables can be buildable getters, setters, constants, wrapped
objects, or descriptor handles according to their completed policy. A literal
default on supported mutable scalar state is an import-time native initializer.

C global declarations can be represented for inspection, but current C wrapper
builds reject native global state. C functions remain the supported runtime
surface.

### Constants And Enums

Constants use `Final[T]`:

```python
from prik.contracts import Final, Int32

MAX_SIZE: Final[Int32] = 256
UNKNOWN_SIZE: Final[Int32]
```

Fortran and C enumerators are also emitted as `Final[...]` integer constants.
The format does not define Python `Enum` classes, and C enum constants do not
become runtime C wrapper globals.

## Classes And Native ABI

An ordinary class describes a wrapped native type. Fields appear before methods
in generated files, although source order is accepted:

```python
from prik.contracts import Float64, Int32

class particle:
    identifier: Int32
    mass: Float64

    def reset(self) -> None: ...
```

An untyped leading `self` is the only untyped callable parameter. Ordinary
fields use the same type and storage syntax as variables.

Fortran `bind(C)` types retain that fact without exposing their layout:

```python
from prik.contracts import Float64, native_abi

@native_abi("c")
class point:
    x: Float64
    y: Float64
```

`@native_abi("c")` is Fortran-specific. A C-native contract already has a C
ABI and must not repeat it.

Class decorators and class-body decorators are:

| Decorator | Valid target | Language and meaning |
| --- | --- | --- |
| `@private` | Class | Shared: omit the class from the generated Python exports. |
| `@abstract` | Class | Fortran: native abstract type; no direct construction. |
| `@native_abi("c")` | Class | Fortran: original type is `bind(C)`. |
| `@abstractmethod` | Method | Fortran: deferred type-bound binding. |
| `@destroy` | Self-only method | Generated lifecycle operation, not a public Python method. May combine only with `@bind`. |
| `@staticmethod` | Method | Shared stub spelling for a method with no passed object. |

A generated default constructor is either self-only or keyword-only with
literal field defaults:

```python
from prik.contracts import Float64, Int32

class state:
    def __init__(
        self,
        *,
        identifier: Int32 = 0,
        scale: Float64 = 1.0,
    ) -> None: ...

    identifier: Int32 = 0
    scale: Float64 = 1.0
```

Removing that declaration removes public construction. A constructor bound to
a native initializer uses `@bind(...)` and exactly one `Pass()` in
`@native_call(...)`.

C aggregate markers preserve declarations for inspection:

| Base or marker | Meaning | C build status |
| --- | --- | --- |
| `CStruct` | C `struct`. | Inspection only. |
| `CUnion` | C `union`. | Inspection only. |
| `CAnonymous` | Nested anonymous C aggregate. | Inspection only. |
| `CAnonymousMember` | `Annotated` marker for the containing anonymous member. | Inspection only. |
| `Opaque` | Identity known, fields intentionally hidden. | Only explicitly supported opaque uses are buildable. |
| `OpaqueHandle`, `WrappedType` | Loaded compatibility/category names. | Not general C aggregate wrapper support. |

For example:

```python
from prik.contracts import CStruct, Int32, Opaque

class context(CStruct, Opaque):
    pass

class packet(CStruct):
    tag: Int32
```

Representing an aggregate does not make it callable by value or expose its
layout in a C wrapper.

## Functions, Methods And Returns

A function declaration contains typed positional parameters, an explicit
return annotation, and an ellipsis body:

```python
from prik.contracts import Float64

def scale(value: Float64, factor: Float64) -> Float64: ...
```

Supported return spellings are:

| Form | Meaning |
| --- | --- |
| `-> None` | No Python result. |
| `-> T` | One direct result. |
| `-> tuple[T1, T2]` | Several ordered Python results. |
| `-> Returns["name", T]` | Replacement result associated with a visible argument. |
| `-> Returns["name", T] | None` | Nullable replacement result. |

`Returns[...]` is a return annotation. `Return(...)` is a different helper used
inside `@native_call`; it names hidden native output storage.

Optional arguments use `= ...` or `= None` with an annotation that supports
absence. Optional descriptor handles also use `| None`. Positional-only,
keyword-only, variadic, and untyped parameters are rejected outside the
generated constructor form.

Methods use the same rules plus an untyped `self`. `Pass()` places that object
in an explicit native argument list. `@bind(...)` is needed only when the
Python declaration and native callable names differ.

### Function And Method Decorators

| Decorator | Valid target | Language and meaning |
| --- | --- | --- |
| `@private` | Function or method | Shared: declaration remains available to contract dependencies but is not exported. |
| `@bind("symbol")` | Function, method, constructor, prototype, or destructor | Shared: select a different native name. |
| `@native_abi("c")` | Function, method, or prototype | Fortran only: original declaration is `bind(C)`. |
| `@standalone` | Module-level function | Fortran only: native procedure is outside a module. |
| `@native_call([...], result=...)` | Function, method, or constructor | Shared: state the complete native argument order and optional native result mapping. |
| `@overload("specific", generic=...)` | Function or method | Shared: add one exact candidate to a generated Python overload set. |
| `@prototype` | Module-level function declaration | Fortran exact procedure interface used by callbacks or declaration expressions. |
| `@pure` | `@prototype` declaration | Fortran: preserve the native pure characteristic. |
| `@raises(status=..., message=..., success=...)` | Function or method | Shared: consume named status outputs and raise on non-success. |
| `@nogil` | Function or method | Shared: request GIL release around the completed native call. |
| `@abstractmethod` | Method | Fortran deferred binding. |
| `@destroy` | Self-only class-body declaration | Lifecycle operation; not exported as a method. |
| `@staticmethod` | Method | Python stub marker for a method without `self`. |

Decorators are validated in context. `@prototype` cannot combine with wrapper
decorators, `@overload` cannot combine with `@native_call`, and `@pure` requires
`@prototype`.

A status projection can hide its consumed output from the Python return:

```python
from prik.contracts import Arg, Float64, Hidden, Int32, native_call, raises

@raises(status="status", success=0)
@native_call([Arg(0), Hidden("status", Int32)])
def checked_scale(value: Float64) -> None: ...
```

### Generic Procedure Overloads

PRIK overloads link a public declaration to a concrete declaration in the same
scope. They are not `typing.overload`:

```python
from prik.contracts import Float64, Int32, overload, private

@private
def convert_int(value: Int32) -> Int32: ...

@private
def convert_real(value: Float64) -> Float64: ...

@overload("convert_int")
def convert(value: Int32) -> Int32: ...

@overload("convert_real")
def convert(value: Float64) -> Float64: ...
```

The linked concrete declaration owns `@native_call`. An overload-level
`@bind(...)` selects a public native generic when the specific itself is not the
link target. Runtime dispatch distinguishes exact scalar dtype, array element
dtype and rank, or wrapped class; it does not use implicit numeric coercion.

The optional `generic=` string preserves a Fortran operator spelling when the
Python method name is ambiguous, such as `.eqv.` versus `==`.

### Prototypes And Callbacks

`@prototype` declares an exact native procedure interface. Prototype arguments
use `In(T)`, `Out(T)`, or `InOut(T)` for direction. `Addr(T)` records primitive
reference transport and `Value(T)` records an explicit non-primitive value
dummy:

```python
from prik.contracts import Addr, Float64, In, InOut, Int32, prototype

@prototype
def update_values(
    count: In(Addr(Int32)),
    scale: In(Float64),
    values: InOut(Float64[:]),
) -> None: ...

def apply_update(callback: update_values) -> None: ...
```

`@pure` is valid only with `@prototype`. Calling a pure prototype name inside a
declaration expression identifies a standalone specification function. Current
callback wrapper support is Fortran-specific; C function pointers can be
inspected but are not buildable C callbacks.

### Defined Operators And Assignment

Fortran defined operators and assignment use ordinary class methods plus
`@overload(...)` links. Generated names include Python data-model methods such
as `__add__`, `__eq__`, and `__invert__`; a named method is also emitted when
Python has no matching operator. Defined assignment is exposed as a mutating
`assign(...)` method. C operator overloading is outside the C language and this
contract surface.

## Projection Metadata

Use `@native_call` when the Python signature does not already state the exact
native call: arguments are reordered, hidden, inserted, passed by address, or
projected into Python results.

The list is exhaustive and follows native argument order:

```python
from prik.contracts import Addr, Arg, Float64, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("status", 0), Addr(Arg(1))])
def solve(a: Float64, b: Float64) -> Int32: ...
```

Here Python receives `(a, b)` and returns `status`; the native procedure receives
`(address(a), status_storage, address(b))`.

### Native-Call Entries

| Entry | Meaning |
| --- | --- |
| `Arg(i)` | Use visible Python argument `i` in its default native representation. |
| `Addr(Arg(i))` | Pass the address of call-local primitive scalar storage. |
| `Value(Arg(i))` | Force primitive, `String[1]`, or supported wrapped scalar value transport. |
| `Return(i)` | Hidden native output storage mapped to Python result `i`. |
| `Return("name", i)` | Same, while preserving the native output name. |
| `Hidden("name", T)` | Typed native output consumed by another decorator and omitted from Python returns. |
| `Allocatable(Arg(i))`, `Pointer(Arg(i))` | Nullable scalar descriptor initialized from visible argument `i`. |
| `Allocatable(Return(...))`, `Pointer(Return(...))` | Nullable scalar descriptor output. |
| `Pass()` | Passed object for a method or newly allocated constructor instance. |
| `Int32(1)`, `Float64(0.5)`, `Bool(False)` | Typed hidden primitive literal. |
| `String[1]("N")` | Typed hidden one-character literal. |
| `Len(Arg(i))`, `Len(Return(i))`, `Len(Work("name"))` | Hidden native character length. |
| `Arg(i).shape[d]`, `Return(i).shape[d]`, `Work("name").shape[d]` | Hidden `SizeT` extent for axis `d`. |
| `Arg(i).strides[d]`, `Return(i).strides[d]`, `Work("name").strides[d]` | Hidden `SizeT` stride for axis `d`. |
| `Int32(Arg(i).shape[d])` | The same extent, materialized as the named integer type. |
| `IsPresent(Arg(i))` | Hidden optional-presence flag. |
| `Work("name")` | Named hidden workspace. |

The optional `result=` keyword maps the native function result. It accepts a
nullable descriptor result such as `result=Allocatable(Return(0))` or an exact
C scalar result described below.

`Addr(Arg(i))` is only for a visible primitive scalar value. Arrays, `T[()]`,
strings, raw addresses, handles, and wrapped objects already have storage or
handle representations and use `Arg(i)`. `Addr(Return(...))` and
`Addr(Work(...))` are rejected.

### Typed Computed Projections

A computed projection has no Python-visible annotation, so its default native
identity is `size_t` in C and `integer(c_size_t)` in Fortran. Wrap it in an
integer contract type when the native parameter is a different integer:

```python
from prik.contracts import Arg, Float64, Int32, native_call

@native_call([Int32(Arg(0).shape[0]), Arg(0)])
def scale(values: Float64[:]) -> None: ...
```

The binding materializes the extent as that type directly, and the generated
Fortran dummy becomes `integer(c_int32_t)`, so a default Fortran `integer`
parameter no longer has to stay visible in the Python signature.

The same form applies to `strides[d]` and `Len(...)`. Fixed-width signed and
unsigned integer contract types, plus `SizeT`, are accepted. The unresolved
`Int` and `UInt` names and all real, Boolean, and character types are rejected
during policy completion. The conversion is not range-checked, so an extent
wider than the stated type wraps rather than raising. Use a type that matches
the native parameter.

A character length has a compiler-fixed ABI. Restate it only when the native
declaration genuinely takes a different integer, not to change how PRIK passes
a Fortran hidden length.

A one-character literal such as `String[1]("N")` is a declaration, not a
conversion: it states the value the native parameter receives. It crosses the boundary as
an interoperable `char`, which a Fortran `character(len=1)` dummy accepts
directly, so a mode or flag character does not have to stay visible in the
Python signature. Its value must be a string containing exactly one character
representable as a C byte. Invalid values and longer fixed-length literals are
rejected during policy completion; the latter would need caller storage and a
separate length.

### Exact C Scalar Identities

C types can have the same NumPy dtype while remaining different native types.
Exact C scalar identities are valid only inside `@native_call` around `Arg(...)`
or `Return(...)`. Unlike a typed computed projection, they state what the native
parameter *is* rather than converting a produced value:

```python
from prik.contracts import Arg, CLongLong, Int64, Return, native_call

@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def convert(value: Int64) -> Int64: ...
```

The complete exact-name mapping is:

| Contract helper | Native C type | Contract helper | Native C type |
| --- | --- | --- | --- |
| `CBool` | `_Bool` | `CChar` | `char` |
| `CSignedChar` | `signed char` | `CUnsignedChar` | `unsigned char` |
| `CShort` | `short` | `CUnsignedShort` | `unsigned short` |
| `CInt` | `int` | `CUnsignedInt` | `unsigned int` |
| `CLong` | `long` | `CUnsignedLong` | `unsigned long` |
| `CLongLong` | `long long` | `CUnsignedLongLong` | `unsigned long long` |
| `CFloat` | `float` | `CDouble` | `double` |
| `CLongDouble` | `long double` | `CFloatComplex` | `float _Complex` |
| `CDoubleComplex` | `double _Complex` | `CLongDoubleComplex` | `long double _Complex` |

Generated C contracts emit a helper only when the public dtype alone would lose
the exact native identity.

## Semantic Type Names

Public annotations use PRIK contract names rather than source-language type
spellings. The selected compiler determines target-dependent mappings before a
contract is generated.

### Scalar And Special Types

| Family | Available names | Normal Python boundary |
| --- | --- | --- |
| Boolean | `Bool`, `Bool8`, `Bool16`, `Bool32`, `Bool64` | `bool` or `numpy.bool_`; arrays use `numpy.bool_`. |
| Signed integer | `Int`, `Int8`, `Int16`, `Int32`, `Int64` | Matching NumPy integer scalar or array dtype. `Int` retains target-dependent C `int` identity. |
| Unsigned integer | `UInt`, `UInt8`, `UInt16`, `UInt32`, `UInt64`, `SizeT` | Matching NumPy unsigned scalar or array dtype; `UInt` and `SizeT` are target-dependent. |
| Real | `Float16`, `Float32`, `Float64`, `Float128` | Matching NumPy real dtype when the selected target supports it. |
| Complex | `Complex64`, `Complex128`, `Complex256` | Matching NumPy complex dtype. |
| Text | `String` | Python `str` for scalar values or NumPy fixed-width bytes storage for arrays. |
| Low-level scalar vocabulary | `Byte`, `Char`, `CEnum`, `Void` | Primarily generated or inspection facts. Write `None` for no Python result; enum uses normally become resolved integer types. |
| Generic value | `Any` | Opaque value vocabulary; a build still needs explicit safe storage and ABI policy. |

`Float128` and `Complex256` describe the selected target's extended C floating
types, not a portable IEEE width promise. The [Data Types](../guide/data-types.md)
guide shows the Python and NumPy mappings.

`Matrix` and `Vector` are loaded compatibility/category names, not substitutes
for concrete array contracts. Author `T[:, :]` and `T[:]`. `OpaqueHandle` and
`WrappedType` are also compatibility/category names; normal wrapped types use
their declared class names.

User-defined and imported class names are valid annotations. `None` is the
no-result spelling and does not come from `prik.contracts`.

## Storage Contracts

The type name says what an element is; the surrounding syntax says how Python
stores or passes it:

| Contract | Meaning | Languages |
| --- | --- | --- |
| `T` | Scalar Python value or wrapped object. | Shared. |
| `T[()]` | Caller-owned rank-zero NumPy storage. | Shared. |
| `T[n]` | Rank-one array with extent `n`. | Shared. |
| `T[:]` | Rank-one array with runtime extent. | Shared. |
| `T[:, :]` | Rank-two array with runtime extents. | Shared. |
| `T[::]` | Rank-one stride-aware array. | Shared. |
| `T[...]` | Assumed-rank storage. | Accepted; build support is feature-specific. |
| `T[Flat]`, `T[n, Flat]` | Contiguous assumed-size/flat-edge storage. | Primarily Fortran and flat-buffer APIs. |
| `Addr(T)` | Python integer carrying a raw native address to `T`. | Shared low-level form. |
| `Addr[n](T)` | Pointer depth greater than one. | Loaded for low-level declarations; callable support is limited. |
| `Allocatable[T]`, `Pointer[T]` | Scalar Fortran descriptor value. | Fortran. |
| `Allocatable[T[...]]`, `Pointer[T[...]]` | Persistent native array descriptor handle. | Fortran. |
| `private[T]` | Private variable, field, or argument. | Shared visibility form. |

Multidimensional arrays default to `ORDER_F` in Fortran-native contracts and
`ORDER_C` in C-native contracts. An explicit order marker is written only when
the contract differs from that default.

### Array Storage And Declaration Expressions

Array dimensions use Python expression syntax:

| Dimension | Meaning |
| --- | --- |
| `:` | Runtime extent. |
| `n`, `3`, `n + 1` | Required extent expression. |
| `lower:upper` | Declared range expression. |
| `::` or `lower:upper:` | Runtime stride accepted on that axis. |
| `Flat` | One contiguous assumed-size edge; first or last concrete axis only. |
| `...` | Assumed rank. |

Expressions may refer to earlier scalar arguments, constants, array attributes,
and supported pure specification functions. `size(values, 2)`, for example,
becomes the second public extent. PRIK rejects expressions it cannot resolve
before lowering.

`Strided` is a compatibility spelling for older explicit forms such as
`T[::Strided]`; author the shorter `T[::]` form.

### Character Length And Shape

`String` uses the first subscription for character length and a second
subscription for storage shape:

| Contract | Length | Storage |
| --- | --- | --- |
| `String` or `String[...]` | Assumed | Scalar Python `str`. |
| `String[n]` | Fixed `n` | Scalar Python `str`. |
| `String[:]` | Deferred | Scalar descriptor value, with `Allocatable` or `Pointer` policy. |
| `String[n][()]` | Fixed `n` | Rank-zero NumPy bytes storage. |
| `String[n][:]` | Fixed `n` | Rank-one NumPy bytes array. |
| `String[:][:]` | Deferred | Rank-one character array contract. |

A single `String[...]` subscription is always a length, never an array shape.
PRIK does not silently pad or truncate a fixed-length public `str`.

### Python And Native Boundaries

`T` describes the Python value; `@native_call` can refine how it reaches the
native procedure. A bare numeric scalar normally passes by value.
`Addr(Arg(i))` creates call-local scalar storage and passes its address.
`T[()]` and ranked arrays already expose storage and use `Arg(i)`.

Raw `Addr(T)` is different: the Python caller supplies the integer address
itself. Wrapped class annotations pass generated wrapper instances and their
completed native handle.

For C, a pointer annotation alone cannot determine whether Python should see a
scalar address, rank-zero storage, an array, a result, or an opaque address.
Express that choice with `Addr(T)`, `T[()]`, `T[...]`, `Returns[...]`, and
`@native_call` as described in [C Support](../language-support/c-support.md).

### Allocatable Array Handles

`Allocatable[T[...]]` represents a persistent Fortran allocatable descriptor,
not a NumPy array. The handle reports allocation state and provides
`to_numpy()`, `allocate(...)`, `deallocate()`, and `resize(...)` only when the
completed policy allows them.

```python
from prik.contracts import Allocatable, Float64

workspace: Allocatable[Float64[:]]
def make_matrix() -> Allocatable[Float64[:, :]]: ...
```

`to_numpy()` returns `None` when unallocated and otherwise returns a live view.
Native reallocation can invalidate an older view; copy it when independent
lifetime is required.

An optional dummy handle uses `Allocatable[T[...]] | None = ...`. `None` means
the optional dummy is absent; unallocated state remains inside a present handle.

### Pointer Array Handles

`Pointer[T[...]]` represents a persistent Fortran pointer descriptor:

```python
from prik.contracts import Float64, Pointer

selection: Pointer[Float64[:]]
def choose() -> Pointer[Float64[:]]: ...
```

The handle exposes association state, `to_numpy()`, `associate(...)`, and
`nullify()`. Allocation, deallocation, and resizing appear only when the full
`PointerPolicy(...)` permits them. A returned NumPy array is a live target view,
not an implicit copy.

## Metadata With `Annotated`

`Annotated[T, ...]` adds facts to a type without changing its public element
type. Metadata falls into four groups.

### Layout, Provenance, And Mutability

| Metadata | Meaning | Normal use |
| --- | --- | --- |
| `ORDER_C`, `ORDER_F`, `ORDER_ANY` | Array orientation. | Author only when it differs from the language default, or when either order is intended. |
| `COPY_F` | Accept C-order Python storage, use an F-order temporary, and copy back visible mutation. | Focused multidimensional array support. |
| `Contiguous` | Native declaration promises contiguity. | Loaded source-provenance/compatibility fact. |
| `Aliased` | Native storage is addressable or may be exposed as an alias. | Fortran `target` and borrowed native objects. |
| `Immutable` | Python-visible value is replace-only, not mutated in place. | Requires a compatible replacement/copy policy for writable native storage. |
| `Polymorphic` | Fortran native declaration is `class(T)`. | Fortran. |
| `AssumedType` | Fortran native declaration is assumed type. | Accepted/generated where source semantics require it; wrapper support is limited. |
| `MaybeUnallocated` | Direct allocatable array function result can be unallocated. | Valid only on that result form. |
| `PointerAssociation("runtime")` | Pointer association is runtime state. | Fortran pointer facts. |
| `SourceName("native-name")` | Preserve a native name that the Python identifier cannot represent. | Shared. |
| `ArrayCategory("...")`, `FortranAllocatable` | Older source-provenance spellings. | Loaded compatibility; use active storage syntax for authored contracts. |
| `CAnonymousMember` | Field is the containing member for a nested anonymous C aggregate. | C inspection contracts. |

### Constraints

`Bounded(...)`, `Finite`, and `Range(...)` are available constraint markers.
Unknown unimported names and positional calls can also round-trip as
project-specific constraints. A constraint is enforced only by a stage that
documents support for it; its presence alone does not invent runtime validation.

```python
from prik.contracts import Annotated, Bounded, Finite, Float64

value: Annotated[Float64, Bounded(0.0, 1.0), Finite]
```

### Ownership, Transfer, And Destruction Policies

The ownership triple is explicit:

```python
from prik.contracts import Annotated, Destruction, Float64, Ownership, Transfer

values: Annotated[
    Float64[:],
    Ownership("caller"),
    Transfer("in_place"),
    Destruction("caller"),
]
```

Accepted policy names are:

| Helper | Values |
| --- | --- |
| `Ownership(...)` | `python`, `native`, `wrapper`, `caller`, `temporary`, `unknown` |
| `Transfer(...)` | `by_value`, `call_local`, `in_place`, `copy_return`, `snapshot_copy`, `borrowed_view`, `wrapper_instance`, `blocked` |
| `Destruction(...)` | `python_refcount`, `wrapper_dealloc`, `native_owner`, `caller`, `call_local`, `none`, `blocked` |

The combination must describe one safe lifetime. For example, writable
`Immutable` storage cannot also request a writable `borrowed_view`.

### Pointer Policy

`PointerPolicy(...)` is keyword-only and requires all ten facts:

```python
from prik.contracts import Annotated, Float64, Pointer, PointerPolicy

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

The loader preserves project-specific string values, and wrapper policy checks
whether the requested operations and lifetime are implemented.

## Visibility And Names

`@private` hides classes, functions, and methods. `private[T]` hides variables,
fields, or arguments:

```python
from prik.contracts import Float64, Int32, private

hidden_value: private[Float64]

@private
def helper(value: Int32) -> None: ...
```

Names that are invalid Python identifiers use `var[...]` for data or
`SourceName(...)` for callable arguments:

```python
from prik.contracts import Annotated, Int32, SourceName

var["class"]: Int32
def consume(class_: Annotated[Int32, SourceName("class")]) -> None: ...
```

`@bind(...)` changes a native callable name. Root imports and aliases change a
Python export name. `SourceName(...)` preserves a native data or argument name.
These are separate operations.

When PRIK generates a Fortran contract, it lowercases Fortran identifiers,
adds a trailing underscore to Python keywords, normalizes other invalid Python
identifiers, and gives remaining collisions deterministic numeric suffixes.
The same policy covers module members, classes, methods, fields, and argument
names. `--strict-wrapper-names` rejects a generated name that would need any of
these fixes.

Fortran `bind(C, name=...)` changes the native symbol, not the Python name. In
an edited contract, `@bind("native_name")` records that native-name distinction;
entry-contract imports and aliases shape the public Python namespace.

## Fortran And C Forms At A Glance

| Contract area | Fortran | C |
| --- | --- | --- |
| Native language selection | Inferred from normal Fortran `.pyi` generation/build context. | Pass `--language c` for a source-free contract. |
| Native scope | Leaf filename is native module; `@standalone` marks external procedures. | Functions are external symbols; file/import structure organizes the contract and Python API. |
| Default multidimensional order | `ORDER_F`. | `ORDER_C`. |
| Scalar reference input | Generated visible `T` plus `Addr(Arg(i))`, or explicit `T[()]` storage. | Pointer meaning must be authored as scalar address, storage, array, output, or raw address. |
| ABI marker | `@native_abi("c")` preserves Fortran `bind(C)`. | Invalid because C language identity already supplies the ABI. |
| Exact native scalar identity | Usually carried by resolved Fortran type/kind. | C cast helpers inside `@native_call` preserve spelling such as `long long`. |
| Classes | Wrapped derived types, fields, methods, inheritance, constructors, finalizers. | Struct/union/anonymous/opaque classes are currently inspection forms, not aggregate wrappers. |
| Module variables | Supported Fortran module-state subset. | Native C globals are inspection-only. |
| Callbacks/prototypes | Supported Fortran callback subset through `@prototype`. | C function pointers are not currently buildable callbacks. |
| Arrays and strings | Full documented Fortran wrapper mechanisms. | Primitive C-contiguous arrays and rank-zero strings in the documented C subset. |

### Fortran Wrapper Contracts

Generated Fortran contracts can contain module leaves, `@standalone`
procedures, `@native_abi("c")`, derived classes, module variables, descriptor
handles, callbacks, generics, defined operators, and projected outputs. The
[Fortran User Guide](../guide/index.md) describes the runtime behavior behind
those spellings.

### C Source Inspection Contracts

C generation can describe primitive functions and pointers, constants, exact
scalar identities, structs, unions, anonymous aggregates, opaque declarations,
and function-pointer placeholders. Current C wrapper builds implement only the
documented primitive scalar, pointer/array, string, projection, status, rename,
and overload subset. Aggregate, global-state, and callback declarations remain
inspection forms and fail before wrapper planning.

## Complete `prik.contracts` Index

This index accounts for every public import name. Importability means the
contract parser recognizes the name; the sections above state where it is
valid and whether it is buildable.

| Group | Public names |
| --- | --- |
| Typing forms | `Annotated`, `Any`, `Final` |
| Scalar types | `Bool`, `Bool8`, `Bool16`, `Bool32`, `Bool64`, `Byte`, `CEnum`, `Char`, `Complex64`, `Complex128`, `Complex256`, `Float16`, `Float32`, `Float64`, `Float128`, `Int`, `Int8`, `Int16`, `Int32`, `Int64`, `SizeT`, `String`, `UInt`, `UInt8`, `UInt16`, `UInt32`, `UInt64`, `Void` |
| Storage and result types | `Addr`, `Allocatable`, `Pointer`, `Returns`, `private` |
| Compatibility/category types | `Matrix`, `Vector`, `OpaqueHandle`, `WrappedType` |
| Class and C inspection markers | `CAnonymous`, `CAnonymousMember`, `CStruct`, `CUnion`, `Opaque` |
| Shape and layout markers | `Contiguous`, `COPY_F`, `Flat`, `ORDER_ANY`, `ORDER_C`, `ORDER_F`, `Strided` |
| General metadata | `Aliased`, `ArrayCategory`, `AssumedType`, `FortranAllocatable`, `Immutable`, `MaybeUnallocated`, `Polymorphic`, `SourceName` |
| Constraints and ownership | `Bounded`, `Finite`, `Range`, `Ownership`, `Transfer`, `Destruction`, `PointerAssociation`, `PointerPolicy` |
| Prototype direction | `In`, `Out`, `InOut` |
| Native-call helpers | `Arg`, `Hidden`, `IsPresent`, `Len`, `Pass`, `Return`, `Value`, `Work` |
| Exact C scalar helpers | `CBool`, `CChar`, `CSignedChar`, `CUnsignedChar`, `CShort`, `CUnsignedShort`, `CInt`, `CUnsignedInt`, `CLong`, `CUnsignedLong`, `CLongLong`, `CUnsignedLongLong`, `CFloat`, `CDouble`, `CLongDouble`, `CFloatComplex`, `CDoubleComplex`, `CLongDoubleComplex` |
| Decorators | `abstract`, `abstractmethod`, `bind`, `destroy`, `native_abi`, `native_call`, `nogil`, `overload`, `private`, `prototype`, `pure`, `raises`, `standalone` |

`staticmethod` is supported Python syntax for methods but is not exported by
`prik.contracts`.

## Current Generated Coverage

| Area | Fortran generation | C generation |
| --- | --- | --- |
| Project layout | Entry plus native-module leaves; compact standalone entry when applicable. | One contract file per selected source or declaration owner. |
| Primitive types | Compiler-resolved kinds and storage names. | Compiler-probed types plus exact C identity helpers when needed. |
| Functions | Module and standalone procedures, results, outputs, callbacks, overloads. | Functions, primitive pointers, projections, renames, and overload candidates. |
| Arrays and strings | Shapes, order, striding, characters, allocatable and pointer descriptors. | C-order array facts and conservative pointer/string starter contracts. |
| Classes | Derived types, fields, methods, constructors, inheritance, abstract/final roles. | Struct, union, anonymous, and opaque inspection classes. |
| Variables/constants | Module variables, parameters, and enum constants. | Global and enum/macro constant inspection declarations. |

Generated output is a conservative starting point. C pointer meaning and any
ownership or Pythonic result projection that native syntax cannot prove must be
authored explicitly.

## Rejected Or Not Yet Supported

The loader rejects malformed language forms before wrapper planning:

- missing imports for `prik.contracts` names;
- unknown types, metadata expressions, decorators, or decorator arguments;
- ordinary function bodies, untyped parameters, `*args`, and `**kwargs`;
- positional-only or keyword-only functions outside the generated constructor;
- Python enum classes instead of `Final[...]` integer constants;
- `typing.overload` instead of PRIK `@overload("specific")`;
- `@overload` combined with `@native_call`;
- `@pure` without `@prototype`;
- `@native_abi(...)` outside Fortran or with a value other than `"c"`;
- incomplete, duplicated, or out-of-range `@native_call` entries;
- untyped hidden literals inside `@native_call`;
- redundant or contradictory layout, storage, mutability, and ownership facts.

Accepted inspection syntax can still be rejected by wrapper policy. Important
examples are C aggregates, globals, callbacks, multi-level pointers, nullable
or retained pointer contracts, and Fortran forms whose ownership or ABI cannot
be completed safely.

## Misuse, Diagnostics And Risk

Failures occur at the first stage that owns the invalid fact: file syntax and
imports while loading, declaration relationships during contract validation,
ownership and ABI support during policy completion, and binary mismatches while
compiling, linking, or importing. Diagnostics include the contract path and
declaration when available.

PRIK never falls back to reparsing native source when a `.pyi` contract omits a
required fact. The edited contract is authoritative, so an incorrect type,
shape, native symbol, ownership, or projection can describe an incorrect native
call. Start from generated output, make focused edits, rebuild, and execute the
changed path once.

## Remaining Format And Runtime Work

The format is broader than current runtime support. Remaining areas include
broader polymorphism, pointer lifetime cases without a provable owner, C
aggregate and callback wrapping, and separate IDE-oriented stubs that do not
lose native contract information. The [feature
matrix](../language-support/feature-matrix.md) records the supported boundary.

## Evidence

The maintained language evidence lives in
[`tests/fortran/infrastructure/semantic_pyi/`](../../../tests/fortran/infrastructure/semantic_pyi/)
and
[`tests/c/infrastructure/semantic_pyi/`](../../../tests/c/infrastructure/semantic_pyi/).
The [contract coverage map](../../../tests/fortran/CONTRACT_COVERAGE.md) links
individual language areas to focused and end-to-end evidence.
