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
| `prik/cli.py` | User CLI, stage selection, output routing, diagnostics, wrapper-build option validation | parser frontends, semantic conversion, wrapper planning, `prik/pipeline/build.py` |
| `prik/pipeline/build.py` | End-to-end Fortran source and semantic `.pyi` extension builds | preprocessing, parser, probes, completed semantic policy, wrapper planning and generation, compilation |
| `prik/__init__.py` | Public Python exports | parser public-entrypoint tests and user examples |
| `prik/semantics/ownership.py` | Central ownership, transfer, destruction, and generated-action policy | policy completion and typed wrapper planning |
| `prik/probes/fortran_types.py` | Fortran kind/storage facts and cache | semantic Fortran conversion and wrapper builds |
| `prik/probes/report.py` | Generated target datatype mapping examples | documentation example tests |
| `examples/blas/` | Complete Reference BLAS correctness example, source inventory, build fixtures, and the authoritative native source set | dedicated BLAS/LAPACK workflow and full-library integration |
| `examples/lapack/` | Complete Reference LAPACK source set and SciPy-exposed float64 correctness inventory | dedicated BLAS/LAPACK workflow and full-library integration |

<!-- PRIK_C_DOCS_START
| `prik/pipeline/preprocessing.py` | Compiler-backed source preprocessing and dependency facts | C and Fortran parser input loading |
| `prik/probes/c_types.py` | C ABI type facts and cache | semantic C conversion and type mapping docs |
PRIK_C_DOCS_END -->

## Common Change Routes

Use this table when you know the behavior you need to change but not the
owning layer. Open the first file, then follow the downstream files only as the
change crosses ownership boundaries.

| Change area | Open first | Public docs to update | Focused evidence |
| --- | --- | --- | --- |
| CLI flags, stage selection, output formatting, diagnostics | `prik/cli.py` | `docs/user/reference/cli-commands.md`, `docs/user/getting-started/beginner-workflow.md` | `tests/fortran/command_line_interface/pipeline/`, `tests/shared/docs/test_examples.py` |
| Compiler preprocessing, include paths, macros, and target flags | `prik/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
| Fortran parser facts and diagnostics | `prik/parsers/fortran/parser.py` | `docs/developer/fortran-parser-reference.md`, `docs/user/examples/recipes/inspect-fortran-api.md` | `tests/fortran/source_parsing/parsing/` |
| Semantic `.pyi` parsing, conversion, printing, package generation, and round-trip behavior | `prik/parsers/pyi/parser.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py`, `prik/wrapper_codegen/printers/pyi_printer.py` | `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/pyi-contracts/index.md`, `docs/user/examples/recipes/semantic-pyi-contracts.md` | `tests/fortran/semantic_pyi_format/`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/semantic_pyi_format/pipeline/` |
| Wrapper-planning errors and support claims | `prik/semantics/policy_completion.py`, `prik/wrapper_codegen/planner.py` | `docs/user/reference/diagnostic-codes.md`, `docs/user/language-support/feature-matrix.md` | `tests/fortran/infrastructure/policy/`, feature-local `policy/`, and `tests/fortran/infrastructure/wrapper_codegen/` |
| Source-driven Fortran wrapper orchestration | `prik/pipeline/build.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/guide/building-shared-library.md` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py` |
| Semantic `.pyi` wrapper orchestration from native artifacts | `prik/pipeline/build.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/building_shared_library/pipeline/test_pyi_build_modes.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/pyi_contracts/exports_and_modules/`, `tests/fortran/pyi_contracts/functions_and_classes/` |
| Ownership, lifetime, output projection, and unsupported wrapper policy | `prik/semantics/policy_completion.py`, `prik/semantics/ownership.py`, `prik/wrapper_codegen/planner.py` | `docs/user/guide/memory-management.md`, `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/policy/`, feature-local `policy/`, and `tests/fortran/infrastructure/wrapper_codegen/` |
| Immediate callback policy, typed adapters, and trampolines | `prik/semantics/wrapper_policy.py`, `prik/semantics/policy_completion.py`, `prik/wrapper_codegen/plan.py`, `prik/wrapper_codegen/planner.py`, `prik/wrapper_codegen/c/binding.py`, `prik/wrapper_codegen/fortran/bridge.py` | `docs/user/guide/callbacks.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/callbacks/` |
| Native compilation, binding support, and shared-library linking | `prik/pipeline/build.py`, `prik/compiling/compilers.py`, `prik/compiling/native_support.py` | `docs/user/reference/fortran-wrapper.md`, `docs/developer/build-system.md` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py` |
| Public Python exports | `prik/__init__.py` | `README.md`, `docs/user/reference/python-api.md` | `tests/fortran/source_parsing/parsing/test_public_entrypoints.py` |
| Reference BLAS source ownership, inventory, and numerical validation | `examples/blas/routine_inventory.py`, `examples/blas/test_routine_coverage.py` | `examples/blas/README.md`, `docs/user/examples/blas-wrapper.md` | `examples/blas/test_*.py`, dedicated BLAS/LAPACK workflow |
| Reference LAPACK source ownership, inventory, and numerical validation | `examples/lapack/routine_inventory.py`, `examples/lapack/test_routine_coverage.py` | `examples/lapack/README.md`, `docs/user/examples/lapack-wrapper.md` | `examples/lapack/test_*.py`, dedicated BLAS/LAPACK workflow |
| Source navigation documentation | `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`, package README files | `docs/developer/source-map.md` | `tests/shared/docs/test_structure.py` |

<!-- PRIK_C_DOCS_START
| Compiler preprocessing, include paths, macros, target flags | `prik/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/c-parser-reference.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| C parser facts and diagnostics | `prik/parsers/c/parser.py` | `docs/developer/c-parser-reference.md`, `docs/user/examples/recipes/inspect-c-api.md` | `tests/c/fixtures/parser/`, `tests/c/semantics/conversion/` |
| Semantic IR shape and cross-stage metadata | `prik/semantics/models.py`, `prik/semantics/metadata.py`, `prik/semantics/fortran2ir.py`, `prik/semantics/c2ir.py` | `docs/user/reference/semantic-ir.md` | `tests/fortran/semantic_ir/semantics/`, `tests/c/semantics/conversion/` |
| Generated Fortran bridge | `prik/wrapper_codegen/fortran/bridge.py`, `prik/wrapper_codegen/printers/source_printers.py` | `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/wrapper_codegen/`, `tests/fortran/` generated artifact assertions |
| Generated CPython binding and Python-visible runtime behavior | `prik/wrapper_codegen/c/binding.py`, `prik/wrapper_codegen/printers/source_printers.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/python-api.md` | `tests/fortran/infrastructure/wrapper_codegen/`, `tests/fortran/` |
PRIK_C_DOCS_END -->

## Package Map

| Package | Purpose | Main files | Primary tests and docs |
| --- | --- | --- | --- |
| `prik/contracts/` | Public semantic `.pyi` contract vocabulary | `__init__.py` | `tests/fortran/semantic_pyi_format/`, semantic `.pyi` reference |
| `prik/pipeline/` | Source preprocessing, semantic `.pyi` loading, and wrapper build orchestration | `preprocessing.py`, `pyi.py`, `build.py` | preprocessing, `.pyi`, and wrapper build tests |
| `prik/probes/` | Compiler-derived target facts plus mapping reports | `fortran_types.py`, `report.py` | target probe and type mapping report tests |
| `prik/runtime/` | Python runtime objects consumed by generated extensions | `handles.py` | runtime handle and wrapper runtime tests |
| `prik/types/` | Semantic-to-Python ecosystem type mappings | `numpy.py` | `tests/shared/types/test_numpy.py` |
| `prik/parsers/` | Public namespace for language and semantic `.pyi` frontends | child parser packages | `tests/fortran/source_parsing/parsing/`, `tests/c/parsing/`, `tests/fortran/semantic_pyi_format/parsing/` |
| `prik/parsers/fortran/` | Fortran lexer, recursive parser, models, type resolver, and parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `type_resolver.py`, `cli.py` | `tests/fortran/source_parsing/parsing/`, `docs/developer/fortran-parser-reference.md` |
| `prik/compiling/` | Native compile objects, compiler command execution, shared-library linking, and native support installation; wrapper build orchestration lives in `prik/pipeline/build.py` | `objects.py`, `compilers.py`, `compiler_profiles.py`, `native_support.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py` |
| `prik/binding_support/` | Bundled header-only native binding support copied into generated wrapper builds | support header | wrapper build tests |
| `prik/utilities/` | Small shared Python utilities | `strings.py`, `visitor.py` | tests that exercise callers |

<!-- PRIK_C_DOCS_START
| `prik/probes/c_types.py` | Compiler-derived target ABI facts for C inspection workflows | `c_types.py` | C target probe tests |
| `prik/parsers/c/` | C lexer, parser, models, preprocessing metadata, and C parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `preprocessor.py`, `type_resolver.py`, `cli.py` | `tests/c/fixtures/parser/`, `docs/developer/c-parser-reference.md` |
| `prik/parsers/pyi/` | Semantic `.pyi` text/file parsing to Python AST. | `parser.py` | `tests/fortran/semantic_pyi_format/parsing/`, `docs/user/reference/semantic-pyi-format.md` |
| `prik/semantics/` | Language-neutral semantic IR, source-to-IR conversion, `.pyi` AST conversion, and policy completion | `models.py`, `fortran2ir.py`, `c2ir.py`, `pyi2ir.py`, `policy_completion.py` | `tests/fortran/semantic_ir/semantics/`, `tests/fortran/semantic_pyi_format/semantics/`, `docs/user/reference/semantic-ir.md`, `docs/user/reference/semantic-pyi-format.md` |
| `prik/wrapper_codegen/` | Canonical wrapper planning, C/Fortran generation, source printing, and semantic `.pyi` printing | `plan.py`, `planner.py`, `generator.py`, `printers/` | `tests/fortran/infrastructure/wrapper_codegen/`, feature-local `wrapper_codegen/` and `end_to_end/` tests, `docs/user/reference/fortran-wrapper.md` |
| `prik/naming/` | Unified public-name and generated-symbol policy for Python, C, and Fortran targets | `policy.py` | naming, visibility, and wrapper runtime tests |
PRIK_C_DOCS_END -->

## Hotspot Index

These files are the maintained source-navigation anchors. If ownership moves,
update this table, the package README files, and the mechanical checks in
`tests/shared/docs/test_structure.py` in the same change.

| Hotspot | Owns |
| --- | --- |
| `prik/__init__.py` | Public Python API exports. |
| `prik/cli.py` | CLI argument validation, stage selection, output routing, and wrapper-build entry. |
| `prik/pipeline/build.py` | End-to-end source and `.pyi` wrapper build orchestration. |
| `prik/pipeline/preprocessing.py` | Compiler-backed source preprocessing and dependency facts. |
| `prik/probes/fortran_types.py` | Fortran kind and storage probing. |
| `prik/semantics/ownership.py` | Central ownership, transfer, destruction, and generated-action policy. |
| `prik/parsers/fortran/parser.py` | Fortran parser project model and diagnostics. |
| `prik/parsers/fortran/cli.py` | Fortran parser report formatting. |
| `prik/semantics/metadata.py` | Cross-stage semantic metadata keys that survive parser, policy, printer, and lowering boundaries. |
| `prik/semantics/models.py` | Semantic IR dataclasses and core model metadata. |
| `prik/semantics/fortran2ir.py` | Fortran parser facts to semantic modules. |
| `prik/parsers/pyi/parser.py` | Minimal `.pyi` text/file parsing to Python AST. |
| `prik/pipeline/pyi.py` | Semantic `.pyi` text/file/path-set conversion and external-type reconciliation. |
| `prik/semantics/pyi2ir.py` | Semantic `.pyi` AST conversion and validation. |
| `prik/semantics/policy_completion.py` | Post-IR semantic policy completion before wrapper planning. |
| `prik/wrapper_codegen/plan.py` | Typed, policy-complete wrapper plan records. |
| `prik/wrapper_codegen/planner.py` | Semantic policy to wrapper-plan conversion. |
| `prik/wrapper_codegen/generator.py` | Ordered direct bridge, binding, header, and source generation. |
| `prik/wrapper_codegen/fortran/bridge.py` | Direct Fortran bridge lowering from typed plans. |
| `prik/wrapper_codegen/c/binding.py` | Direct Python-extension binding lowering from typed plans. |
| `prik/wrapper_codegen/printers/source_printers.py` | Native binding, header, and Fortran source printing. |
| `prik/wrapper_codegen/printers/pyi_printer.py` | Semantic `.pyi` printing. |
| `prik/compiling/objects.py` | Native compile object model. |
| `prik/compiling/compilers.py` | Compiler command execution and tool lookup. |
| `prik/compiling/native_support.py` | Native binding support installation for generated wrappers. |
| `prik/naming/policy.py` | Public wrapper names and generated target-language symbols. |
| `prik/binding_support/` | Native binding support payload copied into generated builds. |

<!-- PRIK_C_DOCS_START
| `prik/probes/c_types.py` | C target ABI type probing. |
| `prik/parsers/c/parser.py` | C parser project model and diagnostics. |
| `prik/parsers/c/cli.py` | C parser report formatting and preprocessing integration. |
| `prik/semantics/c2ir.py` | C parser facts to semantic modules. |
PRIK_C_DOCS_END -->

## Layer-To-Layer Route

For source-driven Fortran wrappers, read in this order:

<!-- PRIK_C_DOCS_START
```text
prik/cli.py
  -> prik/pipeline/build.py
  -> prik/pipeline/preprocessing.py
  -> prik/parsers/fortran/parser.py
  -> prik/probes/fortran_types.py
  -> prik/semantics/fortran2ir.py
  -> prik/semantics/policy_completion.py
  -> prik/wrapper_codegen/planner.py
  -> prik/wrapper_codegen/generator.py
  -> prik/wrapper_codegen/fortran/bridge.py
  -> prik/wrapper_codegen/c/binding.py
  -> prik/compiling/compilers.py
  -> tests/fortran/
```
PRIK_C_DOCS_END -->

For semantic `.pyi` builds, the parser branch is replaced by:

```text
prik/parsers/pyi/parser.py
  -> prik/pipeline/pyi.py
  -> prik/semantics/pyi2ir.py
  -> prik/semantics/policy_completion.py
  -> prik/wrapper_codegen/planner.py
  -> prik/wrapper_codegen/generator.py
```

<!-- PRIK_C_DOCS_START
For inspection-only C workflows, the path currently stops at semantic IR,
`.pyi`:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
```text
prik/cli.py
  -> prik/parsers/c/parser.py
  -> prik/probes/c_types.py
  -> prik/semantics/c2ir.py
  -> prik/wrapper_codegen/printers/pyi_printer.py
  -> prik/semantics/policy_completion.py
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Runtime wrapping of user-supplied C inputs is not implemented yet.
PRIK_C_DOCS_END -->

## Package-Level Notes

The hardest source packages also have local README files:

- `prik/README.md`
- `prik/parsers/README.md`
- `prik/parsers/fortran/README.md`
- `prik/parsers/pyi/README.md`
- `prik/semantics/README.md`
- `prik/compiling/README.md`

<!-- PRIK_C_DOCS_START
- `prik/parsers/c/README.md`
PRIK_C_DOCS_END -->

Keep these files short. They should tell developers where to enter the code,
what the package owns, what it must not own, and where the tests and public docs
live.
