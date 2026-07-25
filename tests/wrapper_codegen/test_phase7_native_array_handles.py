"""Phase 7 typed native-array handle and descriptor plan coverage."""

from __future__ import annotations

import pytest

from tests._shared.ownership_policy_support import parse_pyi_text
from x2py.semantics.ownership import CodegenAction, ObjectKind, PythonBarrierAction
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    ArgumentHandoffMode,
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayOperation,
    NativeArrayOutputProjection,
    NativeArrayResultAllocation,
    NativeArraySourceKind,
    NativeDescriptorHandoffABI,
)
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _phase7_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import (
    Addr,
    Allocatable,
    Annotated,
    Arg,
    Float64,
    Int32,
    MaybeUnallocated,
    Pointer,
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

def replace_names(
    names: Allocatable[String[:][:]],
) -> Returns["names", Allocatable[String[:][:]]]: ...
""",
        module_name="phase7_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def _module_handle_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Aliased, Allocatable, Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, String

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
        module_name="phase7_module_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_phase7_keeps_datatype_specific_state_under_argument_and_result_plans():
    plan = _phase7_plan()
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
    assert NativeArrayOperation.ELEMENT_LENGTH in replacement_names.native_array_handle.operations
    assert plan.required_headers == ("ISO_Fortran_binding.h",)


def test_phase7_module_variables_own_borrowed_handle_plans_and_operation_sets():
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


def test_phase7_deferred_character_module_handles_use_runtime_element_length():
    artifacts = WrapperCodeGenerator().generate(_module_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "bind_c_module_names_element_length()" in c_source
    assert '"elem_len", (unsigned long long)(bind_c_module_names_element_length())' in c_source
    assert "function bind_c_module_names_element_length() result(result)" in bridge_source
    assert "result = len(native_module_names, kind=c_int64_t)" in bridge_source


def test_phase7_plain_module_allocatable_uses_standard_descriptor_callback_without_copy():
    artifacts = WrapperCodeGenerator().generate(_module_handle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void (*callback)(CFI_cdesc_t *, void *)" in c_source
    assert "x2py_module_phase7_module_handles_plain_allocatable_descriptor_callback" in c_source
    assert "descriptor->base_addr" in c_source
    assert "Py_BuildValue" in c_source
    assert "subroutine bind_c_plain_allocatable_descriptor(" in bridge_source
    assert 'bind(c, name="bind_c_plain_allocatable_descriptor")' in bridge_source
    assert "type(c_funptr), value :: callback_address" in bridge_source
    assert "procedure(x2py_plain_allocatable_descriptor_consumer), pointer :: callback" in bridge_source
    assert "call callback(native_plain_allocatable, context)" in bridge_source


def test_phase7_generated_artifacts_follow_one_typed_action_vocabulary():
    artifacts = WrapperCodeGenerator().generate(_phase7_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert artifacts.artifacts.required_headers == ("ISO_Fortran_binding.h",)
    assert '"_native_array_actual_argument_for_binding_positional"' in c_source
    assert '"_native_array_descriptor_argument_for_binding_positional"' in c_source
    assert '"_native_array_descriptor_handoff_for_binding_positional"' in c_source
    assert '"_native_array_handle_from_generated_ops"' in c_source
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
    assert "call x2py_collect_allocatable_array_result(native_maybe_make(n), result)" in bridge_source
    assert "if (allocated(value)) then" in bridge_source
    assert "call move_alloc(value, result)" in bridge_source
    assert "bool bind_c_owned_result_73146804_allocated(CFI_cdesc_t * result);" in c_source
    assert "return PyBool_FromLong(bind_c_owned_result_73146804_allocated(owner_descriptor));" in c_source
    assert "bind_c_owned_result_73146804_deallocate(owner_descriptor);" in c_source
    assert "bind_c_owned_result_73146804_destroy(owner_descriptor);" in c_source
    assert "bind_c_owned_result_73146804_shape(owner_descriptor, &extent_0);" in c_source
    assert "character(kind=c_char, len=:), allocatable :: value_value" in bridge_source
    assert "result_itemsize" in c_source
    assert "CFI_type_char" in c_source
    assert "character(kind=c_char, len=:), allocatable, dimension(:) :: names" in bridge_source


def test_phase7_numeric_owned_result_defaults_to_assignment_then_move_alloc():
    bridge_source = next(
        source.text
        for source in WrapperCodeGenerator().generate(_phase7_plan()).sources
        if source.path.suffix == ".f90"
    )
    start = bridge_source.index("subroutine bind_c_make(")
    end = bridge_source.index("end subroutine", start)
    procedure = bridge_source[start:end]

    assert "real(c_double), allocatable, dimension(:), intent(out) :: result" in procedure
    assert "real(c_double), allocatable, dimension(:) :: result_value" in procedure
    assert "result_value = native_make(n)" in procedure
    assert "if (allocated(result_value)) then" in procedure
    assert "call move_alloc(result_value, result)" in procedure
    assert "if (allocated(result)) then" in procedure
    assert "deallocate(result)" in procedure
    assert "call x2py_collect_allocatable_array_result(native_make(n), result)" not in procedure
    assert "result = result_value" not in procedure
    assert "function bind_c_owned_result_73146804_allocated(" in bridge_source
    assert "real(c_double), allocatable, dimension(:), intent(in) :: result" in bridge_source
    assert "state = allocated(result)" in bridge_source
    assert "subroutine bind_c_owned_result_73146804_deallocate(" in bridge_source
    assert "real(c_double), allocatable, dimension(:), intent(inout) :: result" in bridge_source
    assert "subroutine bind_c_owned_result_73146804_destroy(" in bridge_source


def test_phase7_maybe_unallocated_owned_result_uses_collector_without_local_assignment():
    bridge_source = next(
        source.text
        for source in WrapperCodeGenerator().generate(_phase7_plan()).sources
        if source.path.suffix == ".f90"
    )
    start = bridge_source.index("subroutine bind_c_maybe_make(")
    end = bridge_source.index("end subroutine", start)
    procedure = bridge_source[start:end]

    assert "real(c_double), allocatable, dimension(:), intent(out) :: result" in procedure
    assert "call x2py_collect_allocatable_array_result(native_maybe_make(n), result)" in procedure
    assert "real(c_double), allocatable, dimension(:) :: value" in procedure
    assert "if (allocated(value)) then" in procedure
    assert "call move_alloc(value, result)" in procedure
    assert "if (allocated(result)) then" in procedure
    assert "deallocate(result)" in procedure
    assert "result_value = native_make(n)" not in procedure
    assert "call move_alloc(result_value, result)" not in procedure
    assert "result = result_value" not in procedure
    assert "subroutine x2py_collect_allocatable_array_result(" in procedure


def test_phase7_maybe_unallocated_is_only_valid_on_direct_allocatable_array_results():
    module = parse_pyi_text(
        """
from x2py.contracts import Allocatable, Annotated, Float64, MaybeUnallocated

def invalid_argument(values: Annotated[Allocatable[Float64[:]], MaybeUnallocated]) -> Float64: ...
""",
        module_name="invalid_maybe_unallocated",
    )

    with pytest.raises(ValueError, match="MaybeUnallocated metadata"):
        complete_semantic_policies(module)


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("required_presence", "inconsistent-native-descriptor-presence"),
        ("projected_facts", "invalid-direct-native-descriptor-roles"),
        ("owned_storage", "invalid-owned-native-descriptor-roles"),
        ("operation", "incomplete-native-array-operations"),
        ("header", "inconsistent-required-headers"),
    ],
)
def test_phase7_plan_edits_fail_central_validation(edit: str, diagnostic: str):
    plan = _phase7_plan()
    functions = _functions(plan)
    if edit == "required_presence":
        functions["alloc"].arguments[0].native_array_handle.handoff.presence_role = "edited:present"
    elif edit == "projected_facts":
        functions["replace"].arguments[0].native_array_handle.handoff.extent_roles = ("edited:extent",)
    elif edit == "owned_storage":
        functions["make"].results[0].native_array_handle.handoff.owner_storage_role = None
    elif edit == "operation":
        functions["pointer"].arguments[0].native_array_handle.operations = ()
    else:
        plan.required_headers = ()

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_phase7_plain_module_descriptor_view_requires_matching_completed_interop():
    plan = _module_handle_plan()
    plain = next(variable for variable in plan.namespaces[0].variables if variable.symbol_name == "plain_allocatable")
    assert plain.native_array_handle is not None
    plain.native_array_handle.descriptor_interop = NativeArrayDescriptorInterop.NONE
    plain.native_array_handle.required_headers = ()

    with pytest.raises(ValueError, match="missing-module-allocatable-descriptor-interop"):
        WrapperCodeGenerator().generate(plan)
