"""Typed native-array handle and descriptor planning across storage owners."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.ownership import CodegenAction, ObjectKind, PythonBarrierAction
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy_models import (
    ArgumentHandoffMode,
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayDefaultConstruction,
    NativeArrayDestroyBehavior,
    NativeArrayOperation,
    NativeArrayOutputProjection,
    NativeArrayRelease,
    NativeArrayResultAllocation,
    NativeArraySourceKind,
    NativeDescriptorHandoffABI,
)
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


def _native_handle_plan():
    module = parse_pyi_text(
        """
from prik.contracts import (
    Addr,
    Allocatable,
    Annotated,
    Arg,
    Float64,
    Int32,
    MaybeUnallocated,
    Pointer,
    PointerPolicy,
    Return,
    Returns,
    String,
    native_call,
)

def normal(values: Float64[:]) -> Float64: ...
def alloc(values: Allocatable[Float64[:]]) -> Float64: ...
def pointer(values: Pointer[Float64[:]]) -> Float64: ...
def optional(values: Allocatable[Float64[:]] | None = ...) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def replace(
    values: Allocatable[Float64[:]],
    mode: Int32,
) -> Returns["values", Allocatable[Float64[:]]]: ...

@native_call([Addr(Arg(0))])
def make(n: Int32) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0))])
def maybe_make(n: Int32) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_matrix(n: Int32, m: Int32) -> Allocatable[Float64[:, :]]: ...

@native_call([Arg(0), Allocatable(Return("value", 0))])
def deferred(text: String) -> String | None: ...

def make_names() -> Allocatable[String[:][:]]: ...

def make_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...

@native_call([Arg(0), Return("selected", 0)])
def select_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...

def make_managed_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="wrapper",
        lifetime="wrapper",
        deallocation="deallocate_resize",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="allocate_resize",
        aliasing="descriptor",
        mutability="mutable",
    ),
]: ...

def replace_names(
    names: Allocatable[String[:][:]],
) -> Returns["names", Allocatable[String[:][:]]]: ...
""",
        module_name="memory_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def _generated_c_function(source: str, name: str) -> str:
    signature = f"static PyObject * {name}(PyObject * self, PyObject * args) {{"
    start = source.index(signature)
    end = source.index("\n}\n", start) + len("\n}\n")
    return source[start:end]


def _module_handle_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Allocatable, Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, String

module_allocatable: Annotated[Allocatable[Float64[:]], Aliased]
plain_allocatable: Allocatable[Float64[:]]
module_names: Annotated[Allocatable[String[:][:]], Aliased]
module_pointer: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]
""",
        module_name="memory_module_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_native_handle_plans_keep_datatype_specific_state():
    plan = _native_handle_plan()
    functions = _functions(plan)

    normal = functions["normal"].arguments[0]
    assert normal.object_kind is ObjectKind.NUMPY_ARRAY
    assert normal.native_array_handle is None
    assert normal.native_array_actual is not None
    assert normal.native_array_actual.accepted_sources == (
        NativeArraySourceKind.NDARRAY,
        NativeArraySourceKind.ALLOCATABLE_HANDLE,
        NativeArraySourceKind.POINTER_HANDLE,
    )
    assert normal.native_array_actual.require_contiguous is True
    assert normal.bridge.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER
    assert normal.array is normal.native_call_slot.array

    alloc = functions["alloc"].arguments[0]
    pointer = functions["pointer"].arguments[0]
    for argument, descriptor_kind in (
        (alloc, NativeArrayDescriptorKind.ALLOCATABLE),
        (pointer, NativeArrayDescriptorKind.POINTER),
    ):
        handle = argument.native_array_handle
        assert handle is not None
        assert handle is argument.native_call_slot.native_array_handle
        assert handle.descriptor_kind is descriptor_kind
        assert handle.handoff.abi is NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL
        assert handle.default_handle.construction is NativeArrayDefaultConstruction.FACT_PACKED_EMPTY
        assert handle.default_handle.descriptor_ownership is NativeArrayDescriptorOwnership.OWNED
        assert handle.default_handle.owner_storage_role is None
        assert NativeArrayOperation.DESTROY in handle.default_handle.operations
        assert len(handle.handoff.extent_roles) == handle.array.rank == 1
        assert argument.binding.python_action is PythonBarrierAction.WRAPPER_INSTANCE
        assert argument.bridge.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR

    optional = functions["optional"].arguments[0]
    assert optional.native_array_handle is not None
    assert optional.native_array_handle.optional_absent is True
    assert optional.native_array_handle.handoff.presence_role == optional.bridge.presence_role
    assert alloc.native_array_handle is not None
    assert alloc.native_array_handle.handoff.presence_role is None

    replacement = functions["replace"].arguments[0]
    assert replacement.native_array_handle is not None
    assert replacement.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
    assert replacement.native_array_handle.output_projection is NativeArrayOutputProjection.PROJECTED_HANDLE
    assert replacement.native_array_handle.handoff.extent_roles == ()
    assert (
        replacement.native_array_handle.default_handle.construction
        is NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR
    )
    assert replacement.native_array_handle.default_handle.owner_storage_role is not None
    assert NativeArrayOperation.DESTROY in replacement.native_array_handle.default_handle.operations
    assert replacement.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT

    owned = functions["make"].results[0]
    assert owned.native_array_handle is not None
    assert owned.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    assert owned.native_array_handle.descriptor_ownership is NativeArrayDescriptorOwnership.OWNED
    assert owned.native_array_handle.result_allocation is NativeArrayResultAllocation.ALWAYS_ALLOCATED
    assert owned.native_array_handle.handoff.owner_storage_role is not None
    assert NativeArrayOperation.DESTROY in owned.native_array_handle.operations

    maybe_owned = functions["maybe_make"].results[0]
    assert maybe_owned.native_array_handle is not None
    assert maybe_owned.native_array_handle.result_allocation is NativeArrayResultAllocation.MAYBE_UNALLOCATED

    owned_matrix = functions["make_matrix"].results[0]
    assert owned_matrix.native_array_handle is not None
    assert owned_matrix.native_array_handle.array.rank == 2
    assert owned_matrix.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    assert owned_matrix.native_array_handle.descriptor_ownership is NativeArrayDescriptorOwnership.OWNED

    deferred = functions["deferred"].results[0]
    assert deferred.native_array_handle is None
    assert deferred.scalar_descriptor is not None
    assert deferred.scalar_descriptor.runtime_length is True
    assert deferred.scalar_descriptor.presence_role == f"{deferred.owner_path}:present"

    names = functions["make_names"].results[0]
    assert names.native_array_handle is not None
    assert names.datatype_family.value == "string"
    assert names.array.itemsize is None
    assert NativeArrayOperation.ELEMENT_LENGTH in names.native_array_handle.operations
    assert NativeArrayOperation.RESIZE not in names.native_array_handle.operations

    replacement_names = functions["replace_names"].arguments[0]
    assert replacement_names.native_array_handle is not None
    assert replacement_names.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
    assert replacement_names.native_array_handle.default_handle.construction is NativeArrayDefaultConstruction.NONE
    assert NativeArrayOperation.ELEMENT_LENGTH in replacement_names.native_array_handle.operations
    assert plan.required_headers == ("ISO_Fortran_binding.h",)

    pointer_result = functions["make_pointer"].results[0]
    assert pointer_result.native_array_handle is not None
    assert pointer_result.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.POINTER
    assert pointer_result.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    assert pointer_result.native_array_handle.descriptor_ownership is NativeArrayDescriptorOwnership.OWNED
    assert pointer_result.native_array_handle.result_allocation is NativeArrayResultAllocation.NOT_APPLICABLE
    assert pointer_result.native_array_handle.target_lifetime == "module"
    assert NativeArrayOperation.ASSOCIATE in pointer_result.native_array_handle.operations
    assert NativeArrayOperation.ASSOCIATED in pointer_result.native_array_handle.operations
    assert NativeArrayOperation.NULLIFY in pointer_result.native_array_handle.operations
    assert NativeArrayOperation.CONTIGUOUS in pointer_result.native_array_handle.operations
    assert NativeArrayOperation.DESTROY in pointer_result.native_array_handle.operations

    pointer_output = functions["select_pointer"].results[0]
    assert pointer_output.source_kind == "hidden_output"
    assert pointer_output.native_array_handle is not None
    assert pointer_output.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.POINTER
    assert pointer_output.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    assert pointer_output.native_call_slot is not None
    assert pointer_output.native_call_slot.source_kind == "result"

    managed_pointer = functions["make_managed_pointer"].results[0]
    assert managed_pointer.native_array_handle is not None
    assert {
        NativeArrayOperation.ALLOCATE,
        NativeArrayOperation.DEALLOCATE,
        NativeArrayOperation.RESIZE,
    }.issubset(managed_pointer.native_array_handle.operations)


def test_module_variables_use_borrowed_handle_plans_and_operation_sets():
    plan = _module_handle_plan()
    variables = {variable.symbol_name: variable for variable in plan.namespaces[0].variables}
    allocatable = variables["module_allocatable"].native_array_handle
    plain = variables["plain_allocatable"].native_array_handle
    names = variables["module_names"].native_array_handle
    pointer = variables["module_pointer"].native_array_handle

    assert allocatable is not None
    assert plain is not None
    assert names is not None
    assert pointer is not None
    assert allocatable.borrowed is plain.borrowed is names.borrowed is pointer.borrowed is True
    assert allocatable.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert plain.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert names.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert pointer.descriptor_kind is NativeArrayDescriptorKind.POINTER
    assert NativeArrayOperation.DEALLOCATE in allocatable.operations
    assert NativeArrayOperation.RESIZE in allocatable.operations
    assert NativeArrayOperation.NULLIFY in pointer.operations
    assert NativeArrayOperation.ASSOCIATE in pointer.operations
    assert NativeArrayOperation.CONTIGUOUS in pointer.operations
    assert NativeArrayOperation.DESTROY not in allocatable.operations
    assert NativeArrayOperation.ELEMENT_LENGTH in names.operations
    assert NativeArrayOperation.RESIZE not in names.operations
    assert NativeArrayOperation.DESTROY not in pointer.operations
    assert allocatable.required_headers == ()
    assert plain.extraction_action.value == "descriptor_view"
    assert plain.descriptor_interop is NativeArrayDescriptorInterop.MODULE_ALLOCATABLE_C_DESCRIPTOR
    assert plain.required_headers == ("ISO_Fortran_binding.h",)
    assert pointer.required_headers == ("ISO_Fortran_binding.h",)
    assert plan.required_headers == ("ISO_Fortran_binding.h",)


def test_deferred_character_module_handles_use_runtime_element_length():
    artifacts = WrapperCodeGenerator().generate(_module_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "bind_c_module_names_element_length()" in c_source
    assert '"elem_len", (unsigned long long)(bind_c_module_names_element_length())' in c_source
    assert "function bind_c_module_names_element_length() result(result)" in bridge_source
    assert "result = len(native_module_names, kind=c_int64_t)" in bridge_source


def test_generated_native_handle_artifacts_follow_one_typed_action_vocabulary():
    artifacts = WrapperCodeGenerator().generate(_native_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert artifacts.artifacts.required_headers == ("ISO_Fortran_binding.h",)
    assert "prik_array_actual_unpack(" in c_source
    assert '"_native_array_descriptor_argument_for_binding_positional"' in c_source
    assert '"_native_array_descriptor_handoff_for_binding_positional"' in c_source
    assert '"_native_array_handle_from_generated_ops"' in c_source
    assert '"_bind_contract_native_array_handle"' in c_source
    assert "prik_native_array_handle_capsule_new(" in c_source
    assert "prik_native_array_handle_from_capsule(" in c_source
    assert "PRIK_NATIVE_ARRAY_KIND_ALLOCATABLE" in c_source
    assert "PRIK_NATIVE_ARRAY_KIND_POINTER" in c_source
    assert "prik_native_array_handle_release(owner_handle)" in c_source
    assert "bound_values_native_handle = prik_native_array_handle_from_capsule(bound_values_item" in c_source
    assert "prik_bind_default_memory_handles_replace_values" in c_source
    assert "prik_owned_memory_handles_replace_values_destroy" in c_source
    assert "bound_values_default_binder" in c_source
    assert "CFI_CDESC_T(1)" in c_source
    assert "CFI_CDESC_T(2)" in c_source
    assert "real(c_double), allocatable, dimension(:) :: values" in bridge_source
    assert "real(c_double), pointer, dimension(:) :: values" in bridge_source
    assert "real(c_double), allocatable, dimension(:, :) :: result_value" in bridge_source
    optional_start = bridge_source.index("function bind_c_optional(")
    optional_end = bridge_source.index("end function bind_c_optional", optional_start)
    optional_bridge = bridge_source[optional_start:optional_end]
    assert "real(c_double), allocatable, dimension(:) :: values" in optional_bridge
    assert "type(c_ptr), value :: bound_values_present" in optional_bridge
    assert "real(c_double), allocatable, dimension(:), optional :: values" not in optional_bridge
    optional_c_start = c_source.index("static PyObject * wrap_optional(")
    optional_c_end = c_source.index("static PyObject * wrap_replace(", optional_c_start)
    optional_binding = c_source[optional_c_start:optional_c_end]
    assert "} else {" in optional_binding
    assert "bound_values_elem_len = sizeof(double);" in optional_binding
    assert "bound_values_descriptor_rank = 1;" in optional_binding
    assert "bound_values = (CFI_cdesc_t *)&bound_values_storage;" in optional_binding
    assert "result_value = native_make(n)" in bridge_source
    assert "result_value = native_make_matrix(n, m)" in bridge_source
    assert "call prik_collect_allocatable_array_result(native_maybe_make(n), result)" in bridge_source
    assert "if (allocated(value)) then" in bridge_source
    assert "call move_alloc(value, result)" in bridge_source
    assert "allocated(CFI_cdesc_t * result);" in c_source
    assert "_allocated(owner_descriptor));" in c_source
    assert "_deallocate(owner_descriptor);" in c_source
    assert "_destroy(owner_descriptor);" in c_source
    assert "_shape(owner_descriptor, &extent_0);" in c_source
    assert "character(kind=c_char, len=:), allocatable :: value_value" in bridge_source
    assert "result_itemsize" in c_source
    assert "CFI_type_char" in c_source
    assert "character(kind=c_char, len=:), allocatable, dimension(:) :: names" in bridge_source
    assert "result_owner_status = CFI_establish(result, NULL, CFI_attribute_pointer" in c_source
    assert (
        "PRIK_NATIVE_ARRAY_KIND_POINTER, 1, CFI_type_double, sizeof(double), sizeof(CFI_CDESC_T(1)), result" in c_source
    )


def test_constant_owned_handle_operations_do_not_emit_unused_descriptor_locals():
    artifacts = WrapperCodeGenerator().generate(_native_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    for operation in ("aligned", "descriptor", "destroy", "layout", "native_byte_order", "writeable"):
        function = _generated_c_function(
            c_source,
            f"prik_owned_memory_handles_make_return_{operation}",
        )
        assert "owner_handle" in function
        assert "owner_descriptor" not in function

    allocated = _generated_c_function(
        c_source,
        "prik_owned_memory_handles_make_return_allocated",
    )
    assert "owner_descriptor" in allocated


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("required_presence", "inconsistent-native-descriptor-presence"),
        ("projected_facts", "invalid-direct-native-descriptor-roles"),
        ("owned_storage", "invalid-owned-native-descriptor-roles"),
        ("default_storage", "inconsistent-default-handle-owner-storage-role"),
        ("disabled_default", "invalid-disabled-default-handle-policy"),
        ("default_ownership", "invalid-default-handle-descriptor-ownership"),
        ("default_lifecycle", "invalid-default-handle-lifecycle"),
        ("default_operation", "incomplete-default-handle-operations"),
        ("default_roles", "inconsistent-default-handle-operation-roles"),
        ("default_abi", "inconsistent-default-handle-descriptor-abi"),
        ("operation", "incomplete-native-array-operations"),
        ("header", "inconsistent-required-headers"),
    ],
)
def test_native_handle_plan_edits_fail_central_validation(edit: str, diagnostic: str):
    plan = _native_handle_plan()
    functions = _functions(plan)
    if edit == "required_presence":
        functions["alloc"].arguments[0].native_array_handle.handoff.presence_role = "edited:present"
    elif edit == "projected_facts":
        functions["replace"].arguments[0].native_array_handle.handoff.extent_roles = ("edited:extent",)
    elif edit == "owned_storage":
        functions["make"].results[0].native_array_handle.handoff.owner_storage_role = None
    elif edit == "default_storage":
        functions["replace"].arguments[0].native_array_handle.default_handle.owner_storage_role = None
    elif edit == "disabled_default":
        functions["replace_names"].arguments[
            0
        ].native_array_handle.default_handle.release = NativeArrayRelease.WRAPPER_DEALLOC
    elif edit == "default_ownership":
        functions["replace"].arguments[
            0
        ].native_array_handle.default_handle.descriptor_ownership = NativeArrayDescriptorOwnership.BORROWED
    elif edit == "default_lifecycle":
        default = functions["replace"].arguments[0].native_array_handle.default_handle
        default.release = NativeArrayRelease.NONE
        default.destroy_behavior = NativeArrayDestroyBehavior.NONE
    elif edit == "default_operation":
        functions["replace"].arguments[0].native_array_handle.default_handle.operations = ()
    elif edit == "default_roles":
        functions["replace"].arguments[0].native_array_handle.default_handle.operation_roles = ()
    elif edit == "default_abi":
        functions["replace"].arguments[
            0
        ].native_array_handle.handoff.abi = NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL
    elif edit == "operation":
        functions["pointer"].arguments[0].native_array_handle.operations = ()
    else:
        plan.required_headers = ()

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_plain_module_descriptor_view_requires_matching_completed_interop():
    plan = _module_handle_plan()
    plain = next(variable for variable in plan.namespaces[0].variables if variable.symbol_name == "plain_allocatable")
    assert plain.native_array_handle is not None
    plain.native_array_handle.descriptor_interop = NativeArrayDescriptorInterop.NONE
    plain.native_array_handle.required_headers = ()

    with pytest.raises(ValueError, match="missing-module-allocatable-descriptor-interop"):
        WrapperCodeGenerator().generate(plan)
