---
title: Testing Strategy
audience: developers, contributors
prerequisites: repository structure
related: quality-assurance.md, development-workflow.md
status: maintained
publication: draft
---

# Testing Strategy

The canonical directory and command map is [`../../tests/README.md`](../../tests/README.md).
Use it to select tests by the source package, pipeline stage, or wrapper feature
that owns the changed behavior.

## Choose tests by ownership

Stage and unit tests mirror the implementation pipeline:

- parser syntax and parser models live under `tests/parsing/` by language;
- compiler-derived target facts live under `tests/probes/`;
- preprocessing and build orchestration live under `tests/pipeline/` by
  workflow;
- semantic conversion and completed policy have separate owners under
  `tests/semantics/`;
- wrapper planning, bridge/binding generation, and source/`.pyi` printing live
  under `tests/wrapper_codegen/`;
- runtime handles, naming, and type mapping live under `tests/runtime/`,
  `tests/naming/`, and `tests/types/`;
- documentation, repository-tool, and architecture checks live under
  `tests/docs/`, `tests/tools/`, and `tests/architecture/`.

Run the narrowest owning directory first, then its parent stage when the change
crosses subjects. For example:

```bash
python3 -m pytest -q tests/parsing/fortran
python3 -m pytest -q tests/semantics/conversion/fortran
python3 -m pytest -q tests/semantics/policy
python3 -m pytest -q tests/wrapper_codegen
```

CLI behavior has its own `tests/cli/` owner. Property and regression tests live
with their owning stage and retain their markers, so a stage-directory command
does not omit them.

The legacy lowering AST and `x2py.codegen` package are removed. Their bridge,
binding, and printer implementation tests are not carried through cutover. Any
still-relevant contract is expressed against completed semantic policy,
`WrapperPlan`/`WrapperCodeGenerator`, or public compiled wrapper behavior.

## Wrapper runtime features

Compiled wrapper tests stay organized by user-visible feature, not by internal
pipeline stage. The Fortran index is
[`../../tests/wrapper/fortran/README.md`](../../tests/wrapper/fortran/README.md),
and the roadmap-to-test lookup is
[`../../tests/wrapper/CHECKLIST_COVERAGE.md`](../../tests/wrapper/CHECKLIST_COVERAGE.md).

For a feature with equivalent source and generated-`.pyi` behavior, both build
modes execute one shared behavioral assertion body. Modified-contract behavior
stays in the same feature subject but uses its intentionally different
assertions.

During the wrapper-plan migration, run all Fortran wrapper subjects except the
deferred full BLAS/LAPACK corpus with:

```bash
python3 -m pytest -q tests/wrapper/fortran \
  --ignore=tests/wrapper/fortran/real_libraries/test_real_blas_lapack.py
```

The full LAPACK wrapper test remains CI-only by default. The full BLAS test may
be run locally when its library-scale evidence is needed. One dedicated GitHub
Actions job runs the exact full BLAS and LAPACK nodes together on Python 3.12;
the ordinary Python-version matrix excludes their complete test file. Add the
`ignore-real-library-wrappers` label to a pull request to skip only this
expensive dedicated job. General native-bundle tests remain active in the
ordinary matrix.

## Fixtures and generated expectations

Test module ownership does not move native inputs, `.pyi` contract trees, or
generated expected data. Follow each fixture tree's README and existing
regeneration command. Fixture refreshes must be caused by an intentional
contract change, never by a test-layout migration.

## Required verification

After moving or splitting tests, run collection before execution and compare
the total, parametrized suffixes, function/class names, marker counts, and
skipped-at-collection behavior. Then run every destination directory touched by
the move. Repository-wide collection is required at completion.

For code or test changes, run the complete static-analysis suite documented in
`AGENTS.md`. Documentation-only changes use the focused documentation checks
and whitespace check. Routine work does not require the complete coverage
workflow; coverage investigations must mirror the parallel-data GitHub Actions
workflow before drawing conclusions.
