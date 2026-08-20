# Semantic `.pyi` Format

This feature owns the executable format contract described by the
[Semantic `.pyi` Format](../../../../../docs/user/reference/semantic-pyi-format.md)
reference. It covers contract syntax, semantic loading and printing, imports
and type identity, generated package layout, structural diagnostics, and one
ordinary source-free runtime rebuild from an authoritative generated contract.

Evidence is split by the stage that establishes it:

- `parsing/` checks the Python-AST boundary and supported annotation syntax;
- `semantics/` checks types, values, imports, overloads, projections, and
  stable semantic-IR round trips;
- `pipeline/` checks reviewed contract packages, recursive import discovery,
  diagnostics, cache reuse, and source-to-contract package topology; and
- `end_to_end/` proves that an unedited generated package can rebuild and call
  a precompiled native object without falling back to the Fortran source.

Native artifact selection and linking remain owned by
`building_shared_library/`. Editable export/module, function/class,
and call/result behavior remains owned by the three later
`pyi_contracts/` features.

Run the feature with:

```bash
python3 -m pytest -q tests/fortran/infrastructure/semantic_pyi
```

Refresh the reviewed contract packages only after reviewing a deliberate
format change:

```bash
WRAPPER_UPDATE_PYI_FIXTURES=1 python3 -m pytest -q \
  tests/fortran/infrastructure/semantic_pyi/pipeline/test_contract_package_generation.py
```
