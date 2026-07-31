"""Cross-feature direct-plan scalar boundary validation."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.ownership import CodegenAction, NativeBarrierAction
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
