---
# X2PY_C_DOCS: title: C Parser Reference
title: Deferred Parser Reference
audience: developers
prerequisites: repository structure, parser architecture
related: adding-a-feature.md, repository-structure.md
status: maintained
publication: draft
---

<!-- X2PY_C_DOCS_START

<!&#45;&#45; X2PY_C_DOCS_START
# C Parser Reference
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Status: current reference for the partial C frontend. The `x2py.parsers.c`
package, typed parser models, explicit C CLI parse path, raw directive
metadata, compiler-assisted preprocessing, source-location remapping, project
indexes, legacy parser schema snapshots, C standard-type probe, first semantic IR conversion
subset, semantic conversion path, and starter exact-contract C `.pyi`
generation are implemented.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
This file is the single maintained C parser reference. It replaces the older
standalone architecture and CLI workflow notes; keep parser behavior, public
API, command output, fixtures, semantic conversion, policy completion, and `.pyi`
changes documented here.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Parser-related pull requests should update this file when the documented
feature inventory, public API, diagnostics, project behavior, semantic handoff,
or maintenance workflow changes. The parser-reference guard checks C, Fortran,
and semantic `.pyi` references independently. It watches `x2py/parsers/c/`, `tests/parser/c/`,
`tests/data/c/`, and C standard-type probe tests and expects
`docs/developer/c-parser-reference.md` to change unless the PR is explicitly labeled to skip the
guard.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
## Purpose
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The C parser frontend is a wrapper-oriented source extraction system for
x2py. It extracts stable semantic information from C sources and
headers to help create or update the semantic interface layer.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The implementation must be grammar-style: lex and slice source into C grammar
regions, visit declarations and scopes recursively, reuse shared declarator/type
parsing helpers, and store typed model objects. It must not be implemented as a
giant regex parser, a whole-file scanner, or a compiler-wrapper-only frontend.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
It is not intended to be:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- a compiler-grade C frontend
- a full C preprocessor
- a replacement for semantic `.pyi` interfaces
- a libclang-only wrapper
- a C++ parser
- a complete ABI generator
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
## Source Coverage
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Supported source forms:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- `.c`
- `.h`
- `.i` preprocessed C input
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Project input accepts explicit files and directories in explicit C mode.
Directory scanning in C mode discovers C source/header inputs without changing
Fortran's default directory behavior. Project parsing does not recursively
parse files named by C includes: as with Fortran recorded imports/includes,
only user-supplied files or files beneath a user-supplied directory are parsed.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
## Current Status
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Implemented:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- `x2py.parsers.c` package
- typed C parser models for partial parse reports and raw metadata
- `CParser`, `parse_c_file`, and `parse_c_project`
- top-level `x2py.parse_c_file` and `x2py.parse_c_project` exports alongside
  the `x2py.parsers.c` package entrypoints
- `CParseError` with compiler-style diagnostic formatting
- explicit `x2py &#45;&#45;language c &#45;&#45;parse` output
- explicit `x2py &#45;&#45;language c &#45;&#45;semantics` output
- starter exact-contract `x2py &#45;&#45;language c &#45;&#45;pyi` output for the supported C
  semantic subset
- C JSON partial output and `&#45;&#45;out` behavior
- raw lexer records with comment stripping, line-continuation folding, and
  lightweight token source locations
- top-level source splitting that tracks braces, parentheses, brackets, and
  string/character literals
- raw `#include` collection for quoted and system includes
- raw `#pragma` provenance metadata, including OpenMP declaration pragmas
- strict `CPARSE_PREPROCESSING_REQUIRED` failures for raw macro, conditional,
  macro-include, and other directives that require a real preprocessor
- concrete primitive `CType` objects, pointer/array composition, and concrete
  qualifier objects
- order-insensitive primitive specifier matching with
  `CPARSE_INVALID_SPECIFIER_SEQUENCE` errors for
  invalid combinations such as `unsigned float`
- recursive declarator extraction for parenthesized pointer/array precedence
- nameless `CFunctionType` signatures for function pointer typedefs and
  parameter source facts
- parameter array/function adjustment that keeps written `declared_type` facts
  and exposes effective pointer `type` facts
- simple file-scope variable and `typedef` extraction
- incomplete `struct name;` and `union name;` extraction as concrete tag types
  with `is_incomplete=True`
- named and anonymous struct/union/enum definitions
- aggregate member extraction as `CVariable` objects through the declarator
  backend, including pointer, array, callback-pointer, flexible-array, and
  bit-field source facts with per-member locations
- conservative parser diagnostics for function signatures that use unions by
  value, while pointer-to-union signatures remain ordinary parser facts
- inline tag typedef aliases and trailing tag object declarators as separate
  concrete models
- simple function prototype extraction
- prototype-style metadata distinguishing `int f(void)` from `int f()`
- simple function-definition signature extraction with body skipping
- start/end locations for function definitions, from the signature start
  through the closing brace
- braced and designated initializer source preservation on `CVariable`
- nested anonymous struct/union member definitions as concrete member types
- `_Atomic(type)` type specifiers, preserving the qualified outermost type
  component
- compiler/preprocessed input parsing through the same grammar path with
  `#line`/GCC linemarker remapping for parsed declarations and diagnostics
- file-level preprocessing metadata plus generated/original source identity
  for direct `.i` input where linemarkers provide it
- optional `preprocessing_recipe` JSON on `CFile` output for compiler streams
  generated by the shared x2py CLI
- compiler-derived target ABI probing for every modeled arithmetic primitive,
  `size_t`, `uint32_t`, `time_t`, and opaque `FILE` handles through
  `x2py.probes.c_types`, with reusable memory and persistent caches
- C directory/file-list discovery for `.c`, `.h`, and direct `.i` inputs in
  explicit C mode, while leaving Fortran directory scanning unchanged
- include resolution for quoted includes relative to the current file and
  configured include directories, unresolved include tracking, system include
  tracking, cycle-safe include graph construction, and header/source pairing,
  without recursive include parsing
- project indexes for functions, file-scope variables, typedefs, struct tags,
  union tags, enum tags, enum constants, compiler-recipe macros/constants, and
  functions by file
- basic cross-file typedef chain and struct/union/enum tag resolution, with
  typedef-cycle diagnostics and unresolved references preserved for later
  diagnostics
- unsupported K&R function-definition diagnostics
- legacy C parser project JSON schema snapshots and active fatal diagnostic
  goldens generated from stable `CParseError` output
- C fixture inputs under `tests/data/c/general/`, diagnostic inputs under
  `tests/data/c/errors/parser/`, and partial-parser regression inputs under
  `tests/data/c/json/`, `tests/data/c/tinyexpr/`, `tests/data/c/linmath/`,
  `tests/data/c/nanosvg/`, and top-level C inputs from `tests/data/c/stb/`
- `semantics.c2ir` conversion for the first identity subset: scalar
  functions, const/mutable pointer storage contracts, declared arrays,
  structs/opaque structs, enums, numeric macro constants, local typedef
  chains, standard-type probe facts, and explicit semantic conversion errors
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Still deferred:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- callback policy metadata beyond parser-side callback candidates
- broad compiler-extension declarators
- broader typedef/tag conflict policy beyond the implemented basic project
  resolution
- richer C ownership/callback projection policy beyond exact starter `.pyi`
  stubs
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
## Supported C Subset
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The supported subset focuses on stable wrapper-relevant APIs:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- function prototypes
- function definitions with extractable signatures
- primitive C scalar types
- pointers
- arrays in parameters and aggregate members
- `const`, `restrict`, and `volatile` qualifiers
- `static` and `extern` storage classes where wrapper-relevant
- `struct` definitions
- `union` definitions
- `enum` definitions and enumerators
- `typedef` declarations
- simple global constants
- simple object-like numeric and string macros
- include dependency tracking
- cross-file typedef and tag resolution within parsed project files
- compiler/preprocessed-mode tolerance for common GCC/Clang and MS declaration syntax:
  GNU attributes, `__declspec(...)`, `[[...]]`, `__extension__`, alternate
  qualifier/inline spellings, declaration-level `asm(...)`, calling-convention
  keywords, `typeof(...)`, `_BitInt(...)`, and selected extended scalar names
X2PY_C_DOCS_END &#45;&#45;>

## Unsupported And Deferred Subset

<!&#45;&#45; X2PY_C_DOCS_START
The C parser explicitly reports or defers:
X2PY_C_DOCS_END &#45;&#45;>

- full preprocessor compatibility
- arbitrary macro expansion
- token pasting and stringification
- macro-generated declarations
- complex conditional compilation evaluation
- arbitrary GCC extensions
- arbitrary MSVC extensions
- full ABI generation
- inline assembly
- `_Generic` semantic evaluation
- atomic operation semantics and validation beyond parsed type facts
- full semantic modeling of compiler attributes, calling conventions, assembler
  aliases, `typeof(...)`, `_BitInt(...)`, and extended scalar ABI facts

<!&#45;&#45; X2PY_C_DOCS_START
- K&R style function definitions
- guaranteed struct layout computation
- full bitfield ABI interpretation
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- full compiler-grade C parsing
- C++ parsing
X2PY_C_DOCS_END &#45;&#45;>

## Preprocessing Policy

<!&#45;&#45; X2PY_C_DOCS_START
The C parser should be preprocessor-aware, but it should not become a partial
C preprocessor. Partial macro support is risky in C because macros can define
function names, type names, attributes, calling conventions, parameter lists,
and whole declarations. The parser must not infer a public API from unexpanded
macro-shaped declarations.
X2PY_C_DOCS_END &#45;&#45;>

Raw-source mode means source normalization plus safe directive metadata:

- strip comments and fold backslash-newline continuations while preserving
  source locations
- record `#include` directives as structured include dependencies
- record pragma directives as raw provenance metadata,
  including OpenMP declaration pragmas such as `#pragma omp declare simd` and
  `#pragma omp declare target`
- raise `CPARSE_PREPROCESSING_REQUIRED` for raw macro definitions, undefines,
  conditionals, macro includes, and other directives that require expansion or
  branch selection

<!&#45;&#45; X2PY_C_DOCS_START
- parse only declarations that are already visible as ordinary C without macro
  expansion
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Compiler-assisted preprocessing is required whenever raw C input contains
directives beyond literal includes and pragmas. The user normally gives x2py
`.h` or `.c` files and has it run the configured compiler/preprocessor; direct
`.i` preprocessed inputs are also accepted and use their linemarkers for
locations and source identity. Compiler-recipe macro metadata remains attached
to parse reports for provenance.
X2PY_C_DOCS_END &#45;&#45;>

Examples:

<!&#45;&#45; X2PY_C_DOCS_START
```bash
python -m x2py include/api.h &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler clang-18 \
  -I include \
  -D API_EXPORT= \
  &#45;&#45;std c11

python -m x2py src/api.c &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compiler /usr/bin/gcc-13 \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/sdk

python -m x2py src/api.c &#45;&#45;language c &#45;&#45;parse \
  &#45;&#45;compile-commands build/compile_commands.json
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
`&#45;&#45;compiler` must be the exact executable x2py should run. Versioned names
such as `gcc-13`, `clang-18`, and `/usr/bin/gfortran-12` are preferred over a
generic `gcc`, `clang`, or `gfortran` when several compiler versions are
installed.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Preprocessed mode preserves line mapping. The parser reads
compiler-preprocessed text, including `#line`/linemarker directives, and maps
every parsed declaration, source location, and diagnostic back to the original
`.h` or `.c` file and line number where possible. Without this mapping, errors
and JSON source locations would point at a generated `.i` file or temporary
preprocessor stream instead of the user's source.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
This means macro-heavy APIs are still in scope. The boundary is that x2py v1
should not implement recursive, compiler-compatible macro expansion
internally; it should consume compiler-preprocessed output with preserved line
mapping. When the shared x2py CLI generates a compiler-preprocessed stream, it
stores `preprocessing_recipe` in the per-file `CFile` JSON: compiler
executable, final argv, include dirs, defines, undefines, standard, extra
arguments, working directory, and optional selected `compile_commands.json`
entry. Parsed declarations from compiler or direct `.i` input keep mapped
source locations; direct `.i` files also expose `preprocessed_source_path` and
mapped `original_source_paths` where available.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
## C Type ABI Probe
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
C primitive spellings and types introduced by standard headers are target
facts. Plain `char` signedness, `long` width, `long double` representation,
`size_t`, and `time_t` can vary with compiler target and flags. `FILE` should
remain an opaque library handle rather than exposing private library layout.
Raw parsing therefore remains source-faithful instead of embedding an ABI.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
For direct compiler-backed C semantic and `.pyi` stages, the shared
CLI automatically compiles and runs a small C11 query under the selected
compiler. The standalone command emits the same target-specific report:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
```bash
python3 -m x2py probe &#45;&#45;language c &#45;&#45;compiler /usr/bin/gcc-13 &#45;&#45;std c11
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The report records arithmetic category, underlying C spelling, bit width, and
alignment for all modeled primitive integer, real, and complex types plus
`size_t`, available `uint32_t`, and `time_t`. It records plain `char`
signedness, real mantissa precision and exponent range, and opaque handle and
pointer ABI facts for `FILE`. It also retains the generated C source and exact
compile/run commands. Semantic conversion keeps the name `Int` for builtin C
`int`, stores its measured concrete dtype separately, and maps other primitives
to the measured target width. Unsupported measured widths produce an explicit
semantic conversion error.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The probe must be run with the same target profile as the source being parsed.
It carries `-I`, `-D`, `-U`, and `&#45;&#45;compiler-arg` options into the compile
command because ABI and standard-header typedef facts can change with target
flags, sysroots, library headers, and compiler options. The requested `&#45;&#45;std`
is retained as provenance; the generated query is compiled as C11 because it
uses C11 `_Generic` and `_Alignof`. If a standard-selection flag affects the
target profile and is compatible with the probe source, pass it through
`&#45;&#45;compiler-arg` so it is part of the actual compile command.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Automatic results are cached in memory and persistently. The cache key includes
the probe schema/source, resolved compiler binary identity, target flags,
includes, defines, undefines, requested standard, working directory,
target-related compiler environment, and runner executable/arguments. The
default persistent location is `$XDG_CACHE_HOME/x2py/c_type_probe` or
`~/.cache/x2py/c_type_probe`; `X2PY_CACHE_DIR` changes the internal cache root.
The standalone `x2py probe` command exposes `&#45;&#45;cache-dir` and `&#45;&#45;refresh` for
explicit inspection runs.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The probe does not consume `compile_commands.json` or custom preprocessing
templates directly because one project may contain different target recipes.
Generate a report with the selected compiler and target-relevant flags when you
want to inspect that target:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
```bash
python3 -m x2py probe &#45;&#45;language c &#45;&#45;compiler clang \
  &#45;&#45;compiler-arg=&#45;&#45;target=aarch64-linux-gnu \
  &#45;&#45;compiler-arg=&#45;&#45;sysroot=/opt/aarch64-sysroot \
  &#45;&#45;runner=qemu-aarch64 &#45;&#45;runner=-L &#45;&#45;runner=/opt/aarch64-sysroot \
  > build/aarch64-c-types.json
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The report is an inspection output. Direct-compiler semantic stages measure
their required ABI facts internally; the parser model remains source-faithful
and does not embed host ABI assumptions.
X2PY_C_DOCS_END &#45;&#45;>

## Parser Organization Notes

<!&#45;&#45; X2PY_C_DOCS_START
`x2py/parsers/c/parser.py` is intentionally ordered for maintainers. Read it from
top to bottom in these sections:
X2PY_C_DOCS_END &#45;&#45;>

1. Parser constants, private grammar dataclasses, and small path helpers.
3. Source-location, diagnostic, macro-provenance, and redeclaration helpers.
4. Declaration-specifier and compiler-extension lexical helpers.
6. Function and aggregate visitors.
7. Translation-unit dispatch and project assembly.

<!&#45;&#45; X2PY_C_DOCS_START
5. Recursive declarator grammar and parameter helpers.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
2. `CParser` public parse entrypoints: `parse_file` and `parse_project`.
   `_assemble_project` is the internal already-parsed-file assembly helper.
8. Thin module-level wrappers: `parse_c_file` and `parse_c_project`.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Helper methods remain on `CParser` when they depend on parser state. Their
docstrings describe the narrow parsing responsibility and include examples
where call shape or grammar behavior is not obvious.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
`_assemble_project(files)` assembles translation units that a caller has
already parsed individually. The x2py CLI uses it after compiler preprocessing
and recipe attachment. Most callers should use `parse_c_project(...)`, which
handles source loading before delegating to the same project assembly path.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The C parser now lives under the main `x2py` package. The legacy top-level
`c_parser` package entrypoint was removed, so direct parser imports should use
`x2py.parsers.c` or the stable top-level `x2py` exports. This keeps parser
models, CLI wiring, semantic conversion, and wrapper-facing entrypoints in one
package tree.
X2PY_C_DOCS_END &#45;&#45;>

## Public API

Implemented top-level and package entrypoints:

<!&#45;&#45; X2PY_C_DOCS_START
```python
from x2py import parse_c_file, parse_c_project
# Equivalent parser-package imports remain available:
# from x2py.parsers.c import parse_c_file, parse_c_project
```
X2PY_C_DOCS_END &#45;&#45;>

Implemented signatures:

<!&#45;&#45; X2PY_C_DOCS_START
```python
parse_c_file(
    source_or_path,
    filename=None,
    include_dirs=None,
    preprocessing="raw",
    encoding="utf-8",
)

parse_c_project(
    files,
    include_dirs=None,
    preprocessing="raw",
    encoding="utf-8",
)

```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
These return typed parser models analogous to the Fortran parser API. The
current partial phase can populate `functions`, `structs`, `unions`, `enums`,
`typedefs`, `variables`, `includes`, `macros`, and metadata `diagnostics`.
Incomplete `struct name;` and `union name;` declarations are concrete
`CStruct`/`CUnion` types with `is_incomplete=True` and source locations. The
parser returns concrete objects instead of a declaration-kind tag:
`CFunction`, `CVariable`, `CTypedef`, `CStruct`, `CUnion`, and `CEnum`.
A declaration such as
`typedef struct node { int value; } node_t;` produces a `CStruct` plus a
`CTypedef`, while `struct point { int x; } origin;` produces a `CStruct` plus
a `CVariable`.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
All types inherit from `CType`. Implemented primitive type classes are
`CVoid`, `CBool`, `CChar`, `CSignedChar`, `CUnsignedChar`, `CShort`,
`CUnsignedShort`, `CInt`, `CUnsignedInt`, `CLong`, `CUnsignedLong`,
`CLongLong`, `CUnsignedLongLong`, `CFloat`, `CDouble`, `CLongDouble`,
`CFloatComplex`, `CDoubleComplex`, and `CLongDoubleComplex`. Qualifiers are
`CConst`, `CVolatile`, `CRestrict`, and `CAtomic`, attached to the precise
type component they qualify. `_Atomic int value;` is stored with a `CAtomic`
qualifier; `_Atomic(int) value;` is represented the same way, while
`_Atomic(int *) value;` qualifies the pointer component. Equivalent primitive orderings, such as
`int unsigned` and `double long`, map to the same concrete type while
invalid combinations, such as `unsigned float`, raise `CParseError` with code
`CPARSE_INVALID_SPECIFIER_SEQUENCE`. A single unresolved typedef-name use remains a `CTypedef`
until resolution can establish whether a matching declaration exists.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Nested declarators are `CComposedType` objects whose `components` are read
from the declared name outward:
X2PY_C_DOCS_END &#45;&#45;>

```python
int *values[4];       # CComposedType([CArray(bound="4"), CPointer(), CInt()])
int (*matrix)[4];     # CComposedType([CPointer(), CArray(bound="4"), CInt()])
int *(*table)[4];     # CComposedType([CPointer(), CArray(bound="4"), CPointer(), CInt()])
```

<!&#45;&#45; X2PY_C_DOCS_START
`CFunction` has `result_type` and named `CParameter` objects. Its `.type`
property provides the corresponding nameless `CFunctionType`, which is also
used inside pointer typedefs and variables:
X2PY_C_DOCS_END &#45;&#45;>

```python
int add(int a, int b);     # CFunction(name="add", result_type=CInt(), parameters=[...])
int (*compare)(int, int);  # CVariable(type=CComposedType([CPointer(), CFunctionType(...)]))
```

<!&#45;&#45; X2PY_C_DOCS_START
Function parameters preserve both the written type and C's adjusted callable
type:
X2PY_C_DOCS_END &#45;&#45;>

```python
void process(int values[4], int callback(int));
# values.declared_type: CComposedType([CArray(bound="4"), CInt()])
# values.type:          CComposedType([CPointer(), CInt()])
# callback.declared_type: CFunctionType(...)
# callback.type:          CComposedType([CPointer(), CFunctionType(...)])
```

<!&#45;&#45; X2PY_C_DOCS_START
Callback-bearing parameters are marked as parser-side callback candidates,
without claiming semantic wrappability. Struct and union `members` are
`CVariable` objects; optional `bit_width` and `initializer` fields preserve
source facts without inventing separate field or valued-variable classes.
Member records carry their own field location. A legal final incomplete array
member in a struct is marked as `CArray(is_flexible=True)`; non-final,
sole-member, and union incomplete-array member forms are retained with
`C_INVALID_FLEXIBLE_ARRAY_MEMBER` error diagnostics.
In compiler/preprocessed mode, common compiler declaration syntax is normalized
before grammar parsing.
Harmless attributes are accepted without dropping their declarations. Ignored
extensions that can affect layout, calling convention, symbol identity, or type
identity produce `C_UNMODELED_COMPILER_EXTENSION` warnings with explicit
`unit_kind` values. Static assertions remain diagnostic-only. Grammar-invalid
input raises `CParseError`; identifier spellings are not used to guess that
input belongs to another language.
Unconsumed declarator suffixes are also diagnosed instead of producing partial
objects. Functions
include `prototype_style`, currently `"prototype"` for
typed or explicit `void` parameter lists and `"unspecified"` for empty
parameter lists such as `int f()`. Function definitions do not store
executable body text; they include direct `start` and `end` locations.
Compatible top-level function redeclarations are merged, and a matching
prototype plus definition prefers the definition while retaining the prototype
location in `declaration_locations`. File-scope tentative variable
declarations such as `int i; int i;` are merged; a later initialized
definition such as `int i = 1;` is preferred over an earlier tentative
declaration. Duplicate initialized variables, duplicate function definitions,
duplicate complete tag definitions, and incompatible top-level redeclarations
produce diagnostics. Local declarations inside function bodies are ignored
because body contents are intentionally skipped.
`x2py` exports the C file/project entrypoints in the same style as the
Fortran entrypoints. The typed C parser package remains importable directly.
X2PY_C_DOCS_END &#45;&#45;>

Example: parse one header from Python.

<!&#45;&#45; X2PY_C_DOCS_START
```python
from x2py import parse_c_file

parsed = parse_c_file("include/api.h")
print([function.name for function in parsed.functions])
print([typedef.name for typedef in parsed.typedefs])
```
X2PY_C_DOCS_END &#45;&#45;>

Example: parse a small project with include directories.

<!&#45;&#45; X2PY_C_DOCS_START
```python
from x2py import parse_c_project

project = parse_c_project(["src/api.c", "include/api.h"], include_dirs=["include"])
print(project.include_graph)
print(project.header_source_pairs)
```
X2PY_C_DOCS_END &#45;&#45;>

Example: parse compiler-preprocessed text produced by the shared x2py CLI.

<!&#45;&#45; X2PY_C_DOCS_START
```bash
python -m x2py include/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json \
  &#45;&#45;compiler clang-18 \
  -I include \
  -D API_EXPORT=
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Project-level facts require `parse_c_project(...)`, not just
`parse_c_file(...)`. A single file can report its own pragmas, includes,
compiler-recipe macros, declarations, diagnostics, and unresolved typedef/tag
references. A project parse sees multiple files together and can populate
include graphs, system include records, unresolved include sets, functions by
file, enum constants, likely header/source pairs, and basic cross-file
typedef/tag links.
An include edge is metadata only: a resolved local or system header is not
parsed unless it is also supplied as a project input or falls beneath a
directory input. Generated headers and direct `.i` streams follow that same
explicit-input rule. Include-graph keys use project input/path identity; they
are not module keys.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Raw mode does not evaluate C preprocessor conditionals or expand macros
internally. It rejects those directives before grammar parsing. Compiler mode
receives the already-expanded translation unit from `x2py.pipeline.preprocessing`.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The parser itself should stay parse-only. If the C frontend later gains
wrappability assessment, that should live in the semantic layer after C parser
models are converted to semantic IR or edited `.pyi` policy is loaded, matching
the current Fortran and `.pyi` wrapper-planning boundary.
X2PY_C_DOCS_END &#45;&#45;>

## CLI Usage

<!&#45;&#45; X2PY_C_DOCS_START
Explicit C mode:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
```bash
x2py path/to/api.h &#45;&#45;language c &#45;&#45;parse
x2py path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json
x2py path/to/api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;out report.json
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
There is no separate `&#45;&#45;parse-c` alias: `&#45;&#45;language c &#45;&#45;parse` is the shared
language-selection form. Auto-detection remains deferred: a `.c`, `.h`, or
`.i` input without `&#45;&#45;language c` exits with language-selection guidance.
Explicit C input containing syntax that cannot be consumed by the modeled C
grammar raises a fatal parser diagnostic instead of emitting a partial C
interface.
X2PY_C_DOCS_END &#45;&#45;>

## Current JSON Output

Per-file shape:

<!&#45;&#45; X2PY_C_DOCS_START
```text
{
  "<path>": {
    "filename": "<path>",
    "language": "c",
    "preprocessing": "raw",
    "preprocessing_recipe": "<present only for x2py-generated compiler input>",
    "functions": [
      {
        "name": "run",
        "result_type": {"model": "CInt", "qualifiers": [], "source_text": "int"},
        "parameters": [],
        "storage": [],
        "specifiers": [],
        "is_variadic": false,
        "is_definition": false,
        "prototype_style": "prototype",
        "source_location": {"filename": "<path>", "line": 1, "...": "..."},
        "start": {"filename": "<path>", "line": 1, "...": "..."},
        "end": null
      }
    ],
    "structs": [],
    "unions": [],
    "enums": [],
    "typedefs": [],
    "variables": [],
    "macros": [],
    "includes": [],
    "diagnostics": []
  }
}
```
X2PY_C_DOCS_END &#45;&#45;>

JSON compatibility rules:

- prefer additive schema changes
- serialize concrete `CType` identity using `"model"`; reserve `"type"` for
  actual type relationships such as `CTypedef.type`
- serialize qualifier objects as canonical spellings such as `"const"`
- include `source_location` for declaration/directive records and `location`
  for diagnostics
- preserve unknown or unresolved information rather than dropping it silently
- keep model fields stable enough for golden fixture testing
- document every intentional schema break

<!&#45;&#45; X2PY_C_DOCS_START
- emit references for reused aggregate or typedef objects rather than
  recursive JSON cycles
X2PY_C_DOCS_END &#45;&#45;>

## Semantic And Wrapper-Planning Boundary

The parser should not assess wrappability.

<!&#45;&#45; X2PY_C_DOCS_START
Any future C wrapper-planning rules should be implemented after the parser output is
converted to semantic IR, or after an edited `.pyi` file provides the missing
policy. That keeps the C parser aligned with the current project rule that
policy completion is a semantic concern, not a parser concern.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
For C callback-bearing APIs, the parser should still preserve enough source
facts to let later semantic work decide what is safe:
X2PY_C_DOCS_END &#45;&#45;>

- callback signature
- callback direction: native-to-Python, Python-to-native, or both
- lifetime: call-only, stored by native, or released by a specific API
- associated context/userdata parameter
- nullability rules
- non-default calling convention
- threading or async behavior
- ownership of callback and context memory
- release/unregistration API
- exception/error policy for Python callback failures

Those facts should be stored in parser models, but not turned into a parser-side
`wrappable` report.

## Error Handling

<!&#45;&#45; X2PY_C_DOCS_START
The parser defines `CParseError` with:
X2PY_C_DOCS_END &#45;&#45;>

- `filename`
- `line_number`
- `column`
- `source_line`
- `base_message`
- `code`
- internal parser raise location for debug mode
- `format_diagnostic(color=False, debug=None)`

<!&#45;&#45; X2PY_C_DOCS_START
The CLI should print compiler-style diagnostics without tracebacks by default.
The parser has the error type and formatter. Raw directive collection can emit
non-fatal metadata diagnostics, such as unresolved local includes or macros
that affect declarations but were recorded rather than expanded. K&R-style function
definitions now raise `CParseError` because the current function parser only
models prototype-style declarations and definitions. Invalid primitive
specifier combinations also raise `CParseError`
(`CPARSE_INVALID_SPECIFIER_SEQUENCE`) because their
invalidity does not depend on later typedef resolution. Known unsupported
declaration extensions are diagnosed rather than partially modeled; additional
syntax diagnostics should be added only with focused tests.
Generic grammar rejection uses `CPARSE_INVALID_SYNTAX`. Diagnostic codes are
stable, explicit category identifiers for tests, tools, and documentation. The
shared registry is [`diagnostic-codes.md`](../user/reference/diagnostic-codes.md).
X2PY_C_DOCS_END &#45;&#45;>

## Testing Workflow

Test families should mirror the Fortran parser:

- focused lexer tests
- declaration-specifier tests
- function prototype tests
- function definition tests
- macro/constant tests
- include/project tests
- CLI tests
- semantic conversion tests
- `.pyi` generation/parser tests
- legacy JSON schema golden tests
- error fixture/golden tests
- corpus parse-only tests

<!&#45;&#45; X2PY_C_DOCS_START
- declarator parser tests
- struct/union/enum tests
- typedef tests
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
- C semantic conversion tests
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The C test area contains active partial-parser/raw-metadata tests, including
parse-only cJSON regression coverage under `tests/parser/c/`. The active tests cover
public entrypoints, empty model serialization, CLI discovery, JSON/output-file
behavior, unsupported C stages, comment stripping, line-continuation folding,
top-level splitting, include collection, pragma metadata, raw preprocessing
rejection, explicit-input/non-recursive project include behavior, simple declarations,
variables, typedefs, top-level redeclaration diagnostics, recursive declarator
composition, aggregate definitions, members, enums, simple function
prototypes/definitions, function-definition start/end locations, legacy JSON
schema snapshots, fatal diagnostic goldens, and project-level callback typedef
resolution. The `json` regression inputs
intentionally retain recoverable diagnostics from unsupported constructs; they
do not claim complete library parsing. A separately pinned/provenanced corpus
target remains deferred without disabling parser tests. Golden comparison tests rewrite their baselines when
`C_PARSER_UPDATE_GOLDENS=1` is set. Future implementation branches should
activate only the tests for the capability they implement.
X2PY_C_DOCS_END &#45;&#45;>

Useful local checks for the parse-only frontend:

<!&#45;&#45; X2PY_C_DOCS_START
```bash
python -m x2py tests/data/c/general/math_api.h &#45;&#45;language c &#45;&#45;parse &#45;&#45;json
python tests/parser/c/generate_c_parser_goldens.py tests/data/c/general/math_api.h
pytest -q tests/parsing/c/test_c_declarations_and_declarators.py
pytest -q tests/parsing/c/test_c_fixture_suite.py
pytest -q tests/parser/c tests/probes/test_c_types.py tests/pipeline/preprocessing/ tests/cli/ tests/probes/test_fortran_types.py tests/semantics tests/pyi
pytest -q
```
X2PY_C_DOCS_END &#45;&#45;>

Focused test files by implementation area:

<!&#45;&#45; X2PY_C_DOCS_START
- Lexer, comments, continuations, raw directive handling:
  `tests/parsing/c/test_c_lexer_preprocessor.py`
- Declaration specifiers, qualifiers, declarators, arrays, pointers,
  callbacks, and variables:
  `tests/parsing/c/test_c_declarations_and_declarators.py`
- Function prototypes and definitions:
  `tests/parsing/c/test_c_functions.py`
- Structs, unions, enums, typedefs, and aggregate members:
  `tests/parsing/c/test_c_structs_unions_enums_typedefs.py`
- Project assembly, include graph facts, typedef/tag resolution, and
  redeclarations:
  `tests/parsing/c/test_c_project_resolution.py`
- Compiler extension tolerance and diagnostics:
  `tests/parsing/c/test_c_compiler_extensions.py`
- Corpus/third-party-style fixtures:
  `tests/parsing/c/test_c_corpus.py`
- Project golden fixtures:
  `tests/parsing/c/test_c_fixture_suite.py`
- Parser JSON shape:
  `tests/parsing/c/test_c_json_sanity.py`
- Fatal parser diagnostic goldens:
  `tests/parsing/c/test_c_error_fixture_suite.py`
- Public API and developer tutorial:
  `tests/parsing/c/test_c_public_api_skeleton.py` and
  `tests/parsing/c/test_c_parser_developer_tutorial.py`
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
When adding or changing a C parser feature, add the smallest focused test first
and only update project goldens when the serialized project contract
intentionally changes.
X2PY_C_DOCS_END &#45;&#45;>

### Declaration Coverage Boundary

Active declaration tests currently cover:

- every implemented primitive spelling and selected reordered equivalent
  spellings mapped to their concrete `CType`
- pointer/array precedence, multidimensional arrays, parameter VLA/static
  metadata and pointer adjustment, function-declared callback adjustment,
  function pointers, callback arrays, and functions returning function
  pointers
- legal and invalid flexible array members, precise field locations, and
  named/unnamed/zero-width bit-field source facts
- concrete-type JSON serialization, source locations, and cycle-safe aggregate
  references
- `_Atomic int` and `_Atomic(type)` qualifier placement on scalar and pointer
  declaration forms

<!&#45;&#45; X2PY_C_DOCS_START
- all qualifier objects, storage metadata, simple/braced/designated initializer
  source text, and multiple declarators
- functions, variables, typedefs, struct/union members, enums, incomplete
  tags, inline aggregate aliases, anonymous aggregate typedefs, and recursive
  struct pointers
- tolerance for common GNU/MS declaration extensions, explicit warnings for
  unmodeled ABI-relevant extension semantics, and diagnostics for K&R
  definitions and remaining trailing declarator extensions
- fatal diagnostics for grammar-invalid syntax and invalid primitive-specifier
  combinations while unresolved single typedef-name uses remain deferred
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
This is enough coverage for the currently implemented subset, not for all C
declarations.
X2PY_C_DOCS_END &#45;&#45;>

### Missing Implementation With Examples

<!&#45;&#45; X2PY_C_DOCS_START
| Capability | C example | Current parser boundary | Needed behavior |
| &#45;&#45;- | &#45;&#45;- | &#45;&#45;- | &#45;&#45;- |
| Typedef/tag resolution | `typedef unsigned long size_t; size_t count(void);` and `struct state { int id; }; void step(struct state *s);` | Basic project parsing links typedef chains and struct/union/enum tag references while preserving unresolved objects when context is absent. | Deepen conflict policy for broader projects; included/generated files are parsed only when supplied as project inputs. |
| Preprocessed declarations | `#define API(ret) ret` followed by `API(int) run(void);` | Raw mode raises `CPARSE_PREPROCESSING_REQUIRED`; compiler or `.i` mode parses expanded declarations and maps locations through `#line` markers; x2py-generated streams also record their recipe. | Broaden fixture-driven extension and compiler-family coverage. |
| Additional extension families | `int run(void) __attribute__((visibility("default")));` | Common GNU/MS declaration syntax is accepted; ignored ABI-, layout-, symbol-, or type-relevant semantics produce `C_UNMODELED_COMPILER_EXTENSION`. Broader compiler extensions are not modeled. | Add fixture-driven tolerance or a focused diagnostic for each required extension family. |
X2PY_C_DOCS_END &#45;&#45;>

### Represented With Focused Tests

These forms are represented by the current parser and have dedicated active
regression tests:

<!&#45;&#45; X2PY_C_DOCS_START
```c
const int * const * volatile chain;
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
The current parser creates distinct qualified `CPointer` components for
`chain`, preserving each qualifier on the exact component it qualifies.
Nested declarations such as `struct outer { struct { int x; } inner; };`
build an anonymous `CStruct` used by member `inner`; preprocessed forms retain
mapped nested member locations recursively.
Atomic declarations such as `_Atomic(int *) p;` qualify the pointer component,
while `_Atomic(int) *p;` qualifies the pointed-to integer component.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
For an executable maintainer walkthrough of the parser gateway and
preprocessed source path, read
`tests/parsing/c/test_c_parser_developer_tutorial.py`.
X2PY_C_DOCS_END &#45;&#45;>

## CLI Workflow

<!&#45;&#45; X2PY_C_DOCS_START
The C frontend is always selected explicitly:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
```bash
x2py &#45;&#45;language c &#45;&#45;parse path/to/api.h
x2py &#45;&#45;language c &#45;&#45;semantics path/to/api.h
x2py &#45;&#45;language c &#45;&#45;pyi path/to/api.h
```
X2PY_C_DOCS_END &#45;&#45;>

`&#45;&#45;parse` emits parser facts only. `&#45;&#45;semantics` converts the implemented
identity subset to the shared semantic IR. `&#45;&#45;pyi` emits starter
exact-contract stubs for supported declarations.

Raw macro-heavy files should be preprocessed through the compiler-assisted path
before parsing. Direct `.i` input and compiler streams preserve original source
locations through linemarker remapping where the compiler provides enough
information.

## Maintainer Architecture Notes

The parser is intentionally grammar-style and model-first:

- split top-level declarations while tracking braces, parentheses, brackets,
  strings, and comments
- record unsupported preprocessor forms as diagnostics instead of silently
  guessing
- keep source locations on parsed declarations and diagnostics
- defer wrapping policy to semantic conversion and policy-completion layers

<!&#45;&#45; X2PY_C_DOCS_START
- parse declarations through shared declarator/type helpers
- resolve project-level typedefs and tags after per-file parsing
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
C parsing must remain opt-in so Fortran directory parsing keeps its historical
behavior. Include resolution records graph facts and header/source pairing, but
does not recursively parse arbitrary include trees as new inputs.
X2PY_C_DOCS_END &#45;&#45;>

## Implementation Guide For New Frontends

<!&#45;&#45; X2PY_C_DOCS_START
Use the C parser as the model for adding another C-family frontend, such as a
future C++ parser, but copy the architecture rather than the exact grammar.
X2PY_C_DOCS_END &#45;&#45;>

Recommended package shape:

```text
new_parser/
  __init__.py
  __main__.py
  cli.py
  lexer.py
  models.py
  parser.py
```

The frontend should expose thin public functions from both its parser package
and `x2py`, then keep implementation details inside the parser package:

- `models.py`: source locations, diagnostics, typed declarations, typed native
  types, per-file reports, and project reports.
- `lexer.py`: comment stripping, continuation handling, token/source-location
  helpers, and any frontend-local raw directive collection.
- `parser.py`: grammar-style source slicing, recursive declaration parsing,
  project assembly, and public `parse_*` wrappers.
- `cli.py`: only frontend-specific formatting or package entrypoint behavior.
  The shared `x2py` CLI should own cross-language stage dispatch.

<!&#45;&#45; X2PY_C_DOCS_START
The C data flow is:
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
```text
source path or source text
  -> optional compiler preprocessing and source mapping
  -> CParser.parse_file(...)
  -> CFile parser facts
  -> CParser._assemble_project(...) or parse_c_project(...)
  -> CProject indexes and cross-file resolution facts
  -> semantics.c2ir conversion
  -> policy completion and `.pyi`; a C-input runtime wrapper backend comes later
```
X2PY_C_DOCS_END &#45;&#45;>

Keep these boundaries:

- The parser records source facts. It does not decide Python ownership,
  callback lifetime, ABI-safe calling shims, or projected wrapper signatures.
- Preprocessing belongs to the compiler/toolchain adapter. The parser consumes
  expanded source and uses linemarkers/source maps to report original
  locations.
- Project parsing is explicit-input based. Includes become dependency facts;
  they are not recursive parse roots unless supplied by the user.
- Semantic conversion is the first place where parser-native facts become the
  shared language-neutral model.

The parser algorithm should remain grammar-style:

1. Normalize only source mechanics that are independent of the language
   semantics, such as comments and continuations.
2. Collect raw directives that can be represented safely, such as includes and
   pragmas.
3. Reject unresolved preprocessing constructs in raw mode instead of guessing.
4. Split the translation unit while tracking nesting and literals.
8. Preserve unsupported or unmodeled facts as diagnostics or explicit unknown
   references.
9. Assemble project indexes and run bounded cross-file resolution only after
   every explicit input has been parsed.

<!&#45;&#45; X2PY_C_DOCS_START
5. Parse declaration specifiers into typed primitive/tag/typedef facts.
6. Parse declarators recursively from the declared identifier outward.
7. Dispatch aggregate, enum, typedef, variable, function prototype, and
   function-definition forms through shared helpers.
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
For a future C++ parser, keep the same stage boundaries but expect different
models and grammar: namespaces, classes, templates, overload sets, references,
constructors/destructors, methods, access control, and name mangling cannot be
treated as small extensions to the C declaration parser. The reusable lesson is
the pipeline and test structure, not C declarator syntax.
X2PY_C_DOCS_END &#45;&#45;>

Testing should grow in this order:

1. lexer/source-location tests;
2. declaration/type parser tests;
3. model serialization tests;
4. one-file parse tests;
5. project/index tests;
6. fatal diagnostic fixture tests;
7. compiler-preprocessed fixture tests;
8. semantic conversion tests;
9. `.pyi` round-trip tests;
10. CLI stage-dispatch tests.

Executable references:

- Shared CLI behavior: `tests/cli/`

<!&#45;&#45; X2PY_C_DOCS_START
- C parser walkthrough: `tests/parsing/c/test_c_parser_developer_tutorial.py`
- C declaration coverage: `tests/parsing/c/test_c_declarations_and_declarators.py`
- C project/golden workflow: `tests/parsing/c/test_c_fixture_suite.py`
- C semantic handoff: `tests/semantics/conversion/c/`
X2PY_C_DOCS_END &#45;&#45;>

Fixture layout should be separate from Fortran:

<!&#45;&#45; X2PY_C_DOCS_START
```text
tests/data/c/
  general/
  json/
  tinyexpr/
  linmath/
  nanosvg/
  stb/
  errors/parser/
  corpus/
  scientific/

tests/parser/c/
  fixtures/
    general/
    json/
    errors/
  errors/generate_c_parser_error_goldens.py
```
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Checked-in project JSON files under `tests/parser/c/fixtures/` are active
compiler-preprocessed project goldens. They are generated by
`python tests/parser/c/generate_c_parser_goldens.py`, filter system-header
declaration spillover, and normalize source-text whitespace so compiler/libc
formatting differences do not make CI flaky.
The fixture suite also checks same-stem grouping order and representative raw
preprocessing failures.
Fatal diagnostic goldens are regenerated with
`C_PARSER_UPDATE_GOLDENS=1 PYTHONPATH=. pytest -q tests/parsing/c/test_c_error_fixture_suite.py`.
The standalone error generator remains available for targeted refreshes.
By policy, a paired project records source-to-header include edges but parses
each supplied `.c`, `.h`, or `.i` member separately; include traversal is not
a parser input-discovery mechanism.
X2PY_C_DOCS_END &#45;&#45;>

STB remains a family of independent macro-heavy single-file libraries for
future curated compiler-preprocessed corpus work.

<!&#45;&#45; X2PY_C_DOCS_START
The first real-world corpus target should be cJSON, pinned to an exact release
or commit with license and source provenance. cJSON is small enough for early
stabilization while still covering typedef structs, recursive pointers, public
macro declaration wrappers, constants, `const char *` APIs, `size_t`, and
callback hook members. Library files currently under `tests/data/c/json/`,
`tests/data/c/tinyexpr/`, `tests/data/c/linmath/`, and
`tests/data/c/nanosvg/`, plus STB top-level inputs under `tests/data/c/stb/`,
are regression inputs only until corresponding corpus provenance requirements
are met.
X2PY_C_DOCS_END &#45;&#45;>

## Documentation Set

<!&#45;&#45; X2PY_C_DOCS_START
The C parser documentation now lives in this top-level file:
`docs/developer/c-parser-reference.md`. Shared semantic behavior is documented in
[`semantic-ir.md`](../user/reference/semantic-ir.md), and wrapper-generation policy notes live in
[`wrapper-design-notes.md`](../maintainer/design/wrapper-design-notes.md).
X2PY_C_DOCS_END &#45;&#45;>

<!&#45;&#45; X2PY_C_DOCS_START
Documentation update rule: every C parser implementation change must update
this reference in the same change when behavior, public API, models, CLI
output, tests, fixture workflow, semantic conversion, semantic policy, or
`.pyi` output changes. Do not wait for a separate documentation request before
updating it.
X2PY_C_DOCS_END &#45;&#45;>
X2PY_C_DOCS_END -->
