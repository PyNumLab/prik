---
title: Semantic IR Reference
audience: advanced users, developers
prerequisites: parser references, native datatype model
related: index.md
status: maintained
publication: draft
---

# Semantic IR Reference

Semantic IR is the language-neutral model that every input route converges on.
This page is its datatype and conversion contract: the stable semantic type
names, how Fortran and C spellings map onto them, and what the `.pyi` surface
adds or leaves out. It describes current behavior only.

It is the reference behind `python3 -m prik semantics` output and the type
names that appear in generated contracts. For the surrounding contracts, see
the [Semantic `.pyi` Format](semantic-pyi-format.md) for file syntax, the
[Fortran Wrapper Reference](fortran-wrapper.md) for the Fortran runtime
contract, and [C Support](../language-support/c-support.md) for the supported
C wrapping surface.

## Datatype Mapping

One scalar datatype policy is shared by both frontends. These semantic names
are the stable bridge between a native type spelling, the `.pyi` contract, and
the NumPy dtype a caller must pass.

### Semantic Names

| Semantic dtype | NumPy equivalent | Notes |
| --- | --- | --- |
| `Bool` | `numpy.bool_` | Boolean scalar; `Bool8`, `Bool16`, `Bool32`, and `Bool64` name the native storage width. |
| `Int8`, `Int16`, `Int32`, `Int64` | `numpy.int8`, `numpy.int16`, `numpy.int32`, `numpy.int64` | Signed integers. |
| `UInt8`, `UInt16`, `UInt32`, `UInt64` | `numpy.uint8`, `numpy.uint16`, `numpy.uint32`, `numpy.uint64` | Unsigned integers. |
| `Float32`, `Float64` | `numpy.float32`, `numpy.float64` | Binary floating-point scalars. |
| `Float128` | `numpy.longdouble` | Platform precision varies; `numpy.float128` is not portable. |
| `Complex64`, `Complex128` | `numpy.complex64`, `numpy.complex128` | Complex scalars. |
| `Complex256` | `numpy.clongdouble` | Platform precision varies. |
| `String` | `numpy.str_` or byte storage at ABI boundary | Character policy depends on wrapper ABI. |
| `SizeT` | `numpy.uintp` | Target width is compiler-probed when available. |
| `Any` | `object` | Used for void pointer pointees and intentionally opaque values. |
| `Int` | Target-dependent signed NumPy integer | Ordinary C `int`; the concrete `Int16`/`Int32`/`Int64` dtype and compiler fact are stored separately. |

### Fortran Intrinsics

| Fortran spelling or kind | Semantic dtype | NumPy equivalent |
| --- | --- | --- |
| Unqualified `integer`, `real`, `complex` | Compiler-probed default storage | Matching NumPy numeric dtype |
| Numeric kinds such as `kind=4/8/16` and `kind(...)` expressions | Compiler-probed kind storage | Matching NumPy numeric dtype |
| `integer(int8/int16/int32/int64)` | `Int8` / `Int16` / `Int32` / `Int64` | Matching NumPy signed integer |
| `real(real32/real64/real128)` | `Float32` / `Float64` / `Float128` | Matching NumPy real dtype |
| `complex(real32/real64/real128)` | `Complex64` / `Complex128` / `Complex256` | Matching NumPy complex dtype |
| `double precision`, `double complex` | Compiler-probed double-kind storage | Matching NumPy real or complex dtype |
| Legacy numeric `type*N`, such as `integer*8`, `real*8`, `complex*16`, `logical*1` | Fixed `N`-byte total storage | Matching NumPy dtype |
| Legacy `character*N`, `character*(*)` | `String`; `N`/`*` is length, not kind | `numpy.str_` or ABI byte storage |
| `procedure(...)` | `Procedure` | Callback/interface policy |
| `iso_c_binding` numeric kinds | Compiler-probed interoperable storage | Matching NumPy numeric dtype |
| `logical`, `logical(kind=1/2/4/8)`, `logical(c_bool)` | `Bool` | `numpy.bool_` |
| `character`, `character(len=n)`, `character(kind=1)`, `character(kind=c_char)` | `String` | `numpy.str_` or ABI byte storage |

Compiler-backed Fortran semantic CLI stages measure the storage of every
intrinsic type used by the source after resolving kind expressions. This is
required because default and numeric kind mappings are processor-dependent and
flags such as `-fdefault-real-8` can change them. Results are cached by exact
compiler identity, target flags, expressions, environment, and runner.
Legacy numeric `type*N` extensions carry fixed total storage and therefore do
not need a compiler probe. In particular, `complex*8` is an 8-byte
`Complex64`, while modern `complex(kind=8)` is a compiler kind that is
`Complex128` on the documented `gfortran` target. `DOUBLE PRECISION` and
`DOUBLE COMPLEX` remain compiler-dependent and use the cached probe.
Direct converter calls without compiler facts retain the current GitHub
Actions `gfortran` profile as a fallback. Explicit `iso_fortran_env` kinds are
preferred when a portable source contract needs a fixed precision.

### C Types

| C spelling or parser type | Semantic dtype | NumPy equivalent |
| --- | --- | --- |
| `_Bool` / `CBool` | `Bool` | `numpy.bool_` |
| `char` | Target-probed `Int8` or `UInt8` | Matching NumPy integer |
| `signed char`, `unsigned char` | Target-probed signed or unsigned width | Matching NumPy integer |
| `short`, `unsigned short` | Target-probed signed or unsigned width | Matching NumPy integer |
| `int` / `CInt` | `Int` with concrete probed dtype | Matching signed NumPy integer for the target |
| `unsigned int`, `long`, `unsigned long`, `long long`, `unsigned long long` | Target-probed integer width and signedness | Matching NumPy integer |
| `float`, `double`, `long double` | Target-probed storage width | Matching NumPy real dtype |
| `float _Complex`, `double _Complex`, `long double _Complex` | Target-probed storage width | Matching NumPy complex dtype |
| `int8_t`, `int16_t`, `int32_t`, `int64_t` | `Int8`, `Int16`, `Int32`, `Int64` | Matching signed NumPy integer |
| `uint8_t`, `uint16_t`, `uint32_t`, `uint64_t` | `UInt8`, `UInt16`, `UInt32`, `UInt64` | Matching unsigned NumPy integer |
| `size_t` | `SizeT` or probed unsigned width | `numpy.uintp` or matching `numpy.uint*` |

C primitive spellings are ABI-dependent. Compiler-backed C semantic CLI stages
automatically probe the selected compiler target and use those facts for every
modeled arithmetic primitive. Ordinary C `int` keeps the stable semantic
identity `Int`; its concrete dtype and the compiler fact used to derive it are
stored on `SemanticType`. Other primitive names and dtypes follow the measured
target width and signedness. NumPy is the consumer-side dtype mapping, not the
probe source: it describes the Python interpreter host and may differ from a
selected compiler target or sysroot.

Direct converter calls without a supplied report retain the documented
fallback mappings. A supplied target fact whose width has no semantic dtype
mapping produces `c_unsupported_primitive_abi` instead of silently using a
different width.

### Generated Linux x86_64 Mapping Example

The tables below are the output of the probe commands on the `linux-x86_64`
profile used by GitHub Actions. They come from the same compiler-backed code
paths the wrapper uses, so run the command for your own target rather than
relying on this snapshot; the numbers change with the compiler and flags.

C uses `cc` to measure primitive storage, signedness, alignment, and floating
precision:

```bash
python3 -m prik probe --language c --compiler cc
```

```markdown
Target profile: `linux-x86_64`

| C type | Native target fact | Semantic dtype | NumPy dtype |
| --- | --- | --- | --- |
| `_Bool` | 8-bit bool | `Bool8` | `numpy.bool_` |
| `char` | signed 8-bit | `Int8` | `numpy.int8` |
| `signed char` | signed 8-bit | `Int8` | `numpy.int8` |
| `unsigned char` | unsigned 8-bit | `UInt8` | `numpy.uint8` |
| `short` | signed 16-bit | `Int16` | `numpy.int16` |
| `unsigned short` | unsigned 16-bit | `UInt16` | `numpy.uint16` |
| `int` | signed 32-bit | `Int (Int32 storage)` | `numpy.int32` |
| `unsigned int` | unsigned 32-bit | `UInt32` | `numpy.uint32` |
| `long` | signed 64-bit | `Int64` | `numpy.int64` |
| `unsigned long` | unsigned 64-bit | `UInt64` | `numpy.uint64` |
| `long long` | signed 64-bit | `Int64` | `numpy.int64` |
| `unsigned long long` | unsigned 64-bit | `UInt64` | `numpy.uint64` |
| `float` | 32-bit storage, 24-bit precision | `Float32` | `numpy.float32` |
| `double` | 64-bit storage, 53-bit precision | `Float64` | `numpy.float64` |
| `long double` | 128-bit storage, 64-bit precision | `Float128` | `numpy.longdouble` |
| `float _Complex` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `double _Complex` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `long double _Complex` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `size_t` | unsigned 64-bit | `UInt64` | `numpy.uint64` |
```

Fortran uses the same cached compiler probe as normal semantic conversion and
the standard `storage_size` intrinsic to measure compiler-dependent modern and
double-kind forms. The generated table also lists legacy spellings; numeric
`type*N` rows use their fixed total storage, and character-star rows show
length syntax rather than a different character kind:

```bash
python3 -m prik probe --language fortran --compiler gfortran
```

```markdown
Target profile: `linux-x86_64`

| Fortran type | Native target fact | Semantic dtype | NumPy dtype |
| --- | --- | --- | --- |
| `integer` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer(kind=1)` | 8-bit storage | `Int8` | `numpy.int8` |
| `integer(kind=2)` | 16-bit storage | `Int16` | `numpy.int16` |
| `integer(kind=4)` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer(kind=8)` | 64-bit storage | `Int64` | `numpy.int64` |
| `integer(int8)` | 8-bit storage | `Int8` | `numpy.int8` |
| `integer(int16)` | 16-bit storage | `Int16` | `numpy.int16` |
| `integer(int32)` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer(int64)` | 64-bit storage | `Int64` | `numpy.int64` |
| `integer(c_signed_char)` | 8-bit storage | `Int8` | `numpy.int8` |
| `integer(c_short)` | 16-bit storage | `Int16` | `numpy.int16` |
| `integer(c_int)` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer(c_long)` | 64-bit storage | `Int64` | `numpy.int64` |
| `integer(c_long_long)` | 64-bit storage | `Int64` | `numpy.int64` |
| `integer(c_size_t)` | 64-bit storage | `Int64` | `numpy.int64` |
| `integer(c_int8_t)` | 8-bit storage | `Int8` | `numpy.int8` |
| `integer(c_int16_t)` | 16-bit storage | `Int16` | `numpy.int16` |
| `integer(c_int32_t)` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer(c_int64_t)` | 64-bit storage | `Int64` | `numpy.int64` |
| `real` | 32-bit storage | `Float32` | `numpy.float32` |
| `real(kind=4)` | 32-bit storage | `Float32` | `numpy.float32` |
| `real(kind=8)` | 64-bit storage | `Float64` | `numpy.float64` |
| `real(kind=16)` | 128-bit storage | `Float128` | `numpy.longdouble` |
| `real(real32)` | 32-bit storage | `Float32` | `numpy.float32` |
| `real(real64)` | 64-bit storage | `Float64` | `numpy.float64` |
| `real(real128)` | 128-bit storage | `Float128` | `numpy.longdouble` |
| `real(c_float)` | 32-bit storage | `Float32` | `numpy.float32` |
| `real(c_double)` | 64-bit storage | `Float64` | `numpy.float64` |
| `real(c_long_double)` | 128-bit storage | `Float128` | `numpy.longdouble` |
| `real(kind(1.0e0))` | 32-bit storage | `Float32` | `numpy.float32` |
| `real(kind(1.0d0))` | 64-bit storage | `Float64` | `numpy.float64` |
| `real(kind(1.0q0))` | 128-bit storage | `Float128` | `numpy.longdouble` |
| `complex` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex(kind=4)` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex(kind=8)` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `complex(kind=16)` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `complex(real32)` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex(real64)` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `complex(real128)` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `complex(c_float_complex)` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex(c_double_complex)` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `complex(c_long_double_complex)` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `complex(kind=kind(1.0e0))` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex(kind=kind(1.0d0))` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `complex(kind=kind(1.0q0))` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `logical` | 32-bit storage | `Bool32` | `numpy.bool_` |
| `logical(kind=1)` | 8-bit storage | `Bool8` | `numpy.bool_` |
| `logical(kind=2)` | 16-bit storage | `Bool16` | `numpy.bool_` |
| `logical(kind=4)` | 32-bit storage | `Bool32` | `numpy.bool_` |
| `logical(kind=8)` | 64-bit storage | `Bool64` | `numpy.bool_` |
| `logical(c_bool)` | 8-bit storage | `Bool8` | `numpy.bool_` |
| `character` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character(len=n)` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character(kind=1)` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character(kind=c_char)` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `integer*1` | 8-bit storage | `Int8` | `numpy.int8` |
| `integer*2` | 16-bit storage | `Int16` | `numpy.int16` |
| `integer*4` | 32-bit storage | `Int32` | `numpy.int32` |
| `integer*8` | 64-bit storage | `Int64` | `numpy.int64` |
| `real*4` | 32-bit storage | `Float32` | `numpy.float32` |
| `real*8` | 64-bit storage | `Float64` | `numpy.float64` |
| `real*16` | 128-bit storage | `Float128` | `numpy.longdouble` |
| `double precision` | 64-bit storage | `Float64` | `numpy.float64` |
| `complex*8` | 64-bit storage | `Complex64` | `numpy.complex64` |
| `complex*16` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `complex*32` | 256-bit storage | `Complex256` | `numpy.clongdouble` |
| `double complex` | 128-bit storage | `Complex128` | `numpy.complex128` |
| `logical*1` | 8-bit storage | `Bool8` | `numpy.bool_` |
| `logical*2` | 16-bit storage | `Bool16` | `numpy.bool_` |
| `logical*4` | 32-bit storage | `Bool32` | `numpy.bool_` |
| `logical*8` | 64-bit storage | `Bool64` | `numpy.bool_` |
| `character*1` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character*8` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character*(*)` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
```

## C To Semantic IR Mapping

Status: first C semantic conversion subset implemented in `prik/semantics/c2ir.py`.
The converter consumes `c_parser` models and emits the same language-neutral
semantic IR used by Fortran and edited `.pyi` files. Shared primitive dtype
policy is documented in the datatype mapping section above.

### Supported Identity Subset

- C translation unit -> one `SemanticModule` named from the source file stem.
- C function -> `SemanticFunction`, preserving native name and parameter order.
- C parameter -> `SemanticArgument`.
- C global variable -> `SemanticVariable`.
- C struct/union field -> `SemanticField`.
- `void` return -> `None`.
- `_Bool` -> `Bool`.
- All modeled primitive integer, real, and complex spellings consume supplied
  `prik.preprocessing.probes.c_types` facts. Plain `char` signedness, integer widths, real
  storage widths and precision metadata, and complex storage widths come from
  the selected compiler target.
- `int` keeps semantic name `Int` while its concrete dtype follows the target.
  Other primitive semantic names and dtypes become the measured width-specific
  `Int*`, `UInt*`, `Float*`, or `Complex*` name.
- Direct converter calls without a report retain the earlier Linux-oriented
  primitive fallbacks; C semantic CLI stages supply a cached target report
  automatically.
- Local typedef chains are resolved when their parser model definitions are
  available.
- `size_t` maps to `SizeT` without a target probe; supplied
  `prik.preprocessing.probes.c_types` facts override standard typedefs with width-specific
  `Int*`, `UInt*`, or `Float*` semantic names.
- Opaque standard-type probe facts such as `FILE` create named opaque semantic
  classes when referenced by converted declarations.
- C and Fortran enum definitions become unscoped integer constants. The
  semantic model does not create enum datatypes; named enum arguments, returns,
  fields, and variables keep the enum's underlying integer type.
- C enumerators and Fortran `enum, bind(C)` enumerators are ordinary
  `SemanticVariable` entries with `Final[...]` constant metadata. Enum tag names
  and `bind(C)` facts are preserved only as metadata for documentation and
  diagnostics.
- Native enumerator expressions remain stored in semantic IR. The `.pyi`
  initializer is emitted only when it can be represented as valid Python
  expression syntax.
- Enum underlying storage currently assumes C `int` and records that
  assumption unless an enum-specific compiler fact is supplied. Fortran
  `enum, bind(C)` enumerators use `integer(c_int)`/`Int32`.
- Object-like numeric macros become `Final`-style `SemanticVariable` entries through
  the `Constant` constraint.
- Struct definitions become `SemanticClass` entries. Incomplete structs become
  opaque classes and may be used through direct `Addr(...)` identity contracts.
- Explicit multi-header conversion resolves a struct to the header that defines
  it. Other generated stubs import that owner class instead of emitting
  duplicate definitions.
- Structs originating from private included headers remain usable through
  generated owner-module `class Name(Opaque): pass` dependency stubs.
- Declared C arrays, including adjusted array parameters, become semantic array
  storage contracts with C order for rank greater than one.
- Pointers become explicit `SemanticStorageContract` pointer/address
  metadata. `const` on the pointee makes the storage read-only, and `restrict`
  is preserved as aliasing metadata.

For example:

```c
enum status { STATUS_OK = 0, STATUS_ERROR = 10 };
void set_status(enum status value);
```

becomes:

```python
from prik.contracts import Final, Int

STATUS_OK: Final[Int] = 0
STATUS_ERROR: Final[Int] = 10

def set_status(value: Int) -> None: ...
```

### Conservative Blockers

The converter does not silently invent wrapper policy. Source facts that cannot
form a semantic contract fail during semantic conversion; unsupported policy
fails during post-IR policy completion before wrapper planning:

- unresolved typedef or unknown type references;
- legacy parser reports carrying macro-dependent declarations;
- variadic functions;
- function pointer/callback signatures without a resolved named prototype
  policy;
- mutable numeric or `void *` pointer parameters without ownership,
  scalar-storage, raw-address, or array policy;
- arrays with unknown extents;
- incomplete or external opaque structs used by value;
- unions used in semantic signatures;
- `volatile`, `_Atomic`, bitfields, and unsupported declarator compositions.

For this supported subset, `python3 -m prik semantics api.h --language c`
prints the semantic IR and
`python3 -m prik generate --pyi api.h --language c --out contracts` writes a
starter exact contract. Generated stubs remain conservative: ambiguous ownership,
callback, ABI-extension, and Pythonic projection policy stays out of the
generated `.pyi` until supplied by the semantic model or an edited interface.
In particular, an unresolved typedef is not assumed to be opaque because its
ABI representation is unknown.

## Semantic `.pyi` Contract Surface

Semantic `.pyi` is a Python-valid serialization and editing surface for
semantic IR, not a second semantic model. The syntax, metadata names,
projection notation, diagnostics, generated coverage, and editing workflow are
owned by [Semantic `.pyi` format](semantic-pyi-format.md).

This IR reference keeps only the relationship between that surface and the
underlying semantic model:

- source frontends populate `SemanticModule`, `SemanticFunction`,
  `SemanticArgument`, `SemanticVariable`, `SemanticClass`, and related storage
  contracts;
- `.pyi` printing exposes the public wrapper contract plus the native-call
  metadata required to reconstruct the same semantic IR;
- `.pyi` loading converts the documented contract subset back to semantic IR
  without reparsing native source; and
- policy completion and lowering consume semantic IR, not raw
  `.pyi` syntax.

The shared semantic model separates value type, storage and calling contract,
public array contract, ownership and transfer policy, and source-origin
metadata. The `.pyi` surface exposes only the facts that are part of the public
wrapper contract or required to reconstruct native-call topology. Native
source-provenance details not emitted into the public contract are
intentionally excluded from public contract equality.

Post-IR policy completion turns those facts into two explicit barrier actions
before lowering:

- the Python barrier action, which tells Python binding generation how to
  extract or validate the Python object; and
- the native barrier action, which tells bridge generation how to hand the
  extracted value to native code.

The Python barrier distinguishes Python scalar values, rank-0 NumPy scalar
storage, NumPy array storage, Python strings, raw address values, and generated
wrapper instances. The native barrier distinguishes direct values, call-local
addresses, caller/Python-backed storage addresses, raw addresses, packed array
descriptors, and wrapper-owned native addresses. Both are fixed before any code
is generated, so a contract that cannot select them is rejected rather than
wrapped on a guess.

### Round Trips And Provenance

`prik.parsers.pyi` parses the documented semantic `.pyi` subset into Python AST.
`convert_pyi_to_ir` converts that AST into the same public storage contracts
emitted by the source semantic pipelines; `pyi_file_to_semantic_module` combines file parsing
and conversion. Focused round-trip tests cover:

```text
Fortran parser model -> semantic IR -> .pyi -> semantic IR
```

Generated and edited stubs must not use hidden native-source parsing as a
fallback. If the `.pyi` contract omits native facts required for policy
completion or lowering, PRIK reports a contract or wrapper-planning error instead of
guessing.

### External Type References

External source-language types are modeled in semantic IR by owner-module type
identity. Stub printing may emit owner-module dependency stubs, and
`pyi_paths_to_semantic_modules` reconciles those imports back into semantic
`external_type_ref` metadata. The concrete file syntax for those owner stubs is
documented in
[Semantic `.pyi` format](semantic-pyi-format.md#classes-and-native-abi).

## C Conversion And Build Boundary

### Implemented semantic conversion

An unresolved C typedef is never assumed opaque: its ABI could be an integer,
pointer, struct, or another representation. The frontend emits an opaque class
only when declarations establish that contract, such as a forward struct
declaration or a private included struct used through pointers. An edited
`.pyi` may state it explicitly with `class Name(Opaque): pass`.

The shared model covers C functions, variables, fields, enum and macro
constants, scalar storage, pointers, arrays with known contracts, structs,
unions, opaque declarations, origin metadata, and raw mutability and ownership
facts. The C frontend can emit a conservative starter semantic `.pyi` contract
from those facts. This inspection surface is deliberately broader than runtime
wrapping.

### Implemented direct-C contracts

Source or authored semantic contracts can build the documented direct-C subset:
`void`, arithmetic and C99 complex scalars; one-level primitive pointers used
as scalar addresses, rank-zero storage, projected results, or C-contiguous
arrays; rank-zero strings; hidden outputs and status projection; exact native
scalar identities; symbol renaming and argument reordering; and overload sets
distinguishable by dtype and rank. Some of those meanings require an edited
contract because C pointer syntax alone does not determine Python storage,
shape, ownership, or result projection. [C Support](../language-support/c-support.md#what-is-supported)
is the authoritative build boundary.

### Remaining unsupported forms

Callbacks and function pointers, aggregates and by-value structs or unions,
variadics, unsupported calling conventions, nullable or retained pointers,
pointer results, multi-level pointers, and native global state remain outside
the direct-C wrapper subset. Modeled enum and macro constants and aggregate
declarations remain available for inspection but do not become a runtime C
wrapper API. These forms fail before wrapper planning; PRIK does not generate an
ABI-conversion adapter as a fallback.

New C conversion keeps the notation the rest of this page uses: by-value
scalars as bare types, unrefined pointers as `Addr(T)`, and array notation only
where a real array storage contract is known. `const` stays source provenance
and a policy input; it does not change the boundary spelling.
