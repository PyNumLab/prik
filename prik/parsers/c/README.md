# C Parser Package

This package owns C source facts for inspection workflows. It parses C inputs,
preserves declarations and diagnostics, and feeds semantic conversion. It does
not own runtime wrapping of user-supplied C libraries.

Its canonical import namespace is `prik.parsers.c`. The stable convenience
functions `parse_c_file` and `parse_c_project` are imported from that package,
not from the root facade.

## Entry Points

| File | Owns |
| --- | --- |
| `parser.py` | Translation-unit parsing, project assembly, unsupported construct diagnostics. |
| `lexer.py` | C tokenization and comment/source splitting helpers. |
| `models.py` | Parser model dataclasses and C parse diagnostics. |
| `type_resolver.py` | C type resolution helpers used by parser and semantics. |
| `cli.py` | C parser CLI report formatting and preprocessing recipe wiring. |

Raw directive and include metadata is collected before grammar parsing by
`prik/preprocessing/c.py`. The parser consumes those prepared facts; it does
not own preprocessing.

## Tests And Docs

- Deferred reference: `docs/developer/deferred/c-parser.md`
- User recipe: `docs/user/examples/recipes/inspect-c-api.md`
- Source navigation: `docs/developer/codebase-map.md`, `docs/developer/feature-to-code-map.md`
- Parser tests: `tests/c/fixtures/parser/`
- Semantic handoff tests: `tests/c/infrastructure/semantic_ir/semantics/`

Runtime C-input wrapping is future backend work. Keep C docs clear about the
current boundary: parse, semantic IR, and `.pyi` are implemented;
compiled wrappers for user C inputs are not.
