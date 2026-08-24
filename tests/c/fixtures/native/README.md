C fixture data
==============

This tree holds C-only parser fixtures. Keep these files separate from the
Fortran fixture data so C parser tests can grow without changing the existing
Fortran workflows.

Directories:

- `general/`: small hand-written C headers and sources that mirror the themes
  in the Fortran suite, plus C-specific API shapes.
- `json/`: JSON-library source/header inputs used for compiler-preprocessed
  corpus regression coverage.
- `tinyexpr/`, `linmath/`, `nanosvg/`, and `stb/`: macro-heavy real-world
  inputs used for raw-preprocessing boundary coverage and future curated
  compiler-preprocessed corpus work.
- `errors/parser/`: invalid C snippets for parser diagnostic goldens.
- `corpus/`: future pinned third-party C corpus fixtures with license
  provenance.
- `scientific/`: future scientific C API fixtures.

The C parser is still partial. Fixtures may contain constructs that are not
fully parsed yet when they are useful future-design examples.

The third-party regression inputs do not replace the planned pinned corpus
layout. Before corpus tests claim library coverage, exact provenance and
license requirements must be recorded under `corpus/`.
