# Test-Suite Architecture Checks

`tests/architecture/` owns meta-tests whose subject is the test suite itself:
directory ownership, evidence indexes, collection, markers, and bounded
selections. It is outside the language trees so a structural check does not
live inside the structure it validates.

Language-specific meta-tests use a language subdirectory:

- `c/` validates the mechanically quarantined C tree and its isolation.
- `fortran/` validates the Fortran feature/stage tree, permanent contract
  ledger, real-library isolation, and portable smoke selection.

Product behavior does not belong here. Fortran behavior stays under
`tests/fortran/`, C behavior stays under `tests/c/`, and genuinely
language-neutral product behavior stays under `tests/shared/`.

Run this owner independently with:

```bash
python3 -m pytest -q tests/architecture
```
