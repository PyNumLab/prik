# C Input-Language Tests

`tests/c/` means C is the user-owned native input language. Generated C or
CPython binding code used to implement a Fortran wrapper remains under the
owning Fortran feature.

C language features use the same feature-first, stage-second shape as Fortran:

```text
tests/c/<language-feature>/<owning-stage>/
```

Parsing, preprocessing, command-line handling, semantic IR and `.pyi`
conversion, and other cross-feature mechanisms live under
`tests/c/infrastructure/`. Preserve node IDs where path changes permit,
parameters, markers, skips, xfails, and fixture contents.

The quarantined owners are:

| Owner | Scope |
| --- | --- |
| `data_types/<stage>/` | C scalar type facts and compiler type probes |
| `functions/<stage>/` | C function declarations and their semantic projection |
| `records/<stage>/` | C structs, unions, and typedefs |
| `enumerations/<stage>/` | C enum syntax and semantic projection |
| `infrastructure/cli/` | C-input command dispatch and C-specific argument/output contracts |
| `infrastructure/parsing/` | C lexer, parser, project, corpus, fixture, and public-entrypoint behavior |
| `infrastructure/preprocessing/` | C recipes, dependencies, mappings, execution, and diagnostics |
| `infrastructure/semantic_ir/` | C parser-model conversion to semantic IR |
| `infrastructure/semantic_pyi/` | C semantic `.pyi` conversion and source/generated-contract parity |
| `fixtures/native/` | C source and include inputs |
| `fixtures/parser/` | C parser snapshots and update commands |
| `fixtures/pyi/` | checked C generated-contract packages |
| `_support/` | C-only support shared by more than one C owner |

Run the complete quarantined suite with:

```bash
python3 -m pytest -q tests/c
```

Each directory is also independently collectable. C tests must use these final
paths directly; do not add forwarding imports, fixture aliases, collection
shims, or fallback paths.
