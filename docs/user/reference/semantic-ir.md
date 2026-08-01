---
title: Semantic IR Reference
audience: advanced users, developers
prerequisites: parser references, native datatype model
related: index.md
status: maintained
publication: draft
---

# Semantic IR Reference

<!-- PRIK_C_DOCS_START
This file is the reference for semantic type names, C-to-IR conversion, and the
exact native C semantic stub rules. The user-facing editable `.pyi` syntax and
roadmap live in [Semantic .pyi format](semantic-pyi-format.md); this document keeps the
underlying semantic model and datatype policy in one place.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Sections through [Deferred C Work](#deferred-c-work) describe current semantic
behavior. The final self-contained C runtime-contract section is explicitly a
design proposal and is not implemented C-input wrapper support. The current
Fortran runtime contract is documented separately in
[Fortran wrapper reference](fortran-wrapper.md).
PRIK_C_DOCS_END -->

## Datatype Mapping

<!-- PRIK_C_DOCS_START
This document records the shared scalar datatype policy used when C and Fortran
parser facts are converted to semantic IR. The semantic names are the stable
bridge between parser-native type spellings, `.pyi` output, policy completion,
the implemented Fortran wrapper, and a future C-input wrapper backend.
PRIK_C_DOCS_END -->

### Semantic Names

| Semantic dtype | NumPy equivalent | Notes |
| --- | --- | --- |
| `Bool` | `numpy.bool_` | Boolean scalar. |
| `Int8`, `Int16`, `Int32`, `Int64` | `numpy.int8`, `numpy.int16`, `numpy.int32`, `numpy.int64` | Signed integers. |
| `UInt8`, `UInt16`, `UInt32`, `UInt64` | `numpy.uint8`, `numpy.uint16`, `numpy.uint32`, `numpy.uint64` | Unsigned integers. |
| `Float32`, `Float64` | `numpy.float32`, `numpy.float64` | Binary floating-point scalars. |
| `Float128` | `numpy.longdouble` | Platform precision varies; `numpy.float128` is not portable. |
| `Complex64`, `Complex128` | `numpy.complex64`, `numpy.complex128` | Complex scalars. |
| `Complex256` | `numpy.clongdouble` | Platform precision varies. |
| `String` | `numpy.str_` or byte storage at ABI boundary | Character policy depends on wrapper ABI. |
| `SizeT` | `numpy.uintp` | Target width is compiler-probed when available. |
| `Any` | `object` | Used for void pointer pointees and intentionally opaque values. |

<!-- PRIK_C_DOCS_START
| `Int` | Target-dependent signed NumPy integer | Ordinary C `int`; the concrete `Int16`/`Int32`/`Int64` dtype and compiler fact are stored separately. |
PRIK_C_DOCS_END -->

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

<!-- PRIK_C_DOCS_START
| `iso_c_binding` numeric kinds | Compiler-probed interoperable storage | Matching NumPy numeric dtype |
| `logical`, `logical(kind=1/2/4/8)`, `logical(c_bool)` | `Bool` | `numpy.bool_` |
| `character`, `character(len=n)`, `character(kind=1)`, `character(kind=c_char)` | `String` | `numpy.str_` or ABI byte storage |
PRIK_C_DOCS_END -->

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

<!-- PRIK_C_DOCS_START
### C Types
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| C spelling or parser type | Semantic dtype | NumPy equivalent |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
C primitive spellings are ABI-dependent. Compiler-backed C semantic CLI stages
automatically probe the selected compiler target and use those facts for every
modeled arithmetic primitive. Ordinary C `int` keeps the stable semantic
identity `Int`; its concrete dtype and the compiler fact used to derive it are
stored on `SemanticType`. Other primitive names and dtypes follow the measured
target width and signedness. NumPy is the consumer-side dtype mapping, not the
probe source: it describes the Python interpreter host and may differ from a
selected compiler target or sysroot.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Direct converter calls without a supplied report retain the documented
fallback mappings. A supplied target fact whose width has no semantic dtype
mapping produces `c_unsupported_primitive_abi` instead of silently using a
different width.
PRIK_C_DOCS_END -->

### Generated Linux x86_64 Mapping Example

The following mapping snapshots are generated from the same compiler-backed
code paths used by prik. They target the `linux-x86_64` profile used by GitHub
Actions. The executable documentation test reruns the commands and compares
their complete output, so a compiler fact or semantic mapping change must
update these examples.

<!-- PRIK_C_DOCS_START
C uses `cc` to measure primitive storage, signedness, alignment, and floating
precision:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact linux-x86_64 -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik probe &#45;&#45;language c &#45;&#45;compiler cc &#45;&#45;format markdown
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```markdown
Target profile: `linux-x86_64`

| C type | Native target fact | Semantic dtype | NumPy dtype |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| `_Bool` | 8-bit bool | `Bool` | `numpy.bool_` |
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Fortran uses the same cached compiler probe as normal semantic conversion and
the standard `storage_size` intrinsic to measure compiler-dependent modern and
double-kind forms. The generated table also lists legacy spellings; numeric
`type*N` rows use their fixed total storage, and character-star rows show
length syntax rather than a different character kind:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact linux-x86_64 -->
<!-- PRIK_C_DOCS_START
```bash
python3 -m prik probe &#45;&#45;language fortran &#45;&#45;compiler gfortran &#45;&#45;format markdown
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```markdown
Target profile: `linux-x86_64`

| Fortran type | Native target fact | Semantic dtype | NumPy dtype |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
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
| `logical` | 32-bit storage | `Bool` | `numpy.bool_` |
| `logical(kind=1)` | 8-bit storage | `Bool` | `numpy.bool_` |
| `logical(kind=2)` | 16-bit storage | `Bool` | `numpy.bool_` |
| `logical(kind=4)` | 32-bit storage | `Bool` | `numpy.bool_` |
| `logical(kind=8)` | 64-bit storage | `Bool` | `numpy.bool_` |
| `logical(c_bool)` | 8-bit storage | `Bool` | `numpy.bool_` |
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
| `logical*1` | 8-bit storage | `Bool` | `numpy.bool_` |
| `logical*2` | 16-bit storage | `Bool` | `numpy.bool_` |
| `logical*4` | 32-bit storage | `Bool` | `numpy.bool_` |
| `logical*8` | 64-bit storage | `Bool` | `numpy.bool_` |
| `character*1` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character*8` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
| `character*(*)` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## C To Semantic IR Mapping
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Status: first C semantic conversion subset implemented in `prik/semantics/c2ir.py`.
The converter consumes `c_parser` models and emits the same language-neutral
semantic IR used by Fortran and edited `.pyi` files. Shared primitive dtype
policy is documented in the datatype mapping section above.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### Supported Identity Subset
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- C translation unit -> one `SemanticModule` named from the source file stem.
- C function -> `SemanticFunction`, preserving native name and parameter order.
- C parameter -> `SemanticArgument`.
- C global variable -> `SemanticVariable`.
- C struct/union field -> `SemanticField`.
- `void` return -> `None`.
- `_Bool` -> `Bool`.
- All modeled primitive integer, real, and complex spellings consume supplied
  `prik.probes.c_types` facts. Plain `char` signedness, integer widths, real
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
  `prik.probes.c_types` facts override standard typedefs with width-specific
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For example:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
enum status { STATUS_OK = 0, STATUS_ERROR = 10 };
void set_status(enum status value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
becomes:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Final, Int

STATUS_OK: Final[Int] = 0
STATUS_ERROR: Final[Int] = 10

def set_status(value: Int) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### Conservative Blockers
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The converter does not silently invent wrapper policy. Source facts that cannot
form a semantic contract fail during semantic conversion; unsupported completed
policy fails during wrapper planning:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The current C semantic path supports `&#45;&#45;language c &#45;&#45;semantics` and
starter exact-contract `&#45;&#45;language c &#45;&#45;pyi` output for this supported
subset. Generated stubs remain
conservative: ambiguous ownership, callback, ABI-extension, and Pythonic
projection policy stays out of the generated `.pyi` until supplied by the
semantic model or an edited interface. In particular, an unresolved typedef is
not assumed to be opaque because its ABI representation is unknown.
PRIK_C_DOCS_END -->

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
descriptors, and wrapper-owned native addresses. These decisions are semantic
policy. Wrapper planning, binding/bridge lowering, and printers may create
backend-local temporaries, but they must not infer or override a barrier action
from datatype, source-declaration direction, array category, aliasing, or
memory-storage checks.

Parser-model conversion and semantic/wrapper-model traversal use the shared
`prik.utilities.visitor.ClassVisitor` dispatcher and one configured
`<prefix>_<ClassName>` protocol. The default prefix is `_visit`; specialized
visitors may choose clearer names such as `_print` or `_parse` while still using
the same MRO dispatcher. Barrier/action dispatch tables are allowed only for
completed policy actions; the primitive ABI map is the other deliberate table
because it maps datatype classes to semantic dtypes rather than traversing model
nodes. These tables are separate from model-node dispatch.

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
completion or lowering, prik reports a contract or wrapper-planning error instead of
guessing.

### External Type References

External source-language types are modeled in semantic IR by owner-module type
identity. Stub printing may emit owner-module dependency stubs, and
`pyi_paths_to_semantic_modules` reconciles those imports back into semantic
`external_type_ref` metadata. The concrete file syntax for those owner stubs is
documented in
[Semantic `.pyi` format](semantic-pyi-format.md#classes-and-native-type-markers).

<!-- PRIK_C_DOCS_START
For C, an unresolved typedef is not automatically opaque: its ABI could be an
integer, pointer, struct, or another representation. The C frontend emits an
opaque class when declarations establish that contract, such as a forward
struct declaration or a private included struct used through pointers. An
edited `.pyi` file may also state the policy explicitly with `class
Name(Opaque): pass`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### Deferred C Work
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The shared model represents the current C semantic conversion subset for
functions, variables, fields, constants, scalar storage, pointers, arrays
with known contracts, origin metadata, mutability and ownership facts. The C
frontend can generate starter exact-contract stubs from that model. Remaining C
work includes:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- C wrapper lowering;
- C ownership, callback or pointer policy inference beyond facts already
  present in exact contracts.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Future C conversion should use the same notation documented by the semantic
`.pyi` format reference: by-value scalars as bare types, unrefined pointers as
`Addr(T)`, and array notation only when a real array storage contract is known.
C `const` qualifiers remain source provenance and policy inputs; semantic
`.pyi` still uses the same boundary spelling as generated Fortran contracts.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## Design Proposal: Self-Contained C Semantic `.pyi` Runtime Contract
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
> **Status: design only, not implemented native binding support.** prik currently
> parses C, converts the supported subset to semantic IR, emits and loads
> semantic `.pyi`. It does not currently generate,
> lower, compile, or execute C wrappers. Every runtime behavior, wrapper error,
> and Phase 1/Phase 2 requirement below describes a proposed implementation
> target unless an earlier current-contract section explicitly says otherwise.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The proposed target is Python wrappers for C libraries on a selected Linux ABI.
Its primary design requirement is that a semantic `.pyi` file plus a compiled
library be sufficient to generate a wrapper, with C header parsing used only as
optional input generation. Related deferred policy is tracked in
[wrapper design notes](../../maintainer/design/wrapper-design-notes.md).
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 1. Proposed Phase 1 Boundary
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The proposed Phase 1 would implement the exact callable interface first.
Python would intentionally remain C-like at this stage:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- Every visible Python argument corresponds to one native C parameter, in the
  same order.
- Every direct Python return annotation corresponds to the direct C return.
- Native `void` is written as `None`.
- Native pointer parameters are supplied by the Python caller as pointer-backed
  storage, primarily NumPy zero-dimensional storage or NumPy arrays.
- Output pointer parameters remain input arguments: the caller allocates
  mutable storage and observes changes after the call.
- No argument is synthesized, reordered, omitted or converted into a Python
  result by the wrapper.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Therefore, the proposed Phase 1 would not implement or emit `@native_call`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The purpose of this ordering is to prove that prik can describe, parse, lower
and execute direct C signatures reliably before adding Pythonic adaptations.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 2. Proposed Rules
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
1. The semantic `.pyi` must be sufficient to call every supported wrapped
   symbol without reading C source at build time.
2. Optional C parsing may generate a starter semantic `.pyi`, but generated
   wrappers consume only the semantic `.pyi` and the compiled library.
3. Phase 1 functions use identity parameter mapping only: one Python argument
   per C parameter, in native order.
4. Phase 1 returns use identity return mapping only: the Python return is the
   direct C return, or `None` for native `void`.
5. A C pointer parameter is never silently represented by a plain immutable
   Python scalar. The caller supplies pointer-backed storage.
6. A bare numeric pointer uses `Addr(T)` for a raw address. For an API known
   to use that pointer as scalar storage, use `T[()]` so callers pass rank-zero NumPy
   storage. Numeric pointer parameters with a recorded array shape contract use
   `T[dimension-specs]` or `T[...]`. All these one-level storage forms lower to
   one native pointer; C does not carry rank, shape or stride metadata in an
   ordinary `T *` parameter.
7. Array dimensions express validation constraints, not additional pointer
   depth. `Float64[:, :]` still lowers to one `double *`, never `double **`.
8. With no stride or order modifier, numeric array storage in a C-origin
   semantic stub is implicitly C-contiguous. Generated C stubs omit redundant
   `ORDER_C`.
   Rank-one contiguous storage has no C-versus-Fortran order distinction, so
   `T[:]` and `T[n]` never need `ORDER_F` either. A non-contiguous vector uses
   stride notation such as `T[::]`, not an order modifier.
   For multidimensional storage, order and stride constraints are independent.
   `ORDER_C` is not needed in canonical stubs because bare array notation,
   including `T[::, ::]`, already carries the C orientation.
   The explicit non-default layout form is
   `Annotated[T[dimension-specs], ORDER_F]`, including
   `Annotated[T[::, ::], ORDER_F]` for a Fortran-oriented
   strided contract. `ORDER_ANY` represents a multidimensional strided
   contract with no C/F orientation restriction.
   A stride-aware axis is written `::`, as in
   `Float64[:, ::]` or `Float64[:, 0:n:]`. It is a direct
   interface when any native extent or stride values remain visible arguments;
   the exact interface must not generate them.
9. C `const` does not introduce a second semantic type spelling. A public
   `.pyi` contract uses the same Python boundary shape, and source constness is
   retained only as provenance or explicit policy metadata where needed.
10. Pointer graphs such as `T **` and deeper are not inferred from NumPy
    arrays. They are represented directly as `Addr[n](T)` and require the
    caller to supply a compatible low-level native pointer object.
11. Functions requiring hidden outputs, generated lengths, Python string
    conversion, handle conversion, callback thunks, status-to-exception
    conversion, packing or copy-back are deferred until after identity calls
    work.
12. The current target is a selected Linux ABI. Cross-platform variation and
    non-default calling conventions are deferred.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 3. Proposed Artifact
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The proposed compiler-facing artifact is:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```text
module.prik.pyi
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
It may use prik semantic types, but it would contain only identity-callable
functions in Phase 1.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
A clean `.pyi` for standard type checkers is not part of the proposed Phase 1.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 4. Scalar Types Passed By Value
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Bare scalar types represent native by-value parameters and direct native
returns.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Semantic type | C interpretation on selected target |
| &#45;&#45;- | &#45;&#45;- |
| `Int` | ordinary C `int` |
| `Int8`, `Int16`, `Int32`, `Int64` | fixed-width signed integer types |
| `UInt8`, `UInt16`, `UInt32`, `UInt64` | fixed-width unsigned integer types |
| `Float32` | `float` |
| `Float64` | `double` |
| `SizeT` | `size_t` |
| `CLong`, `CULong` | C `long`, `unsigned long` |
| `Bool` | selected C boolean ABI type |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Example:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
int add(int a, int b);
double multiply(double a, double b);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int

def add(a: Int, b: Int) -> Int: ...
def multiply(a: Float64, b: Float64) -> Float64: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
No decorator is needed or accepted for these identity calls.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 5. Numeric Pointer Storage
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 5.1 Canonical Address And Array Notation
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
A numeric NumPy storage annotation means the caller supplies memory whose data
address is passed directly to C. C ordinary pointer parameters contain no
rank, extent or stride descriptor. Therefore a native `double *values` with no
additional array contract is represented exactly as `Addr(Float64)`;
dimensioned forms are used only when the C declaration, documented API
contract, or completed semantic stub provides those constraints.
A generated Fortran intermediary that prepares Fortran dummy arguments is a
Fortran backend concern and does not change the direct C `T *` contract
described in this document.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Semantic annotation | Python caller supplies | Native parameter |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| `T[()]` | rank-zero NumPy scalar storage | `T *` or `const T *` |
| `Addr(T)` | raw address to compatible storage, for example `array.ctypes.data` | `T *` or `const T *` |
| `Int[:]` | contiguous rank-one NumPy array; C/F order is equivalent | `int *` or `const int *` |
| `Float64[:]` | contiguous rank-one NumPy array; C/F order is equivalent | `double *` or `const double *` |
| `Float64[n]` | one-dimensional array whose size is validated against visible argument or semantic constant `n` | `double *` or `const double *` |
| `Float64[0:n]` | writable one-dimensional array with explicit half-open range `0:n` | `double *` |
| `Float64[:, :]` | writable rank-two C-contiguous NumPy array | `double *` |
| `Float64[3, 4]` | writable C-contiguous NumPy array with exact shape `(3, 4)` | `double *` |
| `Float64[...]` | writable C-contiguous NumPy array of any rank | `double *` |
| `Float64[...][1:4]` | writable C-contiguous NumPy array with rank 1, 2, or 3 | `double *` |
| `Float64[...][1, 2, 5]` | writable C-contiguous NumPy array with rank 1, 2, or 5 | `double *` |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`Float64[...]` means any rank (any number of dimensions). A following rank
selector restricts that set: `Float64[...][1:4]` accepts ranks 1 through 3
because the stop value is exclusive, while `Float64[...][1, 2, 5]` accepts
only ranks 1, 2, and 5. The same forms apply to other numeric element types
and inside shape expressions.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
An axis entry without colons is an extent. `Float64[n]` means a rank-one
array of size `n`, and `Float64[n, m]` means an array with shape `(n, m)`;
neither denotes element indexing. A slice entry such as `Float64[0:n]`
expresses an explicit NumPy-style half-open range. It has the same size as
`Float64[n]` in this simple zero-based case, but retains range semantics for
forms with a lower bound or step.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`Addr(T)` preserves an unrefined one-level C pointer as a raw address. For a
known primitive scalar-storage API, use `T[()]` so the Python
caller supplies a rank-zero NumPy array. `T[dimension-specs]` and `T[...]`
with an optional rank selector are NumPy-backed array-pointer spellings once
an array contract is known. A shape-bearing array annotation already
represents pointer-backed array storage; do not additionally wrap it in
`Addr(...)`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For multidimensional storage, order is orthogonal to rank, dimensions and
stride capability. `Annotated[Float64[:, :], ORDER_F]` denotes a rank-two
dense Fortran-contiguous array, while
`Annotated[Float64[::, ::], ORDER_F]` denotes a rank-two
Fortran-oriented strided array. Bare `Float64[::, ::]` retains
the default `ORDER_C` orientation, and
`Annotated[Float64[::, ::], ORDER_ANY]` imposes no C/F
orientation restriction. `Annotated[Float64[...][1:4], ORDER_F]` expresses
the corresponding Fortran-oriented rank-polymorphic contract. These spellings
define the semantic format; they are explicit because `ORDER_F` and
`ORDER_ANY` are non-default in a C-origin stub. Accepting either in a
runnable C Phase 1 wrapper requires the corresponding native routine to
accept that storage layout directly. For a rank-one array, `ORDER_C` and
`ORDER_F` do not distinguish storage, contiguous or strided, so no order
constraint is written.
For a multidimensional strided annotation, `ORDER_F` is orientation metadata,
not a requirement that NumPy report `F_CONTIGUOUS`; non-unit strides remain
part of the contract.
Source frontends may retain original declaration dimensions, source bounds or
native dummy categories as internal provenance. Those source facts are not part
of the canonical public array annotation unless they produce an actual storage
constraint. In particular, Fortran dummy bounds are established by native
association rather than supplied as Python array metadata. The implemented C
conversion subset is described in the C-to-semantic IR mapping section above.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Stride-aware dimensions use a slice step marker:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Semantic annotation | Meaning | Exact-call condition |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| `Float64[::]` | Rank-one array with a runtime element stride. | Any required stride argument is separately visible in the native signature. |
| `Float64[:, ::]` | Rank-two array whose second axis has runtime stride metadata. | Any required stride argument is separately visible in the native signature. |
| `Float64[::, ::]` | Rank-two strided array with implicit `ORDER_C` orientation. | Any required stride arguments are separately visible in the native signature. |
| `Annotated[Float64[::, ::], ORDER_F]` | Rank-two strided array with required Fortran orientation. | The native routine accepts that orientation and any required stride arguments remain visible. |
| `Annotated[Float64[::, ::], ORDER_ANY]` | Rank-two strided array with no C/F orientation restriction. | The native routine accepts arbitrary orientation and any required stride arguments remain visible. |
| `Float64[:, ::2]` | Rank-two array whose second-axis element step is exactly two. | The native routine consumes that layout directly. |
| `Float64[:, 0:n:]` | Rank-two array with bounded second axis and an arbitrary runtime step. | `n` and any required stride metadata are native inputs. |
| `Float64[:, 0:n:m]` | Rank-two array with bounded second axis and exact symbolic step `m`. | `n` and `m` are native inputs or semantic constants. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`Float64[:, ::]` does not select a strided representation: under Python slice
semantics it is just `Float64[:, :]`. A stride-aware array cannot be passed
correctly to an operation that assumes contiguous storage unless the native
call also receives required strides or the wrapper performs an explicit
packing/copy-back conversion.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Slice dimensions follow `lower:upper:step`. A literal bound or step is checked
directly. A symbolic bound or step, such as `n` or `m` in
`Float64[:, 0:n:m]`, must resolve from a visible scalar parameter or a
declared semantic constant such as `Final[Int]`. A later wrapper projection
may derive native metadata from array storage using NumPy notation, for
example `Arg(0).shape[1]` or `Arg(0).strides[1]` in a later Pythonic view,
but the exact interface does not synthesize such arguments. Resolvable
arithmetic expressions such as `2*n`
can be added later without requiring a new dimension notation. Annotation
steps use NumPy element units, while `Arg(0).strides[1]` has NumPy's byte
units; converting between them is an explicit later mapping decision.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 5.2 Pointer Depth And Opaque Pointers
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`Addr(...)` expresses native pointer depth directly. For a one-level pointer,
it preserves the native address form without inventing rank or shape. A known
primitive scalar-storage use should be expressed as `T[()]` instead. For an
opaque argument or a direct pointer return, `Addr(...)` represents a
typed low-level native pointer object:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Semantic annotation | Native parameter |
| &#45;&#45;- | &#45;&#45;- |
| `Addr(T)` | `T *` or `const T *`; unrefined one-level pointer storage |
| `Addr[2](T)` | `T **` direct low-level pointer object |
| `Addr[n](T)` | `T` followed by exactly `n` native pointer layers, `n >= 2` |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`Addr(x)` is the only canonical depth-one spelling. `Addr[1](x)` is invalid.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For array storage whose dimensions are known, use an array form such as
`Int[n]` or `Float64[:, :]` rather than `Addr(Int)` or `Addr(Float64)`. When
the only available C fact is a data pointer with no rank or extent contract,
retain `Addr(T)`. `Addr[n](T)` is necessary for pointer graphs and for low-level
pointer values that are not represented by a shaped NumPy storage contract.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
A direct pointer object carries a typed native address. Passing or returning
it does not imply allocation, copying, ownership or automatic destruction.
For example, a raw pointer returned by one native function can be passed to a
second native function under matching `Addr(...)` annotations. Pointer-object
construction/allocation helpers are runtime API work, not additional
information required in a semantic function signature.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 5.3 Pointer To Scalar
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void increment(int *value);
void read_count(const int *value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Phase 1 interface:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def increment(value: Int[()]) -> None: ...
def read_count(value: Int[()]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Python use is intentionally storage-oriented:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
value = np.empty((), dtype=np.intc)
value[...] = 7
increment(value)
updated = value.item()
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The wrapper passes `value`'s data address. It does not construct temporary
scalar storage and does not return the mutation.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 5.4 Pointer To Array
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void negate(int n, double *values);
double sum_values(size_t n, const double *values);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Phase 1 interface:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int, SizeT

def negate(n: Int, values: Float64[n]) -> None: ...
def sum_values(n: SizeT, values: Float64[n]) -> Float64: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The caller supplies `n` explicitly because it is an actual C parameter. The
wrapper must not derive it from `len(values)` in Phase 1.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 5.5 Output Pointer Remains An Argument
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void get_count(int *out);
void get_values(int n, double *out);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Phase 1 interface:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int

def get_count(out: Int[()]) -> None: ...
def get_values(n: Int, out: Float64[n]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Example Python use:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
out_count = np.empty((), dtype=np.intc)
get_count(out_count)
count = out_count.item()

out_values = np.empty(n, dtype=np.float64)
get_values(n, out_values)
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Returning `Int` from `get_count()` or allocating and returning
`Float64[n]` from `get_values(n)` is a later Pythonic adaptation, not an
identity call.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 6. Array Constraints
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 6.1 Rank, Accepted Ranks And Fixed Dimensions
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Dimensions refine valid NumPy storage while the native argument remains one
data pointer. They are semantic/API contracts rather than metadata transported
by a C `T *`. A bare pointer imported without such a contract remains raw:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void process_raw(double *values);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Float64

def process_raw(values: Addr(Float64)) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Once the semantic interface records valid array contracts, it may use:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void process_matrix(double *matrix);
void process_any(double *values);
void process_vector_or_matrix(double *values);
void use_row(int (*row)[4]);
void use_matrix(int (*matrix)[4]);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int

def process_matrix(matrix: Float64[:, :]) -> None: ...
def process_any(values: Float64[...]) -> None: ...
def process_vector_or_matrix(values: Float64[...][1, 2]) -> None: ...
def use_row(row: Int[4]) -> None: ...
def use_matrix(matrix: Int[:, 4]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- `Float64[:, :]` validates rank two and C contiguity, then passes one
  `double *`.
- `Float64[...]` accepts any rank and passes one `double *`.
- `Float64[...][1, 2]` accepts rank one or rank two and passes one
  `double *`.
- `Int[4]` validates one fixed row of four `int` values, then passes one
  address.
- `Int[:, 4]` validates contiguous rows of fixed width four, then passes one
  address.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
For function parameters on the selected ABI, `int (*)[4]` is represented as
one pointer plus its fixed row-width contract. It is not represented as
`int **`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 6.2 Strided Direct Interfaces Keep Native Metadata Visible
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The semantic notation can distinguish a stride-aware view from a contiguous
matrix while retaining the exact native parameter list:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void process_bounded_step(int n, int m, double *values);
void process_columns(const double *values, size_t columns, size_t stride_bytes);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int, SizeT

def process_bounded_step(n: Int, m: Int, values: Float64[:, 0:n:m]) -> None: ...
def process_columns(
    values: Float64[:, ::],
    columns: SizeT,
    stride_bytes: SizeT,
) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`::` means the axis stride must be carried or checked rather than assumed
to be contiguous. `::2` is the fixed-step equivalent. `0:n:m` validates a
bounded axis and exact element step using visible native values or declared
semantic constants. In `process_columns`, the caller supplies both the array
storage and its native `stride_bytes` argument; nothing is hidden or
generated. For a multidimensional array, a stride form may be combined with
`ORDER_F`, or with `ORDER_ANY` when no orientation is part of the native
contract; leaving it unannotated retains `ORDER_C`. A later Pythonic view may
hide that argument with
`Arg(0).strides[1]`, or request `Pack` / `CopyBack`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 6.3 Pointer Graphs Are Different
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void use_rows(int **rows);
void update_value(int *****value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Neither declaration is represented by `Int[:, :]`. NumPy array notation
supplies one array data address, optionally accompanied by native
extent/stride values; it does not create a pointer graph. Their exact
low-level Phase 1 interfaces are:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Int

def use_rows(rows: Addr[2](Int)) -> None: ...
def update_value(value: Addr[5](Int)) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The caller supplies an prik-compatible native pointer object with the declared
topology. The wrapper passes it unchanged. Constructing pointer rows from
nested Python sequences and exposing `update_value(value: Int) -> Int` are
later Pythonic adaptations.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 6.4 Contiguity
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Without an explicit layout or stride form, array annotations such as `T[:]`,
`T[:, :]`, `T[n]`, and `T[...]` require C-contiguous numeric storage; a
generated C stub does not repeat this as `ORDER_C`. Explicit non-default
forms such as `Annotated[T[:, :], ORDER_F]`,
`Annotated[T[::, ::], ORDER_F]`, or
`Annotated[T[::, ::], ORDER_ANY]` are exact interfaces when
the native routine accepts that layout and all required metadata remains
visible in the signature. A bare multidimensional stride form such as
`T[:, ::]` is also exact when native metadata is visible, but retains
the implicit `ORDER_C` orientation. Automatic packing, copy-back, or
derivation of native metadata is a later Pythonic transformation.
For rank one, `T[:]` and `T[n]` are also the canonical Fortran-contiguous
spelling; write `T[::]` when contiguity is not required.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 7. Direct Native Returns
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 7.1 Scalars And `void`
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Direct scalar returns and native `void` are identity behavior:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
int status(void);
void reset(void);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def status() -> Int: ...
def reset() -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
An integer return remains an integer return in Phase 1. It is not
automatically converted to an exception.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 7.2 Pointer Returns
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
A direct returned native pointer can be exposed as a low-level pointer object
without changing the C return topology:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
double *raw_values(void);
struct context *context_current(void);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Float64, Opaque

class context(Opaque):
    pass

def raw_values() -> Addr(Float64): ...
def context_current() -> context: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
If a returned pointer is exposed immediately as NumPy storage, shape and
lifetime information is required. This also remains identity mapping because
the C function directly returns the represented pointer:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
double *create_values(int n);
void free_values(double *values);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Annotated, Float64, Int

def create_values(n: Int) -> Annotated[
    Float64[n],
    Owned,
    FreeWith("free_values"),
]: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
This does not require `@native_call` because the C function directly returns
the pointer represented by the Python return annotation. Until shape and
lifetime handling are implemented, return it as the corresponding direct
low-level pointer object or reject the higher-level NumPy view rather than
guessing.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 8. Symbol Names
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Argument and return identity is independent of symbol naming. Phase 1
supports `@bind` without introducing `@native_call`:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
int library_add(int a, int b);
void c_increment(int *value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int, bind

@bind("library_add")
def add(a: Int, b: Int) -> Int: ...

@bind("c_increment")
def increment(value: Int[()]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
`@bind` changes only which exported symbol is loaded. It does not synthesize
arguments, change pointers or alter results.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 9. Structures, Enums And Non-Numeric Pointers
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
By-value enums and by-value structures can be Phase 1 identity interfaces once
their native representation and layout are complete in the semantic `.pyi`:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
struct point { double x; double y; };
struct point scale_point(struct point p, double factor);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64

class point(Structure):
    x: Float64
    y: Float64

def scale_point(p: point, factor: Float64) -> point: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Opaque pointers may be represented directly without creating a Pythonic handle
API:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
struct context;
struct context *context_create(void);
void context_destroy(struct context *ctx);
int context_run(struct context *ctx);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int, Opaque

class context(Opaque):
    pass

def context_create() -> context: ...
def context_destroy(ctx: context) -> None: ...
def context_run(ctx: context) -> Int: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
This is C-like identity behavior: Python receives and passes the native pointer
object. Automatic ownership, destruction, status checking and output-handle
conversion are later policies.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The following remain outside the first identity subset unless their direct
native representations are implemented explicitly:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- Python `str` conversion for `char *` or `const char *` (raw byte/character
  storage may be represented directly);
- Python callables converted into native function pointers (a pre-existing
  low-level native function pointer may later be an identity argument);
- unions;
- variadic functions;
- `void *` beyond an explicitly selected raw/byte-storage representation.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 10. Transformations Excluded From Proposed Phase 1
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Phase 1 must reject, or leave unresolved during optional C import generation,
any interface that requires the wrapper to change the native function shape.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Excluded from the proposed Phase 1:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Desired behavior | Example C shape | Later mechanism |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| Pass a Python scalar through a native pointer | `void increment(int *value)` exposed as `value = increment(value)` | `@native_call([Addr(Arg(0))])` plus readback |
| Generate a hidden length | `double sum(size_t n, const double *x)` exposed as `sum(x)` | `Arg(0).shape[0]` in `@native_call` |
| Turn an output pointer into a Python result | `void get_count(int *out)` exposed as `get_count() -> Int` | `Return(...)` in `@native_call`; the output slot is already addressable |
| Convert native status to exception | `int create(...);` with hidden status | `Status[...]` and `Check(...)` |
| Wrap a raw opaque pointer with ownership behavior | `struct ctx *` / `struct ctx **` | handle and lifetime policy |
| Convert Python strings to C strings | `const char *` from `str` | text encoding/termination policy |
| Generate callback thunks | function-pointer argument | callback lifetime/exception policy |
| Pack or copy a layout the native function does not accept | pointer to accepted native storage | `Pack` / `CopyBack` coercions |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The later syntax is retained as design direction only. It is not required by
the Phase 1 parser, IR, printer or wrapper generator.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 11. Proposed Phase 1 Runtime Errors
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
A future C-input wrapper generator or optional importer would need to report
unsupported behavior instead of silently changing the interface.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Code | Condition |
| &#45;&#45;- | &#45;&#45;- |
| `c_non_identity_call_unsupported` | A declaration or semantic interface requires synthesized, omitted, reordered or transformed parameters/results. |
| `c_pointer_object_mismatch` | A `Addr(T)` argument lacks compatible native pointer-backed storage, or a multi-level pointer argument lacks the declared native pointer topology. |
| `c_numpy_pointer_return_policy_required` | A native pointer return is exposed as a shaped NumPy result without implemented lifetime handling or explicit required metadata; a direct raw `Addr(T)` return remains identity behavior. |
| `c_numpy_dtype_mismatch` | Supplied NumPy storage does not have the exact semantic native element dtype. |
| `c_numpy_rank_mismatch` | Supplied NumPy storage does not satisfy declared rank or fixed-shape constraints. |
| `c_numpy_contiguity_required` | An unqualified dense C-contiguous array annotation receives non-contiguous storage. |
| `c_numpy_stride_mapping_required` | A Pythonic interface hides native stride parameters required for stride-aware storage without an explicit mapping such as `Arg(0).strides[1]`. |
| `c_numpy_writeability_required` | A mutable native pointer receives read-only NumPy storage. |
| `c_opaque_handle_conversion_unsupported` | A raw opaque pointer cannot yet be represented as the documented wrapper-owned `context` handle. |
| `c_string_conversion_unsupported` | A Python string conversion is requested. |
| `c_callback_unsupported` | A Python callback-to-native-function-pointer mapping is requested. |
| `c_union_unsupported` | A callable interface includes an unsupported union. |
| `c_variadic_function_unsupported` | A variadic native function is requested. |
| `c_calling_convention_unsupported` | A non-default calling convention is required. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 12. Proposed Phase 1 Parser And Wrapper Requirements
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The proposed Phase 1 implementation would need to:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
1. Parse scalar annotations and direct `None`/scalar return annotations.
2. Parse unrefined one-level pointer forms `Addr(T)` and accept raw address
   values; known scalar-storage uses should support `T[()]`.
3. Parse numeric array storage forms: `T[:]`, `T[:, :]`,
   fixed or symbolic extents such as `T[3, 4]` and `T[n]`, explicit dependent
   ranges or steps such as `T[0:n]` and `T[:, 0:n:m]`, and rank-polymorphic
   forms such as `T[...]`, `T[...][1:4]`, and `T[...][1, 2, 5]`.
4. Lower each supported one-level scalar-storage or array-storage
   annotation to exactly one native pointer of its leaf type.
5. Parse and lower direct pointer forms `Addr[n](T)` as exactly `n` native
   pointer layers, accepting compatible low-level native pointer objects at
   runtime.
6. Validate NumPy dtype, rank, fixed dimensions, explicit layout/stride
   constraints including `ORDER_F` and `ORDER_ANY`, and writeability before
   calling native code.
7. Preserve the visible parameter order exactly, including visible native
   count or stride parameters.
8. Preserve direct native scalar, pointer and native `void` returns.
9. Parse and apply `@bind("symbol")` for identity symbol renaming.
10. Parse complete by-value `Structure`, integer enum constants, and opaque pointer leaf
   declarations if those existing declaration features are already runnable;
   otherwise report them as not yet supported without approximating them.
11. Reject `@native_call`, `Arg`, `Return`, `Returns`, `Status`, `Check`,
   `Pack`, `CopyBack` and callback conversion constructs as later-phase
   syntax if encountered in a Phase 1 runnable input.
12. Accept stride-aware direct interfaces only when any required native count
    or stride arguments remain visible; deriving them from array metadata is a
    later Pythonic mapping.
13. Never consult C source after a supported semantic `.pyi` has been parsed.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 13. Proposed Phase 1 Runtime Tests
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.1 By-Value Scalar Identity
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
int add(int a, int b);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def add(a: Int, b: Int) -> Int: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The wrapper passes two native `int` values and returns one native `int`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.2 Mutable Scalar Pointer Storage
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void increment(int *value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def increment(value: Int[()]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify that writable rank-zero NumPy storage is accepted, its data
address is passed to the native call, and native mutation is observed after the
call. A plain Python `int` must be rejected for this signature.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.3 Read-Only Scalar Pointer Storage
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void read_count(const int *value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def read_count(value: Int[()]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify matching rank-zero scalar storage acceptance and exact native
pointer lowering without writable requirements.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.4 Array Pointer With Explicit Count
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
double sum_values(size_t n, const double *values);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, SizeT

def sum_values(n: SizeT, values: Float64[n]) -> Float64: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify that the caller passes `n`, that the wrapper passes it
unchanged, and that no hidden `len(values)` argument is generated.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.5 Explicit Output Storage
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void get_count(int *out);
void get_values(int n, double *out);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int

def get_count(out: Int[()]) -> None: ...
def get_values(n: Int, out: Float64[n]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify mutation of caller-allocated output storage and that the
functions return `None`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.6 Matrices And Pointer-To-Fixed-Array
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void matrix_data(double *matrix);
void matrix_rows(int (*matrix)[4]);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Float64, Int

def matrix_data(matrix: Float64[:, :]) -> None: ...
def array_data(values: Float64[...]) -> None: ...
def vector_matrix_or_rank5(values: Float64[...][1, 2, 5]) -> None: ...
def matrix_rows(matrix: Int[:, 4]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify one native pointer argument for each function, rank/shape
validation, and rejection of a representation treating either argument as
`T **`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.7 Direct Pointer Graph Identity
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
void use_rows(int **rows);
void update_value(int *****value);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Int

def use_rows(rows: Addr[2](Int)) -> None: ...
def update_value(value: Addr[5](Int)) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify exact pointer depth in the parsed ABI contract and that
these arguments accept only matching direct low-level pointer objects. They
must not accept `Int[:, :]` or add any `@native_call` transformation.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.8 Raw Opaque Pointer Identity
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
struct context;
struct context *context_create(void);
void context_destroy(struct context *ctx);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Opaque

class context(Opaque):
    pass

def context_create() -> context: ...
def context_destroy(ctx: context) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify that the returned raw native pointer object is accepted by
`context_destroy` without handle wrapping, ownership inference or
`@native_call`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.9 Symbol Binding Without Transformation
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```c
int library_add(int a, int b);
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int, bind

@bind("library_add")
def add(a: Int, b: Int) -> Int: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Tests must verify that `@bind` changes symbol lookup only and leaves
argument/return lowering unchanged.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
#### 13.10 Transformation Is Not Phase 1
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The Phase 1 parser or semantic conversion must reject a runnable interface using
later transformation syntax such as:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Arg, Int, Returns, native_call

@native_call([Addr(Arg(0))])
def increment(value: Int) -> Returns["value", Int]: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The safe Phase 1 spelling for the same C function is:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Int

def increment(value: Int[()]) -> None: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 14. Phase 2: Pythonic Adaptations After Identity Works
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
After Phase 1 can call direct signatures reliably, an optional Pythonic
generation mode can use `@native_call` to expose APIs that differ from their
C parameter lists. The settled design direction is:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```python
from prik.contracts import Addr, Annotated, Arg, Float64, Int, Return, Returns, SizeT, native_call, raises

# C: void increment(int *value);
@native_call([Addr(Arg(0))])
def increment_value(value: Int) -> Returns["value", Int]: ...

# C: void get_count(int *out);
@native_call([Return(0)])
def get_count() -> Int: ...

# C: double sum_values(size_t n, const double *values);
@native_call([As[SizeT](Arg(0).shape[0]), Arg(0)])
def sum_values(values: Float64[:]) -> Float64: ...

# C: void process_columns(const double *values, size_t n, ptrdiff_t stride_bytes);
@native_call([Arg(0), Arg(0).shape[1], Arg(0).strides[1]])
def process_columns(values: Float64[:, ::]) -> None: ...

# C: void get_values(int n, double *out);
@native_call([Arg(0), Return(0)])
def get_values(n: Int) -> Float64[n]: ...

# C: int context_create(struct context **out);
@native_call(
    [Return(0)],
    returns=Status[Int, Check(success=0, raises=RuntimeError)],
)
def context_create() -> Annotated[context, Owned, FreeWith("context_destroy")]: ...
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Phase 2 also introduces policies and coercions such as:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
- Python `str` to configured native text conversion;
- callback thunk creation and lifetime/exception handling;
- `Pack` and `CopyBack` for non-contiguous arrays;
- opaque handles and native ownership management;
- status conversion and hidden native outputs;
- derived NumPy metadata such as `Arg(i).shape`, `Arg(i).shape[...]`,
  `Arg(i).strides[...]`, `Arg(i).size` and `Arg(i).itemsize`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
None of these transformations is necessary to complete Phase 1.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
### 15. Decisions Deferred Beyond Phase 1
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The following decisions do not block the identity-call implementation:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
1. Final implementation order within Phase 2 transformations.
2. Bare-string convenience defaults, writable text buffers and arrays of
   strings.
3. Callback policies beyond the basic future design direction.
4. Convenience construction of pointer rows from nested Python sequences and
   other high-level builders for `T **` and deeper graphs. Direct
   `Addr[n](T)` pointer objects are already Phase 1 identity values.
5. Converting native pointer returns into NumPy views beyond explicitly shaped,
   explicitly owned or borrowed storage. Returning direct `Addr(T)` objects is
   already identity behavior.
6. Automatic derivation of hidden layout/stride arguments and packing or
   copy-back for storage the native routine does not accept directly.
7. Clean generated `.pyi` files for IDEs and type checkers.
8. Module/library selection, platform variants and non-default calling
   conventions.
9. Unions, writable native globals and variadic functions.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
No deferred behavior may be silently inferred by the Phase 1 wrapper
generator.
PRIK_C_DOCS_END -->
