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
| `prik/policy/ownership.py` | Central ownership, transfer, destruction, and generated-action policy | policy completion and typed wrapper planning |
| `prik/probes/fortran_types.py` | Fortran kind/storage facts and cache | semantic Fortran conversion and wrapper builds |
| `prik/pipeline/type_mapping_report.py` | Cross-stage target datatype mapping examples | semantic and codegen datatype catalogues plus documentation example tests |
| `prik/semantics/scalar_types.py` | Stable scalar names, families, and intrinsic storage facts | source-to-IR conversion and policy completion |
| `prik/codegen/primitive_scalar_types.py` | Resolved semantic-to-NumPy projection and implemented backend scalar lowering facts | mapping reports plus binding and bridge generation |
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
| CLI flags, stage selection, output formatting, diagnostics | `prik/cli.py` | `docs/user/reference/cli-commands.md`, `docs/user/getting-started/beginner-workflow.md` | `tests/fortran/command_line_interface/pipeline/`, `tests/docs/test_examples.py` |
| Compiler preprocessing, include paths, macros, and target flags | `prik/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/compiler-preprocessing.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
| Datatype probing, semantic normalization, NumPy projection, and mapping reports | `prik/probes/fortran_types.py`, `prik/semantics/scalar_types.py`, `prik/codegen/primitive_scalar_types.py`, `prik/pipeline/type_mapping_report.py` | `docs/maintainer/internal-architecture/type-system.md`, `docs/user/reference/semantic-ir.md` | `tests/fortran/data_types/` |
| Fortran parser facts and diagnostics | `prik/parsers/fortran/parser.py` | `docs/developer/fortran-parser-reference.md`, `docs/user/examples/recipes/inspect-fortran-api.md` | `tests/fortran/source_parsing/parsing/` |
| Semantic `.pyi` parsing, conversion, printing, package generation, and round-trip behavior | `prik/parsers/pyi/parser.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py`, `prik/printers/pyi.py` | `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/pyi-contracts/index.md`, `docs/user/examples/recipes/semantic-pyi-contracts.md` | `tests/fortran/semantic_pyi_format/`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_package_generation.py`, `tests/fortran/semantic_pyi_format/pipeline/test_contract_loading.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/semantic_pyi_format/pipeline/` |
| Wrapper-planning errors and support claims | `prik/policy/completion.py`, `prik/planning/planner.py` | `docs/user/reference/diagnostic-codes.md`, `docs/user/language-support/feature-matrix.md` | `tests/fortran/infrastructure/semantics/`, feature-local `policy/`, and `tests/fortran/infrastructure/codegen/` |
| Source-driven Fortran wrapper orchestration | `prik/pipeline/build.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/guide/building-shared-library.md` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py` |
| Semantic `.pyi` wrapper orchestration from native artifacts | `prik/pipeline/build.py`, `prik/pipeline/pyi.py`, `prik/semantics/pyi2ir.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/building_shared_library/pipeline/test_pyi_build_modes.py`, `tests/fortran/semantic_pyi_format/end_to_end/test_authoritative_contract_runtime.py`, `tests/fortran/pyi_contracts/exports_and_modules/`, `tests/fortran/pyi_contracts/functions_and_classes/` |
| Ownership, lifetime, output projection, and unsupported wrapper policy | `prik/policy/completion.py`, `prik/policy/ownership.py`, `prik/policy/models.py`, `prik/policy/construction.py`, `prik/planning/planner.py` | `docs/user/guide/memory-management.md`, `docs/user/reference/semantic-pyi-format.md`, `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/semantics/`, feature-local `policy/`, and `tests/fortran/infrastructure/codegen/` |
| Immediate callback policy, typed adapters, and trampolines | `prik/policy/models.py`, `prik/policy/construction.py`, `prik/policy/completion.py`, `prik/planning/models.py`, `prik/planning/planner.py`, `prik/codegen/c/binding.py`, `prik/codegen/fortran/bridge.py` | `docs/user/guide/callbacks.md`, `docs/user/reference/semantic-pyi-format.md` | `tests/fortran/callbacks/` |
| Native compilation, binding support, and shared-library linking | `prik/pipeline/build.py`, `prik/compiling/compilers.py`, `prik/compiling/native_support.py` | `docs/user/reference/fortran-wrapper.md`, `docs/developer/build-system.md` | `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`, `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py` |
| Public Python exports | `prik/__init__.py` | `README.md`, `docs/user/reference/python-api.md` | `tests/fortran/source_parsing/parsing/test_public_entrypoints.py` |
| Reference BLAS source ownership, inventory, and numerical validation | `examples/blas/routine_inventory.py`, `examples/blas/tests/test_routine_coverage.py` | `examples/blas/README.md`, `docs/user/examples/blas-wrapper.md` | `examples/blas/tests/test_*.py`, `examples/blas/ci/full_surface.py`, dedicated real-libraries workflow |
| Reference LAPACK source ownership, inventory, and numerical validation | `examples/lapack/routine_inventory.py`, `examples/lapack/tests/test_routine_coverage.py` | `examples/lapack/README.md`, `docs/user/examples/lapack-wrapper.md` | `examples/lapack/tests/test_*.py`, `examples/lapack/ci/full_surface.py`, dedicated real-libraries workflow |
| FFTPACK public-module boundary, source ownership, and numerical validation | `examples/fftpack/routine_inventory.py`, `examples/fftpack/tests/test_routine_coverage.py` | `examples/fftpack/README.md`, `docs/user/examples/fftpack-wrapper.md` | `examples/fftpack/tests/test_*.py`, `tests/fortran/building_shared_library/end_to_end/real_libraries/test_fftpack_routines.py`, dedicated real-libraries workflow |
| MINPACK source ownership, parameter constants, and numerical validation | `examples/minpack/routine_inventory.py`, `examples/minpack/tests/test_routine_coverage.py` | `examples/minpack/README.md`, `docs/user/examples/minpack-wrapper.md` | `examples/minpack/tests/test_*.py`, `tests/fortran/building_shared_library/end_to_end/real_libraries/test_minpack_routines.py`, dedicated real-libraries workflow |
| Source navigation documentation | `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`, package README files | `docs/developer/source-map.md` | `tests/docs/test_reference_and_source_map.py` |

<!-- PRIK_C_DOCS_START
| Compiler preprocessing, include paths, macros, target flags | `prik/pipeline/preprocessing.py` | `docs/user/examples/recipes/compiler-preprocessing.md`, `docs/developer/compiler-preprocessing.md`, `docs/developer/c-parser-reference.md`, `docs/developer/fortran-parser-reference.md` | `tests/fortran/source_preprocessing/preprocessing/`, `tests/fortran/source_preprocessing/preprocessing/test_parser_boundaries.py` |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| C parser facts and diagnostics | `prik/parsers/c/parser.py` | `docs/developer/c-parser-reference.md`, `docs/user/examples/recipes/inspect-c-api.md` | `tests/c/fixtures/parser/`, `tests/c/semantics/conversion/` |
| Semantic IR shape and cross-stage metadata | `prik/semantics/models.py`, `prik/semantics/metadata.py`, `prik/semantics/fortran2ir.py`, `prik/semantics/c2ir.py` | `docs/user/reference/semantic-ir.md` | `tests/fortran/semantic_ir/semantics/`, `tests/c/semantics/conversion/` |
| Generated Fortran bridge | `prik/codegen/fortran/bridge.py`, `prik/printers/fortran.py`, `prik/pipeline/wrapper.py` | `docs/user/reference/fortran-wrapper.md` | `tests/fortran/infrastructure/codegen/`, `tests/fortran/` generated-wrapper assertions |
| Generated CPython binding and Python-visible runtime behavior | `prik/codegen/c/binding.py`, `prik/codegen/c/python_surface.py`, `prik/codegen/c/naming.py`, `prik/printers/c.py`, `prik/pipeline/wrapper.py` | `docs/user/reference/fortran-wrapper.md`, `docs/user/reference/python-api.md` | `tests/fortran/infrastructure/codegen/`, `tests/fortran/` |
PRIK_C_DOCS_END -->

## Package Map

| Package | Purpose | Main files | Primary tests and docs |
| --- | --- | --- | --- |
| `prik/contracts/` | Public semantic `.pyi` contract vocabulary | `__init__.py` | `tests/fortran/semantic_pyi_format/`, semantic `.pyi` reference |
| `prik/pipeline/` | Source preprocessing, semantic `.pyi` loading, cross-stage datatype reporting, plan-to-source wrapper generation, and native build orchestration | `preprocessing.py`, `pyi.py`, `type_mapping_report.py`, `wrapper.py`, `build.py` | preprocessing, `.pyi`, datatype report, wrapper generation, and build tests |
| `prik/probes/` | Compiler-derived target facts | `fortran_types.py` | target probe tests |
| `prik/runtime/` | Python runtime objects consumed by generated extensions | `handles.py` | runtime handle and wrapper runtime tests |
| `prik/parsers/` | Public namespace for language and semantic `.pyi` frontends | child parser packages | `tests/fortran/source_parsing/parsing/`, `tests/c/parsing/`, `tests/fortran/semantic_pyi_format/parsing/` |
| `prik/parsers/fortran/` | Fortran lexer, recursive parser, models, type resolver, and parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `type_resolver.py`, `cli.py` | `tests/fortran/source_parsing/parsing/`, `docs/developer/fortran-parser-reference.md` |
| `prik/semantics/` | Language-neutral semantic IR, scalar datatype vocabulary, source-to-IR conversion, `.pyi` conversion, and raw ownership or descriptor metadata | `models.py`, `scalar_types.py`, `fortran2ir.py`, `c2ir.py`, `pyi2ir.py`, `ownership_metadata.py`, `native_array_handles.py` | `tests/fortran/data_types/semantics/`, `tests/fortran/semantic_ir/semantics/`, `tests/fortran/semantic_pyi_format/semantics/` |
| `prik/policy/` | Post-IR ownership, export, wrapper-policy construction, immutable policy models, descriptor-handle policy, and ordered completion | `ownership.py`, `exports.py`, `models.py`, `native_array_handles.py`, `construction.py`, `completion.py` | infrastructure semantics and feature-local policy tests |
| `prik/planning/` | Editable backend-neutral wrapper-plan records and mechanical policy projection | `models.py`, `planner.py` | infrastructure and feature-local codegen tests |
| `prik/codegen/` | Backend datatype projection, plan-driven docstrings, and direct lowering into C and Fortran syntax nodes | `primitive_scalar_types.py`, `docstrings.py`, `nodes.py`, `c/`, `fortran/` | data-type and infrastructure codegen, feature-local codegen, and end-to-end tests |
| `prik/printers/` | Language-specific serialization of C nodes, Fortran nodes, and semantic IR | `c.py`, `fortran.py`, `pyi.py` | source-printer and semantic-contract printer tests |
| `prik/compiling/` | Native compile objects, compiler command execution, shared-library linking, and native support installation; wrapper build orchestration lives in `prik/pipeline/build.py` | `objects.py`, `compilers.py`, `compiler_profiles.py`, `native_support.py` | `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`, `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py` |
| `prik/binding_support/` | Bundled header-only native binding support copied into generated wrapper builds | support header | wrapper build tests |
| `prik/utilities/` | Small shared Python utilities | `strings.py`, `visitor.py` | `tests/fortran/infrastructure/utilities/` and tests that exercise callers |

<!-- PRIK_C_DOCS_START
| `prik/probes/c_types.py` | Compiler-derived target ABI facts for C inspection workflows | `c_types.py` | C target probe tests |
| `prik/parsers/c/` | C lexer, parser, models, preprocessing metadata, and C parser CLI helpers | `parser.py`, `lexer.py`, `models.py`, `preprocessor.py`, `type_resolver.py`, `cli.py` | `tests/c/fixtures/parser/`, `docs/developer/c-parser-reference.md` |
| `prik/parsers/pyi/` | Semantic `.pyi` text/file parsing to Python AST. | `parser.py` | `tests/fortran/semantic_pyi_format/parsing/`, `docs/user/reference/semantic-pyi-format.md` |
| `prik/naming/` | Unified public-name and generated-symbol policy for Python, C, and Fortran targets | `policy.py`, `native_symbols.py` | naming, visibility, and wrapper runtime tests |
PRIK_C_DOCS_END -->

## Hotspot Index

These files are the maintained source-navigation anchors. If ownership moves,
update this table, the package README files, and the mechanical checks in
`tests/docs/test_reference_and_source_map.py` in the same change.

| Hotspot | Owns |
| --- | --- |
| `prik/__init__.py` | Public Python API exports. |
| `prik/cli.py` | CLI argument validation, stage selection, output routing, and wrapper-build entry. |
| `prik/pipeline/build.py` | End-to-end source and `.pyi` wrapper build orchestration. |
| `prik/pipeline/preprocessing.py` | Compiler-backed source preprocessing and dependency facts. |
| `prik/pipeline/type_mapping_report.py` | Target facts, semantic conversion, and backend NumPy projection rendered as a mapping report. |
| `prik/probes/fortran_types.py` | Fortran kind and storage probing. |
| `prik/semantics/scalar_types.py` | Stable primitive scalar identities, families, and intrinsic storage widths. |
| `prik/semantics/ownership_metadata.py` | Raw ownership and pointer-contract metadata keys and normalized semantic setters. |
| `prik/semantics/native_array_handles.py` | Raw semantic descriptor-handle facts attached before policy completion. |
| `prik/policy/ownership.py` | Central ownership, transfer, destruction, and generated-action policy. |
| `prik/policy/exports.py` | Completed Python namespace and export-name policy. |
| `prik/parsers/fortran/parser.py` | Fortran parser project model and diagnostics. |
| `prik/parsers/fortran/cli.py` | Fortran parser report formatting. |
| `prik/semantics/metadata.py` | Cross-stage semantic metadata keys that survive parser, policy, printer, and lowering boundaries. |
| `prik/semantics/models.py` | Semantic IR dataclasses and core model metadata. |
| `prik/semantics/fortran2ir.py` | Fortran parser facts to semantic modules. |
| `prik/parsers/pyi/parser.py` | Minimal `.pyi` text/file parsing to Python AST. |
| `prik/pipeline/pyi.py` | Semantic `.pyi` text/file/path-set conversion and external-type reconciliation. |
| `prik/semantics/pyi2ir.py` | Semantic `.pyi` AST conversion and validation. |
| `prik/policy/models.py` | Immutable backend-neutral completed wrapper-policy vocabulary. |
| `prik/policy/construction.py` | Wrapper-policy construction rules and completed-policy accessors. |
| `prik/policy/completion.py` | Ordered post-IR semantic policy completion before wrapper planning. |
| `prik/policy/native_array_handles.py` | Completed descriptor-handle policy and build requirements. |
| `prik/planning/models.py` | Typed, policy-complete wrapper plan records. |
| `prik/planning/planner.py` | Semantic policy to wrapper-plan conversion. |
| `prik/naming/native_symbols.py` | Stable generated native-symbol construction shared by planning and code generation. |
| `prik/codegen/docstrings.py` | Plan-driven Python-facing documentation generation. |
| `prik/codegen/primitive_scalar_types.py` | Primitive scalar backend and NumPy lowering catalogue. |
| `prik/pipeline/wrapper.py` | Single plan-to-rendered-wrapper orchestration and generated-wrapper result records. |
| `prik/codegen/fortran/bridge.py` | Direct Fortran bridge lowering from typed plans. |
| `prik/codegen/c/binding.py` | Direct Python-extension binding lowering from typed plans. |
| `prik/codegen/c/python_surface.py` | Executable derived-class facade and thin class-overload forwarding source. |
| `prik/codegen/c/naming.py` | Shared symbols referenced by generated C and the embedded Python facade. |
| `prik/printers/c.py` | C binding and header node serialization. |
| `prik/printers/fortran.py` | Fortran bridge node serialization. |
| `prik/printers/pyi.py` | Semantic IR serialization as editable `.pyi`. |
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
  -> prik/policy/completion.py
  -> prik/planning/planner.py
  -> prik/pipeline/wrapper.py
  -> prik/codegen/fortran/bridge.py
  -> prik/codegen/c/binding.py
  -> prik/compiling/compilers.py
  -> tests/fortran/
```
PRIK_C_DOCS_END -->

For semantic `.pyi` builds, the parser branch is replaced by:

```text
prik/parsers/pyi/parser.py
  -> prik/pipeline/pyi.py
  -> prik/semantics/pyi2ir.py
  -> prik/policy/completion.py
  -> prik/planning/planner.py
  -> prik/pipeline/wrapper.py
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
  -> prik/printers/pyi.py
  -> prik/policy/completion.py
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
