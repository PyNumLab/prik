---
title: Preprocessing Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, native project compiler flags
related: ../architecture.md, index.md, parsers.md, semantics.md, ../concepts/datatype-lifecycle.md
status: maintained
publication: draft
---

# Preprocessing Package

## Purpose And Boundaries

`prik/preprocessing/` turns original Fortran source into authoritative parser
input and measures compiler-dependent target facts needed by semantic
conversion. Compiler expansion, native Fortran includes, and executable probes
are separate mechanisms with separate results. The package does not parse
declarations, assign semantic scalar identities, choose NumPy dtypes, or
complete wrapper policy.

## Local Structure

```text
prik/preprocessing/
├── source.py
├── fortran.py
└── probes/
    └── fortran_types.py
```

The C preprocessing and target-probe modules remain deferred from the
published Fortran contributor workflow.

## Internal Workflow

```text
original Fortran path + PreprocessingConfig
  -> compiler expansion and line-marker recovery
  -> native Fortran INCLUDE expansion
  -> PreprocessResult(source, provenance, dependencies, recipe, diagnostics)
  -> Fortran parser

compiler identity + target flags + kind/storage requirements
  -> executable target probe
  -> FortranTypeProbeReport
  -> Fortran-to-IR conversion
```

Recipes retain compiler, adapter, argv, include directories, macro flags,
included files, source mappings, and diagnostics so a build can explain or
replay its parser input. Probe cache identity includes the compiler and target
configuration; measured facts must not cross targets silently.

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `source.py` | `PreprocessingConfig`, `PreprocessingRecipe`, `PreprocessResult`, `SourceMapping`, `IncludedFile` | Runs compiler preprocessing, collects provenance and dependencies, and coordinates native include expansion. |
| `fortran.py` | `expand_native_fortran_includes()` | Recursively expands native `INCLUDE` statements while preserving original locations and diagnostics. |
| `probes/fortran_types.py` | `FortranTypeProbeRecipe`, `FortranTypeProbeReport` | Compiles and runs target programs for kind expressions, storage widths, logical representations, and compile-time values. |

## Execution Examples

Coordinated preprocessing:

```bash
python3 prik/preprocessing/source.py
```

```text
Before Fortran include expansion:
module greeting
include 'constants.inc'
...
After Fortran include expansion:
module greeting
integer, parameter :: answer = 42
...
Native includes: 1; diagnostics: 0
```

Native include expansion in isolation:

```bash
python3 prik/preprocessing/fortran.py
```

```text
Expanded parser input:
module geometry
integer, parameter :: dimensions = 3
end module geometry
Native include dependencies: 1
Generated source mappings: 5
Diagnostics: 0
```

Compiler-measured Fortran type facts:

```bash
python3 prik/preprocessing/probes/fortran_types.py
```

```text
selected_int_kind(9) = 4
```

The first two outputs prove that prepared source retains dependency and source
mapping facts. The probe output is a native kind value, not yet a stable
semantic scalar or NumPy dtype. The probe example requires `gfortran` or
`f95`.

## Tests

- [Fortran preprocessing](../../../tests/fortran/source_preprocessing/preprocessing/)
- [Parser boundary tests](../../../tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py)
- [Fortran target probes](../../../tests/fortran/data_types/probes/test_fortran_type_probes.py)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change compiler expansion, provenance, recipes, or diagnostics in
  `source.py`.
- Change native `INCLUDE` behavior in `fortran.py`.
- Change target measurement or cache identity in `probes/fortran_types.py`.
- Change parser grammar downstream; change stable scalar identity or backend
  mapping in the owning semantic/codegen package.

## Invariants And Common Mistakes

- Preserve original source coordinates through every source transformation.
- Run native probes in temporary working directories so `.mod` and other
  compiler products cannot pollute the repository.
- Do not combine textual preprocessing and target measurement into one generic
  operation simply because both run before parsing.
