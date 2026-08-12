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

`prik/parsers/` owns syntax-level facts. The Fortran frontend preserves source
units, declarations, visibility, locations, and diagnostics. The semantic
`.pyi` frontend deliberately stops at a standard Python AST. A parser reports
what its input says; it does not assign a stable semantic type, choose
ownership, decide wrapper support, or emit a Python API.

The C-input frontend is intentionally deferred from the published contributor
workflow. This guide covers the supported Fortran and semantic-`.pyi` path;
generated C binding remains documented under [code generation](codegen.md).

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
└── pyi/
    ├── __init__.py
    └── parser.py
```

## What This Stage Receives And Produces

```text
prepared Fortran text
  -> logical lines with original locations
  -> Fortran parser models and diagnostics
  -> Fortran-to-IR conversion

semantic .pyi text
  -> ast.Module
  -> .pyi-to-IR conversion
```

Fortran parser models retain source spellings such as `real(kind=...)`,
`intent`, and declaration shapes. Target-dependent kind values arrive from
preprocessing probes and are resolved in semantic conversion, not here.

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/parsers/__init__.py`](../../../prik/parsers/__init__.py) | Declares the parser frontend namespaces. | The package-level frontend layout changes. |
| [`prik/parsers/fortran/__init__.py`](../../../prik/parsers/fortran/__init__.py) | Re-exports the supported Fortran parser API: parser functions, `FortranParser`, parser models, and `FortranParseError`. | The supported Fortran-parser import API changes. |
| [`prik/parsers/fortran/__main__.py`](../../../prik/parsers/fortran/__main__.py) | Module launcher for `python3 -m prik.parsers.fortran`; delegates to the CLI. | Module-launch behavior changes, not parser semantics. |
| [`prik/parsers/fortran/utils.py`](../../../prik/parsers/fortran/utils.py) | `detect_source_form()` and `split_csv()` are small, grammar-neutral lexical helpers. | Source-form detection or top-level comma splitting changes. |
| [`prik/parsers/fortran/lexer.py`](../../../prik/parsers/fortran/lexer.py) | `strip_comment()` and `preprocess_lines()` remove comments, fold continuations, and retain logical-line locations. | Lexical normalization or source-coordinate retention changes. |
| [`prik/parsers/fortran/models.py`](../../../prik/parsers/fortran/models.py) | Passive parser records including `FortranFile`, `FortranProject`, `FortranModule`, variables, signatures, derived types, enums, shapes, and `FortranParseError`. | A parser-level source fact or diagnostic representation changes. |
| [`prik/parsers/fortran/type_resolver.py`](../../../prik/parsers/fortran/type_resolver.py) | `extract_kind_from_type_spec()` preserves type, kind, and character syntax without measuring its meaning. | Parser-level type-spec spelling extraction changes. |
| [`prik/parsers/fortran/parser.py`](../../../prik/parsers/fortran/parser.py) | `FortranParser`, source-unit records, `parse_fortran_file()`, and `parse_fortran_project()` slice units, build models, resolve parser-level scope, and order projects. | Grammar, declaration extraction, source-unit structure, parser diagnostics, or project ordering changes. |
| [`prik/parsers/fortran/cli.py`](../../../prik/parsers/fortran/cli.py) | `main()` turns parser requests into stable human or JSON reports. | Parser CLI arguments or report presentation changes. |
| [`prik/parsers/pyi/__init__.py`](../../../prik/parsers/pyi/__init__.py) | Re-exports `parse_pyi_text()` and `parse_pyi_file()`. | The supported raw-`.pyi` parser import surface changes. |
| [`prik/parsers/pyi/parser.py`](../../../prik/parsers/pyi/parser.py) | `parse_pyi_text()` and `parse_pyi_file()` validate and return `ast.Module` without semantic interpretation. | Accepted Python syntax or raw parse diagnostics change. |

Read `fortran/parser.py` by entrypoint, then source-unit scanning, then the
visitor that owns the construct you are changing. Do not add policy or codegen
conditions to a parser visitor: preserve the fact and let the next stage
decide whether it is supported.

## Execution Examples

Logical-line preparation:

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

Fortran file parsing:

```bash
python3 prik/parsers/fortran/parser.py
```

```text
Module: metrics
Parameter: n = 4
Procedure: scale(values: real[1])
```

Type-spec preservation:

```bash
python3 prik/parsers/fortran/type_resolver.py
```

```text
integer(4) -> 4
real(kind=selected_real_kind(15, 307)) -> selected_real_kind(15, 307)
character(len=16, kind=c_char) -> len=16, kind=c_char
```

Parser report formatting:

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

Raw semantic-`.pyi` parsing:

```bash
python3 prik/parsers/pyi/parser.py
```

```text
Parsed AST: Module
Function node: scale
Argument annotation: Float64
Semantic conversion performed: False
```

These outputs are intentionally parse-only. They show preserved source facts,
not a completed `SemanticModule`, wrapper plan, or generated source.

## Tests And What They Prove

- [Fortran parser tests](../../../tests/fortran/source_parsing/parsing/) cover source forms, units, declarations, diagnostics, and project ordering.
- [Fortran parser CLI tests](../../../tests/fortran/command_line_interface/pipeline/) cover parser command dispatch and report output.
- [Semantic `.pyi` parsing tests](../../../tests/fortran/semantic_pyi_format/parsing/) cover raw `.pyi` AST parsing and diagnostics.
- [Semantic IR conversion tests](../../../tests/fortran/semantic_ir/semantics/) prove the downstream Fortran-model handoff.
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py) fixes the five demonstrations above.

## Change Routes

- Change source form, comments, continuations, or logical locations in
  `fortran/utils.py` or `fortran/lexer.py`.
- Change parser facts in `fortran/models.py`; change grammar and source-unit
  construction in `fortran/parser.py`.
- Change parser report layout in `fortran/cli.py`.
- Change only raw `.pyi` AST parsing in `pyi/parser.py`; put meaning in
  `semantics/pyi2ir.py`.
- If a change needs target kind values, use preprocessing probes; if it needs
  ownership, projection, or support, use policy after semantic conversion.

## Invariants And Common Mistakes

- Preserve original source locations through lexical and structural parsing.
- Keep parser models passive and source-faithful; do not attach completed
  policy to them.
- `parse_fortran_project()` only receives explicit project files; it does not
  invent recursive source discovery.
- A construct that parses successfully is not automatically wrapper support.
- The `.pyi` parser returns Python AST. Contract interpretation starts only in
  `semantics/pyi2ir.py`.
