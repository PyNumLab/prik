# C Parser Tests

This directory contains active tests for the implemented partial C parser.

Guidelines:

- keep these tests separate from the Fortran parser tests
- keep wrapper-plan support diagnostics under the owning Fortran feature's
  `wrapper_codegen/` stage, not under C parser tests
- add parser snapshots only when the corresponding schema and preprocessing
  recipe are stable
- keep the checked-in cJSON regression inputs active while a separately pinned
  and provenanced corpus remains deferred

## Active cJSON Regression

The normal parser test run has no intentionally skipped C parser tests.
`tests/c/fixtures/native/json/cJSON.h` and `cJSON.c` exercise the header, source and
project paths in `test_c_corpus.py`; a separately pinned copy with license and
source provenance remains documentation work rather than a disabled test.

## Legacy Parser Snapshots

Checked-in compatibility snapshots cover grouped projects from `tests/c/fixtures/native/general/`,
`tests/c/fixtures/native/json/`, `tests/c/fixtures/native/tinyexpr/`, `tests/c/fixtures/native/linmath/`, and
`tests/c/fixtures/native/nanosvg/`, plus top-level C inputs from `tests/c/fixtures/native/stb/`.
They preserve historical JSON shape for schema sanity checks. They are not
active parser output goldens: macro-heavy inputs now require compiler
preprocessing, and reproducible compiler-recipe snapshots need a separate
curated fixture workflow.

## Developer Walkthrough

`test_c_parser_developer_tutorial.py` is an executable reading guide for
`x2py/parsers/c/parser.py`. It shows the shared declaration/declarator gateway, the
`parse_file` routing of declaration roles, and the preprocessed linemarker
path without replacing the feature-focused test modules.

`test_c_fixture_suite.py` keeps fixture grouping coverage and verifies that
representative macro-heavy fixtures fail clearly in raw mode.

## Error Goldens

Fatal diagnostic fixtures live in `tests/c/fixtures/native/errors/parser/` and their
expected metadata lives in `fixtures/errors/`. Regenerate them with:

```bash
C_PARSER_UPDATE_GOLDENS=1 PYTHONPATH=. pytest -q tests/c/parsing/test_c_error_fixture_suite.py
```

The standalone error generator remains available for targeted refreshes, and
the comparison tests rewrite checked-in error baselines when
`C_PARSER_UPDATE_GOLDENS=1` is set.
