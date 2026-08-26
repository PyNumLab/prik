---
title: Parsing Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, prepared source
related: ../architecture.md, index.md, preprocessing.md, semantics.md, ../codebase-map.md
status: maintained
publication: reviewed
---

# Parsing Stage

## Purpose And Boundaries

`prik/parsers/` records syntax-level facts. The Fortran frontend preserves
source units, declarations, visibility, locations, and diagnostics. The
semantic-`.pyi` frontend returns a standard Python AST. A parser reports what
its input says; it does not assign stable semantic types, choose ownership,
decide wrapper support, or emit a Python API.

The `c/` frontend preserves C declarations, types, locations, directives, and
project relationships before semantic conversion. It follows the same rule: a
declaration it accepts is a source fact, not wrapper support. The supported
wrapping surface belongs to
[C support](../../user/language-support/c-support.md).

## Inputs And Results

```text
prepared Fortran text
  -> lexer: logical lines with original locations
  -> source-unit scanner: classified file-level units and their regions
  -> FortranParser visitors and scoped declaration collection
  -> source-visible type, shape, kind, and visibility resolution
  -> FortranFile or dependency-aware FortranProject
  -> Fortran-to-IR conversion

prepared C text and directive metadata
  -> C lexer and declaration/declarator parser
  -> CFile or resolved CProject
  -> C-to-IR conversion

semantic .pyi text or path
  -> ast.parse
  -> ast.Module
  -> .pyi-to-IR conversion
```

`FortranFile` and `FortranProject` preserve parser facts. A parsed intrinsic
kind expression, `intent`, or array shape is still source syntax, not a
compiler-measured target fact or completed wrapper decision. The `.pyi` result
is Python syntax only; contract interpretation begins in `semantics/`.

## Local Structure

```text
prik/parsers/
├── __init__.py
├── fortran/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── lexer.py
│   ├── models.py
│   ├── parser.py
│   ├── type_resolver.py
│   └── utils.py
├── pyi/
│   ├── __init__.py
│   └── parser.py
└── c/
    ├── cli.py
    ├── lexer.py
    ├── models.py
    ├── parser.py
    └── type_resolver.py
```

## Directory Tour

| Module | Public boundary and result | Change it when |
| --- | --- | --- |
| [`prik/parsers/__init__.py`](../../../prik/parsers/__init__.py) | Names the language frontend namespaces; it does not flatten their APIs. | The parser-frontend layout changes. |
| [`prik/parsers/fortran/__init__.py`](../../../prik/parsers/fortran/__init__.py) | Re-exports `FortranParser`, `parse_fortran_file()`, `parse_fortran_project()`, parser models, and `FortranParseError`. | The supported Fortran-parser import surface changes. |
| [`prik/parsers/fortran/__main__.py`](../../../prik/parsers/fortran/__main__.py) | Runs the Fortran parser CLI for `python3 -m prik.parsers.fortran`. | Module-launch behavior changes. |
| [`prik/parsers/fortran/utils.py`](../../../prik/parsers/fortran/utils.py) | `detect_source_form()` chooses fixed or free form; `split_csv()` separates only top-level Fortran comma lists. | Source-form detection or grammar-neutral list splitting changes. |
| [`prik/parsers/fortran/lexer.py`](../../../prik/parsers/fortran/lexer.py) | `preprocess_lines()` produces logical lines with original coordinates; `strip_comment()` preserves string literals and OpenMP directives. | Comment handling, continuation folding, or location preservation changes. |
| [`prik/parsers/fortran/models.py`](../../../prik/parsers/fortran/models.py) | Passive source-fact records: `FortranFile`, `FortranProject`, units, declarations, shapes, and `FortranParseError`. | A parser result, source fact, or diagnostic representation changes. |
| [`prik/parsers/fortran/type_resolver.py`](../../../prik/parsers/fortran/type_resolver.py) | `extract_kind_from_type_spec()` preserves intrinsic kind and character syntax after declaration parsing. | Parser-level type-spec spelling extraction changes. |
| [`prik/parsers/fortran/parser.py`](../../../prik/parsers/fortran/parser.py) | `FortranParser`, `parse_fortran_file()`, and `parse_fortran_project()` build file and project models. | Grammar, source-unit structure, declarations, parser diagnostics, or project assembly changes. |
| [`prik/parsers/fortran/cli.py`](../../../prik/parsers/fortran/cli.py) | `main()` formats parser reports and diagnostics. Its `--semantics` and `--pyi` options explicitly invoke later stages. | Parser CLI arguments, report layout, or diagnostic presentation changes. |
| [`prik/parsers/c/`](../../../prik/parsers/c/README.md) | `parse_c_file()` and `parse_c_project()` build `CFile`/`CProject` records; the local lexer, models, resolver, and CLI preserve C declarations, project facts, diagnostics, and report output. | C tokenization, declarations, type resolution, project assembly, or parser reports change. |
| [`prik/parsers/pyi/__init__.py`](../../../prik/parsers/pyi/__init__.py) | Re-exports `parse_pyi_text()` and `parse_pyi_file()`. | The supported raw-`.pyi` parser import surface changes. |
| [`prik/parsers/pyi/parser.py`](../../../prik/parsers/pyi/parser.py) | Parses text or a file into `ast.Module` with no contract interpretation. | Raw Python syntax input, file reading, or parse diagnostics change. |

## Module Workflows

### `fortran/parser.py`: source units to parser models

Start at `parse_fortran_file()` for one source string or path. It delegates to
`FortranParser.parse_file()`, whose algorithm is:

1. Read the source and call `preprocess_lines()` to retain logical lines and
   original coordinates.
2. Ask the stateless `_SourceUnitScanner` to find direct file-level units and
   classify each unit's specification, execution, and `contains` regions.
3. Dispatch each `SourceUnit` to its `_visit_<Unit>` method. The visitor creates
   an explicit `_ParserScope` and parses only the regions allowed for that unit.
4. Shared declaration helpers create `FortranVariable`, `FortranArgument`,
   `FortranProcedureSignature`, and other passive source records.
5. Resolve derived-type links, source-visible compile-time symbols, and
   file-owned interfaces, then assemble a `FortranFile`.

Execution statements do not become wrapper metadata. Procedure-internal
subprograms are ignored after their boundaries are recognized; procedure-local
interfaces are revisited only when needed to type callback dummy arguments.

`parse_fortran_project()` accepts a mapping of names to source, explicit
paths, or a directory. It parses each file once, resolves cross-file
compile-time facts, checks project-level duplicate symbols, orders directory
files by dependencies, and returns a `FortranProject`. The project result is a
registry of the preserved file models, not a semantic module.

The source file follows this reading order: public entrypoints, unit visitors,
file and project assembly, source-unit preparation, grammar/header helpers,
scope and declaration parsing, finalization, then project diagnostics. Read
the visitor for the unit you are changing before its private helper group.

### `lexer.py`, `utils.py`, and `type_resolver.py`: syntax preservation

`detect_source_form()` uses a known filename suffix first, then a small
fixed-form continuation-column heuristic. `preprocess_lines()` removes comments
without touching quoted strings, folds fixed- and free-form continuations, and
returns `(logical_line, original_line_number, original_source_line)` tuples.
Those tuples are the location contract used by parser diagnostics.

`split_csv()` uses the shared balanced-expression scanner, so commas inside
dimensions, calls, brackets, or quoted text do not split a Fortran list.
`extract_kind_from_type_spec()` operates after the declaration parser isolates
an intrinsic type specifier: it preserves positional or `kind=` syntax and
keeps character length and kind together. Neither helper evaluates a kind
expression.

### `models.py`: passive parser vocabulary

`FortranVariable` and `FortranArgument` hold a declaration's spelling,
attributes, type, kind, and shape. `FortranProcedureSignature`,
`FortranDerivedType`, `FortranInterface`, and the module-like records organize
those facts by source unit. `FortranFile` is one parsed source; `FortranProject`
adds cross-file registries and dependencies. `FortranParseError` renders a
source-located, compiler-style diagnostic.

These records may provide structured views of preserved expressions and shapes,
but they do not make target, ownership, or wrapper-support decisions.

### `pyi/parser.py`: Python syntax only

`parse_pyi_text()` calls `ast.parse()` and returns its `ast.Module`.
`parse_pyi_file()` reads UTF-8 text then uses the same function. The module
does not recognize PRIK decorators, validate contract types, or build a
`SemanticModule`; `semantics/pyi2ir.py` owns all of that interpretation.

### `c/`: prepared C source to parser models

`parse_c_file()` preserves one translation unit; `parse_c_project()` resolves
explicitly supplied units into shared typedef, tag, function, and declaration
registries. The lexer and type resolver retain C spelling and declarator
topology without choosing Python storage or wrapper support. Compiler directive
handling belongs to `preprocessing/c.py`, and runtime eligibility belongs to
post-IR policy.

### `cli.py`: presentation after parsing

`python3 -m prik.parsers.fortran` enters `__main__.py`, which delegates to
`cli.main()`. The normal CLI path parses one or more files or directories and
renders a human-readable report or JSON. `--semantics` and `--pyi` deliberately
cross the parser boundary into semantic conversion and printing; they are
inspection conveniences, not parser behavior.

## Run The Workflows

Logical-line preparation preserves a line's original location after a free-form
continuation is folded:

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

The script supplies one continued subroutine declaration and prints the logical
records returned by the lexer. `line 1` remains the origin of the folded first
statement, which is the location a later parser diagnostic should report.

Type-spec extraction preserves syntax without evaluating it:

```bash
python3 prik/parsers/fortran/type_resolver.py
```

```text
integer(4) -> 4
real(kind=selected_real_kind(15, 307)) -> selected_real_kind(15, 307)
character(len=16, kind=c_char) -> len=16, kind=c_char
```

It passes three type-specification fragments to the extractor. The output
retains expressions such as `selected_real_kind(15, 307)` instead of evaluating
them, leaving target-dependent meaning for later stages.

Fortran file parsing assembles the parser model used by the next stage:

```bash
python3 prik/parsers/fortran/parser.py
```

```text
Module: metrics
Parameter: n = 4
Procedure: scale(values: real[1])
```

The script parses one in-memory module containing a parameter and a rank-one
subroutine argument. The output is parser vocabulary only: no semantic type,
ownership, or wrapper decision has been added.

The CLI example uses that same parser result and normal report formatter:

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

The CLI script parses one small file and formats the resulting project record.
Its nested report shows the same module and procedure hierarchy exposed by the
programmatic parser, rather than a separate interpretation path.

The semantic-`.pyi` parser returns an AST before any contract interpretation:

```bash
python3 prik/parsers/pyi/parser.py
```

```text
Parsed AST: Module
Function node: scale
Argument annotation: Float64
Semantic conversion performed: False
```

The script parses a one-function `.pyi` string and selects its AST node. The
function name and annotation are syntax facts; `False` confirms that semantic
conversion remains the next stage's responsibility.

The C parser example shows the equivalent source-fact boundary:

```bash
python3 prik/parsers/c/parser.py
```

```text
Parsed: state_api.h
Typedef: api_size -> unsigned long
Struct: state (id)
Function: count() -> api_size
Function: step(value) -> pointer to struct state
```

It parses a typedef, struct, value-returning function, and pointer parameter
into a `CFile`. The printed native spellings are parser facts; they do not claim
that an aggregate or pointer form is buildable.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Fortran parser suite](../../../tests/fortran/infrastructure/parsing/) | Source forms, units, declarations, scopes, diagnostics, project assembly, and parser models. |
| [Public parser entrypoints](../../../tests/fortran/infrastructure/parsing/test_public_entrypoints.py) | File, project, and singular-unit entrypoint contracts. |
| [Source forms and diagnostics](../../../tests/fortran/infrastructure/parsing/test_source_form_and_diagnostics_regressions.py) | Logical source preparation, unit boundaries, and public diagnostic metadata. |
| [Parser CLI](../../../tests/fortran/infrastructure/cli/pipeline/test_stage_dispatch.py) | Module launcher, report modes, diagnostic presentation, and explicit semantic/`.pyi` inspection modes. |
| [Semantic `.pyi` parsing](../../../tests/fortran/infrastructure/semantic_pyi/parsing/test_python_ast_contracts.py) | Raw `ast.Module` results and the AST-to-semantic-conversion handoff. |
| [C parser suite](../../../tests/c/infrastructure/parsing/) | C tokenization, declarations, compiler extensions, diagnostics, project assembly, fixtures, and public entrypoints. |
| [C parser CLI](../../../tests/c/infrastructure/cli/pipeline/) | C input selection, stage dispatch, output contracts, and report behavior. |

## Change Routes

- Change source forms, comments, continuations, or logical locations in
  `fortran/utils.py` or `fortran/lexer.py`.
- Change a parser result record or its diagnostic shape in `fortran/models.py`.
- Change type-spec spelling preservation in `fortran/type_resolver.py`.
- Change grammar, source-unit classification, declarations, source-visible
  compile-time resolution, or project assembly in `fortran/parser.py`.
- Change presentation and CLI options in `fortran/cli.py`.
- Change C tokenization, models, type resolution, grammar, project assembly, or
  report presentation in the corresponding module under `c/`.
- Change only raw `.pyi` AST parsing in `pyi/parser.py`; put contract meaning in
  `semantics/pyi2ir.py`.

## Boundaries And Invariants

- Preprocess compiler directives before parsing; the raw Fortran parser
  preserves branch alternatives rather than choosing one.
- Preserve source coordinates through lexical and structural parsing.
- Keep parser models source-faithful and policy-free.
- A construct that parses successfully is not automatically wrapper support.
- Treat serialized C parser output as a maintained format: prefer additive
  changes, preserve concrete model identity and source or diagnostic locations,
  retain unresolved facts, and use references instead of recursive copies when
  a type object is reused. Refresh parser goldens only for intentional format
  changes.
- Target kind values come from preprocessing probes; stable semantic types and
  contract interpretation come from `semantics/`.

## Failure Boundary

This stage reports invalid parser input, malformed or mismatched unit endings,
unsupported wrapper-relevant syntax, duplicate parser symbols, and invalid raw
Python syntax. It delegates compiler expansion and target facts to
`preprocessing/`, shared meaning to `semantics/`, and support decisions to
`policy/`. Start with the first incorrect logical line, source unit, or parser
model—not the later semantic or build failure.
