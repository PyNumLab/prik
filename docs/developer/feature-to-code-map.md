---
title: Feature To Code Map
audience: developers, contributors
prerequisites: source map, testing strategy
related: source-map.md, ../user/language-support/feature-matrix.md
status: maintained
publication: draft
---

# Feature To Code Map

Use this page when starting from a user-visible feature. The table points to
the public docs, implementation files, focused tests, and evidence required
before documentation may call the behavior supported.

## Feature Map

| Feature or behavior | Public docs | Main implementation files | Focused tests | Support evidence |
| --- | --- | --- | --- | --- |
| Fortran parse output | `docs/developer/fortran-parser-reference.md` | `prik/parsers/fortran/parser.py`, `models.py`, `lexer.py`, `type_resolver.py` | `tests/fortran/source_parsing/parsing/`, `tests/fortran/source_parsing/parsing/test_fortran_fixture_suite.py` | Parser facts and diagnostics match fixtures |
| Semantic `.pyi` generation | `docs/user/reference/semantic-pyi-format.md` | `prik/printers/pyi.py` | `tests/fortran/semantic_pyi_format/pipeline/`, `tests/fortran/semantic_pyi_format/pipeline/test_modern_example.py` | Printed `.pyi` round-trips or matches fixtures |
| Semantic `.pyi` conversion and editing | `docs/user/reference/pyi-contracts/index.md`, `docs/user/reference/semantic-pyi-format.md`, `docs/user/examples/recipes/semantic-pyi-contracts.md` | `prik/parsers/pyi/parser.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py`, `models.py` | `tests/fortran/semantic_pyi_format/` | Edited contracts parse to Python AST, then become semantic IR with preserved native facts |
| Semantic and wrapper-planning errors | `docs/user/guide/error-handling.md`, `docs/user/reference/diagnostic-codes.md` | `prik/semantics/fortran2ir.py`, `prik/policy/completion.py`, `prik/planning/planner.py` | `tests/fortran/infrastructure/semantics/`, feature-local `policy/`, and feature-local `codegen/` tests | Each owning stage rejects unsupported or incomplete contracts |
| Fortran wrapper orchestration | `docs/user/reference/fortran-wrapper.md`, `docs/user/guide/building-shared-library.md` | `prik/pipeline/build.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, multi-source wrapper tests | Builds report artifacts and compile/link as documented |
| Completed semantic policy to generated wrapper | `docs/user/reference/fortran-wrapper.md` | `prik/policy/completion.py`, `prik/planning/models.py`, `prik/planning/planner.py`, `prik/codegen/docstrings.py`, `prik/pipeline/wrapper.py` | `tests/fortran/infrastructure/semantics/`, `tests/fortran/infrastructure/codegen/`, and feature-local policy/codegen tests | Runtime policy is explicit, the typed plan is complete, and the generated wrapper compiles and runs |
| Native compilation and binding support | `docs/user/reference/fortran-wrapper.md`, `docs/user/guide/building-shared-library.md`, `docs/developer/build-system.md`, `docs/developer/quality-assurance.md` | `prik/compiler/`, `prik/binding_support/` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, build-mode tests | Generated sources compile, link, import, and clean up correctly |
| Source documentation structure | `docs/developer/source-map.md` | `docs/`, package README files, `tests/docs/test_reference_and_source_map.py` | documentation metadata, navigation, source-map, and example tests | Pages have metadata, audience separation, and source coverage checks |

<!-- PRIK_C_DOCS_START
| CLI stage selection and output | `docs/user/getting-started/beginner-workflow.md`, `docs/user/reference/cli-commands.md` | `prik/cli.py`, `prik/parsers/fortran/cli.py`, `prik/parsers/c/cli.py` | `tests/fortran/command_line_interface/pipeline/`, parser CLI tests, documentation example tests | Command output and diagnostics match checked expectations |
| Compiler preprocessing | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/compiler-preprocessing.md`, parser references | `prik/preprocessing/source.py`, parser CLI helpers | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py`, C preprocessing tests | Preprocessed input and dependency facts are stable |
| C parse output | `docs/developer/c-parser-reference.md`, `docs/user/examples/recipes/inspect-c-api.md` | `prik/parsers/c/parser.py`, `models.py`, `lexer.py`, `type_resolver.py` | `tests/c/parsing/test_c_declarations_and_declarators.py`, `tests/c/parsing/test_c_fixture_suite.py` | Parser facts and diagnostics match fixtures |
| Semantic IR | `docs/user/reference/semantic-ir.md` | `prik/semantics/models.py`, `fortran2ir.py`, `c2ir.py` | `tests/fortran/semantic_ir/semantics/`, `tests/c/semantics/conversion/` | Source facts lower without losing wrapper-relevant meaning |
| Generated Fortran bridge | `docs/user/reference/fortran-wrapper.md` | `prik/codegen/fortran/bridge.py`, `prik/printers/fortran.py`, `prik/pipeline/wrapper.py` | `tests/fortran/infrastructure/codegen/`, `tests/fortran/` | Generated bridge compiles and preserves native calling contract |
| Generated CPython binding | `docs/user/reference/fortran-wrapper.md` | `prik/codegen/c/binding.py`, `prik/codegen/c/python_surface.py`, `prik/printers/c.py`, `prik/pipeline/wrapper.py` | `tests/fortran/infrastructure/codegen/`, `tests/fortran/` | Extension imports, validates Python inputs, dispatches overloads in C, and installs the derived-class Python facade |
| Public API exports | `README.md`, `docs/user/reference/python-api.md` | `prik/__init__.py` | `tests/fortran/source_parsing/parsing/test_public_entrypoints.py`, C public API tests | Import paths are intentional and documented |
PRIK_C_DOCS_END -->

## First-File Rule

<!-- PRIK_C_DOCS_START
For a feature change, start with the implementation file named in the feature
map and read only the downstream files that the change actually crosses. For
example, a CLI output change normally starts and ends in `prik/cli.py`, while a
wrapper output-projection change must move through semantic policy completion,
the typed wrapper planner, and the selected bridge and binding implementation
methods.
PRIK_C_DOCS_END -->

When the user-visible behavior changes, update the public docs in the same row
before or alongside the implementation. The documentation structure test keeps
this routing page tied to the source hotspots and package README files.

## Workflow Feature Pointers

| User workflow | Start in code | Do not mark supported until |
| --- | --- | --- |
| Wrapping functions and subroutines | `prik/semantics/fortran2ir.py`, policy completion, `prik/planning/planner.py`, bridge and binding generators | Runtime tests compile, import, call, and verify return and failure behavior |
| Wrapping modules and module variables | parser module facts, semantic module conversion, naming policy, wrapper generators | Python-visible names, accessors, and unsupported module constructs are tested |
| Arrays and allocatables | semantic array contracts, ownership policy, typed wrapper plans, bridge/binding array handlers | dtype, shape, rank, contiguity, mutation, returned arrays, and failure paths are tested; ordinary NumPy array actuals validate and extract their buffer directly in the C binding, descriptor handles use the planned runtime-handle path, and strided contracts carry a dense-actual role for zero-copy fast-path selection |
| Pointer arguments | semantic metadata, ownership policy, bridge/binding pointer handlers | Owner, lifetime, association, and blocked cases are explicit and tested |
| Optional arguments | parser optional attributes, semantic arguments, binding argument parsing | Present/absent calls and unsupported combinations are tested |
| Generic interfaces | parser interface facts, semantic overload sets, `FunctionOverloadSet`, binding dispatch | Overload selection and ambiguity failures are tested at runtime |
| Enumerations | parser enum facts, semantic constants/classes, codegen projection | Python-visible values and unsupported enum forms are tested |
| Packaging and distribution | `prik/pipeline/build.py`, `prik/compiler/`, future packaging integration | Build artifacts, native dependencies, and platform constraints are documented and tested |

<!-- PRIK_C_DOCS_START
| Derived types | semantic classes, ownership policy, bridge class handling, CPython class binding | Lifetime, construction, field access, finalization, and invalid calls are tested |
| Callbacks | completed callback policy, `CallbackHandoffPlan`, direct Fortran adapter lowering, direct CPython trampoline lowering | Callback ABI/copy direction is validated before emission; lifetime, same-thread re-entry, exception abort, and call-scoped cleanup are compiled and tested |
| Error handling | stage diagnostics, generated cleanup paths, CPython exception state | Failure path tests prove diagnostics or Python exceptions |
PRIK_C_DOCS_END -->

## Evidence Rule

A feature can appear in user workflow docs only after the implementation,
focused tests, and runtime evidence match the public claim. Parser or semantic
support alone is not enough for runtime wrapper support.
