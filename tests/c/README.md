# C Input-Language Tests

`tests/c/` means C is the user-owned native input language. Generated C or
CPython binding code used to implement a Fortran wrapper remains under the
owning Fortran feature.

The meta-test that validates this directory's quarantine and isolation lives
outside it under `tests/architecture/c/`.

C receives a mechanical quarantine during the language-first migration. Move
existing C parsing, probes, preprocessing, semantic conversion, pipeline, CLI
dispatch, property tests, fixtures, and helpers without redesigning their
behavior. Preserve node IDs where path changes permit, parameters, markers,
skips, xfails, and fixture contents.

The quarantined owners are:

| Owner | Scope |
| --- | --- |
| `cli/` | C-input command dispatch and C-specific argument/output contracts |
| `parsing/` | C lexer, parser, project, corpus, fixture, and public-entrypoint behavior |
| `probes/` | C compiler type probes |
| `preprocessing/` | C recipes, dependencies, mappings, execution, and diagnostics |
| `semantics/conversion/` | C parser model and C semantic `.pyi` conversion |
| `pipeline/` | C source/generated-contract parity |
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
