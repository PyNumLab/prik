---
title: Language Feature Matrix
audience: users
prerequisites: getting started
related: index.md, c-support.md, ../reference/cli-commands.md, ../reference/diagnostic-codes.md
status: maintained
publication: reviewed
---

# Language Feature Matrix

This matrix is the user-facing support index for native-language features. It
points each feature to its user guide, evidence, and limitations. Start with
[C Support](c-support.md) for the complete C workflow, or the [User
Guide](../guide/index.md) for the broader Fortran workflow.

A row may claim support only when the linked evidence proves that behavior in
the current repository. Runtime wrapper support requires compiled, imported,
and called wrapper tests. Parser or semantic support alone is listed as
inspection-only or partial support.

## At A Glance

PRIK wraps **Fortran and C code**. Fortran supports the broader language
surface; C wrappers support target-probed primitive functions and authored
pointer, array, and string contracts. [C Support](c-support.md) defines that
exact C boundary.

| Capability | Fortran | C |
| --- | --- | --- |
| Primitive arguments and results | Supported for all documented kinds | Supported for target-probed arithmetic and C99 complex types, including `void` results |
| NumPy arrays | Supported with documented rank, shape, layout, stride, and mutation contracts | Supported for ranks 1–15 with primitive non-Boolean elements and C-contiguous storage |
| Strings | Supported for scalars and fixed-width arrays | Supported for rank-zero inputs and caller-owned storage |
| Procedures and API shaping | Functions, subroutines, modules, state, optional arguments, generics, and defined operators | Externally linked functions, output and status projection, renaming, argument reordering, and dtype/rank overloads |
| Pointers and managed storage | Allocatable arrays are supported; pointer arrays are partially supported | One-level primitive pointer parameters support scalar addresses, rank-zero storage, projected results, and arrays |
| Callbacks | Supported for immediate call-scoped use | Unsupported |
| User-defined types and global state | Scalar derived types support fields, methods, constructors, and finalizers; arrays of derived types remain unsupported | `struct`, `union`, and global-state wrappers are unsupported |

The detailed rows below add the owning docs, evidence, and exact limitation for
each feature. Each status group separates Fortran, C, and shared capabilities
where they apply.

## Status Meanings

| Status | Meaning |
| --- | --- |
| Supported | The documented subset has current runtime or inspection evidence. |
| Partially supported | A useful subset is implemented and tested, but important related forms are blocked or deferred. |
| Unsupported | PRIK intentionally blocks the form or has no safe wrapper contract for it yet. |

## Supported Runtime Features

### Fortran

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Primitive scalar and array calls | Supported | [Data types](../guide/data-types.md), [arrays](../guide/arrays.md), [functions](../guide/wrapping-functions.md), [subroutines](../guide/wrapping-subroutines.md) | [Scalar runtime evidence](../../../tests/fortran/data_types/end_to_end/test_scalar_wrapper_parity.py), [array runtime evidence](../../../tests/fortran/arrays/end_to_end/test_array_wrapper_parity.py) | Native scalar arguments require exact NumPy dtypes where documented. |
| Generic procedure interfaces | Supported | [Generic interfaces](../guide/generic-interfaces.md) | [Generic interface tests](../../../tests/fortran/generic_interfaces/end_to_end/test_generic_interfaces.py) | Defined operators and assignment are tracked separately. |
| Defined operators and assignment overloads | Supported | [Defined operators](../guide/wrapping-derived-types.md#defined-operators) | [Defined operator tests](../../../tests/fortran/generic_interfaces/end_to_end/test_defined_operators.py) | Supported operators are those covered by the wrapper guide and runtime tests. |
| Output arguments and multiple results | Supported | [Subroutine projection](../guide/wrapping-subroutines.md) | [Calls and results tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/calls_and_results/end_to_end/test_edited_call_surfaces.py), [function result tests](../../../tests/fortran/functions/end_to_end/test_documented_function_journeys.py) | Tuple ordering and caller-provided array behavior follow the wrapper guide. |
| Optional arguments | Supported | [Optional arguments](../guide/optional-arguments.md) | [Optional argument tests](../../../tests/fortran/optional_arguments/end_to_end/test_optional_runtime.py) | Unsupported optional combinations fail during wrapper planning. |
| Allocatable array handles, descriptor arguments, and owned results | Supported | [Allocatables](../guide/allocatables.md) | [Allocatable runtime tests](../../../tests/fortran/allocatables/end_to_end/test_allocatable_handles.py), [scalar-derived matrix tests](../../../tests/fortran/derived_types/end_to_end/test_scalar_actual_dummy_matrix.py) | Array module/field handles borrow their owner; result handles own persistent descriptor storage. Wrapper-owned scalar-derived allocatables use typed holders; module scalar allocatables use reversible `move_alloc` transactions for compatible dummies. |
| Pointer scalar projections and array handles | Partially supported | [Pointers](../guide/pointers.md) | [Pointer handle tests](../../../tests/fortran/pointers/end_to_end/test_pointer_handles.py), [pointer policy tests](../../../tests/fortran/pointers/policy/test_pointer_ownership_policy.py), [scalar-derived matrix tests](../../../tests/fortran/derived_types/end_to_end/test_scalar_actual_dummy_matrix.py) | Descriptor arguments, module/field handles, strided views, wrapper-owned pointer-array results and outputs, scalar-derived pointer holders, and module pointer reassociation transactions are supported. Target deallocation and writable reassociation remain policy-gated. |
| Array-valued function results | Supported | [Array results](../guide/arrays.md#mutation-and-results) | [Array result tests](../../../tests/fortran/arrays/end_to_end/test_array_results.py) | Ownership and dtype/shape behavior are limited to documented array result forms. |
| NumPy array argument contracts | Supported | [Arrays](../guide/arrays.md) | [Array contract tests](../../../tests/fortran/arrays/end_to_end/test_array_contract_validation.py), [multidimensional tests](../../../tests/fortran/arrays/end_to_end/test_layout_and_strided_arrays.py) | Wrong dtype, rank, shape, contiguity, alignment, or mutability is rejected. |
| Derived-type scalar boundaries and methods | Supported | [Derived types](../guide/wrapping-derived-types.md) | [Derived boundary tests](../../../tests/fortran/derived_types/end_to_end/test_derived_boundaries.py), [method tests](../../../tests/fortran/derived_types/end_to_end/test_type_bound_methods.py) | Derived-type arrays and some polymorphic forms are not included. |
| Default and keyword constructors with finalizers | Supported | [Constructors and finalizers](../guide/wrapping-derived-types.md#key-concepts) | [Constructor/finalizer tests](../../../tests/fortran/derived_types/end_to_end/test_default_constructors_and_finalizers.py), [borrowed finalizer tests](../../../tests/fortran/derived_types/end_to_end/test_borrowed_components.py) | Construction commits ownership only after initialization; borrowed wrappers never run an owning finalizer. |
| Generic constructor interfaces and overloaded runtime initialization | Supported | [Constructors](../guide/wrapping-derived-types.md#custom-constructor) | [Edited class surface tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/functions_and_classes/end_to_end/test_edited_class_surfaces.py), [class policy tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/functions_and_classes/policy/test_class_surface_policy.py) | Candidates require distinguishable completed Python signatures; incomplete or ambiguous sets are blocked before emission. |
| Module variables, constants, saved state, and common-block procedure state | Supported | [Wrapping modules](../guide/wrapping-modules.md) | [Module state tests](../../../tests/fortran/modules/end_to_end/test_module_variables_and_state.py), [scalar-derived matrix tests](../../../tests/fortran/derived_types/end_to_end/test_scalar_actual_dummy_matrix.py), [common-block tests](../../../tests/fortran/modules/end_to_end/test_common_blocks.py) | Common-block storage is not exported as Python variables. Rank-zero derived module objects use direct, scoped, allocation-transaction, or pointer-transaction handoff selected before lowering. `character` module state is supported in every form: a declared-length scalar reads and writes as `str` at exactly its declared byte width, an `allocatable` or `pointer` scalar reads as a detached `str` or `None`, and arrays reach Python as fixed-width bytes. Only declared-length non-descriptor scalars are writable by assignment; descriptor scalars are read-only snapshots for numeric and `character` state alike, and arrays are mutated in place through their view or handle rather than rebound. |
| Fortran enum constants | Supported | [Enumerations](../guide/enumerations.md) | [Enum runtime tests](../../../tests/fortran/enumerations/end_to_end/test_enum_runtime.py), [enum semantic tests](../../../tests/fortran/enumerations/semantics/test_enum_semantics.py), [enum diagnostics](../../../tests/fortran/enumerations/parsing/test_enum_diagnostics.py) | No Python `Enum` or `IntEnum` classes are generated. |
| Scalar character arguments, results, and fields | Supported | [Strings](../guide/strings.md) | [Character argument tests](../../../tests/fortran/strings/end_to_end/test_character_boundaries.py), [edge-case tests](../../../tests/fortran/strings/end_to_end/test_character_edge_cases.py) | Character arrays use fixed-width NumPy bytes dtype. Scalar `character` `allocatable` and `pointer` values are supported for `intent(in)`, `intent(out)`, `intent(inout)`, and function results, at deferred (`len=:`) and declared (`len=n`) length; a mutable dummy returns the value the procedure left behind, or `None`. PRIK frees the target it allocated for the call while it can still prove that identity, but never a target the procedure reassociated or the library owns; a procedure that returns a fresh allocation each call leaks unless it frees its own. |
| Character arrays and caller-supplied deferred-length character storage | Supported | [Strings](../guide/strings.md) | [Character edge tests](../../../tests/fortran/strings/end_to_end/test_character_edge_cases.py) | Character arrays use fixed-width NumPy bytes dtype, whose width each accessor reports from the Fortran declaration; Unicode/object arrays are unsupported. Scalar `character` `allocatable` and `pointer` values work for every intent and as function results. A mutable `pointer` dummy that the native procedure reassociates without deallocating orphans the target the adapter allocated for that call. A deferred-length `character(len=:), allocatable` module array does not build under GNU Fortran 11.4, which raises an internal compiler error on that declaration. |
| Scalar kind coverage | Supported | [Data types](../guide/data-types.md) | [Scalar kind tests](../../../tests/fortran/data_types/end_to_end/test_primitive_scalar_runtime.py) | Real and complex storage wider than the target's `long double` is blocked; `real(10)` and C `long double` map to NumPy `longdouble`. All `logical` kinds are supported and adapt to one-byte NumPy Booleans at the boundary. |
| Multi-source builds, Makefiles, verbose mode, and output placement | Supported | [Building the shared library](../guide/building-shared-library.md) | [Multi-source tests](../../../tests/fortran/infrastructure/building/end_to_end/test_multi_source_builds.py), [compiler verbose tests](../../../tests/fortran/infrastructure/building/compiling/test_compiler_verbose.py) | Wrapped project sources compile in dependency order derived from their module/`use` graph, falling back to the given order when a compiled source was not parsed. PRIK does not discover sources you did not name, prebuilt module paths, or external libraries. |
| Visibility, naming, keyword escaping, and collision policy | Supported | [Generic interfaces](../guide/generic-interfaces.md#key-rules) | [Visibility/naming tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/exports_and_modules/end_to_end/test_visibility_naming.py) | Strict mode rejects names that default mode can normalize. |
| Immediate call-scoped Python callbacks | Supported | [Callbacks](../guide/callbacks.md) | [Callback plan tests](../../../tests/fortran/callbacks/codegen/test_callback_planning.py), [scalar callback tests](../../../tests/fortran/callbacks/end_to_end/test_scalar_callbacks.py), [array callback tests](../../../tests/fortran/callbacks/end_to_end/test_array_callbacks.py), [combined shape tests](../../../tests/fortran/callbacks/end_to_end/test_supported_callback_shapes.py) | Direct wrapper-plan generation supports entering-thread callbacks only. Stored, optional, asynchronous, or cross-thread callbacks are unsupported. |
| Runtime error projection, GIL policy, recursion, OpenMP path, and GNU ABI checks | Supported | [Error handling](../guide/error-handling.md) | [Status projection runtime](../../../tests/fortran/error_handling/end_to_end/test_status_projection.py), [status and GIL lowering](../../../tests/fortran/error_handling/codegen/test_status_error_lowering.py), [recursion tests](../../../tests/fortran/error_handling/end_to_end/test_runtime_recursion.py), [OpenMP tests](../../../tests/fortran/error_handling/end_to_end/test_openmp_runtime.py), [ABI tests](../../../tests/fortran/infrastructure/building/end_to_end/test_runtime_compatibility.py) | OpenMP and ABI evidence is compiler/platform-specific; callers still own native synchronization. |
| Fortran source wrapper builds | Supported | [Building the shared library](../guide/building-shared-library.md) | [Build modes](../../../tests/fortran/infrastructure/building/end_to_end/test_source_build_modes.py), [runtime ABI](../../../tests/fortran/infrastructure/building/end_to_end/test_runtime_compatibility.py) | Implemented for ordered Fortran source inputs. |
| `value` arguments and existing `bind(C)` procedures | Supported | [Data types](../guide/data-types.md) | [`value` and `bind(C)` tests](../../../tests/fortran/data_types/end_to_end/test_value_and_bind_c.py) | Existing `bind(C)` support is deliberately ABI-guarded. |
| Opaque `bind(C)` and `sequence` derived-type layout through accessors | Supported | [Derived types](../guide/wrapping-derived-types.md) | [Derived layout tests](../../../tests/fortran/derived_types/end_to_end/test_opaque_layout.py) | C struct layout access is not enabled. |

### C

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Primitive scalar calls | Supported | [Build a scalar C function](c-support.md#build-a-scalar-c-function) | [C scalar runtime](../../../tests/c/primitive_scalars/end_to_end/test_direct_c_scalar_matrix.py) | Covers target-probed arithmetic and C99 complex scalars, including `void` results. Public NumPy dtypes remain canonical while the native boundary preserves exact C scalar identities. |
| One-level primitive pointer parameters | Supported | [Choose the pointer contract](c-support.md#choose-the-pointer-contract) | [Pointer contracts](../../../tests/c/primitive_pointers/end_to_end/test_direct_c_pointer_contracts.py) | Covers scalar addresses, rank-zero storage, projected results, and C-contiguous arrays. Pointer results, multi-level pointers, and nullable or ownership-sensitive pointers remain unsupported. |
| NumPy array arguments | Supported | [Author a contract for pointers and arrays](c-support.md#author-a-contract-for-pointers-and-arrays) | [Pointer contracts](../../../tests/c/primitive_pointers/end_to_end/test_direct_c_pointer_contracts.py) | Covers ranks 1–15 with primitive non-Boolean elements and C-contiguous storage. PRIK validates dtype, rank, shape, layout, and writeability before the call. |
| Rank-zero C strings | Supported | [Pass C strings](c-support.md#pass-c-strings) | [String contracts](../../../tests/c/primitive_strings/end_to_end/test_direct_c_strings.py) | Covers string inputs and caller-owned rank-zero storage. Arrays of strings remain unsupported. |
| Output, status, naming, and overload projection | Supported | [Rename and reorder arguments](c-support.md#rename-reorder-and-address-arguments), [return several outputs](c-support.md#return-several-c-outputs), [raise Python exceptions](c-support.md#hide-native-outputs-and-raise-python-exceptions), [overload sets](c-support.md#present-several-c-symbols-as-one-python-name) | [Projection and overload evidence](../../../tests/c/primitive_scalars/end_to_end/test_direct_c_runtime.py), [hidden-output and status evidence](../../../tests/c/primitive_strings/end_to_end/test_direct_c_strings.py) | Covers hidden outputs, status projection, symbol renaming, argument reordering, typed literals, derived lengths and shapes, and overload sets distinguishable by dtype and rank. |
| C source, header, and semantic-contract builds | Supported | [Build and inspect APIs](c-support.md#build-and-inspect-apis) | [C build pipeline](../../../tests/c/infrastructure/building/pipeline/test_c_build_cli.py), [collision forwarder](../../../tests/c/symbol_collisions/end_to_end/test_collision_adapter_runtime.py) | Supports ordinary compiler preprocessing, including standard includes and macros, plus explicit native dependencies. A selected collision adapter isolates a binding-header name conflict; it is not an ABI fallback. |

## Inspection And Contract Support

### Fortran

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Fortran parse, semantic IR, and `.pyi` inspection | Supported | [CLI commands](../reference/cli-commands.md#parse-and-semantics) | [Fortran parser fixtures](../../../tests/fortran/infrastructure/parsing/test_fortran_fixture_suite.py), [Fortran semantic tests](../../../tests/fortran/infrastructure/semantic_ir/semantics/) | Inspection support does not by itself prove runtime wrapper support. |
| Semantic `.pyi` wrapper builds from explicit native artifacts | Partially supported | [Editing `.pyi` contracts](../reference/pyi-contracts/index.md) | [format and authoritative-input tests](../../../tests/fortran/infrastructure/semantic_pyi/), [multi-source contract tests](../../../tests/fortran/infrastructure/building/end_to_end/test_multi_source_builds.py), [native build plan tests](../../../tests/fortran/infrastructure/building/end_to_end/test_source_build_modes.py) | Source/generated/modified multi-source package parity is covered. Support is limited to contract forms with linked build evidence; no general parity claim is made for every source-supported Fortran feature. |
| Scalar inheritance and polymorphic dispatch | Partially supported | [Inheritance and polymorphic input](../guide/wrapping-derived-types.md#inheritance-and-polymorphic-input-dispatch) | [Inheritance tests](../../../tests/fortran/derived_types/end_to_end/test_inheritance_and_polymorphism.py) | Abstract types wrap as non-instantiable Python base classes and deferred bindings resolve through the caller's concrete type. Polymorphic results, mutable dummies, arrays, allocatable/pointer scalars, and `class(*)` are blocked. |
| Assumed-size, assumed-rank, and lower-bound array contracts | Partially supported | [Arrays](../guide/arrays.md) | [Assumed-rank tests](../../../tests/fortran/arrays/end_to_end/test_assumed_rank_arrays.py) | Assumed type and derived-type arrays remain blocked. Character arrays require fixed-width NumPy bytes dtype. |

### C

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| C parse, semantic IR, and `.pyi` inspection | Partially supported | [C Support](c-support.md#build-and-inspect-apis) | [C parser fixtures](../../../tests/c/infrastructure/parsing/test_c_fixture_suite.py), [C semantic tests](../../../tests/c/infrastructure/semantic_ir/semantics/) | Parser coverage is broader than the supported C wrapper subset; parser acceptance is not a runtime-support claim. |

### Shared

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Generated wrapper API documentation | Partially supported | [Editing `.pyi` contracts](../reference/pyi-contracts/index.md) | [Documentation reference checks](../../../tests/docs/test_reference_and_codebase_map.py), [semantic contract tests](../../../tests/fortran/infrastructure/semantic_pyi/semantics/test_calls_and_projections.py) | Published guides cover the shared generated surface; automatic per-symbol reference generation has not been selected. |

## Unsupported Or Blocked Forms

PRIK normally blocks these before code generation and reports the boundary and
the reason, rather than emitting a wrapper that could lose precision, corrupt
memory, or outlive its native storage. Parameterized derived types are the
documented diagnostic-stage exception below.

### Fortran

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Unproved pointer lifetime and ownership-changing operations | Unsupported | [Pointer safety](../guide/pointers.md#safety-checklist) | [Pointer policy tests](../../../tests/fortran/pointers/policy/test_pointer_ownership_policy.py), [pointer runtime tests](../../../tests/fortran/pointers/runtime/test_pointer_handle_protocol.py) | Native targets must outlive every handle use; allocation, target deallocation, resize, and writable reassociation require explicit completed policy. |
| Persistent callbacks and procedure pointers | Unsupported | [Callback limitations](../guide/callbacks.md#important-limitations) | [Callback policy tests](../../../tests/fortran/callbacks/policy/test_callback_policy.py), [scalar callback tests](../../../tests/fortran/callbacks/end_to_end/test_scalar_callbacks.py) | Callbacks are valid only during the wrapped call. |
| Advanced multi-source dependency discovery and external-library integration | Unsupported | [Multiple source files](../guide/building-shared-library.md#multiple-source-files) | [Multi-source tests](../../../tests/fortran/infrastructure/building/end_to_end/test_multi_source_builds.py) | PRIK does not discover sources you did not name, prebuilt module search paths, or external libraries. Dependency ordering among the sources it parses is supported. |
| Blocked array forms | Unsupported | [Arrays](../guide/arrays.md) | [Array semantic tests](../../../tests/fortran/arrays/semantics/test_array_semantics.py), [diagnostics](../reference/diagnostic-codes.md) | Assumed type `type(*)`, arrays of derived types, and character arrays not representable as fixed-width bytes need missing runtime contracts. |
| Unsupported polymorphic forms | Unsupported | [Inheritance limits](../guide/wrapping-derived-types.md#inheritance-and-polymorphic-input-dispatch) | [Inheritance tests](../../../tests/fortran/derived_types/codegen/test_class_surfaces.py) | Results, mutable dummies, arrays, polymorphic allocatable/pointer scalars, and `class(*)` are blocked. Abstract types and deferred bindings are supported. |
| Ambiguous or incomplete constructor overload sets | Unsupported | [Constructor limitations](../guide/wrapping-derived-types.md#custom-constructor) | [Constructor semantic tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/functions_and_classes/semantics/test_method_and_constructor_contracts.py), [class-plan validation tests](../../../tests/fortran/infrastructure/semantic_pyi/contracts/functions_and_classes/policy/test_class_surface_policy.py) | Candidates must have distinguishable exact runtime signatures and compatible native-owner lifecycles. A Fortran `interface <typename>` is wrapped as the type's overloaded constructor. |
| Parameterized derived types | Unsupported | [Fortran support boundaries](fortran-support.md#important-boundaries) | [Parameterized-declaration parsing](../../../tests/fortran/derived_types/parsing/test_parameterized_derived_types.py) | The parser preserves the declaration and its parameter expressions, but wrapper semantics do not model type parameters. A build can currently reach compiler probing and surface a raw compiler diagnostic instead of a PRIK diagnostic. |
| Real and complex storage wider than the target `long double` | Unsupported | [Datatype limits](../guide/data-types.md#unsupported-widths-and-forms) | [Scalar kind tests](../../../tests/fortran/data_types/semantics/test_fortran_scalar_semantics.py) | PRIK compares the compiler-measured mantissa against the target's `long double` instead of trusting storage size, which alone cannot separate x87 extended precision from IEEE binary128. `real(16)` is blocked on an x87 target; `real(10)` and C `long double` are supported. |

### C

| Feature | Status | User docs | Evidence | Limitations |
| --- | --- | --- | --- | --- |
| Callbacks and function pointers | Unsupported | [C Support](c-support.md#current-limits) | [C policy blockers](../../../tests/c/primitive_scalars/policy/test_direct_c_policy.py), [prebuild callback rejection](../../../tests/c/infrastructure/building/pipeline/test_c_direct_rejections.py) | C callback and function-pointer parameters may be parsed, but wrapper policy rejects them before planning. |
| Aggregates, global state, and enum constants | Unsupported | [C Support](c-support.md#current-limits) | [Aggregate, global-state, and enum rejection](../../../tests/c/infrastructure/building/pipeline/test_c_direct_rejections.py) | `struct` and `union` wrappers, native global state, and enum constants are not exposed by C wrappers. |
| Variadics, local symbols, qualifiers, and calling conventions | Unsupported | [C Support](c-support.md#current-limits) | [C policy blockers](../../../tests/c/primitive_scalars/policy/test_direct_c_policy.py), [prebuild qualifier and declaration rejection](../../../tests/c/infrastructure/building/pipeline/test_c_direct_rejections.py) | Variadic functions, `static` symbols, `volatile` or `_Atomic` values, and unsupported calling conventions fail before wrapper planning. |
| Pointer results and ownership-sensitive pointers | Unsupported | [C Support](c-support.md#current-limits) | [Pointer policy blockers](../../../tests/c/primitive_scalars/policy/test_direct_c_policy.py), [prebuild raw-address rejection](../../../tests/c/infrastructure/building/pipeline/test_c_direct_rejections.py) | Pointer results, multi-level pointers, raw or nullable pointers, and APIs with retained or ownership-sensitive pointers are unsupported. |
| Unsupported C array and string forms | Unsupported | [C Support](c-support.md#current-limits) | [Array policy blockers](../../../tests/c/primitive_scalars/policy/test_direct_c_policy.py), [string contract blockers](../../../tests/c/primitive_strings/end_to_end/test_direct_c_strings.py) | Arrays of strings, Boolean arrays, native C array declarators, ranks outside 1–15, and non-C-contiguous arrays are unsupported. |
