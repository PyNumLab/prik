## Contributing

### Contribution license

x2py is distributed under the MIT License. By submitting a contribution, you
agree that your contribution is licensed under the same MIT terms and represent
that you have the right to submit it. If an employer or another organization
owns the work, obtain its authorization before contributing.

### Pull requests

- **CI must be green before merging**: do not merge a PR unless all checks pass (including `test` and `parser-reference-guard`).
- **Explain fixture/golden updates**: if you update any JSON under `tests/data/fortran/` or `tests/parser/fortran/fixtures/`, include a short note in the PR describing why the expected output changed.
- **Run the QA stack for parser/compiler changes**: install `python -m pip install -e ".[qa]"`, use the workflows in `docs/quality.md`, and update that file when a staged adoption task or scheduled triage item changes.

### Parser reference guard

This repo includes a CI guard that may require updating parser reference docs
when parser-related files change.

- **C parser changes**: if you change `x2py/parsers/c/`, `tests/parser/c/`, or
  `tests/data/c/`, update `docs/c_parser.md` when the change affects the
  documented feature inventory, public API, diagnostics, fixtures, semantic
  handoff, or maintenance workflow. The guard also treats
  `tests/probes/test_c_types.py` as C parser related.
- **Fortran parser changes**: if you change `x2py/parsers/fortran/`,
  `tests/parser/fortran/`, or `tests/data/fortran/`, update
  `docs/fortran_parser.md` when the change affects the documented feature
  inventory, public API, diagnostics, fixtures, semantic handoff, or
  maintenance workflow. The guard also tracks focused Fortran parser tests
  directly under `tests/parser/`.
- **Shared parser workflow changes**: if you change shared parser CLI or
  preprocessing behavior, update `docs/c_parser.md` or
  `docs/fortran_parser.md`, whichever parser behavior changed.
- **Bypass (use sparingly)**: add the PR label `ignore-parser-reference-guard` to skip that guard for changes that do not meaningfully affect the reference.
