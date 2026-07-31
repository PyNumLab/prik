---
title: Source Map
audience: developers, contributors
prerequisites: repository checkout, developer guide
related: feature-to-code-map.md, testing-strategy.md
status: maintained
publication: draft
---

# Source Map

Use this page when you need to find the owning source files before changing a
feature. It is populated from the current maintained developer guide and the
current Python package layout.

## Top-Level Entry Points

| Start here | Owns | Continue to |
| --- | --- | --- |
| `x2py/cli.py` | User CLI, stage selection, output routing, diagnostics, wrapper-build option validation | parser frontends, semantic conversion, wrapper planning, `x2py/pipeline/build.py` |
| `x2py/pipeline/build.py` | End-to-end Fortran source and semantic `.pyi` extension builds | preprocessing, parser, probes, completed semantic policy, wrapper planning and generation, compilation |
| `x2py/__init__.py` | Public Python exports | parser public-entrypoint tests and user examples |
| `x2py/semantics/ownership.py` | Central ownership, transfer, destruction, and generated-action policy | policy completion and typed wrapper planning |
| `x2py/probes/fortran_types.py` | Fortran kind/storage facts and cache | semantic Fortran conversion and wrapper builds |
| `x2py/probes/report.py` | Generated target datatype mapping examples | documentation example tests |

<!-- X2PY_C_DOCS_START
| `x2py/pipeline/preprocessing.py` | Compiler-backed source preprocessing and dependency facts | C and Fortran parser input loading |
| `x2py/probes/c_types.py` | C ABI type facts and cache | semantic C conversion and type mapping docs |
X2PY_C_DOCS_END -->

## Common Change Routes

Use this table when you know the behavior you need to change but not the
owning layer. Open the first file, then follow the downstream files only as the
change crosses ownership boundaries.

| Change area | Open first | Public docs to update | Focused evidence |
| --- | --- | --- | --- |
| CLI flags, stage selection, output formatting, diagnostics | `x2py/cli.py` | `docs/user/reference/cli-commands.md`, `docs/user/getting-started/beginner-workflow.md` | `tests/fortran/command_line_interface/pipeline/`, `tests/shared/docs/test_examples.py` |
| Compiler preprocessing, include paths, macros, and target flags | `x2py/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
| Fortran parser facts and diagnostics | `x2py/parsers/fortran/parser.py` | `docs/developer/fortran-parser-reference.md`, `docs/user/examples/recipes/inspect-fortran-api.md` | `tests/fortran/source_parsing/parsing/` |
| Semantic `.pyi` parsing, conversion, printing, package generation, and round-trip behavior | `x2py/parsers/pyi/parser.py`, `x2py/pipeline/pyi.py`, `x2py/semantics/pyi2ir.py`, `x2py/wrapper_codegen/printers/pyi_printer.py` | `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/pyi-contracts/index.md`, `docs/user/examples/recipes/semantic-pyi-contracts.md` | `tests/fortran/semantic_pyi_format/`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/semantic_pyi_format/pipeline/` |
| Wrapper-planning errors and support claims | `x2py/semantics/policy_completion.py`, `x2py/wrapper_codegen/planner.py` | `docs/user/reference/diagnostic-codes.md`, `docs/user/language-support/feature-matrix.md` | `tests/fortran/infrastructure/policy/`, feature-local `policy/`, and `tests/fortran/infrastructure/wrapper_codegen/` |
| Source-driven Fortran wrapper orchestration | `x2py/pipeline/build.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/guide/building-shared-library.md` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py` |
| Semantic `.pyi` wrapper orchestration from native artifacts | `x2py/pipeline/build.py`, `x2py/pipeline/pyi.py`, `x2py/semantics/pyi2ir.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/building_shared_library/pipeline/test_pyi_build_modes.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/pyi_contracts/exports_and_modules/`, `tests/fortran/pyi_contracts/functions_and_classes/` |
| Ownership, lifetime, output projection, and unsupported wrapper policy | `x2py/semantics/policy_completion.py`, `x2py/semantics/ownership.py`, `x2py/wrapper_codegen/planner.py` | `docs/user/guide/memory-management.md`, `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/policy/`, feature-local `policy/`, and `tests/fortran/infrastructure/wrapper_codegen/` |
| Immediate callback policy, typed adapters, and trampolines | `x2py/semantics/wrapper_policy.py`, `x2py/semantics/policy_completion.py`, `x2py/wrapper_codegen/plan.py`, `x2py/wrapper_codegen/planner.py`, `x2py/wrapper_codegen/c/binding.py`, `x2py/wrapper_codegen/fortran/bridge.py` | `docs/user/guide/callbacks.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/callbacks/` |
| Native compilation, binding support, and shared-library linking | `x2py/pipeline/build.py`, `x2py/compiling/compilers.py`, `x2py/compiling/native_support.py` | `docs/user/reference/fortran-wrapper.md`, `docs/developer/build-system.md` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py` |
| Public Python exports | `x2py/__init__.py` | `README.md`, `docs/user/reference/python-api.md` | `tests/fortran/source_parsing/parsing/test_public_entrypoints.py` |
| Source navigation documentation | `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`, package README files | `docs/developer/source-map.md` | `tests/shared/docs/test_structure.py` |

<!-- X2PY_C_DOCS_START
| Compiler preprocessing, include paths, macros, target flags | `x2py/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/c-parser-reference.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
| C parser facts and diagnostics | `x2py/parsers/c/parser.py` | `docs/developer/c-parser-reference.md`, `docs/user/examples/recipes/inspect-c-api.md` | `tests/c/fixtures/parser/`, `tests/c/semantics/conversion/` |
| Semantic IR shape and cross-stage metadata | `x2py/semantics/models.py`, `x2py/semantics/metadata.py`, `x2py/semantics/fortran2ir.py`, `x2py/semantics/c2ir.py` | `docs/user/reference/semantic-ir.md` | `tests/fortran/semantic_ir/semantics/`, `tests/c/semantics/conversion/` |
| Generated Fortran bridge | `x2py/wrapper_codegen/fortran/bridge.py`, `x2py/wrapper_codegen/printers/source_printers.py` | `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/wrapper_codegen/`, `tests/fortran/` generated artifact assertions |
| Generated CPython binding and Python-visible runtime behavior | `x2py/wrapper_codegen/c/binding.py`, `x2py/wrapper_codegen/printers/source_printers.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/python-api.md` | `tests/fortran/infrastructure/wrapper_codegen/`, `tests/fortran/` |
X2PY_C_DOCS_END -->

## Package Map

| Package | Purpose | Main files | Primary tests and docs |
| --- | --- | --- | --- |
| `x2py/contracts/` | Public semantic `.pyi` contract vocabulary | `__init__.py` | `tests/fortran/semantic_pyi_format/`, semantic `.pyi` reference |
| `x2py/pipeline/` | Source preprocessing, semantic `.pyi` loading, and wrapper build orchestration | `preprocessing.py`, `pyi.py`, `build.py` | preprocessing, `.pyi`, and wrapper build tests |
| `x2py/probes/` | Compiler-derived target facts plus mapping reports | `fortran_types.py`, `report.py` | target probe and type mapping report tests |
| `x2py/runtime/` | Python runtime objects consumed by generated extensions | `handles.py` | runtime handle and wrapper runtime tests |
| `x2py/types/` | Semantic-to-Python ecosystem type mappings | `numpy.py` | `tests/shared/types/test_numpy.py` |
| `x2py/parsers/` | Public namespace for language and semantic `.pyi` frontends | child parser packages | `tests/fortran/source_parsing/parsing/`, `tests/c/parsing/`, `tests/fortran/semantic_pyi_format/parsing/` |
| `x2py/parsers/fortran/` | Fortran lexer, recursive parser, models, type resolver, and parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `type_resolver.py`, `cli.py` | `tests/fortran/source_parsing/parsing/`, `docs/developer/fortran-parser-reference.md` |
| `x2py/compiling/` | Native compile objects, compiler command execution, shared-library linking, and native support installation; wrapper build orchestration lives in `x2py/pipeline/build.py` | `objects.py`, `compilers.py`, `compiler_profiles.py`, `native_support.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py` |
| `x2py/binding_support/` | Bundled header-only native binding support copied into generated wrapper builds | support header | wrapper build tests |
| `x2py/utilities/` | Small shared Python utilities | `strings.py`, `visitor.py` | tests that exercise callers |

<!-- X2PY_C_DOCS_START
| `x2py/probes/c_types.py` | Compiler-derived target ABI facts for C inspection workflows | `c_types.py` | C target probe tests |
| `x2py/parsers/c/` | C lexer, parser, models, preprocessing metadata, and C parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `preprocessor.py`, `type_resolver.py`, `cli.py` | `tests/c/fixtures/parser/`, `docs/developer/c-parser-reference.md` |
| `x2py/parsers/pyi/` | Semantic `.pyi` text/file parsing to Python AST. | `parser.py` | `tests/fortran/semantic_pyi_format/parsing/`, `docs/user/reference/semantic-pyi-format.md` |
| `x2py/semantics/` | Language-neutral semantic IR, source-to-IR conversion, `.pyi` AST conversion, and policy completion | `models.py`, `fortran2ir.py`, `c2ir.py`, `pyi2ir.py`, `policy_completion.py` | `tests/fortran/semantic_ir/semantics/`, `tests/fortran/semantic_pyi_format/semantics/`, `docs/user/reference/semantic-ir.md`, `docs/user/reference/semantic-pyi-format.md` |
| `x2py/wrapper_codegen/` | Canonical wrapper planning, C/Fortran generation, source printing, and semantic `.pyi` printing | `plan.py`, `planner.py`, `generator.py`, `printers/` | `tests/fortran/infrastructure/wrapper_codegen/`, feature-local `wrapper_codegen/` and `end_to_end/` tests, `docs/user/reference/fortran-wrapper.md` |
| `x2py/naming/` | Unified public-name and generated-symbol policy for Python, C, and Fortran targets | `policy.py` | naming, visibility, and wrapper runtime tests |
X2PY_C_DOCS_END -->

## Hotspot Index

These files are the maintained source-navigation anchors. If ownership moves,
update this table, the package README files, and the mechanical checks in
`tests/shared/docs/test_structure.py` in the same change.

| Hotspot | Owns |
| --- | --- |
| `x2py/__init__.py` | Public Python API exports. |
| `x2py/cli.py` | CLI argument validation, stage selection, output routing, and wrapper-build entry. |
| `x2py/pipeline/build.py` | End-to-end source and `.pyi` wrapper build orchestration. |
| `x2py/pipeline/preprocessing.py` | Compiler-backed source preprocessing and dependency facts. |
| `x2py/probes/fortran_types.py` | Fortran kind and storage probing. |
| `x2py/semantics/ownership.py` | Central ownership, transfer, destruction, and generated-action policy. |
| `x2py/parsers/fortran/parser.py` | Fortran parser project model and diagnostics. |
| `x2py/parsers/fortran/cli.py` | Fortran parser report formatting. |
| `x2py/semantics/metadata.py` | Cross-stage semantic metadata keys that survive parser, policy, printer, and lowering boundaries. |
| `x2py/semantics/models.py` | Semantic IR dataclasses and core model metadata. |
| `x2py/semantics/fortran2ir.py` | Fortran parser facts to semantic modules. |
| `x2py/parsers/pyi/parser.py` | Minimal `.pyi` text/file parsing to Python AST. |
| `x2py/pipeline/pyi.py` | Semantic `.pyi` text/file/path-set conversion and external-type reconciliation. |
| `x2py/semantics/pyi2ir.py` | Semantic `.pyi` AST conversion and validation. |
| `x2py/semantics/policy_completion.py` | Post-IR semantic policy completion before wrapper planning. |
| `x2py/wrapper_codegen/plan.py` | Typed, policy-complete wrapper plan records. |
| `x2py/wrapper_codegen/planner.py` | Semantic policy to wrapper-plan conversion. |
| `x2py/wrapper_codegen/generator.py` | Ordered direct bridge, binding, header, and source generation. |
| `x2py/wrapper_codegen/fortran/bridge.py` | Direct Fortran bridge lowering from typed plans. |
| `x2py/wrapper_codegen/c/binding.py` | Direct Python-extension binding lowering from typed plans. |
| `x2py/wrapper_codegen/printers/source_printers.py` | Native binding, header, and Fortran source printing. |
| `x2py/wrapper_codegen/printers/pyi_printer.py` | Semantic `.pyi` printing. |
| `x2py/compiling/objects.py` | Native compile object model. |
| `x2py/compiling/compilers.py` | Compiler command execution and tool lookup. |
| `x2py/compiling/native_support.py` | Native binding support installation for generated wrappers. |
| `x2py/naming/policy.py` | Public wrapper names and generated target-language symbols. |
| `x2py/binding_support/` | Native binding support payload copied into generated builds. |

<!-- X2PY_C_DOCS_START
| `x2py/probes/c_types.py` | C target ABI type probing. |
| `x2py/parsers/c/parser.py` | C parser project model and diagnostics. |
| `x2py/parsers/c/cli.py` | C parser report formatting and preprocessing integration. |
| `x2py/semantics/c2ir.py` | C parser facts to semantic modules. |
X2PY_C_DOCS_END -->

## Layer-To-Layer Route

For source-driven Fortran wrappers, read in this order:

<!-- X2PY_C_DOCS_START
```text
x2py/cli.py
  -> x2py/pipeline/build.py
  -> x2py/pipeline/preprocessing.py
  -> x2py/parsers/fortran/parser.py
  -> x2py/probes/fortran_types.py
  -> x2py/semantics/fortran2ir.py
  -> x2py/semantics/policy_completion.py
  -> x2py/wrapper_codegen/planner.py
  -> x2py/wrapper_codegen/generator.py
  -> x2py/wrapper_codegen/fortran/bridge.py
  -> x2py/wrapper_codegen/c/binding.py
  -> x2py/compiling/compilers.py
  -> tests/fortran/
```
X2PY_C_DOCS_END -->

For semantic `.pyi` builds, the parser branch is replaced by:

```text
x2py/parsers/pyi/parser.py
  -> x2py/pipeline/pyi.py
  -> x2py/semantics/pyi2ir.py
  -> x2py/semantics/policy_completion.py
  -> x2py/wrapper_codegen/planner.py
  -> x2py/wrapper_codegen/generator.py
```

<!-- X2PY_C_DOCS_START
For inspection-only C workflows, the path currently stops at semantic IR,
`.pyi`:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
```text
x2py/cli.py
  -> x2py/parsers/c/parser.py
  -> x2py/probes/c_types.py
  -> x2py/semantics/c2ir.py
  -> x2py/wrapper_codegen/printers/pyi_printer.py
  -> x2py/semantics/policy_completion.py
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Runtime wrapping of user-supplied C inputs is not implemented yet.
X2PY_C_DOCS_END -->

## Package-Level Notes

The hardest source packages also have local README files:

- `x2py/README.md`
- `x2py/parsers/README.md`
- `x2py/parsers/fortran/README.md`
- `x2py/parsers/pyi/README.md`
- `x2py/semantics/README.md`
- `x2py/compiling/README.md`

<!-- X2PY_C_DOCS_START
- `x2py/parsers/c/README.md`
X2PY_C_DOCS_END -->

Keep these files short. They should tell developers where to enter the code,
what the package owns, what it must not own, and where the tests and public docs
live.
