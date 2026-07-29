"""Direct-plan scalar storage and raw-address boundary lowering."""

from __future__ import annotations

import pytest

from tests._shared.ownership_policy_support import parse_pyi_text
from x2py.semantics.ownership import CodegenAction, NativeBarrierAction, ObjectKind, PythonBarrierAction
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import ArgumentHandoffMode, BridgeDataAction
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _scalar_boundary_plan():
    module = parse_pyi_text(
        """
def storage(x: Float64[()]) -> None: ...
def raw(x: Addr(Float64)) -> None: ...
def direct_storage_result() -> Float64[()]: ...
@native_call([Return("out", 0)])
def hidden_storage_result() -> Float64[()]: ...
""",
        module_name="scalar_boundaries",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_scalar_storage_and_raw_address_plans_keep_explicit_boundary_facts():
    plan = _scalar_boundary_plan()
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    storage_function = functions["storage"]
    raw_function = functions["raw"]
    direct_function = functions["direct_storage_result"]
    hidden_function = functions["hidden_storage_result"]
    storage = storage_function.arguments[0]
    raw = raw_function.arguments[0]
    direct_result = direct_function.results[0]
    hidden_result = hidden_function.results[0]

    assert storage.native_call_slot is storage_function.native_call_slots[storage.native_position]
    assert storage.object_kind is ObjectKind.NUMPY_ARRAY
    assert storage.array.rank == 0
    assert storage.array.category == "scalar_storage"
    assert storage.binding.python_action is PythonBarrierAction.SCALAR_STORAGE
    assert storage.binding.writable is True
    assert storage.bridge.native_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
    assert storage.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
    assert storage.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW
    assert storage.bridge.copy_reason is None
    assert raw.native_call_slot is raw_function.native_call_slots[raw.native_position]
    assert raw.binding.python_action is PythonBarrierAction.RAW_ADDRESS
    assert raw.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert raw.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
    assert raw.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW
    assert raw.bridge.copy_reason is None
    assert direct_result.object_kind is ObjectKind.NUMPY_ARRAY
    assert direct_result.array.rank == 0
    assert direct_result.array.category == "scalar_storage"
    assert direct_result.binding.codegen_action is CodegenAction.COPY_OUT
    assert direct_result.bridge.native_action is NativeBarrierAction.NONE
    assert direct_result.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
    assert hidden_result.object_kind is ObjectKind.NUMPY_ARRAY
    assert hidden_result.array.rank == 0
    assert hidden_result.array.category == "scalar_storage"
    assert hidden_result.binding.codegen_action is CodegenAction.COPY_OUT
    assert hidden_result.bridge.native_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
    assert hidden_result.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION


def test_scalar_storage_and_raw_address_lower_to_direct_named_paths():
    artifacts = WrapperCodeGenerator().generate(_scalar_boundary_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_storage(void * x);" in c_source
    assert "PyArray_TYPE((PyArrayObject *)bound_x_obj) != NPY_FLOAT64" in c_source
    assert "PyArray_NDIM((PyArrayObject *)bound_x_obj) != 0" in c_source
    assert "PyArray_ISNOTSWAPPED((PyArrayObject *)bound_x_obj)" in c_source
    assert "PyArray_ISALIGNED((PyArrayObject *)bound_x_obj)" in c_source
    assert "PyArray_ISWRITEABLE((PyArrayObject *)bound_x_obj)" in c_source
    assert "bound_x = PyArray_DATA((PyArrayObject *)bound_x_obj);" in c_source
    assert "bind_c_storage(bound_x);" in c_source
    assert "void bind_c_raw(void * x);" in c_source
    assert "if (!PyLong_Check(bound_x_obj))" in c_source
    assert "bound_x = PyLong_AsVoidPtr(bound_x_obj);" in c_source
    assert "bind_c_raw(bound_x);" in c_source
    assert "void * bind_c_direct_storage_result(void);" in c_source
    assert "void bind_c_hidden_storage_result(void ** out);" in c_source
    assert c_source.count("PyArray_New(&PyArray_Type, 0, NULL, NPY_FLOAT64") == 2
    assert "bind_c_hidden_storage_result(&out);" in c_source

    assert 'subroutine bind_c_storage(bound_x) bind(c, name="bind_c_storage")' in bridge_source
    assert 'subroutine bind_c_raw(bound_x) bind(c, name="bind_c_raw")' in bridge_source
    assert bridge_source.count("type(c_ptr), value :: bound_x") == 2
    assert bridge_source.count("call c_f_pointer(bound_x, x)") == 2
    assert "call native_storage(x)" in bridge_source
    assert "call native_raw(x)" in bridge_source
    assert (
        'function bind_c_direct_storage_result() result(result) bind(c, name="bind_c_direct_storage_result")'
        in bridge_source
    )
    assert 'subroutine bind_c_hidden_storage_result(out) bind(c, name="bind_c_hidden_storage_result")' in bridge_source
    assert "real(c_double) :: result_value" in bridge_source
    assert "real(c_double), pointer :: result_copy" in bridge_source
    assert "call c_f_pointer(result, result_copy)" in bridge_source
    assert "result_copy = result_value" in bridge_source
    assert "real(c_double) :: out_value" in bridge_source
    assert "real(c_double), pointer :: out_copy" in bridge_source
    assert "call c_f_pointer(out, out_copy)" in bridge_source
    assert "out_copy = out_value" in bridge_source
    assert "dimension()" not in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("native_action", "invalid-scalar-storage-native-action"),
        ("handoff", "invalid-scalar-storage-handoff-mode"),
        ("data_action", "invalid-scalar-storage-data-action"),
        ("codegen", "invalid-scalar-storage-codegen-action"),
        ("array", "invalid-scalar-storage-array"),
    ],
)
def test_scalar_address_handoff_plan_edits_fail_before_lowering(edit, diagnostic):
    plan = _scalar_boundary_plan()
    storage = plan.namespaces[0].functions[0].arguments[0]
    if edit == "native_action":
        storage.bridge.native_action = NativeBarrierAction.PASS_VALUE
    elif edit == "handoff":
        storage.bridge.handoff_mode = ArgumentHandoffMode.VALUE
    elif edit == "data_action":
        storage.bridge.data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.bridge.copy_reason = "edited scalar-storage copy"
        storage.native_call_slot.bridge_data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.native_call_slot.bridge_copy_reason = "edited scalar-storage copy"
    elif edit == "codegen":
        storage.binding.codegen_action = CodegenAction.SNAPSHOT_COPY
    else:
        storage.array.rank = 1

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


@pytest.mark.parametrize(
    ("action", "reason", "diagnostic"),
    [
        (BridgeDataAction.COPY_REPRESENTATION, None, "missing-bridge-copy-reason"),
        (BridgeDataAction.ASSOCIATE_VIEW, "unnecessary second copy", "unexpected-bridge-copy-reason"),
        (BridgeDataAction.BLOCKED, None, "blocked-bridge-data-action"),
    ],
)
def test_bridge_data_action_invariant_rejects_unjustified_or_blocked_plans(action, reason, diagnostic):
    plan = _scalar_boundary_plan()
    function = plan.namespaces[0].functions[0]
    storage = function.arguments[0]
    storage.bridge.data_action = action
    storage.bridge.copy_reason = reason
    storage.native_call_slot.bridge_data_action = action
    storage.native_call_slot.bridge_copy_reason = reason
    assert function.native_call_slots[storage.native_position] is storage.native_call_slot

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_scalar_copy_in_out_reuses_one_binding_local_without_bridge_copy():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="one_copy",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    value = plan.namespaces[0].functions[0].arguments[0]
    assert value.bridge.data_action is BridgeDataAction.DIRECT_TRANSFER
    assert value.bridge.copy_reason is None

    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert c_source.count("int32_t bound_value;") == 1
    assert "x2py_scalar_unpack(bound_value_obj, NPY_INT32, &bound_value)" in c_source
    assert "bind_c_bump(&bound_value);" in c_source
    assert "PyObject * result_obj = NULL;" in c_source
    assert "result_obj = x2py_scalar_to_python(NPY_INT32, &bound_value);" in c_source
    assert "integer(c_int32_t) :: value" in bridge_source
    assert "call native_bump(value)" in bridge_source
    assert "value =" not in bridge_source
    assert "value_input" not in bridge_source
