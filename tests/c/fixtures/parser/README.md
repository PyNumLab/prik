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

`tests/c/fixtures/native/json/cJSON.h` and `cJSON.c` exercise the header, source and
project paths in `test_c_corpus.py`; a separately pinned copy with license and
source provenance remains documentation work rather than a disabled test.
The exact compiler-preprocessed project snapshot is a Linux reference golden
and is skipped on other platforms. Portable parser and preprocessing behavior
continues to run there.

## Project Goldens

Checked-in compatibility snapshots cover grouped projects from `tests/c/fixtures/native/general/`,
`tests/c/fixtures/native/json/`, `tests/c/fixtures/native/tinyexpr/`, `tests/c/fixtures/native/linmath/`, and
`tests/c/fixtures/native/nanosvg/`, plus top-level C inputs from `tests/c/fixtures/native/stb/`.
They preserve the compiler-preprocessed Linux reference payload and historical
JSON shape. Do not refresh them from macOS or another compiler/libc reference
environment.

## Developer Walkthrough

`test_c_parser_developer_tutorial.py` is an executable reading guide for
`prik/parsers/c/parser.py`. It shows the shared declaration/declarator gateway, the
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
