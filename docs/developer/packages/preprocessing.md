---
title: Preprocessing Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, native project compiler flags
related: ../architecture.md, index.md, parsers.md, semantics.md
status: maintained
publication: reviewed
---

# Preprocessing Stage

## Purpose And Boundaries

`prik/preprocessing/` turns original Fortran source into parser input and
measures the compiler-dependent facts that semantic conversion needs. It owns
compiler invocation, source provenance, native `INCLUDE` expansion, and
target probes. It does not parse declarations, construct semantic IR, choose
semantic scalar identities, or complete wrapper policy.

The package contains early C-frontend modules: `c.py` collects raw directive
metadata and `probes/c_types.py` measures C ABI facts. C support is not yet
complete; a future C frontend may build on them. They do not participate in
the current Fortran wrapper path.

## A Fortran Source Through This Stage

The primary route is `preprocess_source()` in `source.py`. It retains the
prepared source and the facts that explain how it was produced:

```text
Fortran source path + PreprocessingConfig
  -> select compiler command: direct compiler, compile database, or template
  -> compiler-expanded source
  -> source mappings, dependencies, optional macros, diagnostics, and recipe
  -> native Fortran INCLUDE expansion
  -> PreprocessResult.source
  -> Fortran parser

semantic requirements + compiler and target configuration
  -> Fortran type probe: generate, compile, and run a small program
  -> FortranTypeProbeReport(values, recipe, source_text)
  -> Fortran-to-IR conversion
```

`PreprocessResult` is prepared parser input plus provenance; it is not parsed
syntax or semantic meaning. `FortranTypeProbeReport` is a compiler measurement
plus its recipe; it is not a stable semantic scalar or NumPy dtype.

## Local Structure

```text
prik/preprocessing/
├── __init__.py
├── source.py
├── fortran.py
├── c.py                         deferred C inspection support
└── probes/
    ├── fortran_types.py
    └── c_types.py               deferred C inspection support
```

## Directory Tour

| Module | Public boundary and result | Change it when |
| --- | --- | --- |
| [`prik/preprocessing/__init__.py`](../../../prik/preprocessing/__init__.py) | Re-exports the supported shared source-preparation records, adapters, and entrypoints. | The shared preprocessing import surface changes. |
| [`prik/preprocessing/source.py`](../../../prik/preprocessing/source.py) | `preprocess_source()` is the compiler-backed route. `PreprocessingConfig` selects its command; `PreprocessResult` returns expanded text, provenance, and diagnostics. | Compiler adapters, invocations, recipes, mappings, dependencies, macros, or diagnostics change. |
| [`prik/preprocessing/fortran.py`](../../../prik/preprocessing/fortran.py) | `expand_native_fortran_includes()` turns remaining textual `INCLUDE` statements into parser input while retaining mappings and diagnostics. | Native Fortran include discovery or expansion changes. |
| [`prik/preprocessing/probes/fortran_types.py`](../../../prik/preprocessing/probes/fortran_types.py) | `evaluate_fortran_type_requirements()` and `evaluate_fortran_type_facts()` turn semantic requirements into cached compiler measurements; `FortranTypeProbeReport` retains values and recipe. | Fortran fact generation, validation, cache identity, or semantic-facing probe results change. |

## Module Workflows

### `source.py`: compiler-backed parser input

`preprocess_source()` is the normal boundary. Start with it when changing the
prepared-source path. It validates `PreprocessingConfig`, then
`build_preprocess_invocation()` selects a command-template, compile-database,
or direct-compiler invocation. It executes that invocation, collects compiler
line markers, dependencies, optional macros, and diagnostics, then delegates
remaining native Fortran `INCLUDE` statements to `fortran.py`.

The public records divide the work: `PreprocessingPlan` and `Invocation`
describe a request and command before execution; `PreprocessingRecipe` and
`PreprocessResult` record the completed operation; `SourceMapping`,
`IncludedFile`, `MacroDefinition`, and `PreprocessingDiagnostic` retain its
side facts. The convenience runners return only source or source plus a typed
recipe; use `preprocess_source()` when the next stage needs the complete
result.

The source is organized in the same order: configuration and validation,
adapter facades, invocation construction, provenance recovery, then execution
and result assembly. Private helpers belong to one of those phases.

### `fortran.py`: native includes after compiler expansion

`expand_native_fortran_includes()` receives an already compiler-expanded
Fortran stream. It resolves an `INCLUDE` beside its including source before the
configured directories, expands it recursively, and returns parser text,
dependency edges, source mappings, and diagnostics. It records a missing file
or cycle rather than making parser decisions; `source.py` promotes error
diagnostics after assembling the complete result.

### `probes/fortran_types.py`: target facts for semantic conversion

The module generates a small Fortran program, compiles and runs it for the
configured target, validates its result, and caches the report by compiler,
flags, runner, environment, and generated source.

`evaluate_fortran_type_requirements()` and
`evaluate_fortran_type_facts()` receive semantic requirement records. They
reuse a supplied or cached `FortranTypeProbeReport` and return the values that
the Fortran semantic converter needs. `probe_fortran_type_expressions()` is
the uncached measurement boundary; `probe_fortran_type_expressions_cached()`
is the normal repeated-use boundary. A report is valid only for the target
identity encoded in its recipe and cache key.

## Run The Workflows

`source.py` demonstrates the source-preparation handoff. Its complete direct
example also prints a small C source-preparation demonstration; C frontend
support remains future work.

```bash
python3 prik/preprocessing/source.py
```

```text
Before Fortran include expansion:
module greeting
include 'constants.inc'
contains
subroutine show_answer()
print *, answer
end subroutine show_answer
end module greeting

After Fortran include expansion:
module greeting
integer, parameter :: answer = 42
contains
subroutine show_answer()
print *, answer
end subroutine show_answer
end module greeting
Native includes: 1; diagnostics: 0
...
```

The Fortran-specific module shows the parser input and provenance it returns:

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

The target-probe example shows a compiler measurement, not a fixed semantic
type. It requires `gfortran` or `f95`.

```bash
python3 prik/preprocessing/probes/fortran_types.py
```

```text
selected_int_kind(9) = 4
```

The reported number is target-dependent. The example establishes that the
compiler, rather than PRIK, supplied the fact.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Fortran preprocessing](../../../tests/fortran/source_preprocessing/preprocessing/) | Adapters, recipes, mappings, native includes, diagnostics, and parser handoffs. |
| [Parser boundaries](../../../tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py) | Prepared source reaches parsing with preserved facts and unsupported raw constructs stop at the correct boundary. |
| [Fortran type probes](../../../tests/fortran/data_types/probes/test_fortran_type_probes.py) | Compiler facts, requirement evaluation, cache separation, and report validation. |

## Change Routes

- Change compiler expansion, commands, provenance, recipes, or diagnostics in
  `source.py`.
- Change native Fortran `INCLUDE` behavior in `fortran.py`.
- Change compiler-measured Fortran facts or cache identity in
  `probes/fortran_types.py`.
- Change stable scalar identity in `semantics/`, backend dtype projection in
  `codegen/`, and wrapper behavior in the later owning stage.

## Boundaries And Invariants

- Preserve original coordinates through every source transformation.
- Keep compiler expansion, native include expansion, and target measurement
  as separate operations.
- Run probes in temporary directories so compiler products cannot enter the
  repository.
- Do not reuse source provenance or a probe report across a materially
  different compiler target.

## Failure Boundary

This stage reports invalid preprocessing configuration, compiler execution
failures, missing native includes, include cycles, and invalid probe results.
It delegates declaration syntax to `parsers/`, stable meaning to `semantics/`,
and wrapper support to later stages. Start with the first incorrect prepared
source, provenance record, or compiler fact—not the later parser or build
failure.
