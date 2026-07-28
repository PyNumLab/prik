---
title: Test Suite Organization Checklist
audience: maintainers
prerequisites: testing strategy, repository structure
related: ../../../developer/testing-strategy.md, ../../../../tests/README.md
status: active-roadmap
publication: draft
---

# Test Suite Organization Checklist

This checklist is the authoritative migration record for organizing pytest
modules by pipeline ownership while preserving the feature-oriented Fortran
wrapper suite. Check an item only after its collection and execution evidence
has been recorded here.

## Non-negotiable contract

- [x] Read `AGENTS.md` before auditing or editing tests.
- [x] Preserve product behavior, test meaning, fixtures, native data, generated
  contract data, parametrization, IDs, markers, skips, and coverage policy.
- [x] Keep `tests/wrapper/fortran/` organized by user-visible feature.
- [x] Keep source, generated-`.pyi`, and modified-`.pyi` scenarios for one
  wrapper feature together; reuse one behavioral assertion body when source and
  generated-contract behavior is identical.
- [x] Exclude LAPACK runtime execution from local verification.
- [x] Preserve unrelated dirty-worktree changes. Initial audit: worktree clean.
- [x] No executable product behavior changed. The only product-module edit is a
  path-only documentation-string update in `x2py/parsers/c/parser.py`.

## Baseline collection evidence

Captured before any pytest module moved on 2026-07-10.

| Measure | Baseline |
| --- | ---: |
| Total cases | 5,747 |
| Path-normalized function/class/parameter multiset SHA-256 | `82662d1da6c7cb299878bbac4a08dfcfb43ecf9c6c6fdd04d5dc96de80939c37` |
| `property` cases | 25 |
| `fuzz` cases | 2 |
| `benchmark` cases | 3 |
| `regression` cases | 0 |
| Skipped during collection | 0 |

The normalized hash removes only the pytest module path before the first
`::`. It retains class names, function names, parametrization suffixes, and
duplicates, so path-only moves leave the hash unchanged.

### Baseline counts by current directory

| Directory | Cases |
| --- | ---: |
| `tests/benchmarks/` | 3 |
| `tests/parser/c/` | 346 |
| `tests/parser/` excluding `c/` | 3,171 |
| `tests/property/` | 27 |
| `tests/pyi/` | 290 |
| `tests/semantics/` | 434 |
| root-level `tests/test_*.py` | 83 |
| `tests/tools/` | 1,154 |
| `tests/wrapper/fortran/` | 239 |
| **Total** | **5,747** |

Per-module counts are preserved by the pre-move `pytest --collect-only -q`
inventory and will be compared against the destination modules after each
coherent move. Split modules must account for the original total shown below.

| Oversized module | Lines | Baseline cases | Planned concepts |
| --- | ---: | ---: | --- |
| `tests/parser/test_cli.py` | 3,566 | 140 | argument/configuration contract, output/reporting, and stage dispatch |
| `tests/pyi/test_pyi_to_ir.py` | 3,013 | 190 | Python-AST parsing, imports/packages, classes/overloads, type/value forms, call projection |
| `tests/semantics/test_ownership_policy.py` | 2,878 | 82 | completed policy, bridge dispatch, binding dispatch |
| `tests/semantics/test_fortran2ir.py` | 2,718 | 69 | declarations/types, procedures/interfaces, modules/visibility, imports/expressions |
| `tests/parser/test_preprocessing_cli.py` | 2,596 | 74 | configuration/adapters, dependency discovery, native include expansion, CLI orchestration |
| `tests/semantics/test_pyi_printer.py` | 2,315 | 77 | declarations/types, procedures/projections, imports/packages, policy metadata |
| `tests/test_runtime_handles.py` | 2,004 | 79 | public handles, generated-operation factories, array/descriptor ABI packing |
| `tests/semantics/test_c2ir.py` | 1,827 | 63 | declarations/types, functions/callbacks, records/enums, projects/diagnostics |
| `tests/parser/test_procedure_and_type_parsing.py` | 1,639 | 83 | procedures/interfaces, declarations/types, derived types/type-bound behavior |
| `tests/parser/test_fortran_parser_regression_contracts.py` | 1,356 | 57 | lexical/source-form regressions, declarations/scopes, procedures/interfaces |

## Proposed old-to-new ownership map

This map was recorded before moves. A row naming a split is incomplete until
all original cases are accounted for in its destination modules.

| Current pytest module(s) | Destination owner |
| --- | --- |
| `tests/parser/c/test_*.py` | `tests/parsing/c/test_*.py` |
| Fortran parser tests in `tests/parser/test_*.py` other than CLI, probes, and preprocessing | `tests/parsing/fortran/`, with the two named oversized parser modules split by concept |
| `tests/parser/test_cli.py` | split under `tests/cli/` |
| `tests/parser/test_preprocessing_cli.py`, `test_preprocessor_and_execution_boundaries.py` | split/move under `tests/pipeline/preprocessing/` |
| `tests/parser/test_c_standard_type_probe.py`, `test_fortran_type_probe.py` | `tests/probes/test_c_types.py`, `tests/probes/test_fortran_types.py` |
| `tests/property/test_parser_properties.py` | split between `tests/parsing/c/` and `tests/parsing/fortran/`; retain `property`/`fuzz` markers |
| `tests/property/test_semantic_properties.py` | owning `tests/semantics/conversion/` destination; retain `property` marker |
| `tests/pyi/test_pyi_to_ir.py` | parser-only cases in `tests/parsing/pyi/`; conversion concepts in `tests/semantics/conversion/pyi/` |
| `tests/pyi/test_contract_package_generation.py`, `test_pyi_fixture_suite.py` | integration-oriented `tests/pipeline/pyi_builds/` |
| `tests/semantics/test_c2ir.py`, `test_fortran2ir.py`, `test_semantic_conversion_smoke.py` | split/move under `tests/semantics/conversion/{c,fortran}/` and `tests/semantics/conversion/` |
| `tests/semantics/test_ownership_policy.py` | completed decisions in `tests/semantics/policy/`; generator dispatch cases in `tests/codegen/bridges/` and `tests/codegen/bindings/` |
| `tests/semantics/test_ir2ast.py`, `test_visitor_protocol.py` | `tests/lowering/` |
| `tests/semantics/test_pyi_printer*.py` | `tests/wrapper_codegen/printers/`, with the oversized printer module split by emitted concept |
| `tests/test_runtime_handles.py` | split under `tests/runtime/handles/` |
| `tests/test_naming_policy.py` | `tests/naming/test_policy.py` |
| `tests/tools/test_documentation_examples.py`, `test_documentation_structure.py` | `tests/docs/` |
| `tests/tools/test_numpy_types.py`, `test_type_mapping_report.py` | `tests/types/` |
| `tests/tools/test_package_structure.py` | `tests/architecture/test_package_structure.py` |
| `tests/wrapper/fortran/layout_rules/test_codegen_structure.py` | `tests/architecture/test_dependency_boundaries.py` |
| Remaining `tests/tools/test_*.py` | remain under `tests/tools/` because they exercise repository tools |
| `tests/benchmarks/test_parser_benchmarks.py` | remains under `tests/benchmarks/` |
| Other `tests/wrapper/fortran/**/test_*.py` | remain feature-oriented in place |

Data and generated fixture trees under `tests/data/`, `tests/parser/**/fixtures/`,
`tests/pyi/fixtures/`, `tests/semantics/fixtures/`, and wrapper contract fixture
trees are not part of this map and must not move.

## Final split mapping and helper ownership

| Original oversized module | Final pytest modules |
| --- | --- |
| `tests/parser/test_cli.py` | `tests/cli/test_argument_contract.py`, `test_output_contract.py`, `test_stage_dispatch.py` |
| `tests/pyi/test_pyi_to_ir.py` | `tests/parsing/pyi/test_python_ast_contracts.py`; `tests/semantics/conversion/pyi/test_calls_and_projections.py`, `test_classes_and_overloads.py`, `test_pyi_conversion_imports_and_packages.py`, `test_types_and_values.py` |
| `tests/semantics/test_ownership_policy.py` | `tests/semantics/policy/test_accessor_and_storage_policy.py`, `test_native_array_ownership.py`, `test_policy_defaults_and_validation.py`; `tests/lowering/test_array_interop_policy.py`; `tests/codegen/bridges/test_bridge_handle_policy_dispatch.py`; `tests/codegen/bindings/test_binding_handle_policy_dispatch.py` |
| `tests/semantics/test_fortran2ir.py` | `tests/semantics/conversion/fortran/test_compile_time_values.py`, `test_fortran_conversion_procedures_and_interfaces.py`, `test_modules_and_imports.py`, `test_types_and_storage.py` |
| `tests/parser/test_preprocessing_cli.py` | `tests/pipeline/preprocessing/test_cli.py`, `test_configuration_and_adapters.py`, `test_dependencies_and_includes.py`, `test_execution.py` |
| `tests/semantics/test_pyi_printer.py` | `tests/wrapper_codegen/printers/test_calls_and_policy_metadata.py`, `test_classes_and_methods.py`, `test_pyi_printer_imports_and_packages.py`, `test_types_and_declarations.py` |
| `tests/test_runtime_handles.py` | `tests/runtime/handles/test_array_actual_abi.py`, `test_descriptor_abi.py`, `test_factories_and_lifecycle.py`, `test_handle_protocols.py` |
| `tests/semantics/test_c2ir.py` | `tests/semantics/conversion/c/test_functions_and_callbacks.py`, `test_projects_and_diagnostics.py`, `test_records_and_enums.py`, `test_types_and_constants.py` |
| `tests/parser/test_procedure_and_type_parsing.py` | `tests/parsing/fortran/test_fortran_parser_procedures_and_interfaces.py`, `test_declarations_and_shapes.py`, `test_derived_types_and_program_units.py` |
| `tests/parser/test_fortran_parser_regression_contracts.py` | `tests/parsing/fortran/test_source_form_and_diagnostics_regressions.py`, `test_declaration_and_scope_regressions.py`, `test_procedure_and_interface_regressions.py` |

Property tests were also moved into their owning stages: parser properties are
split among C parsing, Fortran parsing, and preprocessing; semantic properties
are split among C, Fortran, `.pyi`, and shared semantic conversion. Their
`property` and `fuzz` markers are unchanged.

Shared ordinary helpers now live in the nearest `_support.py`: CLI,
preprocessing, C/Fortran conversion, printer, runtime-handle, and the two
Fortran parser split families each have a local support module. Four helpers
cross an intentional ownership boundary and therefore live in `tests/_shared/`:
parser properties, `.pyi` parsing/conversion, semantic conversion/CLI, and
ownership-policy/codegen dispatch. The obsolete `tests/parser/conftest.py` was
removed after all parser pytest modules left that subtree.

The pre-existing `tests/docs/test_structure.py` remains 1,052 lines after
explicit review. It is one cohesive repository-wide documentation schema with
shared indexes and parametrized checks; splitting its constants from their
consumers would make the contract harder to audit. Every migrated module is at
or near 1,000 lines or below; the 1,004-line `.pyi` call/projection module is a
single cohesive native-call/projection subject.

## Migration groups and evidence

### Documentation and architecture contract

- [x] Create this checklist before moving pytest modules.
- [x] Create `tests/README.md` as the canonical test-suite map.
- [x] Replace the placeholder `docs/developer/testing-strategy.md` with the
  intended ownership and focused-command contract.
- [x] Synchronize developer source maps and repository-structure documentation.
- [x] Synchronize roadmap/checklist, workflow, CI, comments, and commands that
  name moved pytest paths.

### Parsing, probes, CLI, and preprocessing

- [x] Move/split the group according to the proposed map.
- [x] Record collection comparison: every original case retained.
- [x] Record focused execution results for `tests/parsing`, `tests/probes`,
  `tests/cli`, and `tests/pipeline/preprocessing`.

### Semantic conversion and `.pyi` pipeline integration

- [x] Move/split the group according to the proposed map.
- [x] Record collection comparison: every original case retained.
- [x] Record focused execution results for `tests/semantics/conversion` and
  `tests/pipeline/pyi_builds`.

### Policy, planning, lowering, and code generation

- [x] Move/split the group according to the proposed map.
- [x] Confirm every bridge/binding test asserts dispatch from completed policy
  rather than semantic inference in generation.
- [x] Record collection comparison: every original case retained.
- [x] Record focused execution results for `tests/semantics/policy`,
  `tests/semantics/policy`, `tests/lowering`, and `tests/codegen`.

### Runtime, types, naming, docs, tools, and architecture

- [x] Move/split the group according to the proposed map.
- [x] Record collection comparison: every original case retained.
- [x] Record focused execution results for each final directory.

### Wrapper preservation

- [x] Wrapper feature modules remain in their existing subject directories.
- [x] Wrapper README and checklist mappings name existing modules and test nodes.
- [x] Source/generated-contract parity helpers remain shared.
- [x] `tests/wrapper/fortran/layout_rules`: 9 passed without LAPACK execution.

## Structural enforcement

- [x] Root-level pytest modules are eliminated.
- [x] Every major source package has one documented test owner.
- [x] Stage directories contain only tests owned by that stage.
- [x] Wrapper runtime tests stay under `tests/wrapper/fortran/`.
- [x] Tools tests exercise repository tools only.
- [x] Documentation tests live under `tests/docs/`.
- [x] Architecture/layout tests live under `tests/architecture/`, except the
  wrapper feature-index/checklist integrity guard retained with wrapper layout.
- [x] Deprecated pytest directories cannot regain pytest modules.
- [x] `tests/README.md` references existing destinations.
- [x] Wrapper README/checklist references remain valid.

## Final verification evidence

- [x] `python3 -m pytest --collect-only -q`: 5,758 cases.
- [x] Every baseline case is accounted for; marker counts match. Final
  comparison has 34 intentional path-parametrization renames and 45 additions:
  the 34 replacement parameters, 9 new structural cases, and 2 documentation
  parametrizations for this checklist.
- [x] AST comparison found 1,549 of 1,550 original top-level test definitions
  byte-for-byte equivalent after parsing; the sole expected difference is the
  `Path(__file__)` parent-depth update in the moved modern-Fortran printer test.
  No assertion or decorator AST changed.
- [x] Final marker counts: property 25, fuzz 2, benchmark 3, regression 0,
  slow 0; skipped-at-collection remains 0.
- [x] All final stage directories pass focused execution.
- [x] Broader non-LAPACK wrapper suite: 262 passed, 1 existing generated-C
  incompatible-pointer warning; all real-library tests were excluded.
- [x] `python3 -m ruff check .`: passed.
- [x] `python3 -m ruff format --check .`: passed.
- [x] Bandit blocking check: passed; the command reports the three legacy
  non-package roots absent and scans `x2py`.
- [x] Vulture blocking check: passed.
- [x] Radon policy automatic base: could not resolve without CI SHA variables.
- [x] `PR_BASE_SHA=origin/main` Radon policy rerun: passed, hotspot average
  15.02 across 238 C-or-worse blocks.
- [x] Advisory Radon complexity and maintainability reports: completed; average
  complexity C (15.0168), maintainability report unchanged in product scope.
- [x] `git diff --check`: passed.

### Intentional path-parametrization renames

The two documentation navigation tests retain their function names and meaning;
only each parameter suffix changed from an old target to its replacement. Each
row therefore accounts for two of the 34 normalized-ID differences.

| Old parameter | New parameter |
| --- | --- |
| `tests/parser/test_cli.py` | `tests/cli/` |
| `tests/parser/test_fortran_fixture_suite.py` | `tests/parsing/fortran/test_fortran_fixture_suite.py` |
| `tests/parser/test_parser_public_entrypoints.py` | `tests/parsing/fortran/test_public_entrypoints.py` |
| `tests/parser/test_preprocessing_cli.py` | `tests/pipeline/preprocessing/` |
| `tests/parser/test_preprocessor_and_execution_boundaries.py` | `tests/pipeline/preprocessing/test_parser_boundaries.py` |
| `tests/pyi/test_contract_package_generation.py` | `tests/pipeline/pyi_builds/test_contract_package_generation.py` |
| `tests/pyi/test_pyi_fixture_suite.py` | `tests/pipeline/pyi_builds/test_contract_fixtures.py` |
| `tests/pyi/test_pyi_to_ir.py` | `tests/parsing/pyi/` |
| `tests/semantics/test_c2ir.py` | `tests/semantics/conversion/c/` |
| `tests/semantics/test_fortran2ir.py` | `tests/semantics/conversion/fortran/` |
| `tests/semantics/test_ir2ast.py` | `tests/lowering/test_semantic_ir.py` |
| `tests/semantics/test_pyi_printer.py` | `tests/wrapper_codegen/printers/` |
| `tests/semantics/test_pyi_printer_modern_example.py` | `tests/wrapper_codegen/printers/test_modern_example.py` |
| `tests/tools/test_documentation_examples.py` | `tests/docs/test_examples.py` |
| `tests/tools/test_documentation_structure.py` | `tests/docs/test_structure.py` |

### Focused execution record

| Owner | Result |
| --- | ---: |
| `tests/architecture` | 13 passed |
| `tests/cli` | 149 passed |
| `tests/parsing` | 3,211 passed |
| `tests/probes` | 52 passed |
| `tests/pipeline` | 200 passed |
| `tests/semantics` | 457 passed |
| `tests/lowering` | 43 passed |
| `tests/codegen` | 117 passed |
| `tests/runtime` | 79 passed |
| `tests/types` | 9 passed |
| `tests/naming` | 4 passed |
| `tests/docs` | 1,123 passed |
| `tests/tools` | 18 passed, 5 parked benchmark-policy tests skipped |
| `tests/benchmarks` | 3 parked benchmarks skipped |
| `tests/wrapper/fortran/layout_rules` | 9 passed |
| `tests/wrapper/fortran --ignore=tests/wrapper/fortran/real_libraries` | 262 passed, 1 compiler warning |

No LAPACK runtime test was executed. Source-build and manifest runtime evidence
remains under the existing wrapper feature subjects because moving those tests
to internal pipeline directories would violate the feature-oriented wrapper
rule. No pytest module was intentionally left in a deprecated pytest location;
only fixture/generator trees remain under `tests/parser/`, `tests/pyi/`, and
`tests/semantics/`.

## Completion gate

- [x] Every pytest module has one documented primary owner.
- [x] Every split accounts for all original collected cases.
- [x] No parametrized case, marker, skip, assertion, fixture, or helper behavior
  was lost.
- [x] No maintained documentation contains a stale moved pytest path.
- [x] No unrelated product failure is hidden, weakened, skipped, or rewritten.
- [x] Final tree, mapping, split rationale, helper moves, collection evidence,
  focused results, wrapper verification, static checks, retained locations, and
  any product failures are recorded here and in the handoff.

## Post-Cutover Supersession

The earlier inventory and execution record above documents the historical test
move and intentionally retains its old paths as evidence. After the canonical
wrapper-plan cutover, `tests/codegen/`, `tests/lowering/`, `x2py.codegen`, and
the adjacent legacy lowering/build entrypoints are removed. Still-required
contracts belong to completed semantic-policy tests, `tests/wrapper_codegen/`
plan and direct-generation tests, or compiled public behavior under
`tests/wrapper/fortran/`.
