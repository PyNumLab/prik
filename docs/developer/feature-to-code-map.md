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
| Fortran parse output | `docs/developer/fortran-parser-reference.md` | `x2py/parsers/fortran/parser.py`, `models.py`, `lexer.py`, `type_resolver.py` | `tests/parsing/fortran/`, `tests/parsing/fortran/test_fortran_fixture_suite.py` | Parser facts and diagnostics match fixtures |
| Semantic `.pyi` generation | `docs/user/reference/semantic-pyi-format.md` | `x2py/wrapper_codegen/printers/pyi_printer.py` | `tests/wrapper_codegen/printers/`, `tests/wrapper_codegen/printers/test_modern_example.py` | Printed `.pyi` round-trips or matches fixtures |
| Semantic `.pyi` conversion and editing | `docs/user/reference/editing-semantic-pyi-contracts.md`, `docs/user/reference/semantic-pyi-format.md`, `docs/user/examples/recipes/semantic-pyi-contracts.md` | `x2py/parsers/pyi/parser.py`, `x2py/pipeline/pyi.py`, `x2py/semantics/pyi2ir.py`, `models.py` | `tests/parsing/pyi/`, `tests/pipeline/pyi_builds/test_contract_fixtures.py` | Edited contracts parse to Python AST, then become semantic IR with preserved native facts |
| Semantic and wrapper-planning errors | `docs/user/guide/error-handling.md`, `docs/user/reference/diagnostic-codes.md` | `x2py/semantics/fortran2ir.py`, `x2py/semantics/policy_completion.py`, `x2py/wrapper_codegen/planner.py` | `tests/semantics/conversion/`, `tests/semantics/policy/`, `tests/wrapper_codegen/` | Each owning stage rejects unsupported or incomplete contracts |
| Fortran wrapper orchestration | `docs/user/reference/fortran-wrapper.md`, `docs/user/examples/recipes/build-and-import-cli.md`, `docs/user/examples/recipes/build-multiple-fortran-sources.md` | `x2py/pipeline/build.py` | `tests/wrapper/fortran/build_from_source/test_build_modes.py`, multi-source wrapper tests | Builds report artifacts and compile/link as documented |
| Completed semantic policy to wrapper artifacts | `docs/user/reference/fortran-wrapper.md` | `x2py/semantics/policy_completion.py`, `x2py/wrapper_codegen/plan.py`, `planner.py`, `generator.py` | `tests/semantics/policy/`, `tests/wrapper_codegen/`, `tests/wrapper/fortran/` | Runtime policy is explicit, the typed plan is complete, and generated artifacts compile and run |
| Native compilation and binding support | `docs/user/reference/fortran-wrapper.md`, `docs/user/examples/recipes/generate-editable-makefile.md`, `docs/developer/build-system.md`, `docs/developer/quality-assurance.md` | `x2py/compiling/`, `x2py/binding_support/` | `tests/wrapper/fortran/build_from_source/test_runtime_abi.py`, build-mode tests | Generated sources compile, link, import, and clean up correctly |
| Source documentation structure | `docs/developer/source-map.md` | `docs/`, package README files, `tests/docs/test_structure.py` | documentation structure and example tests | Pages have metadata, audience separation, and source coverage checks |

<!-- X2PY_C_DOCS_START
| CLI stage selection and output | `docs/user/tutorials/basic-wrapper.md`, `docs/user/examples/verified-cookbook.md`, `docs/user/reference/cli-commands.md` | `x2py/cli.py`, `x2py/parsers/fortran/cli.py`, `x2py/parsers/c/cli.py` | `tests/cli/`, parser CLI tests, documentation example tests | Command output and diagnostics match checked expectations |
| Compiler preprocessing | `docs/user/examples/recipes/compiler-preprocessing.md`, parser references | `x2py/pipeline/preprocessing.py`, parser CLI helpers | `tests/pipeline/preprocessing/`, `tests/pipeline/preprocessing/test_parser_boundaries.py`, C preprocessing tests | Preprocessed input and dependency facts are stable |
| C parse output | `docs/developer/c-parser-reference.md`, `docs/user/examples/recipes/inspect-c-api.md` | `x2py/parsers/c/parser.py`, `models.py`, `lexer.py`, `type_resolver.py` | `tests/parsing/c/test_c_declarations_and_declarators.py`, `tests/parsing/c/test_c_fixture_suite.py` | Parser facts and diagnostics match fixtures |
| Semantic IR | `docs/user/reference/semantic-ir.md` | `x2py/semantics/models.py`, `fortran2ir.py`, `c2ir.py` | `tests/semantics/conversion/fortran/`, `tests/semantics/conversion/c/` | Source facts lower without losing wrapper-relevant meaning |
| Generated Fortran bridge | `docs/user/reference/fortran-wrapper.md` | `x2py/wrapper_codegen/fortran/bridge.py`, `x2py/wrapper_codegen/printers/source_printers.py` | `tests/wrapper_codegen/`, `tests/wrapper/fortran/` | Generated bridge compiles and preserves native calling contract |
| Generated CPython binding | `docs/user/reference/fortran-wrapper.md` | `x2py/wrapper_codegen/c/binding.py`, `x2py/wrapper_codegen/printers/source_printers.py` | `tests/wrapper_codegen/`, `tests/wrapper/fortran/` | Extension imports, validates Python inputs, and returns documented values |
| Public API exports | `README.md`, `docs/user/reference/python-api.md` | `x2py/__init__.py` | `tests/parsing/fortran/test_public_entrypoints.py`, C public API tests | Import paths are intentional and documented |
X2PY_C_DOCS_END -->

## First-File Rule

<!-- X2PY_C_DOCS_START
For a feature change, start with the implementation file named in the feature
map and read only the downstream files that the change actually crosses. For
example, a CLI output change normally starts and ends in `x2py/cli.py`, while a
wrapper output-projection change must move through semantic policy completion,
the typed wrapper planner, and the selected bridge and binding implementation
methods.
X2PY_C_DOCS_END -->

When the user-visible behavior changes, update the public docs in the same row
before or alongside the implementation. The documentation structure test keeps
this routing page tied to the source hotspots and package README files.

## Workflow Feature Pointers

| User workflow | Start in code | Do not mark supported until |
| --- | --- | --- |
| Wrapping functions and subroutines | `x2py/semantics/fortran2ir.py`, policy completion, `x2py/wrapper_codegen/planner.py`, bridge and binding generators | Runtime tests compile, import, call, and verify return and failure behavior |
| Wrapping modules and module variables | parser module facts, semantic module conversion, naming policy, wrapper generators | Python-visible names, accessors, and unsupported module constructs are tested |
| Arrays and allocatables | semantic array contracts, ownership policy, typed wrapper plans, bridge/binding array handlers | dtype, shape, rank, contiguity, mutation, returned arrays, and failure paths are tested |
| Pointer arguments | semantic metadata, ownership policy, bridge/binding pointer handlers | Owner, lifetime, association, and blocked cases are explicit and tested |
| Optional arguments | parser optional attributes, semantic arguments, binding argument parsing | Present/absent calls and unsupported combinations are tested |
| Generic interfaces | parser interface facts, semantic overload sets, `FunctionOverloadSet`, binding dispatch | Overload selection and ambiguity failures are tested at runtime |
| Enumerations | parser enum facts, semantic constants/classes, codegen projection | Python-visible values and unsupported enum forms are tested |
| Packaging and distribution | `x2py/pipeline/build.py`, `x2py/compiling/`, future packaging integration | Build artifacts, native dependencies, and platform constraints are documented and tested |

<!-- X2PY_C_DOCS_START
| Derived types | semantic classes, ownership policy, bridge class handling, CPython class binding | Lifetime, construction, field access, finalization, and invalid calls are tested |
| Callbacks | completed callback policy, `CallbackHandoffPlan`, direct Fortran adapter lowering, direct CPython trampoline lowering | Callback ABI/copy direction is validated before emission; lifetime, same-thread re-entry, exception abort, and call-scoped cleanup are compiled and tested |
| Error handling | stage diagnostics, generated cleanup paths, CPython exception state | Failure path tests prove diagnostics or Python exceptions |
X2PY_C_DOCS_END -->

## Evidence Rule

A feature can appear in user workflow docs only after the implementation,
focused tests, and runtime evidence match the public claim. Parser or semantic
support alone is not enough for runtime wrapper support.
