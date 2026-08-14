# Semantic `.pyi` Parser Package

This package owns syntax-only parsing for semantic `.pyi` contracts. It reads
inline text or files and returns Python AST modules. Semantic interpretation is
handled by `prik/semantics/pyi2ir.py`, and combined file/text loading is handled
by `prik/pipeline/pyi.py`.

Its public parser namespace is `prik.parsers.pyi`; the `prik` root facade does
not re-export `parse_pyi_text` or `parse_pyi_file`.
