# C Parser Package

This package owns C source facts for inspection and direct-C wrapper workflows.
It parses C inputs, preserves declarations and diagnostics, and feeds semantic
conversion. Runtime support remains narrower than parser acceptance and is
decided after semantic conversion; this package does not own that policy.

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

- Public support boundary: `docs/user/language-support/c-support.md`
- Source navigation: `docs/developer/codebase-map.md`, `docs/developer/feature-to-code-map.md`
- Parser tests: `tests/c/infrastructure/parsing/`
- Semantic handoff tests: `tests/c/infrastructure/semantic_ir/semantics/`
- Direct-C policy, codegen, and runtime tests: `tests/c/primitive_scalars/`,
  `tests/c/primitive_pointers/`, `tests/c/primitive_strings/`, and
  `tests/c/symbol_collisions/`

Compiled C-input wrappers are implemented for the direct-C subset published in
the C support guide. Keep contributor claims equally clear in both directions:
parser and semantic inspection cover more declarations than runtime wrapping,
while the documented scalar, pointer, array, string, output, status, and
collision-forwarder paths have compiled evidence.
