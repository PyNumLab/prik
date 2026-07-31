# Language-Neutral Tests

`tests/shared/` owns only behavior that does not import, select, parameterize,
or fall back between C and Fortran. A test is not shared merely because both
languages currently use the same Python helper.

Final shared owners include architecture, generic CLI parsing/output,
language-neutral semantic-contract syntax, documentation, naming, repository
tools, type utilities, and other genuinely language-independent mechanisms.
Language-specific behavior stays under `tests/fortran/` or `tests/c/`.

The maintained shared owner directories are `architecture/`, `docs/`,
`naming/`, `tools/`, `types/`, and `utilities/`. Do not declare an empty
owner directory: benchmark cases stay with the feature or tool they measure
and use the `benchmark` marker when cross-suite selection is needed.

Run the final shared owner independently with:

```bash
python3 -m pytest -q tests/shared
```

Do not add cross-language forwarding imports or compatibility paths.
