# Semantic `.pyi` Parser Package

This package owns syntax-only parsing for semantic `.pyi` contracts. It reads
inline text or files and returns Python AST modules. Semantic interpretation is
handled by `prik/semantics/pyi2ir.py`, and combined file/text loading is handled
by `prik/pipeline/pyi.py`.

Its canonical parser namespace is `prik.parsers.pyi`; `parse_pyi_text` and
`parse_pyi_file` also remain stable root-level `prik` exports.
