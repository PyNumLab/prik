# Parser Frontends

This namespace groups syntax-level frontends without flattening their
language-specific models:

- `prik.parsers.c` parses C source and headers.
- `prik.parsers.fortran` parses Fortran source and provides parser reports.
- `prik.parsers.pyi` parses semantic `.pyi` contracts to Python AST.

Cross-language semantic interpretation belongs to `prik.semantics`, while
preprocessing and build orchestration belong to `prik.pipeline`. Stable parser
convenience functions remain exported from the `prik` package root.

See `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`,
`docs/developer/c-parser-reference.md`, `docs/developer/fortran-parser-reference.md`, and
`docs/user/reference/semantic-pyi-format.md` for maintained behavior.
