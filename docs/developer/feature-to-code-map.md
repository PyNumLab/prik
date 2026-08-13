---
title: Feature-to-Code Map
audience: developers, contributors
prerequisites: PRIK Architecture, Codebase Map
related: architecture.md, codebase-map.md, packages/index.md, testing-strategy.md
status: maintained
publication: reviewed
---

# Feature-to-Code Map

This map connects a user-visible capability to its primary source owners,
documentation, and focused evidence. It is a change-routing index, not a
second support matrix: [Architecture](architecture.md) defines the stage
handoffs, the [Codebase Map](codebase-map.md) lists package ownership, and the
public feature matrix states the support boundary and limitations.

## Feature Routes

Links in the documentation column are reviewed pages. Plain repository paths
identify the planned `docs/developer/` pages that may need revision before
publication.

| Capability | Relevant documentation | Primary owners | Focused evidence |
| --- | --- | --- | --- |
| Fortran inspection and semantic IR | `docs/developer/packages/parsers.md` | `prik/parsers/fortran/parser.py`, `prik/semantics/fortran2ir.py`, `prik/semantics/models.py` | `tests/fortran/source_parsing/parsing/`, `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py`, `tests/fortran/semantic_ir/semantics/` |
| CLI commands and reports | [Beginner workflow](../user/getting-started/beginner-workflow.md) | `prik/cli.py`, `prik/parsers/fortran/cli.py` | `tests/fortran/command_line_interface/pipeline/`, `tests/docs/test_examples.py` |
| Source preparation and target types | `docs/developer/packages/preprocessing.md` | `prik/preprocessing/source.py`, `prik/preprocessing/fortran.py`, `prik/preprocessing/probes/fortran_types.py`, `prik/semantics/scalar_types.py`, `prik/codegen/primitive_scalar_types.py` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`, `tests/fortran/data_types/` |
| Semantic `.pyi` generation and editing | [.pyi contracts](../user/reference/pyi-contracts/index.md) | `prik/printers/pyi.py`, `prik/parsers/pyi/parser.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py` | `tests/fortran/semantic_pyi_format/parsing/`, `tests/fortran/semantic_pyi_format/semantics/`, `tests/fortran/semantic_pyi_format/pipeline/`, `tests/fortran/semantic_pyi_format/pipeline/test_modern_example.py`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py` |
| Source-first extension builds | [Building the shared library](../user/guide/building-shared-library.md) | `prik/pipeline/build.py`, `prik/pipeline/wrapper.py`, `prik/compiler/compilers.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py`, `tests/fortran/` |
| Contract-first extension builds | [.pyi contracts](../user/reference/pyi-contracts/index.md) | `prik/pipeline/build.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py` | `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/pyi_contracts/exports_and_modules/` |
| Calls, results, optional arguments, and arrays | [Functions](../user/guide/wrapping-functions.md), [subroutines](../user/guide/wrapping-subroutines.md), [arrays](../user/guide/arrays.md) | `prik/semantics/fortran2ir.py`, `prik/policy/completion.py`, `prik/planning/planner.py`, `prik/codegen/c/binding.py`, `prik/codegen/fortran/bridge.py` | `tests/fortran/functions/`, `tests/fortran/arrays/`, `tests/fortran/optional_arguments/`, `tests/fortran/pyi_contracts/calls_and_results/` |
| Modules, interfaces, constants, and exported names | [Modules](../user/guide/wrapping-modules.md), [interfaces](../user/guide/generic-interfaces.md), [enumerations](../user/guide/enumerations.md) | `prik/parsers/fortran/parser.py`, `prik/semantics/fortran2ir.py`, `prik/policy/exports.py`, `prik/naming/policy.py` | `tests/fortran/modules/`, `tests/fortran/generic_interfaces/`, `tests/fortran/enumerations/`, `tests/fortran/pyi_contracts/exports_and_modules/` |
| Derived objects, allocatables, pointers, and lifetimes | [Derived types](../user/guide/wrapping-derived-types.md), [allocatables](../user/guide/allocatables.md), [pointers](../user/guide/pointers.md), [memory management](../user/guide/memory-management.md) | `prik/policy/ownership.py`, `prik/policy/construction.py`, `prik/policy/native_array_handles.py`, `prik/planning/planner.py`, `prik/runtime/handles.py` | `tests/fortran/derived_types/`, `tests/fortran/allocatables/`, `tests/fortran/pointers/` |
| Callbacks and projected errors | [Callbacks](../user/guide/callbacks.md), [error handling](../user/guide/error-handling.md) | `prik/policy/models.py`, `prik/policy/completion.py`, `prik/planning/planner.py`, `prik/codegen/c/binding.py`, `prik/codegen/fortran/bridge.py` | `tests/fortran/callbacks/`, `tests/fortran/error_handling/`, `tests/fortran/infrastructure/semantics/` |
| Native compilation, extension runtime, and public build API | `docs/developer/packages/compiler.md`, `docs/developer/workflows/quality-assurance.md` | `prik/__init__.py`, `prik/pipeline/build.py`, `prik/compiler/objects.py`, `prik/compiler/compilers.py`, `prik/compiler/native_support.py`, `prik/runtime/native_support/` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, `tests/fortran/source_parsing/parsing/test_public_entrypoints.py` |

The listed files are the first owners for a capability, not a complete call
graph. When a change crosses a representation boundary, the
[Architecture](architecture.md) identifies the next stage and the relevant
[package guide](packages/index.md) gives its local route.
