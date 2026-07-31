# C Parser Package

This package owns C source facts for inspection workflows. It parses C inputs,
preserves declarations and diagnostics, and feeds semantic conversion. It does
not own runtime wrapping of user-supplied C libraries.

Its canonical import namespace is `x2py.parsers.c`. The stable convenience
functions `x2py.parse_c_file` and `x2py.parse_c_project` remain available from
the package root.

## Entry Points

| File | Owns |
| --- | --- |
| `parser.py` | Translation-unit parsing, project assembly, unsupported construct diagnostics. |
| `lexer.py` | C tokenization and comment/source splitting helpers. |
| `models.py` | Parser model dataclasses and C parse diagnostics. |
| `preprocessor.py` | Preprocessor metadata collection. |
| `type_resolver.py` | C type resolution helpers used by parser and semantics. |
| `cli.py` | C parser CLI report formatting and preprocessing recipe wiring. |

## Tests And Docs

- Public reference: `docs/developer/c-parser-reference.md`
- User recipe: `docs/user/examples/recipes/inspect-c-api.md`
- Source navigation: `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`
- Parser tests: `tests/c/fixtures/parser/`
- Semantic handoff tests: `tests/c/semantics/conversion/`

Runtime C-input wrapping is future backend work. Keep C docs clear about the
current boundary: parse, semantic IR, and `.pyi` are implemented;
compiled wrappers for user C inputs are not.
