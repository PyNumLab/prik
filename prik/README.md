# PRIK Source Package

This package contains the Python implementation for PRIK. Start from the
public behavior you are changing, then follow the owning layer instead of
jumping directly into generated-code internals.

## Main Entry Points

| File or package | Owns |
| --- | --- |
| `cli.py` | User CLI stages, output routing, diagnostics, and wrapper option validation. |
| `contracts/` | Public names used by semantic `.pyi` contracts. |
| `pipeline/` | Preprocessing, semantic `.pyi` loading, and end-to-end wrapper builds. |
| `probes/` | C ABI facts, Fortran kind/storage facts, and type mapping reports. |
| `runtime/` | Python runtime objects used by generated extensions. |
| `types/` | Semantic-to-Python ecosystem type mappings. |
| `parsers/` | Parser namespace containing the `c`, `fortran`, and semantic `.pyi` frontends. |
| `semantics/` | Language-neutral semantic IR, policy completion, and `.pyi` conversion. |
| `codegen/` | Canonical wrapper plans, direct native bridge/binding generation, and source printers. |
| `compiling/` | Native compiler objects, wrapper compilation, native support installation, and linking. |
| `utilities/` | Small domain-neutral helpers, including class visitor dispatch. |

The package root contains the public entrypoint modules plus the shared
`stage_values.py` record support. Supported library symbols are flattened
through `prik.__init__`; internal modules import their canonical owner.
`prik.contracts` remains a deliberate public submodule because its import path
is part of semantic `.pyi` syntax. Parser-specific imports use the public
`prik.parsers.c`, `prik.parsers.fortran`, and `prik.parsers.pyi` namespaces.

## Source Navigation Docs

- `docs/developer/source-map.md`
- `docs/developer/feature-to-code-map.md`
- `docs/developer/repository-structure.md`
- `docs/maintainer/internal-architecture/pipeline-map.md`

Keep user-facing support claims in the docs backed by focused tests and, for
wrapper behavior, runtime tests that compile, import, call, mutate, and check
failure paths as applicable.
