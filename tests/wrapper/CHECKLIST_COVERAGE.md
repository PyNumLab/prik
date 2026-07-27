# Wrapper Checklist Coverage

This file maps the active semantic `.pyi` wrapper roadmap to concrete wrapper
test subjects. Use paths relative to `tests/wrapper/fortran/` so moved test
modules are searchable without relying on old flat filenames.

Wrapper generator route status is maintained only in
`docs/maintainer/roadmap/wrapper-plan-migration-checklist.md`. Its exhaustive,
test-enforced matrix lists every collected wrapper node as `wrapper-plan` or
`not-applicable`. Historical migration statuses remain in the roadmap's
recorded progression, not in the live ledger.

## Stage 1 — Searchable Layout, Contract Output, And Fixtures

| Roadmap item | Evidence |
| --- | --- |
| Stable top-level subjects | `fortran/build_from_source/README.md`, `fortran/build_from_pyi/README.md`, `fortran/multiple_files/README.md`, `fortran/external_routines/README.md`, `fortran/real_libraries/README.md`, `fortran/edit_pyi_contracts/README.md`, `fortran/arrays/README.md`, `fortran/scalars/README.md`, `fortran/function_calls/README.md`, `fortran/strings/README.md`, `fortran/derived_types/README.md`, `fortran/callbacks/README.md`, `fortran/module_state/README.md`, `fortran/runtime_behavior/README.md`, `fortran/naming/README.md`, `fortran/layout_rules/README.md` |
| Native wrapper fixtures live in shared data corpus | `tests/data/fortran/wrapper/`, `tests/data/fortran/blas/`, `tests/data/fortran/lapack/`, `layout_rules/test_wrapper_guide_layout.py` |
| Runtime contracts live beside consuming subject tests | `build_from_pyi/contracts/runtime_abi/`, `build_from_pyi/modified_contracts/basic_subroutine/flatten_m1.pyi`, `build_from_pyi/modified_contracts/basic_subroutine/alias_increment.pyi`, `build_from_pyi/invalid_contracts/projection_metadata/incomplete_native_call.pyi`, `edit_pyi_contracts/modified_contracts/fnative_call_examples_native_order/fnative_call_examples_f90.pyi`, `edit_pyi_contracts/modified_contracts/fnative_call_examples_immutable/fnative_call_examples_f90.pyi`, `edit_pyi_contracts/modified_contracts/fallocatable_views_explicit_ownership/fallocatable_views_f90.pyi`, `edit_pyi_contracts/modified_contracts/module_variables_visibility/fmodule_vars_f90.pyi`, `layout_rules/test_wrapper_guide_layout.py` |
| Generated wrapper `.pyi` packages are checked fixtures, not tmp-only artifacts | `build_from_pyi/test_pyi_wrapper_builds.py`, `build_from_pyi/test_contract_package_runtime.py`, `build_from_source/test_source_generated_pyi_contracts.py`, `multiple_files/test_multi_source_builds.py`, `external_routines/test_external_procedures.py`, `real_libraries/test_real_blas_lapack.py`, `arrays/test_array_generated_pyi_contracts.py`, `scalars/test_scalar_generated_pyi_contracts.py`, `function_calls/test_function_call_generated_pyi_contracts.py`, `strings/test_string_generated_pyi_contracts.py`, `derived_types/test_derived_type_generated_pyi_contracts.py`, `callbacks/test_callback_generated_pyi_contracts.py`, `module_state/test_module_state_generated_pyi_contracts.py`, `runtime_behavior/test_runtime_behavior_generated_pyi_contracts.py`, `naming/test_naming_generated_pyi_contracts.py`, `tests/pipeline/pyi_builds/test_contract_package_generation.py` |
| Exact `.pyi` generation-regression suite remains separate | `tests/pyi/fixtures/general/`, `tests/pipeline/pyi_builds/test_contract_fixtures.py` |
| Subject README and stale-path guard | `layout_rules/test_wrapper_guide_layout.py` |
| Explicit `.pyi` output and single-entry contract behavior | `tests/pipeline/pyi_builds/test_contract_package_generation.py`, `build_from_pyi/test_contract_package_runtime.py`, `build_from_pyi/test_pyi_wrapper_builds.py` |

## Stage 2 — Structured Native Build Model

| Roadmap item | Evidence |
| --- | --- |
| Structured extension-level native build plan | `build_from_source/test_build_modes.py::test_source_build_result_records_structured_native_plan`, `build_from_pyi/test_pyi_wrapper_builds.py::test_generated_pyi_fixture_builds_from_native_object_without_source_reparse` |
| Ordered link item model across native item kinds | `build_from_source/test_build_modes.py::test_native_link_plan_serializes_interleaved_item_kinds` |
| Explicit extension link order preserves declared objects and arguments | `build_from_source/test_compiler_verbose.py::test_link_keeps_the_declared_object_and_link_argument_order` |

## Stage 3 — Multi-Source Combined Contract Generation

| Roadmap item | Evidence |
| --- | --- |
| One explicit package for ordered multi-source `--pyi --out` | `multiple_files/test_multi_source_builds.py::test_multi_source_pyi_out_writes_one_flat_combined_package` |
| Source/generated-contract parity with same extension name, namespaces, and link order | `multiple_files/test_multi_source_builds.py::test_multi_source_generated_contract_build_matches_source_runtime_and_link_order` |
| Modified entry export policy while preserving native module children | `multiple_files/test_multi_source_builds.py::test_multi_source_modified_entry_preserves_modules_and_adds_documented_alias`, `build_from_pyi/test_pyi_wrapper_builds.py::test_reduced_entry_generates_only_reachable_module_variable_bindings` |

## Stage 4 — Shared Parity Harness And Standalone Procedures

| Roadmap item | Evidence |
| --- | --- |
| Shared source/generated fixture pattern for standalone externals | `external_routines/test_external_procedures.py::test_fixed_form_standalone_external_runtime_parity`, `external_routines/test_external_procedures.py::test_free_form_standalone_external_runtime_parity`, `external_routines/test_external_procedures.py::test_one_source_with_several_standalone_externals_exports_each_at_root` |
| Fixed-form, free-form, multi-procedure, and compact BLAS-like external contracts | `external_routines/test_external_procedures.py::test_generated_external_contracts_are_non_empty_root_fragments`, `external_routines/test_external_procedures.py::test_compact_blas_like_folder_generates_one_external_entry_and_preserves_separate_objects` |
| External bridge placement and module-procedure contrast | `external_routines/test_external_procedures.py::test_classic_external_bridge_uses_implicit_declaration_and_no_module_use`, `external_routines/test_external_procedures.py::test_module_procedure_bridge_uses_native_module_scope` |
| `@external` with `@bind` and handwritten source-free contracts | `external_routines/test_external_procedures.py::test_external_bind_renames_python_export_without_changing_native_call` |
| C-order flat storage over assumed-size native external buffers | `external_routines/test_external_procedures.py::test_handwritten_c_order_flat_contract_passes_rank_preserving_bridge_view` |
| Invalid root/module placement edits fail before code generation | `external_routines/test_external_procedures.py::test_package_entry_rejects_non_external_root_declaration_before_codegen`, `external_routines/test_external_procedures.py::test_namespace_imported_module_rejects_external_marker_before_codegen` |

## Stage 5 — Full Generated-Contract Runtime Parity

| Roadmap item | Evidence |
| --- | --- |
| Scalar and verified baseline array routines rebuild from generated `.pyi` contracts, expose the same normalized Python names as source builds, compare generated packages against checked fixtures, and use the same runtime assertion bodies; both `fmath.f` and `fmath_f90.f90` also replay the legacy and wrapper-plan generators; isolated scalar-only parity covers primitive kinds, value/address projection, hidden output, copy-in/copy-out, rank-zero storage, raw addresses, and direct-plus-hidden multiple-result tuple assembly without array/string route blockers | `scalars/test_verified_baseline.py::test_fmath_scalar_sources_use_canonical_wrapper_plan`, `scalars/test_verified_baseline.py::test_fortran_wrapper_pipeline_builds_importable_extension`, `scalars/test_verified_baseline.py::test_f90_wrapper_pipeline_builds_importable_extension`, `scalars/test_verified_baseline.py::test_fortran_array_wrapper_pipeline_matches_fmath_results_with_contiguous_arrays`, `scalars/test_verified_baseline.py::test_f90_array_wrapper_distinguishes_contiguous_and_strided_contracts`, `scalars/test_fortran_enums.py::test_fortran_enums_preserve_integer_runtime_surface`, `scalars/test_scalar_boundary_plan.py`, `scalars/test_scalar_kinds.py::test_scalar_kind_coverage_uses_compiler_probed_wrapper_types`, `scalars/test_value_and_bind_c.py::test_value_and_existing_bind_c_renamed_symbol_use_correct_abi` |
| Function-call contracts rebuild from generated `.pyi` fixtures with the same optional-argument handling, scalar replacement writeback, hidden output projection, multiple-result ordering, allocatable nullable outputs, native-call projection metadata, native shared-library link inputs, and validation failures as source builds | `function_calls/test_optional_arguments.py::test_optional_arguments_drive_fortran_present_behavior`, `function_calls/test_optional_arguments.py::test_fixed_form_optional_arguments_drive_fortran_present_behavior`, `function_calls/test_optional_arguments.py::test_optional_array_descriptors_preserve_presence_and_storage_state`, `function_calls/test_scalar_writeback_plan.py::test_scalar_copy_in_out_returns_replacement`, `function_calls/test_output_arguments.py::test_output_arguments_and_multiple_results_follow_python_projection_rules`, `function_calls/test_native_call_examples.py::test_native_call_examples_cover_scalar_array_string_and_object_projection`, `function_calls/test_native_call_examples.py::test_native_call_examples_build_from_generated_pyi_and_native_shared_library` |
| Array contracts rebuild from generated `.pyi` fixtures with the same dtype, rank, shape, order, stride, lower-bound, writeability, byte-order, alignment, zero-extent, assumed-rank dispatch, ordinary Python-owned result behavior, and allocatable result-handle behavior as source builds | `arrays/test_array_contracts.py::test_remaining_array_contracts_are_validated_before_fortran_calls`, `arrays/test_array_results.py::test_array_results_follow_data_buffer_and_descriptor_handle_contracts`, `arrays/test_array_results.py::test_owned_allocatable_results_preserve_handle_state`, `arrays/test_assumed_rank_arrays.py::test_assumed_rank_arguments_dispatch_to_runtime_rank`, `arrays/test_assumed_rank_arrays.py::test_assumed_rank_bridge_dispatches_each_runtime_rank_argument`, `arrays/test_multidimensional_arrays.py::test_rank2_contiguous_contract_requires_fortran_contiguous`, `arrays/test_multidimensional_arrays.py::test_rank2_assumed_shape_accepts_fortran_ordered_strided_views`, `arrays/test_multidimensional_arrays.py::test_rank2_assumed_shape_rejects_non_positive_strides`, `arrays/test_multidimensional_arrays.py::test_rank2_explicit_shape_requires_fortran_contiguous`, `arrays/test_multidimensional_arrays.py::test_rank3_contiguous_contract_requires_fortran_contiguous`, `arrays/test_multidimensional_arrays.py::test_rank3_assumed_shape_accepts_fortran_ordered_strided_views` |
| Character contracts rebuild from generated `.pyi` fixtures with the same fixed-length buffers, assumed-length strings, nullable deferred scalar results, deferred-width native handles, copy-in/copy-out behavior, optional strings, Unicode handling, embedded-NUL validation, and raw fixed-width array addresses as source builds | `strings/test_character_arguments.py::test_legacy_fortran_character_arguments_and_results`, `strings/test_character_arguments.py::test_modern_fortran_character_arguments_and_results`, `strings/test_character_arguments.py::test_deferred_allocatable_string_results_use_canonical_plan`, `strings/test_character_arguments.py::test_deferred_character_array_handles_use_canonical_plan`, `strings/test_character_arguments.py::test_raw_fixed_width_character_arrays_use_canonical_plan`, `strings/test_character_edge_cases.py::test_fortran_character_edge_cases_follow_copy_in_copy_out_policy`, `tests/semantics/conversion/pyi/test_calls_and_projections.py::test_projected_replacement_without_native_call_keeps_writable_argument_storage`, `tests/semantics/conversion/pyi/test_calls_and_projections.py::test_native_call_projected_output_keeps_visible_storage_writable` |
| Derived-type contracts rebuild from generated `.pyi` fixtures with the same fields, independent module-procedure and method surfaces, constructors, finalizers, borrowed child lifetime, scalar object boundaries, inheritance, polymorphic dispatch, complete scalar actual/dummy compatibility, descriptor-backed scalar module proxies, and wrapper-owned allocatable/pointer holders as source builds | `derived_types/test_derived_type_methods.py::test_modern_fortran_derived_type_exposes_class_and_type_bound_methods`, `derived_types/test_constructors_and_finalizers.py::test_fortran_default_constructor_keywords_and_finalization`, `derived_types/test_borrowed_finalizers.py::test_borrowed_child_wrapper_never_finalizes_native_component`, `derived_types/test_derived_layout.py::test_bind_c_derived_types_use_accessors_and_fortran_value_copy`, `derived_types/test_derived_type_boundaries.py::test_scalar_derived_types_cross_procedure_boundaries`, `derived_types/test_phase8_derived_plan.py`, `derived_types/test_scalar_derived_actual_dummy_matrix.py`, `derived_types/test_inheritance.py::test_fortran_extension_types_generate_python_inheritance`, `derived_types/test_pointers.py::test_pointer_array_handles_block_on_unsupported_result_owner_policy`, `tests/wrapper_codegen/test_phase8_scalar_derived_actual_dummy_matrix.py`, `tests/semantics/conversion/pyi/test_classes_and_overloads.py::test_method_declarations_keep_module_procedure_targets_independent` |
| Callback contracts route through wrapper-plan generation without legacy lowering and rebuild from generated `.pyi` fixtures with the same primitive scalar values, array, character-storage, and derived callback conversions, call-scoped lifetime, nested same-thread entry, GIL handling, reference cleanup, and fatal exception behavior as source builds | `callbacks/test_all_callback_shapes.py::test_immediate_callbacks_cover_all_supported_argument_shapes`, `callbacks/test_scalar_callbacks.py::test_immediate_scalar_dummy_procedure_calls_python_callback`, `callbacks/test_scalar_callbacks.py::test_callback_exception_prints_traceback_and_aborts_host_process`, `callbacks/test_array_callbacks.py::test_immediate_dummy_procedure_converts_array_arguments_and_results`, `callbacks/test_derived_callbacks.py::test_immediate_dummy_procedure_converts_derived_arguments_and_results`, `tests/wrapper_codegen/test_phase10_callbacks.py`, `tests/semantics/conversion/pyi/test_types_and_values.py::test_convert_pyi_to_ir_preserves_prototype_argument_names_and_dimensions` |
| Module-state contracts rebuild from generated `.pyi` fixtures with the same scalar module attributes, parameter behavior, saved native state, plain and `Aliased` live allocatable module views, borrowed field handles, owned allocatable result handles, same-handle allocatable descriptor mutation, explicit-copy independence, fresh extraction after state changes, rank-zero descriptor copying/nullability, and common-block encapsulation as source builds; isolated scalar and native-handle owners also replay legacy and wrapper-plan routes | `module_state/test_module_state.py::test_scalar_module_variables_use_attributes_and_parameters_have_no_native_setter`, `module_state/test_scalar_module_variable_plan.py::test_whole_scalar_module_variable_behavior_uses_canonical_plan`, `module_state/test_allocatable_views.py::test_allocatable_module_fields_and_results_expose_lifetime_safe_handles`, `module_state/test_allocatable_views.py::test_plain_allocatable_module_array_exposes_current_live_view`, `module_state/test_allocatable_views.py::test_scalar_descriptor_module_variables_return_copied_optional_values`, `module_state/test_allocatable_replacement.py::test_allocatable_inout_arrays_mutate_and_return_the_same_handle`, `module_state/test_allocatable_replacement.py::test_projected_allocatable_descriptor_preserves_same_handle_identity`, `derived_types/test_pointers.py::test_module_native_array_handles_use_canonical_plan`, `module_state/test_common_blocks.py::test_common_block_storage_stays_internal_to_wrapped_fortran` |
| Runtime behavior contracts rebuild from generated or edited `.pyi` fixtures with the same recursion/reentrancy behavior, `@hold_gil` GIL policy, `@raises(...)` status projection, and generated wrapper policy code as source-backed builds | `runtime_behavior/test_runtime_recursion.py::test_recursive_native_runtime_calls`, `runtime_behavior/test_runtime_policies.py::test_pyi_runtime_policies_release_gil_and_project_native_errors`, `runtime_behavior/test_runtime_policies.py::test_compiled_runtime_policies_release_gil_and_project_native_errors`, `runtime_behavior/test_openmp_runtime.py::test_openmp_enabled_procedure_builds_with_explicit_gnu_flags` |
| Naming and generic-interface contracts rebuild from generated `.pyi` fixtures with the same public-name normalization, visibility filtering, keyword/collision policy, public generic dispatch, type-bound binding names, defined operators, comparisons, named operators, and assignment behavior as source builds | `naming/test_visibility_naming.py::test_visibility_and_default_python_name_fixing_policy`, `naming/test_generic_interfaces.py::test_fortran_generic_interfaces_dispatch_in_generated_c_extension`, `naming/test_generic_interfaces.py::test_fixed_form_fortran_generic_interface_dispatches_in_generated_c_extension`, `naming/test_defined_operators.py::test_fortran_defined_operators_and_assignment_dispatch_in_generated_c_extension`, `tests/wrapper_codegen/printers/test_pyi_printer_imports_and_packages.py::test_fortran_generated_contracts_reserve_colliding_public_names_by_namespace`, `tests/semantics/conversion/pyi/test_classes_and_overloads.py::test_pyi_keyword_normalized_type_bound_method_keeps_native_binding_name` |
| Shared native-array runtime handles validate generated operation tables at construction, require generated `shape`, `array_actual`, and `descriptor` operations, reject `None` from present-handle operations, require typed non-null handoffs for array actuals, normalize descriptor field records or contiguous descriptor data addresses, resolve deferred character dtype from runtime element length, expose common metadata, state dispatch, absent-state `to_numpy()` short-circuiting, present-state extraction rejection for `None`, dtype/rank validation for extracted arrays, completed live-view dispatch for borrowed, contiguous, and strided descriptor views, owner retention, policy-gated pointer operations, explicit unsupported-extraction errors, and no implicit-copy fallback | `tests/runtime/handles/` |

## Stage 7 — Library-Scale And Mixed-Bundle Evidence

| Roadmap item | Evidence |
| --- | --- |
| Full real BLAS and LAPACK corpora generate checked contract packages, build full root-procedure wrappers with `build_pyi_extension`, import every root procedure from cached full native shared libraries, and run selected NumPy-style calls against those full modules | `real_libraries/test_real_blas_lapack.py::test_full_library_wrapper_imports_every_root_procedure_from_cached_shared_library` |
| Several contracts imported by one entry resolve from one archive or one shared library while preserving child module namespaces | `real_libraries/test_stage7_native_bundles.py::test_imported_contracts_resolve_from_one_archive_or_shared_library` |
| Module procedures use separately supplied `.mod` directories while standalone `@external` procedures need no module search inputs | `real_libraries/test_stage7_native_bundles.py::test_mixed_module_external_bundle_resolves_all_native_input_kinds`, `real_libraries/test_stage7_native_bundles.py::test_missing_module_directory_reports_compile_error` |
| Mixed native modules and standalone externals expose modules below namespaces and externals at the root while object, archive, direct shared-library, and named-library link items preserve order | `real_libraries/test_stage7_native_bundles.py::test_mixed_module_external_bundle_resolves_all_native_input_kinds` |
| Static archive dependency order, linker archive groups, and required transitive named libraries resolve at runtime | `real_libraries/test_stage7_native_bundles.py::test_static_archive_dependency_order_resolves_transitive_library`, `real_libraries/test_stage7_native_bundles.py::test_static_archive_groups_resolve_cyclic_archive_dependencies`, `real_libraries/test_stage7_native_bundles.py::test_required_transitive_named_library_resolves_runtime_symbol` |
| Missing symbols, duplicate definitions, incompatible artifacts, missing `.mod` directories, and unavailable dependent shared libraries report native diagnostics without source fallback | `real_libraries/test_stage7_native_bundles.py::test_missing_symbol_reports_native_link_or_loader_error`, `real_libraries/test_stage7_native_bundles.py::test_duplicate_native_definitions_report_linker_error`, `real_libraries/test_stage7_native_bundles.py::test_incompatible_native_artifact_reports_linker_error`, `real_libraries/test_stage7_native_bundles.py::test_missing_module_directory_reports_compile_error`, `real_libraries/test_stage7_native_bundles.py::test_unavailable_dependent_shared_library_reports_loader_error` |

## Stage 8 — Editable Contract Semantics

| Roadmap item | Evidence |
| --- | --- |
| Editable native-order contracts can omit `@native_call` when native dummies remain visible, including scalar/array output storage, raw array addresses with completed shape/orientation, fixed-length string identity calls with no observable Python `str` mutation, function results, and derived-type output slots | `edit_pyi_contracts/test_native_order_contracts.py::test_editable_contract_can_use_native_order_arguments_without_native_call`, `edit_pyi_contracts/test_native_order_contracts.py::test_raw_array_addresses_use_canonical_plan`, `edit_pyi_contracts/modified_contracts/fnative_call_examples_native_order/fnative_call_examples_f90.pyi` |
| Post-IR immutable replacement policy copies a read-only Python array into mutable native storage and returns a detached replacement without mutating the original object | `edit_pyi_contracts/test_policy_dispatch_contracts.py::test_immutable_array_policy_copies_in_and_returns_replacement`, `edit_pyi_contracts/modified_contracts/fnative_call_examples_immutable/fnative_call_examples_f90.pyi` |
| Immutable writable scalar, string, array, and derived-type arguments use policy-selected native temporaries and return replacements without mutating the original Python-visible object | `edit_pyi_contracts/test_policy_dispatch_contracts.py::test_immutable_scalar_string_array_and_derived_policies_return_replacements`, `edit_pyi_contracts/modified_contracts/fnative_call_examples_immutable_kinds/fnative_call_examples_f90.pyi` |
| Contradictory owner/transfer/destruction triples fail before bridge generation with the declaration and rejected triple in the diagnostic | `edit_pyi_contracts/test_policy_dispatch_contracts.py::test_contradictory_ownership_contract_fails_before_bridge_generation`, `edit_pyi_contracts/invalid_contracts/contradictory_ownership/fnative_call_examples_f90.pyi` |
| Explicit editable ownership triples produce native-owned borrowed module handles, wrapper-owned borrowed component handles, and wrapper-owned result handles with distinct release boundaries; borrowed wrapper children retain their owner and finalization runs exactly once | `edit_pyi_contracts/test_ownership_contracts.py`, `edit_pyi_contracts/modified_contracts/fallocatable_views_explicit_ownership/fallocatable_views_f90.pyi`, `edit_pyi_contracts/modified_contracts/fborrowed_finalizer_explicit_ownership/fborrowed_finalizer_f90.pyi` |
| Edited contracts remove classes, methods, constructors, class members, and individual overload candidates; they can also add a renamed `@bind` declaration and a new overload group over existing native specifics. Missing overload binds for private module or type-bound specifics preserve the native compiler accessibility error | `edit_pyi_contracts/test_surface_edit_contracts.py`, `edit_pyi_contracts/modified_contracts/foverloads_pruned_surface/`, `edit_pyi_contracts/modified_contracts/foverloads_without_constructor_member/`, `edit_pyi_contracts/modified_contracts/foverloads_added_bindings/`, `edit_pyi_contracts/modified_contracts/foverloads_private_specific_without_bind/`, `edit_pyi_contracts/modified_contracts/foverloads_private_type_bound_specifics_without_bind/` |
| Edited `.pyi` contracts can remove a public function and hide declarations with `@private` or `private[...]` while preserving unaffected runtime behavior | `edit_pyi_contracts/test_visibility_contracts.py::test_editable_contract_removes_and_hides_public_declarations`, `edit_pyi_contracts/modified_contracts/module_variables_visibility/fmodule_vars_f90.pyi` |
| Native `Addr(Arg(...))` projection remains primitive-scalar-only while array descriptor arguments and results complete native-array handle policy before lowering; returned pointer arrays own persistent descriptor storage without claiming ownership of their targets | `tests/semantics/policy/test_accessor_and_storage_policy.py::test_policy_completion_rejects_addr_projection_for_array_descriptor_handles`, `tests/semantics/policy/test_native_array_ownership.py::test_native_array_handle_policies_complete_before_ir_lowering`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_pointer_result_uses_owned_pointer_descriptor_without_target_deallocation`, `derived_types/test_pointers.py::test_pointer_array_results_use_owned_descriptors_without_owning_targets` |
| Native array handle bridge and binding architecture dispatches from completed descriptor-kind and handle-kind policy pairs | `tests/semantics/policy/test_native_array_ownership.py::test_native_array_handle_dispatcher_routes_completed_policy_to_named_method`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_generated_artifacts_follow_one_typed_action_vocabulary`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_plan_edits_fail_central_validation` |
| Module native-array handles lower from typed borrowed-handle plans to private operation wrappers for state, shape, pointer/descriptor handoff, allocatable `.to_numpy()`/`deallocate()`/`resize(shape)`, pointer `associate(other)`/`nullify()`, and policy-gated pointer shape-changing operations | `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_module_variables_own_borrowed_handle_plans_and_operation_sets`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_module_pointer_association_uses_standard_descriptor_assignment`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_generated_artifacts_follow_one_typed_action_vocabulary`, `derived_types/test_pointers.py::test_module_and_derived_pointer_handles_track_native_association` |
| Generated and caller-created native array handles use typed operation sets. Contract constructors start empty; read-only calls pack empty facts, while writable calls lazily attach a versioned native record and persistent compiler descriptor to the same handle. Caller-created pointers can copy an associated or unassociated descriptor state before that attachment. ABI-compatible, separately built extensions validate and reuse the record for allocatable and pointer mutation | `tests/runtime/test_contract_constructors.py`, `tests/semantics/policy/test_native_array_ownership.py::test_visible_descriptor_writeback_completes_caller_handle_construction_lifecycle`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_keeps_datatype_specific_state_under_argument_and_result_plans`, `module_state/test_allocatable_replacement.py::test_allocatable_inout_arrays_mutate_and_return_the_same_handle`, `module_state/test_allocatable_replacement.py::test_caller_created_allocatable_crosses_separately_built_extensions`, `derived_types/test_pointers.py::test_caller_created_pointer_handle_tracks_native_output_association`, `derived_types/test_pointers.py::test_caller_created_pointer_crosses_separately_built_extensions` |
| Owned allocatable results use planned persistent descriptor ownership, collect bridge-local data before transfer, expose owner-addressed operations, and release through the shared handle finalizer path; source and generated-`.pyi` modes retain compiled behavior coverage | `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_numeric_owned_result_defaults_to_assignment_then_move_alloc`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_maybe_unallocated_owned_result_uses_collector_without_local_assignment`, `tests/semantics/policy/test_native_array_ownership.py::test_hidden_allocatable_handle_output_completes_as_owned_result_before_lowering`, `tests/runtime/handles/test_factories_and_lifecycle.py::test_generated_owned_handle_factory_passes_persistent_owner_to_every_operation`, `arrays/test_array_results.py::test_maybe_unallocated_allocatable_result_preserves_absent_state`, `module_state/test_allocatable_views.py::test_allocatable_module_fields_and_results_expose_lifetime_safe_handles`, `module_state/test_allocatable_views.py::test_maybe_unallocated_direct_allocatable_results_preserve_unallocated_state`, `module_state/test_allocatable_replacement.py::test_allocatable_inout_arrays_mutate_and_return_the_same_handle` |
| Pointer-valued functions and nonoptional pointer-array `intent(out)` dummies use the owned-result descriptor path, preserve associated and unassociated states, and destroy only wrapper descriptor storage; optional outputs and `intent(inout)` descriptors remain Python-visible | `tests/semantics/conversion/fortran/test_fortran_conversion_procedures_and_interfaces.py::test_pointer_array_output_visibility_follows_intent_and_optional_presence`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_pointer_result_uses_owned_pointer_descriptor_without_target_deallocation`, `derived_types/test_pointers.py::test_module_and_derived_pointer_handles_track_native_association`, `derived_types/test_pointers.py::test_pointer_array_results_use_owned_descriptors_without_owning_targets` |
| Native array descriptor arguments record required and optional-presence roles in the typed plan; direct bridge and binding lowering consume those roles while runtime helpers validate descriptor kind, dtype, rank, and shape metadata | `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_keeps_datatype_specific_state_under_argument_and_result_plans`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_generated_artifacts_follow_one_typed_action_vocabulary`, `tests/runtime/handles/test_descriptor_abi.py` |
| Concrete-rank numeric array arguments retain the NumPy extraction path and use native handle actuals without converting through `to_numpy()`; optional and assumed-rank behavior remains covered at the public wrapper boundary | `tests/wrapper_codegen/test_phase6a_array_buffers.py::test_required_array_buffer_dispatches_through_named_binding_and_bridge_methods`, `tests/runtime/handles/test_array_actual_abi.py`, `tests/wrapper/fortran/arrays/test_array_contracts.py::test_remaining_array_contracts_are_validated_before_fortran_calls`, `tests/wrapper/fortran/arrays/test_assumed_rank_arrays.py::test_assumed_rank_arguments_dispatch_to_runtime_rank`, `tests/wrapper/fortran/function_calls/test_optional_arguments.py::test_optional_arguments_drive_fortran_present_behavior` |
| Runtime normal-array argument packing uses the generated Bind-C array tuple shape for ndarray inputs and native handle array-actual handoff: pointer address, optional runtime rank, optional item size, extents, and optional upper bounds plus unit strides; allocated/associated handles pack without calling `to_numpy()`, and unallocated/unassociated handles block before generated handoff | `tests/runtime/handles/test_array_actual_abi.py::test_array_actual_argument_abi_packer_uses_ndarray_data_pointer_and_shape_fields`, `tests/runtime/handles/test_array_actual_abi.py::test_array_actual_argument_abi_packer_uses_allocatable_native_array_actual_without_numpy_conversion`, `tests/runtime/handles/test_array_actual_abi.py::test_array_actual_argument_abi_packer_uses_pointer_native_array_actual_dtype_metadata`, `tests/runtime/handles/test_array_actual_abi.py::test_array_actual_argument_abi_packer_rejects_absent_handles_before_generated_handoff` |
| Runtime descriptor-handle argument packing returns validated standard descriptor facts (`base_addr`, `elem_len`, `rank`, and dimension lower bounds, extents, and stride multipliers) for non-projected calls, while projected writable calls require a typed persistent standard-descriptor handoff; generated C establishes call-local CFI storage only for the fact-packed path, optional present handles add a distinct non-null presence token, and optional absent `None` produces null fields without accepting unsupported descriptor kinds | `tests/runtime/handles/test_descriptor_abi.py::test_descriptor_argument_abi_packer_returns_required_descriptor_fields`, `tests/runtime/handles/test_descriptor_abi.py::test_descriptor_argument_abi_packer_positional_helper_matches_generated_call_shape`, `tests/runtime/handles/test_descriptor_abi.py::test_descriptor_argument_abi_packer_maps_optional_presence_and_absence`, `tests/runtime/handles/test_descriptor_abi.py::test_descriptor_argument_abi_packer_rejects_wrong_kind_and_unsupported_descriptor_kind`, `tests/runtime/handles/test_descriptor_abi.py::test_projected_descriptor_handoff_requires_persistent_standard_descriptor_storage` |
| Generated pointer descriptor-view decoding is selected by the typed handle plan and direct backend lowering; runtime decoding validates the standard descriptor fields needed to build live strided views | `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_plain_module_descriptor_view_requires_matching_completed_interop`, `tests/wrapper_codegen/test_phase7_native_array_handles.py::test_phase7_generated_artifacts_follow_one_typed_action_vocabulary`, `tests/runtime/handles/test_descriptor_abi.py` |
| Runtime pointer descriptor-view extraction accepts decoded descriptor mappings or field-record objects, validates required decoded TS29113 fields and descriptor rank against the handle contract, rejects null decoded descriptors for present associated state, and builds positive- or negative-stride NumPy views in the shared helper | `tests/runtime/handles/test_descriptor_abi.py::test_pointer_c_descriptor_helper_builds_strided_numpy_view_from_decoded_fields`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_c_descriptor_helper_builds_negative_stride_numpy_view_from_decoded_fields`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_c_descriptor_helper_accepts_field_record_objects`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_c_descriptor_helper_validates_decoded_descriptor_fields`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_descriptor_view_policy_uses_decoded_descriptor_fields_for_strided_view`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_descriptor_view_policy_rejects_decoded_descriptor_rank_mismatch`, `tests/runtime/handles/test_descriptor_abi.py::test_pointer_descriptor_view_policy_rejects_null_descriptor_for_present_state` |
| Native array handle extraction is view-only: absent descriptors return `None`; plain and `Aliased` allocatables expose current mutable native storage through different completed mechanisms with identical public behavior; pointer contiguous/descriptor paths never copy; stale views are unsupported; and independent storage requires explicit `.copy()` | `module_state/test_allocatable_views.py::test_plain_allocatable_module_array_exposes_current_live_view`, `derived_types/test_phase8_derived_plan.py::test_aliased_module_derived_object_uses_direct_live_field_handles`, `derived_types/test_phase8_derived_plan.py::test_pointer_field_descriptor_views_use_canonical_plan`, `tests/runtime/handles/test_handle_protocols.py`, `tests/runtime/handles/test_descriptor_abi.py`, `tests/semantics/policy/test_native_array_ownership.py::test_aliased_does_not_change_allocatable_live_view_semantics` |
| Phase 8 completes canonical derived type identity, origin, owner retention, release, native handoff, field policy, recursive member paths, exact unsupported-shape blockers, subordinate plan facets, lifecycle actions, and cross-backend edit validation before lowering | `tests/wrapper_codegen/test_phase8_derived_types.py`, `tests/semantics/conversion/fortran/test_fortran_conversion_procedures_and_interfaces.py::test_procedure_local_derived_type_rename_uses_origin_type_identity`, `tests/wrapper_codegen/printers/test_pyi_printer_imports_and_packages.py` |
| Phase 9 completes class registration, constructor kind and lifecycle, method ownership and invocation, exact overload predicates, base ordering, inherited fields, and closed scalar polymorphic variants before lowering; both backends consume the same class/function plans | `tests/wrapper_codegen/test_phase9_class_surfaces.py`, `tests/semantics/conversion/pyi/test_classes_and_overloads.py`, `derived_types/test_phase9_bound_constructors.py`, `naming/test_phase9_class_overloads.py` |
| Default and keyword construction, explicit bound construction, exact constructor/method overloads, borrowed-child finalization, extension inheritance, and scalar polymorphic input run through the direct wrapper-plan class path | `derived_types/test_constructors_and_finalizers.py`, `derived_types/test_phase9_bound_constructors.py`, `naming/test_phase9_class_overloads.py`, `derived_types/test_borrowed_finalizers.py`, `derived_types/test_inheritance.py`, `derived_types/test_derived_type_methods.py` |
| Reduced derived procedure boundaries replay passing legacy/source behavior through direct plans for required and optional wrapper inputs, exact-type rejection, in-place and caller-supplied output identity, ordinary, `sequence`, and `bind(C)` exact typed native value copies, direct and hidden owned results, checked allocation, conversion cleanup, and exactly-once owner finalization | `derived_types/test_phase8_derived_plan.py::test_scalar_derived_objects_use_canonical_plan`, `derived_types/test_phase8_derived_plan.py::test_value_copy_and_optional_derived_inputs_match_source_oracle`, `derived_types/test_scalar_derived_actual_dummy_matrix.py::test_sequence_derived_value_uses_the_same_typed_opaque_call_path`, `derived_types/test_phase8_derived_plan.py::test_borrowed_child_retains_owner_and_finalizes_exactly_once`, `tests/wrapper_codegen/test_phase8_derived_types.py::test_mixed_derived_results_check_allocation_and_own_every_failure_path_before_scalar_conversion` |
| Plain non-target module objects use live typed member proxies while `Aliased` objects use direct addresses; both retain the module, reject module replacement, and expose live scalar, fixed-string, ordinary-array, nested-derived, allocatable-handle, and pointer-handle fields with completed getter/setter and parent-owner behavior. Detached whole-object `Snapshot[T]` is removed | `derived_types/test_phase8_derived_plan.py::test_plain_module_derived_proxy_reads_and_writes_live_members`, `derived_types/test_phase8_derived_plan.py::test_aliased_module_derived_object_uses_direct_live_field_handles`, `derived_types/test_phase8_derived_plan.py::test_fixed_string_fields_use_canonical_plan`, `derived_types/test_phase8_derived_plan.py::test_pointer_field_descriptor_views_use_canonical_plan` |
| Every wrapper build uses completed policy and the canonical wrapper-plan generator; dependency isolation is structural, while unsupported derived shapes retain exact policy blockers | `derived_types/test_phase8_derived_plan.py::test_scalar_derived_objects_use_canonical_plan`, `callbacks/test_all_callback_shapes.py::test_immediate_callbacks_cover_all_supported_argument_shapes`, `derived_types/test_phase9_bound_constructors.py::test_bound_constructor_replaces_field_initialization_with_direct_pass_projection`, `tests/wrapper_codegen/test_phase0b_contracts.py::test_wrapper_build_pipeline_imports_canonical_generator`, `tests/wrapper_codegen/test_phase8_derived_types.py::test_unsupported_derived_shapes_fail_on_exact_completed_policy_blockers` |

## Build From Source

- `build_from_source/test_build_modes.py`
- `build_from_source/test_compiler_verbose.py`
- `build_from_source/test_source_generated_pyi_contracts.py`
- `build_from_source/test_runtime_abi.py`

## Build From `.pyi`

- `build_from_pyi/test_contract_package_runtime.py`
- `build_from_pyi/test_pyi_wrapper_builds.py`

## Multiple Files

- `multiple_files/test_multi_source_builds.py`

## External Routines

- `external_routines/test_external_procedures.py`

## Real Libraries

- `real_libraries/test_real_blas_lapack.py`
- `real_libraries/test_stage7_native_bundles.py`

## Edit `.pyi` Contracts

- `edit_pyi_contracts/test_native_order_contracts.py`
- `edit_pyi_contracts/test_ownership_contracts.py`
- `edit_pyi_contracts/test_policy_dispatch_contracts.py`
- `edit_pyi_contracts/test_surface_edit_contracts.py`
- `edit_pyi_contracts/test_visibility_contracts.py`

## Arrays

- `arrays/test_array_contracts.py`
- `arrays/test_array_results.py`
- `arrays/test_assumed_rank_arrays.py`
- `arrays/test_array_generated_pyi_contracts.py`
- `arrays/test_multidimensional_arrays.py`

## Scalars

- `scalars/test_fortran_enums.py`
- `scalars/test_scalar_boundary_plan.py`
- `scalars/test_scalar_generated_pyi_contracts.py`
- `scalars/test_scalar_kinds.py`
- `scalars/test_value_and_bind_c.py`
- `scalars/test_verified_baseline.py`

## Function Calls

- `function_calls/test_function_call_generated_pyi_contracts.py`
- `function_calls/test_native_call_examples.py`
- `function_calls/test_optional_arguments.py`
- `function_calls/test_output_arguments.py`
- `function_calls/test_scalar_writeback_plan.py`

## Strings

- `strings/test_character_arguments.py`
- `strings/test_character_edge_cases.py`
- `strings/test_string_generated_pyi_contracts.py`

## Derived Types

- `derived_types/test_borrowed_finalizers.py`
- `derived_types/test_constructors_and_finalizers.py`
- `derived_types/test_derived_layout.py`
- `derived_types/test_phase8_derived_plan.py`
- `derived_types/test_derived_type_boundaries.py`
- `derived_types/test_derived_type_methods.py`
- `derived_types/test_derived_type_generated_pyi_contracts.py`
- `derived_types/test_inheritance.py`
- `derived_types/test_pointers.py`

## Callbacks

- `callbacks/test_all_callback_shapes.py`
- `callbacks/test_array_callbacks.py`
- `callbacks/test_derived_callbacks.py`
- `callbacks/test_callback_generated_pyi_contracts.py`
- `callbacks/test_scalar_callbacks.py`

## Module State

- `module_state/test_allocatable_replacement.py`
- `module_state/test_scalar_module_variable_plan.py`
- `module_state/test_allocatable_views.py`
- `module_state/test_common_blocks.py`
- `module_state/test_module_state_generated_pyi_contracts.py`
- `module_state/test_module_state.py`

## Runtime Behavior

- `runtime_behavior/test_runtime_behavior_generated_pyi_contracts.py`
- `runtime_behavior/test_openmp_runtime.py`
- `runtime_behavior/test_runtime_policies.py`
- `runtime_behavior/test_runtime_recursion.py`

## Naming

- `naming/test_defined_operators.py`
- `naming/test_naming_generated_pyi_contracts.py`
- `naming/test_generic_interfaces.py`
- `naming/test_visibility_naming.py`

## Layout Rules

- `layout_rules/test_wrapper_guide_layout.py`
- `tests/architecture/test_dependency_boundaries.py` for source dependency and codegen-structure rules
