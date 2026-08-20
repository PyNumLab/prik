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

Links in the documentation column are reviewed pages.

Find the capability, read its documentation, start with the leftmost owner,
and run its focused evidence. Use the [Architecture](architecture.md) when the
change crosses a stage boundary.

| Capability | Relevant documentation | Change route | Focused evidence |
| --- | --- | --- | --- |
| Fortran inspection and semantic IR | [Parsers](packages/parsers.md) | `prik/parsers/fortran/parser.py` → `prik/semantics/fortran2ir.py` → `prik/semantics/models.py` | `tests/fortran/infrastructure/parsing/`, `tests/fortran/infrastructure/semantic_ir/semantics/` |
| CLI commands and reports | [Beginner workflow](../user/getting-started/beginner-workflow.md) | `prik/cli.py` → `prik/parsers/fortran/cli.py` | `tests/fortran/infrastructure/cli/pipeline/`, `tests/docs/test_examples.py` |
| Source preparation and target types | [Preprocessing](packages/preprocessing.md) | `prik/preprocessing/source.py` → `prik/preprocessing/fortran.py` → `prik/preprocessing/probes/fortran_types.py` → `prik/semantics/scalar_types.py` → `prik/codegen/primitive_scalar_types.py` | `tests/fortran/infrastructure/preprocessing/`, `tests/fortran/data_types/` |
| Semantic `.pyi` generation and editing | [.pyi contracts](../user/reference/pyi-contracts/index.md) | `prik/parsers/pyi/parser.py` → `prik/semantics/pyi2ir.py` → `prik/pipeline/pyi.py` → `prik/printers/pyi.py` | `tests/fortran/infrastructure/semantic_pyi/parsing/`, `tests/fortran/infrastructure/semantic_pyi/semantics/`, `tests/fortran/infrastructure/semantic_pyi/pipeline/` |
| Source-first extension builds | [Building the shared library](../user/guide/building-shared-library.md) | `prik/pipeline/build.py` → `prik/pipeline/wrapper.py` → `prik/compiler/compilers.py` | `tests/fortran/infrastructure/building/end_to_end/test_source_build_modes.py`, `tests/fortran/infrastructure/building/end_to_end/test_multi_source_builds.py` |
| Contract-first extension builds | [.pyi contracts](../user/reference/pyi-contracts/index.md) | `prik/pipeline/build.py` → `prik/pipeline/pyi.py` → `prik/semantics/pyi2ir.py` | `tests/fortran/infrastructure/semantic_pyi/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/infrastructure/semantic_pyi/contracts/exports_and_modules/` |
| Calls, results, and optional arguments | [Functions](../user/guide/wrapping-functions.md), [subroutines](../user/guide/wrapping-subroutines.md) | `prik/semantics/fortran2ir.py` → `prik/policy/completion.py` → `prik/planning/planner.py` → `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py` | `tests/fortran/functions/`, `tests/fortran/optional_arguments/`, `tests/fortran/infrastructure/semantic_pyi/contracts/calls_and_results/` |
| Arrays | [Arrays](../user/guide/arrays.md) | `prik/semantics/fortran2ir.py` → `prik/policy/completion.py` → `prik/planning/planner.py` → `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py` | `tests/fortran/arrays/` |
| Modules, interfaces, constants, and exported names | [Modules](../user/guide/wrapping-modules.md), [interfaces](../user/guide/generic-interfaces.md), [enumerations](../user/guide/enumerations.md) | `prik/parsers/fortran/parser.py` → `prik/semantics/fortran2ir.py` → `prik/policy/exports.py` → `prik/naming/policy.py` | `tests/fortran/modules/`, `tests/fortran/generic_interfaces/`, `tests/fortran/infrastructure/semantic_pyi/contracts/exports_and_modules/` |
| Derived objects, allocatables, pointers, and lifetimes | [Derived types](../user/guide/wrapping-derived-types.md), [allocatables](../user/guide/allocatables.md), [pointers](../user/guide/pointers.md), [memory management](../user/guide/memory-management.md) | `prik/policy/ownership.py` → `prik/policy/construction.py` → `prik/policy/native_array_handles.py` → `prik/planning/planner.py` → `prik/runtime/handles.py` | `tests/fortran/derived_types/`, `tests/fortran/allocatables/`, `tests/fortran/pointers/` |
| Callbacks | [Callbacks](../user/guide/callbacks.md) | `prik/policy/models.py` → `prik/policy/completion.py` → `prik/planning/planner.py` → `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py` | `tests/fortran/callbacks/` |
| Projected errors | [Error handling](../user/guide/error-handling.md) | `prik/policy/models.py` → `prik/policy/completion.py` → `prik/planning/planner.py` → `prik/codegen/c/binding.py` and `prik/codegen/fortran/bridge.py` | `tests/fortran/error_handling/` |
| Native compilation, extension runtime, and public build API | [Compiler](packages/compiler.md), [Quality Assurance](workflows/quality-assurance.md) | `prik/__init__.py` → `prik/pipeline/build.py` → `prik/compiler/objects.py` → `prik/compiler/compilers.py` → `prik/compiler/native_support.py` → `prik/runtime/native_support/` | `tests/fortran/infrastructure/building/end_to_end/test_runtime_compatibility.py`, `tests/fortran/infrastructure/parsing/test_public_entrypoints.py` |

Each change route begins with the first owner for a capability; it is not a
complete call graph. When a change crosses a representation boundary, the
[Architecture](architecture.md) identifies the next stage and the relevant
[architecture component guide](packages/index.md) gives its local route.
