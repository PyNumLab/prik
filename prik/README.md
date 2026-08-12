# PRIK Source Package

This package contains the Python implementation for PRIK. Start from the
public behavior you are changing, then follow the owning layer instead of
jumping directly into generated-code internals.

## Main Entry Points

| File or package | Owns |
| --- | --- |
| `cli.py` | User CLI stages, output routing, diagnostics, and wrapper option validation. |
| `stage_values.py` | Shared stage-result records used by public inspection workflows. |
| `contracts/` | Public names used by semantic `.pyi` contracts. |
| `compiler/` | Reusable compiler commands, compile objects, native support installation, and linking. |
| `preprocessing/` | C/Fortran source preparation, provenance, native includes, and compiler-derived target facts. |
| `pipeline/` | Semantic `.pyi` loading, datatype mapping reports, wrapper generation orchestration, and end-to-end builds. |
| `runtime/` | Python runtime objects used by generated extensions. |
| `parsers/` | Parser namespace containing the `c`, `fortran`, and semantic `.pyi` frontends. |
| `semantics/` | Language-neutral semantic IR, scalar datatype vocabulary, declaration-expression provenance, and `.pyi` conversion. |
| `policy/` | Completed ownership and interoperability policy. |
| `planning/` | Editable backend-neutral wrapper implementation plans. |
| `codegen/` | Backend datatype projection, plan-driven documentation, and direct C/Fortran syntax-node lowering. |
| `printers/` | C, Fortran, and semantic `.pyi` serialization. |
| `binding_support/` | Header-only native support installed into generated wrapper builds. |
| `naming/` | Shared public-name and generated-symbol policy. |
| `utilities/` | Shared parsing, normalization, rendering, evaluation, and visitor helpers. |

The package root contains the public entrypoint modules plus the shared
`stage_values.py` record support. Supported library symbols are flattened
through `prik.__init__`; internal modules import their canonical owner.
`prik.contracts` remains a deliberate public submodule because its import path
is part of semantic `.pyi` syntax. Parser-specific imports use the public
`prik.parsers.c`, `prik.parsers.fortran`, and `prik.parsers.pyi` namespaces.

Array declaration expressions cross three source packages in a fixed order:
`utilities/declaration_expressions.py` parses and normalizes expression text,
`semantics/` records native callable provenance, `policy/` completes support,
and `codegen/` consumes only the completed plan while lowering generated
nodes. Follow that order when changing an expression feature; language
printers, bridges, and bindings must not infer missing expression semantics.

## Source Navigation Docs

- `docs/developer/source-map.md`
- `docs/developer/feature-to-code-map.md`
- `docs/developer/repository-structure.md`
- `docs/maintainer/internal-architecture/pipeline-map.md`

Keep user-facing support claims in the docs backed by focused tests and, for
wrapper behavior, runtime tests that compile, import, call, mutate, and check
failure paths as applicable.
