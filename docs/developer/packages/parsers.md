---
title: Parsers Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, prepared source
related: ../architecture.md, index.md, preprocessing.md, semantics.md, ../source-map.md
status: maintained
publication: draft
---

# Parsers Package

## Purpose And Boundaries

`prik/parsers/` owns syntax-level frontends. The Fortran frontend preserves
source units, declarations, visibility, locations, and diagnostics. The
semantic `.pyi` frontend deliberately stops at Python AST. Parsers report what
source says; they do not choose ownership, wrapper support, NumPy lowering, or
generated API behavior.

## Local Structure

```text
prik/parsers/
├── fortran/
│   ├── lexer.py
│   ├── models.py
│   ├── parser.py
│   ├── type_resolver.py
│   ├── cli.py
│   ├── utils.py
│   └── __main__.py
└── pyi/
    └── parser.py
```

## Internal Workflow

```text
prepared Fortran text -> logical lines -> parser models -> Fortran-to-IR
semantic .pyi text    -> Python ast.Module          -> .pyi-to-IR
```

The essential Fortran objects are `FortranParser`, `SourceUnit` and its unit
subclasses, `FortranFile`, `FortranProject`, `FortranParseError`, and the
public `parse_fortran_file()` and `parse_fortran_project()` functions. The
semantic `.pyi` frontend exposes `parse_pyi_text()` and `parse_pyi_file()` and
returns a standard `ast.Module`.

## Important Files

| File | Responsibility |
| --- | --- |
| `fortran/lexer.py` | Detects source form, strips comments, folds continuations, and preserves logical-line locations. |
| `fortran/models.py` | Defines passive parser models and diagnostics. |
| `fortran/parser.py` | Parses files/projects, resolves structural scope, and assembles source units. |
| `fortran/type_resolver.py` | Preserves parser-level type, kind, and character syntax without target evaluation. |
| `fortran/cli.py` | Formats stable human and JSON parser reports. |
| `pyi/parser.py` | Parses semantic `.pyi` syntax into Python AST without semantic interpretation. |

## Execution Examples

```bash
python3 prik/parsers/fortran/lexer.py
```

```text
Detected source form: free
line 1: subroutine shift(value,offset)
line 3:   real, intent(inout) :: value
line 4:   real, intent(in) :: offset
line 5: end subroutine shift
```

```bash
python3 prik/parsers/fortran/parser.py
```

```text
Module: metrics
Parameter: n = 4
Procedure: scale(values: real[1])
```

```bash
python3 prik/parsers/fortran/type_resolver.py
```

```text
integer(4) -> 4
real(kind=selected_real_kind(15, 307)) -> selected_real_kind(15, 307)
character(len=16, kind=c_char) -> len=16, kind=c_char
```

```bash
python3 prik/parsers/fortran/cli.py
```

```text
File: geometry.f90
  Modules: 1
    - module geometry (vars=0, uses=0)
      Procedures: 1
        - function norm(value:real[0]) -> real[0]
```

```bash
python3 prik/parsers/pyi/parser.py
```

```text
Parsed AST: Module
Function node: scale
Argument annotation: Float64
Semantic conversion performed: False
```

The detailed Fortran reference below records the complete maintained subset,
API behavior, diagnostics, fixtures, and reimplementation constraints.

## Tests

- [Fortran parser tests](../../../tests/fortran/source_parsing/parsing/)
- [Fortran parser CLI tests](../../../tests/fortran/command_line_interface/pipeline/)
- [Semantic `.pyi` parsing tests](../../../tests/fortran/semantic_pyi_format/parsing/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

Start lexical/source-coordinate changes in `fortran/lexer.py`, grammar and
model construction in `fortran/parser.py`, report changes in `fortran/cli.py`,
and raw `.pyi` syntax changes in `pyi/parser.py`. Semantic meaning begins in
the matching converter. Parser support alone never establishes wrapper
support.

## Detailed Fortran Reference

This document defines the currently supported parser subset, expected behavior,
and practical usage from terminal and Python.

## 1) Supported features (comprehensive)

### 1.1 Source forms and preprocessing

- Free-form Fortran: `.f90`, `.f95`, `.f03`, `.f08`
- Fixed-form Fortran: `.f`, `.for`, `.ftn`
- Free/fixed comment stripping
- Continuation handling for both forms

### 1.2 Procedure parsing

- `subroutine` headers
- `function` headers
- Header modifiers: `pure`, `elemental`, `recursive`
- Function `result(...)` parsing (tolerant support for `results(...)`)

### 1.3 Declaration/argument parsing

- Intrinsic types: `integer`, `real`, `complex`, `logical`, `character`
- Kind extraction from declaration specs (`kind=...`)
- Attribute extraction:
  - `intent(in|out|inout)`
  - `optional`
  - `value`
  - `allocatable`
  - `pointer`
  - `target`
- Array extraction:
  - `dimension(...)`
  - variable-level shape syntax (`x(:)`, `x(n)`)

### 1.4 Modules, imports, and project context

- Module discovery
- Module variable extraction
- Shared specification-part parsing for module-like scopes (modules,
  submodules, programs, and block-data units), preserving original line
  numbers while skipping contained procedure bodies where they are not
  wrap-relevant
- `use` extraction at module and procedure scope
- Explicit `use` symbol mappings preserve imported `source` names and local
  `target` names for renamed imports
- Propagation of module-level `use` imports into contained procedures
- Folder/project parsing with dependency-aware ordering
- Cross-file kind constant resolution (e.g., kinds modules)
- Cached compile-time expression resolution for local/module parameters,
  module/program variable shapes, and character lengths

### 1.5 Derived type parsing

- `type :: ... end type` and legacy `type name ... end type` discovery
- Parameterized derived-type headers such as `type :: buffer_type(k, n)`
  and declarations such as `type(buffer_type(real64, 4))`
- Type attributes (e.g., `abstract`)
- Inheritance (`extends(parent)`)
- Field extraction including shape/pointer/allocatable
- Type-bound procedures:
  - `procedure ... :: ...` bindings with attributes (e.g. `pass(self)`, `nopass`)
  - `generic ... :: name => target1, target2`

### 1.6 Parser diagnostics and wrapper planning boundary

- Parser diagnostics report source-level parse errors and unsupported parser
  constructs.
- Parser JSON remains parse-only and does not contain wrapper-plan decisions
  or support diagnostics.
- Wrapper builds complete policy from semantic IR and validate the resulting
  wrapper plan. Unsupported contracts report the owning plan path and
  completed-policy diagnostic.

## 2) Public API surface

Supported public API:

- `parse_fortran_file(source_or_path, filename=None, encoding="utf-8") -> FortranFile`
- `parse_fortran_project(files, encoding="utf-8") -> FortranProject`

## Parser organization notes

`prik/parsers/fortran/parser.py` is now intentionally organized into clearly labeled
sections and carries embedded implementation guidance. Start with the thin public
wrappers at the bottom, then read the class from top to bottom:

- Regex/constants, parser-wide type aliases, private unit dataclasses, and the
  compile-time resolver
- `FortranParser` internals grouped by domain:
  - public parse entrypoints (`parse_file`, `parse_project`). The supported
    module-level API remains the wrappers listed above.
  - source-unit visitors for files, modules, submodules, programs,
    procedures, interfaces, derived types, and block data
  - recursive source-unit slicing (`header`, specification part, execution
    part, `contains`) with original line numbers preserved on each slice
  - shared declaration parsing for module variables, program/block-data
    variables, procedure arguments/results, and derived-type fields
  - `_helper_*` methods for scoped parsing, expression resolution, same-level
    duplicate checks, and shared specification-part collection
- Thin module-level convenience wrappers that delegate to a shared parser
  instance

Parser methods carry focused docstrings, with examples where a grammar visitor
or lexical helper is easier to understand from a concrete call.

The Fortran parser is now packaged under `prik.parsers.fortran` rather than a
top-level parser package. The package includes its CLI module, lexer,
JSON-compatible parse models, project parser, type resolver, and utility
helpers. Public callers should use the stable top-level `prik` parser exports
or `prik.parsers.fortran` package imports.

## Implementation Inventory And Maintenance

This file is the single maintained Fortran parser reference. It replaces the
older standalone implementation-reference document; parser feature inventory,
testing workflow, and maintenance guard policy live here.

The implementation inventory is maintained across these surfaces:

- `prik/parsers/fortran/parser.py` owns source slicing, declaration extraction,
  diagnostics, project ordering, dependency resolution, and compile-time
  expression resolution.
- `prik/parsers/fortran/models.py` owns parse-only dataclasses and JSON-compatible
  parser facts.
- `prik/semantics/fortran2ir.py` owns conversion from parser facts to semantic IR,
  including kind mapping, compile-time specialization, storage contracts,
  projection metadata, and wrapper-planning inputs.
- `tests/fortran/source_parsing/parsing/` covers parser contracts, source-unit slicing, diagnostics,
  project behavior, and fixture regressions.
- `tests/fortran/semantic_ir/semantics/` covers semantic conversion, datatype precision mapping,
  wrapper planning, `.pyi` emission, and compile-time specialization.

<!-- PRIK_C_DOCS_START
Parser-related pull requests should update this file when the documented
feature inventory, public API, diagnostics, project behavior, semantic handoff,
or maintenance workflow changes.
PRIK_C_DOCS_END -->

`parse_file` is the central orchestration path. The scanner first constructs
fully classified direct file-level units, then each class visitor parses only
the stored regions and children it owns. This is the key parser design: each
Fortran grammar unit has a header, a specification region, optional execution
region, optional `contains` region, and retained direct children. The
differences between modules, programs, procedures, derived types, interfaces,
and block data are expressed by small visitor decisions and grammar flags
rather than separate whole-file parsing loops.

Nested unit boundaries and placement outside execution regions are checked even
when they are not exported as wrapper metadata. Internal procedures inside a
host procedure's `contains` block are structurally sliced, then their
declarations and bodies are skipped. Once an execution boundary is detected,
procedure bodies and standalone included execution fragments are intentionally
skipped. Procedure-local interface blocks are still visited enough to type
callback dummy arguments and to preserve interface metadata.

### 2.1 Recursive parser sketch

Small input:

```fortran
module m
  integer, parameter :: n = 4
contains
  subroutine scale(x)
    real, intent(inout) :: x(n)
  end subroutine scale
end module m
```

The parser handles it in this order:

1. `parse_file` preprocesses the source and asks the stateless
   `_SourceUnitScanner.scan_file_units` collaborator to scan at file scope.
   The result is one `ModuleUnit` carrying the module name, exact lines, source
   locations, classified grammar regions, and retained direct children. The
   scanner remains independent of `_ParserScope` and constructed models.
2. the shared `ClassVisitor._visit` dispatcher selects `_visit_ModuleUnit`.
3. `_visit_ModuleUnit` creates a module `_ParserScope` and sends the unit's
   already-classified specification lines to `_parse_specification_part`.
4. `_parse_specification_part` uses the shared declaration backend:
   `_helper_parse_declaration_line` parses `integer, parameter :: n = 4` into a
   typed `_Declaration`, then `_store_declaration` dispatches to the
   module-like-variable storage helper, which appends the resulting parameter
   variable to `FortranModule.variables`.
5. The module visitor reads the scanner-owned direct children. It finds one
   procedure unit, `scale`, and dispatches it to
   `_visit_ProcedureUnit`.
6. `_visit_ProcedureUnit` creates a procedure `_ParserScope` and visits only
   the stored specification part. The same declaration backend parses
   `real, intent(inout) :: x(n)` and sends the typed declaration to the
   procedure-symbol storage helper, which updates `x` in the procedure argument
   symbol table.

Scope is always an explicit argument to the shared helpers. That is the reason
two modules can each define `type :: state` without conflict, while two
same-level `module m` declarations or two same-level contained procedures with
the same name are rejected by `_helper_validate_sibling_units`.

The ownership boundary is deliberate: `_SourceUnitScanner` recognizes unit
openers and terminators, matches nested boundaries, and separates
specification, execution, and `contains` regions. `FortranParser` owns scopes,
model visitors, declaration parsing, sibling validation, and diagnostics that
depend on constructed parser models. Splitting the scanner into another file
would not strengthen that boundary; its private source tuples, grammar records,
and unit classes are all local to this parser module.

Declaration parsing has its own local ownership boundary. `_Declaration`
records the normalized type spelling and declaration attributes shared by an
entity list. For example, `real(kind=rk), pointer, dimension(:) :: values`
produces one declaration with base type `real`, kind `rk`, pointer enabled, and
shape `[:]`; `values` remains a separate entity name. Storage helpers then turn
that record into procedure symbols, derived-type fields, or module-like
variables. The record is parser-internal and never becomes a second public
parser model or semantic-policy object.

Each `SourceUnit` is fully classified by the scanner. In addition to its exact
source span, kind, and name, it owns its header, specification, execution,
`contains`, footer, and retained direct child units. A child records whether it
occurred in its parent's specification or `contains` region, so a module-level
interface is not confused with a contained procedure. Children are retained
only when later parser work needs them for model construction or validation.
That includes module-like unit children, interface procedure declarations,
procedure-local interfaces used to type callback dummy arguments, and local
declarative units whose syntax still needs validation. Internal procedures
below a procedure's `contains` statement are structurally scanned but are not
retained as wrapper targets. Execution regions remain opaque.

While matching one unit's terminator, the scanner keeps a stack of `_OpenUnit`
records. Each record names one unit that has opened but not yet closed and
stores its structural region. The top record is the innermost unit; popping it
after its terminator exposes the containing module, interface, or procedure.
This stack is structural parser state only: it contains no `_ParserScope` and
does not own declarations or parser models.

End-name validation is strict for structural units whose names define exported
scope boundaries, such as modules, submodules, programs, interfaces, and
derived types. Procedure end-name mismatches are still tolerated while slicing
third-party sources because some accepted fixture code contains copy/paste
procedure end labels; the procedure is closed by unit kind so parsing can
continue, and duplicate procedure names are validated at the sibling scope.

The only separate specification-line visitors are grammar-specific:
module-like units share `_parse_module_like_spec_line`, procedures use
`_parse_procedure_spec_line` for `implicit`, `external`, `import`, and
local `parameter` handling, and derived types use
`_parse_type_spec_line` for `sequence`, `private`, and type-bound
declaration rules. All three still call the same declaration parser/pusher for
actual declarations.

Most parser organization changes are structural, but behavior, model-schema,
coverage, or fixture changes should be reflected in this reference.

Parameter constants expose both `value` and serialized `symbolic_value` when
available. `value` is reserved for a literal/evaluated result after
compile-time folding. If an initializer cannot be evaluated safely, such as
`selected_real_kind(...)`, `value` is `None` and `symbolic_value` preserves the
original initializer for validation, debugging, downstream diagnostics, and
JSON consumers.

Source-level compile-time resolution consumes those parsed parameter models;
it does not rescan stored source text for a second parameter representation.
The parser first builds one `_CompileTimeSymbols` table whose module entries
have already resolved transitive aliases. For example, module parameters
`word = 4` and `rk = word * 2` produce `{"word": "4", "rk": "8"}`;
`use kinds, only: wp => rk` then exposes `{"wp": "8"}` to the consuming
scope. File parsing and project/CLI parsing use the same table construction and
the same procedure, module-like-variable, and derived-field consumers.

This resolution is limited to facts visible from source. Compiler-dependent
expressions such as `selected_real_kind(12)` remain symbolic for the later
probe/semantic stages. Imported module expressions in procedure argument
shapes also remain symbolic at file and project boundaries so policy completion
can retain their native spelling and role dependencies.

Procedure-local parameters may be folded into argument shapes during procedure
finalization. Module-level and `use`-associated parameters used in procedure
argument shapes are kept symbolic in the signature (`x(n)` remains `["n"]`)
and are treated as valid scope references for policy completion. Module/program
variable shapes and parameter values can be resolved through the compile-time
resolver when enough information is available.

## Reimplementation Guide For Another Parser

Use the Fortran parser as the reference for any source language with nested
program units, scoped declarations, and a later semantic handoff. The details
are Fortran-specific, but the parser architecture is reusable.

Recommended frontend responsibilities:

- Keep one typed model layer for parse-only facts.
- Keep one parser orchestration class with thin public wrappers.
- Slice source into grammar units before parsing declarations.
- Pass scope explicitly into shared helpers rather than using global mutable
  parser state for symbol resolution.
- Parse only wrapper-relevant specification facts; skip executable bodies once
  they are outside the parser contract.
- Preserve source locations and original line numbers through preprocessing and
  recursive slicing.
- Emit parser diagnostics for malformed source, but leave wrappability policy
  to semantic policy completion.

The Fortran data flow is:

```text
source path or source text
  -> compiler/native include preprocessing
  -> FortranParser.parse_file(...)
  -> classified source units with original line numbers
  -> scoped specification parsing
  -> FortranFile parser facts
  -> directory source discovery when requested
  -> each FortranFile parsed exactly once
  -> dependency ordering of the existing FortranFile objects
  -> FortranProject cross-file resolution and indexes
  -> semantics.fortran2ir conversion
  -> policy completion, `.pyi`, and the implemented Fortran wrapper stages
```

The recursive parsing pattern is:

1. Construct each unit with its header, grammar regions, and retained direct
   children already classified.
2. Parse declarations only from the stored specification part.
3. Recurse only into retained direct children that later parser work needs.
4. Keep procedure execution regions opaque and omit inaccessible internal
   procedures from the retained child tree.
5. Validate sibling names and scope-local duplicate declarations.
6. Finalize procedure arguments/results after local declarations and
   parameters are known.
7. Resolve source-visible cross-file or imported compile-time aliases through
   one project symbol table, while leaving compiler-dependent facts for
   semantic conversion and target probing.

When adding another parser, keep these test layers separate:

- parser unit tests for grammar slicing and declarations;
- parser fixture tests for stable JSON/model output;
- parser error fixture tests for fatal diagnostic contracts;
- project tests for dependency ordering and cross-file resolution;
- CLI tests for frontend selection, stage dispatch, output files, and debug
  behavior;
- semantic conversion tests for parser-to-IR mapping;
- `.pyi` tests for generated and edited interface round trips.

Executable references:

- Fortran parser walkthrough: `tests/fortran/source_parsing/parsing/test_developer_tutorial.py`
- Procedure/type parsing: `tests/fortran/source_parsing/parsing/`
- Scope and project behavior: `tests/fortran/modules/parsing/test_scope_handling.py` and
  `tests/fortran/modules/parsing/test_project_scope_models.py`
- Fortran fixture workflow: `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`
- Shared CLI behavior: `tests/fortran/command_line_interface/pipeline/`
- Fortran semantic handoff: `tests/fortran/semantic_ir/semantics/`

## 3) Terminal usage and expected outputs

### 3.1 Basic CLI invocation

```bash
python -m prik parse path/to/file.f90
```

Recognizable Fortran files can omit `--language`. Directories require explicit
frontend selection:

```bash
python -m prik parse path/to/fortran_src --language fortran
```

Fortran directories are recursively scanned for `.f`, `.for`, `.ftn`, `.f90`,
`.f95`, `.f03`, `.f08`.

The Fortran frontend rejects unsupported non-Fortran syntax before
wrapper-focused parsing when it appears outside executable procedure/program
bodies, which are intentionally not represented in the extracted interface.

The human-readable parse tree keeps scope variables compact by default as
`vars=N`. Add `--show-vars` to print the variables, or `--print-limit N` to
print only the first `N` items in each repeated section.

### 3.2 Human-readable output example

Input Fortran (`tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90`):

<!-- prik-doc-source: tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 -->
```fortran
module m1
contains
subroutine add1(n, x)
  integer, intent(in) :: n
  real(kind=8), intent(inout), dimension(n) :: x
end subroutine add1
end module m1
```

Command:

<!-- prik-doc-test: exact -->
```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

Expected output:

<!-- prik-doc-test-output -->
```text
File: tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
  Modules: 1
    - module m1 (vars=0, uses=0)
      Procedures: 1
        - subroutine add1(n:integer[0], x:real(8)[1])
```

The same command with `--show-vars` uses the variable-expanded report path.
This fixture currently has no module variables to print, so the output remains
compact:

<!-- prik-doc-test: exact -->
```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 --show-vars
```

<!-- prik-doc-test-output -->
```text
File: tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
  Modules: 1
    - module m1 (vars=0, uses=0)
      Procedures: 1
        - subroutine add1(n:integer[0], x:real(8)[1])
```

For large files:

```bash
python -m prik parse path/to/file.f90 --show-vars --print-limit 50
```

`--print-limit` applies independently to modules, submodules, programs, block
data units, derived types, fields, procedures, and variables when variables are
shown. Counts such as `Procedures: 80` and `Variables: 657` still show the full
totals even when only the first `N` entries are printed.

Interpretation:

- Parsed entities are counted per file.
- Free procedures (outside modules) are shown in top-level `Procedures`.
- Module-contained procedures are nested under each module.
- Empty sections are omitted from the human-readable report.

More complex example:

Input Fortran (`mixed_example.f90`):

<!-- PRIK_C_DOCS_START
```fortran
subroutine driver(n)
  integer, intent(in) :: n
end subroutine driver

module math_ops
  use iso_c_binding, only: c_double
  implicit none
  real(c_double) :: alpha
contains
  subroutine saxpy(n, a, x, y)
    integer, intent(in) :: n
    real(c_double), intent(in) :: a
    real(c_double), dimension(n), intent(in) :: x
    real(c_double), dimension(n), intent(inout) :: y
  end subroutine saxpy

  function dot(x, y) result(r)
    real(c_double), dimension(:), intent(in) :: x, y
    real(c_double) :: r
  end function dot
end module math_ops

module io_ops
  implicit none
contains
  subroutine dump(v)
    real, dimension(:), intent(in) :: v
  end subroutine dump
end module io_ops
```
PRIK_C_DOCS_END -->

Command:

```bash
python -m prik mixed_example.f90
```

```text
File: mixed_example.f90
  Procedures: 1
    - subroutine driver(n:integer[0])
  Modules: 2
    - module math_ops (vars=1, uses=1)
      Procedures: 2
        - subroutine saxpy(n:integer[0], a:real[0], x:real[1], y:real[1])
        - function dot(x:real[1], y:real[1])
    - module io_ops (vars=0, uses=0)
      Procedures: 1
        - subroutine dump(v:real[1])
```

### 3.3 JSON and semantic output

Print parser JSON:

```bash
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 --json
```

Write parser JSON:

```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 --json --out report.json
```

Expected JSON layout:

- Top-level object keyed by input path
- Per-file payload with keys:
  - `signatures`
  - `types`
  - `modules`
  - `submodules`
  - `programs`
  - `block_data`

When `prik parse --json` applies compiler preprocessing, the per-file payload
also contains `preprocessing_recipe`. The CLI applies compiler preprocessing
for file-based parsing; compiler linemarkers remain accepted for provenance.
The recipe records the exact compiler executable or adapter, argv, include
paths, macro flags, standard, extra compiler arguments, working directory,
include graph, source mappings, diagnostics, and optional macro metadata used
to produce the parsed stdout stream.

Fortran CPP directives are handled by the configured compiler. Native Fortran
`include "file.inc"` statements are then expanded recursively by the
preprocessing layer before the single parser pass. Native INCLUDE is textual
insertion into the current scope; it is not a `use` import from a separately
compiled module. Include lookup is relative to the including file first, then
the configured include directories, duplicate textual inclusion is preserved,
and missing files or cycles produce `INCLUDE_NOT_FOUND` or `INCLUDE_CYCLE`
diagnostics.

`use` import shape:

<!-- PRIK_C_DOCS_START
- A bare module import such as `use iso_c_binding` is serialized as an empty
  symbol list for that module.
- An explicit import such as `use iso_c_binding, only: c_int` is serialized as
  a list of mapping objects:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```json
"uses": {
  "iso_c_binding": [
    {
      "source": "c_int",
      "target": null
    }
  ]
}
```
PRIK_C_DOCS_END -->

- A renamed import such as
  `use list_input, delete_input => delete_input_list` records both sides:

```json
"uses": {
  "list_input": [
    {
      "source": "delete_input_list",
      "target": "delete_input"
    }
  ]
}
```

<!-- PRIK_C_DOCS_START
For compatibility in Python tests and simple consumers, `FortranUseMapping`
entries compare equal to their local name, so
`module.uses["iso_c_binding"] == ["c_int"]` remains true for direct equality
checks. Prefer reading `source`, `target`, or `local_name` in new code.
PRIK_C_DOCS_END -->

### 3.4 Semantic and wrapper-plan output

Parser output and semantic IR are separate stages. Run parser inspection with:

```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

Build a wrapper with the default wrapper stage. If the completed plan cannot
lower a contract, the build reports the precise plan owner and blocker:

```bash
python -m prik tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

Parser JSON stays parse-only.

Semantic IR JSON uses the same output channels, but the per-file payload is the
semantic model projection instead of raw parser output:

```bash
python -m prik semantics tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

Generated `.pyi` text is printed with:

```bash
python -m prik generate --pyi tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

### 3.5 Parse-error diagnostics and debug mode

When parsing fails, the CLI prints a compiler-style diagnostic to `stderr` and
exits with status code `1`. By default this output is intended for end users: it
includes the source location, diagnostic code, message, source line, and caret
context, but it does **not** include a Python traceback.

Example command:

```bash
python -m prik tests/fortran/source_parsing/parsing/fixtures/errors/err_duplicate_argument_name.f90
```

Example diagnostic shape:

```text
tests/fortran/source_parsing/parsing/fixtures/errors/err_duplicate_argument_name.f90:1:1: error[PARSE_DUPLICATE_ARGUMENT]: Duplicate argument name 'x' in procedure 'dup'.
  |
1 | subroutine dup(x, y, x)
  | ^
```

ANSI color is enabled by default when available; no color flag is needed for
normal use. To disable color explicitly, pass `--no-color` or set the standard
`NO_COLOR` environment variable:

```bash
python -m prik bad.f90 --no-color
NO_COLOR=1 python -m prik bad.f90
```

For parser development, use `--debug` to re-raise
`FortranParseError` and let Python print the full traceback showing where the
error was raised internally:

```bash
python -m prik bad.f90 --debug
```

The same developer mode can be enabled with the environment variable
`FORTRAN_PARSER_DEBUG=1`:

```bash
FORTRAN_PARSER_DEBUG=1 python -m prik bad.f90
```

In debug mode, the traceback's final exception message also includes a
`note: parser raised at ...` line with the internal parser file, line, and
function that created the diagnostic.

## 4) Python usage and expected outputs

### 4.1 Parse a project directory

```python
from prik import parse_fortran_project
from pathlib import Path

project = parse_fortran_project(Path("src"))
print(len(project.files))
print(len(project.modules))
```

Expected behavior:

- Recursively discovers supported Fortran source paths.
- Parses each discovered file exactly once into a `FortranFile`.
- Orders those existing file models from dependency providers to consumers.
- Resolves cross-file kinds/imports and returns an indexed `FortranProject`.

The directory control flow is deliberately explicit:

```text
parse_project
  -> _discover_project_paths
  -> _parse_project_files
  -> _order_project_files
  -> _assemble_project
```

In-memory `{filename: source}` input uses `_parse_named_project_sources`
instead of filesystem discovery. Explicit file lists use
`_parse_project_files` and preserve caller order.

### 4.2 Parse single file and convert it to semantic IR

```python
from pathlib import Path
from prik import parse_fortran_file
from semantics.fortran2ir import fortran_file_to_semantic_modules

p = Path("tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90")
code = p.read_text()

parsed = parse_fortran_file(code, filename=str(p))
modules = fortran_file_to_semantic_modules(parsed, standalone_module_name=p.stem)
print("procedures", len(parsed.procedures))
print("semantic modules", len(modules))
```

Expected behavior:

- `parsed` is a `FortranFile` aggregate model with parsed units and symbols.
- `modules` is the semantic IR projection used by `.pyi` printing and wrapper
  planning.

### 4.3 Structured argument specifications

Compatibility fields such as `FortranArgument.shape`, `lbound`, `ubound`, and
`kind` remain serialized as strings/lists. For callers that need typed access,
argument and variable models also expose structured helpers:

- `structured_shape` returns a `FortranShape` containing parsed dimensions.
- Slice-like dimensions such as `1:n:2` are represented as `FortranSlice`.
- Whole-expression function calls such as `lbound(x, 1)` are represented as
  `FortranFunctionCall`.
- `kind_expression` and `value_expression` parse `kind` and `value` strings
  using the same lightweight expression model.

Example:

```python
arg.shape
# ["lbound(src, 2):ubound(src, 2)"]

dim = arg.structured_shape.dimensions[0]
dim.lower.name
# "lbound"
dim.upper.name
# "ubound"
```

### 4.4 Declaration-expression ownership

The declaration parser preserves balanced Fortran 2008/2018 bound text for all
declaration owners: module variables, derived-type fields, dummy arguments, and
procedure results. Nested calls, array constructors, component references, and
colons inside nested syntax do not split an outer dimension or bound.

Semantic conversion sends every explicit extent through the shared
`prik.utilities.declaration_expressions` layer. That layer retains the native
spelling in `source_shape` and produces the language-neutral public spelling
used by `.pyi`, including
`size(a)` to `a.size`, `size(a, dim)` to `a.shape[dim - 1]`, and `rank(a)` to
`a.ndim`. Post-IR policy then resolves public scalar and array-property
references to wrapper roles. Binding and bridge generators only render the
completed expression for their target language; they do not infer declaration
semantics.

`lbound(a, dim)` uses the lower bound declared for that dummy axis rather than
Python's index origin. `ubound(a, dim)` combines that bound with the runtime
extent, and the shared expression layer reduces the common
`ubound-lbound+1` form to `a.shape[dim - 1]`. Direct inquiries preserve the
standard zero-extent results: lower bound one and upper bound zero.

Parsing and preservation are intentionally broader than wrapper execution.
Valid specification expressions whose value exists only in private native
state remain available as source metadata but produce an explicit policy
blocker when no boundary role can supply them. Calls to user specification
functions also remain in the language-neutral expression. Semantic conversion
resolves each call to a local module procedure, through the declaration owner's
`USE` mappings, or to a concrete procedure interface in the same declaration
scope. It records the visible spelling, original native name, native placement,
and resolved declaration.

A wildcard import is resolved only when file/project parsing has indexed the
named procedure in exactly one imported module; conversion does not guess from
an unavailable module export list. The `.pyi` loader reconstructs the same
identity from module functions, imports, and `@prototype` declarations. A
prototype is one signature model: annotation use makes it a callback signature,
while call use names a standalone procedure entity. Post-IR policy validates
purity, scalar-integer result, argument association, and accessibility, then
selects either a module `use` or a standalone procedure declaration backed by
the generated abstract interface. A pure prototype cannot also be a Python
callback because its generated adapter calls the Python runtime; that mixed use
is blocked before planning. The binding and bridge consume only that
completed action. Fortran 2023 vector bounds and `RANK` clauses are outside the
parser's advertised Fortran 2008/2018 language modes.

## 5) Running tests

Run all tests:

```bash
PYTHONPATH=. pytest -q
```

Run parser-focused tests:

```bash
python -m prik parse tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90 --language fortran --json
PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/
PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py
PYTHONPATH=. pytest -q tests/fortran/command_line_interface/pipeline/
```

Focused test files by implementation area:

- Parser walkthrough and expected developer flow:
  `tests/fortran/source_parsing/parsing/test_developer_tutorial.py`
- Procedure headers, declarations, derived types, interfaces, and type-bound
  procedures:
  `tests/fortran/source_parsing/parsing/`
- Function header edge cases:
  `tests/fortran/functions/parsing/test_function_headers.py`
- Scope handling and project namespace behavior:
  `tests/fortran/modules/parsing/test_scope_handling.py` and
  `tests/fortran/modules/parsing/test_project_scope_models.py`
- Preprocessing, native includes, and execution-boundary skipping:
  `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`
- Parser diagnostics and fatal error contracts:
  `tests/fortran/source_parsing/parsing/test_error_handling.py`
- Regression contracts:
  `tests/fortran/source_parsing/parsing/`
- Public entrypoints:
  `tests/fortran/source_parsing/parsing/test_public_entrypoints.py`
- Parser fixture goldens:
  `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`
- Parser error fixture goldens:
  `tests/fortran/source_parsing/parsing/test_error_fixture_suite.py`
- Parser JSON shape:
  `tests/fortran/source_parsing/parsing/test_json_sanity.py`
- Cached Fortran compiler/type and intrinsic-storage probing:
  `tests/fortran/data_types/probes/test_fortran_type_probes.py`
- Shared CLI behavior:
  `tests/fortran/command_line_interface/pipeline/`

When adding or changing a Fortran parser feature, add a focused parser test
near the implementation concern first, then update fixture goldens only when
the serialized parser contract intentionally changes.

Update golden JSON fixtures:

```bash
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py
```

Update selected fixture(s):

```bash
python tests/fortran/source_parsing/parsing/generate_parser_goldens.py tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

In-test auto-update mode:

```bash
FORTRAN_PARSER_UPDATE_GOLDENS=1 PYTHONPATH=. pytest -q tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py --confcutdir=tests/
```

Semantic and `.pyi` fixtures have separate generators:

```bash
python tests/fortran/semantic_ir/semantics/generate_semantic_fixtures.py
WRAPPER_UPDATE_PYI_FIXTURES=1 python3 -m pytest -q tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py
```

## 6) Error handling

All parse failures raise `FortranParseError`, a subclass of `ValueError`. The
exception keeps structured metadata for consumers:

- `filename` — source path supplied to the parser, if any
- `line_number` — 1-based source line where the error was detected, if known
- `source_line` — original source text for context, if known
- `base_message` — stable error text without location/source context
- `code` — stable, explicit diagnostic category identifier; manually
  constructed fallback errors use `PARSE_ERROR`, while grammar rejection uses
  `PARSE_INVALID_SYNTAX`

Diagnostic codes are for programmatic matching in tests, tools, and
documentation. The category name states the failure class directly. The shared
registry is [`diagnostic-codes.md`](../../user/reference/diagnostic-codes.md).

`str(error)` and `error.format_diagnostic(color=False)` render a
compiler-style diagnostic:

```text
<filename>:<line>:1: error[<CATEGORY>]: <message>
  |
<N> | <source line>
  | ^
```

If no filename is available, the location is rendered as `<unknown>`. If a line
number or source line is unavailable, that part of the diagnostic is omitted or
shown with `?` as appropriate. Use `error.base_message` when tests or API
consumers need only the message text.

`format_diagnostic(color=True)` adds ANSI styling. The CLI requests colored
diagnostics by default when available; pass `--no-color` or set `NO_COLOR=1` to
disable ANSI output. On Windows, ANSI console compatibility is enabled through
`colorama` when it is installed.

For parser development, `format_diagnostic(debug=True)` appends a note with the
internal parser file, line, and function that raised the error. The CLI exposes
this through `--debug` or `FORTRAN_PARSER_DEBUG=1`; normal CLI parse errors intentionally hide Python
tracebacks.

The sections below list each error category, the triggering condition, and the
exact `base_message` format (with `<...>` placeholders for runtime values).

### 6.1 Unknown or unsupported type declaration

Triggered when a declaration line cannot be matched to any known intrinsic type,
`type(...)`, or `character` variant.

**In a procedure:**

```
Unknown or unsupported datatype declaration for procedure '<name>': <line>
```

Example Fortran that triggers this:

```fortran
subroutine bad(x)
  weirdtype :: x
end subroutine bad
```

Example error:

```
bad.f90:2:1: error[PARSE_UNSUPPORTED_DECLARATION]: Unknown or unsupported datatype declaration for procedure 'bad': weirdtype :: x
  |
2 |   weirdtype :: x
  | ^
```

**In a derived type:**

```
Unknown or unsupported datatype declaration in type '<name>': <line>
```

**In a module:**

```
Unknown or unsupported datatype declaration in module '<name>': <line>
```

### 6.2 Duplicate declaration

Triggered when the same symbol is declared more than once in the same scope.

**In a procedure (arguments and local declarations):**

```
Duplicate declaration of symbol '<name>' in procedure '<proc>'.
```

Example:

```fortran
subroutine dup(x)
  real :: x
  integer :: x
end subroutine dup
```

Example error:

```
dup.f90:3:1: error[PARSE_DUPLICATE_DECLARATION]: Duplicate declaration of symbol 'x' in procedure 'dup'.
  |
3 |   integer :: x
  | ^
```

**PARAMETER constants:**

```
Duplicate PARAMETER declaration of symbol '<name>' in procedure '<proc>'.
```

**In a derived type:**

```
Duplicate field '<name>' in derived type '<type>'.
```

**In a module:**

```
Duplicate variable '<name>' in module '<module>'.
```

### 6.3 Duplicate procedure name

Triggered when the same procedure name appears more than once within the same
module or global scope.
Internal procedures inside separate host `contains` blocks are scoped to their
host and do **not** conflict with each other.

**Global scope:**

```
Duplicate procedure name '<name>' in global scope.
```

**Module scope:**

```
Duplicate procedure name '<name>' in module '<module>'.
```

Example:

```fortran
subroutine work(n)
  integer, intent(in) :: n
end subroutine work

subroutine work(n)
  integer, intent(in) :: n
end subroutine work
```

Example error:

```
dup.f90:5:1: error[PARSE_DUPLICATE_PROCEDURE]: Duplicate procedure name 'work' in global scope.
  |
5 | subroutine work(n)
  | ^
```

### 6.4 Duplicate argument name

Triggered when a procedure's argument list contains the same name more than once.

```
Duplicate argument name '<name>' in procedure '<proc>'.
```

Example:

```fortran
subroutine dup(x, y, x)
  integer, intent(in) :: x
  real, intent(in) :: y
end subroutine dup
```

Example error:

```
dup_arg.f90:1:1: error[PARSE_DUPLICATE_ARGUMENT]: Duplicate argument name 'x' in procedure 'dup'.
  |
1 | subroutine dup(x, y, x)
  | ^
```

### 6.5 Star-kind declarations

Legacy `type*N` declarations, such as `real*8`, are accepted in both fixed-form
and modern-extension files. Numeric star declarations preserve their fixed
total storage width for semantic conversion. This matters most for complex
types: `complex*8` is an 8-byte `Complex64`, while modern `complex(kind=8)` is
a compiler kind and is 16 bytes on the documented `gfortran` target.
`DOUBLE PRECISION` and `DOUBLE COMPLEX` retain a compiler-dependent double-kind
expression and use the cached Fortran type probe. For `CHARACTER*N` and
`CHARACTER*(*)`, the star value is a length, not a kind or element storage
width.

```fortran
subroutine accepted(x)
  real*8 :: x
end subroutine accepted
```

See the [generated modern and legacy datatype mapping](../../user/reference/semantic-ir.md#generated-linux-x86_64-mapping-example)
for the exact GitHub Actions target results.

### 6.6 Source-form metadata

The parser records source-form metadata from the filename and lexer, but does
not reject a construct solely because a `.f77` suffix was used. Grammar-region
validation still applies after preprocessing.

### 6.7 Implicit none — undeclared argument or result

Triggered when `implicit none` is active and an argument (or function result)
has no matching type declaration.

**Argument:**

```
Argument '<name>' in procedure '<proc>' has no type declaration (implicit none is active).
```

**Function result:**

```
Function result '<name>' in procedure '<proc>' has no type declaration (implicit none is active).
```

Example:

```fortran
subroutine foo(x, y)
  implicit none
  integer, intent(in) :: x
end subroutine foo
```

Example error:

```
implicit_none.f90:1:1: error[PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL]: Argument 'y' in procedure 'foo' has no type declaration (implicit none is active).
  |
1 | subroutine foo(x, y)
  | ^
```

### 6.8 Unknown datatype for function result

Triggered when a function result has no resolvable type after parsing (and
`implicit none` prevents implicit typing).

```
Unknown datatype for function result '<name>' in procedure '<proc>'.
```

Example:

```fortran
function f(x) result(res)
  implicit none
  real :: x
end function f
```

Example error:

```
bad.f90:1:1: error[PARSE_UNKNOWN_FUNCTION_RESULT_TYPE]: Unknown datatype for function result 'res' in procedure 'f'.
  |
1 | function f(x) result(res)
  | ^
```

### 6.9 Unknown datatype for a module variable

Triggered by `_validate_module_variables` when a parsed module variable still
has `base_type == "unknown"` after declaration parsing.

```
Unknown type for variable '<name>' in module '<module>'.
```

### 6.10 Unknown datatype for a derived type field

Triggered by `_validate_derived_type_fields` when a field still has
`base_type == "unknown"`.

```
Unknown type for field '<name>' in derived type '<type>'.
```

### 6.11 PARAMETER symbol without type in `implicit none` scope

Triggered when a legacy `PARAMETER (...)` statement names a symbol that has not
been typed and `implicit none` is in effect.

```
Unknown datatype for PARAMETER symbol '<name>' in procedure '<proc>'.
```

Example:

```fortran
      subroutine cst(a)
      implicit none
      real a
      parameter ( zero = 0.0e+0 )
      end
```

Example error:

```
legacy.f:4:1: error[PARSE_UNKNOWN_PARAMETER_TYPE]: Unknown datatype for PARAMETER symbol 'zero' in procedure 'cst'.
  |
4 |       parameter ( zero = 0.0e+0 )
  | ^
```

### 6.12 Function result variable shadows an argument

Triggered when a `result(name)` clause reuses an argument name (and the two
names are different from each other — the special case `result(f)` on a
function named `f` is allowed).

```
Function result variable '<result>' in function '<func>' shadows an argument name.
```

Example:

```fortran
function f(res) result(res)
  integer, intent(in) :: res
end function f
```

Example error:

```
shadow.f90:1:1: error[PARSE_RESULT_SHADOWS_ARGUMENT]: Function result variable 'res' in function 'f' shadows an argument name.
  |
1 | function f(res) result(res)
  | ^
```

### 6.13 Failed to resolve declared argument

An internal safety check: if a symbol was explicitly declared but its type
could not be applied (a parser regression guard), the following error is raised.

```
Failed to resolve declared argument '<name>' in procedure '<proc>'.
```

## 7) Scope note

This parser is intentionally wrapper-focused and not a complete Fortran front
end. Unsupported syntax should be surfaced through parser diagnostics or later
semantic policy inputs for incremental parser extension.


### External callback dummy declarations

The parser accepts legacy callback-style declarations inside procedure scopes, including:

- `external :: cb` (treated as a procedure-typed dummy)
- `real, external :: f` / `integer, external :: g` (typed external function dummies)

Under `implicit none`, these declarations count as valid argument declarations, so callback arguments are not reported as missing datatype declarations.

## 8) File, project, and semantic entrypoints

Use the stable top-level API:

- `parse_fortran_file(source_or_path, filename=None, encoding="utf-8") -> FortranFile`
- `parse_fortran_project(files, encoding="utf-8") -> FortranProject`

Lower-level unit parsers are internal `FortranParser` methods.

Semantic conversion lives in `prik/semantics/fortran2ir.py`. It accepts parsed `FortranFile`
(or selected `FortranModule`) structures and converts metadata into semantic IR
consumed by the `.pyi` printer and current Fortran wrapper/runtime stages.
Compiler-backed shared-CLI semantic stages resolve compiler-dependent kind
expressions, measure numeric and logical intrinsic storage with `storage_size`,
attach those facts to semantic types, and reuse memory and persistent caches.
The shared CLI applies project symbol completion even when the input contains
only one source file. That completion follows explicit renamed `use`
associations through project modules and propagates parent/ancestor
host-associated symbols into submodules before compiler-backed stages run.
This includes both a direct intrinsic rename such as `wp => real64` in a
single-file module and a re-exported chain such as `dp => rk => real64`; the
standalone compiler probe therefore receives the intrinsic expression
(`real64`) rather than a project-local alias that is out of scope in the
generated probe program.
Character declarations are excluded from storage probing: their semantic type
is `String`, while fixed or deferred element length is carried separately from
the declaration or runtime descriptor. The generated mapping report describes
the modeled eight-bit character code unit directly and does not manufacture a
compiler probe fact for character rows. For the maintained GitHub Actions
`gfortran` profile, unqualified `integer`, `real`, and `complex` map to `Int32`,
`Float32`, and `Complex64`; target-changing flags can change those mappings.
Source-driven wrapper builds add the normalized native Fortran compiler flags
to the internal probe configuration, so semantic type facts and native
implementation compilation use the same default-kind profile. The
[generated target datatype mapping](../../user/reference/semantic-ir.md#generated-linux-x86_64-mapping-example)
measures and verifies those storage facts.

The Fortran probe cache key includes the generated expression source, resolved
compiler binary identity, target flags, includes, macros, requested standard,
working directory, target-related environment, and runner. The persistent
location is `$XDG_CACHE_HOME/prik/fortran_type_probe` or
`~/.cache/prik/fortran_type_probe`; `PRIK_CACHE_DIR` changes the internal cache
root. The standalone `prik probe` command additionally exposes `--cache-dir`
and `--refresh` for explicit inspection runs.

The standalone probe can create a reusable report containing the exact
compile-time and storage expressions needed by a source:

```bash
python3 -m prik probe --language fortran --compiler gfortran \
  --expr='selected_real_kind(12)' \
  --expr='storage_size(real(0.0,kind=8))' \
  --out build/fortran-types.json
```

The report is an inspection and verification output. Semantic conversion and
wrapper builds measure the facts they need internally from their selected
compiler; the report is not a second semantic-stage input path. A missing
required expression is reported explicitly instead of falling back to an
unrelated target mapping.

The semantic converter also supports compile-time specialization for values the
parser intentionally leaves symbolic. Use
`collect_semantic_compile_time_requirements(parsed)` to list missing parameter
or kind values, then pass a dictionary such as
`{"selected_real_kind(12)": 8}` to
`fortran_module_to_semantic_module(..., compile_time_values=...)` or
`fortran_file_to_semantic_modules(..., compile_time_values=...)`. Existing
semantic IR can be copied and specialized with
`resolve_semantic_compile_time_values(module, {"n": 64})`.
