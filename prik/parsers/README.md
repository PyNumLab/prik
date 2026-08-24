# Parser Frontends

This namespace groups syntax-level frontends without flattening their
language-specific models:

- `prik.parsers.c` parses C source and headers.
- `prik.parsers.fortran` parses Fortran source and provides parser reports.
- `prik.parsers.pyi` parses semantic `.pyi` contracts to Python AST.

Cross-language semantic interpretation belongs to `prik.semantics`, while
preprocessing and build orchestration belong to `prik.pipeline`. Stable parser
APIs are imported from their owning language package, not from the `prik` root
facade.

See `docs/developer/packages/parsers.md`, `docs/developer/codebase-map.md`,
`docs/developer/feature-to-code-map.md`, and
`docs/user/reference/semantic-pyi-format.md` for maintained behavior.
