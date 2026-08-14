"""Direct-return plus hidden-output scalar aggregation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import CodegenAction, NativeBarrierAction
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _multiple_result_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Addr, Arg, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("status", 1)])
def with_scalar(n: Int32) -> tuple[Int32, Int32]: ...
""",
        module_name="multiple_scalar_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_multiple_scalar_result_plan_has_ordered_binding_consumers_and_shared_hidden_slot():
    function = _multiple_result_plan().namespaces[0].functions[0]
    direct, hidden = function.results

    assert [(result.source_kind, result.result_position) for result in function.results] == [
        ("direct_return", 0),
        ("hidden_output", 1),
    ]
    assert direct.native_call_slot is None
    assert hidden.native_call_slot is function.native_call_slots[hidden.bridge.abi_position]
    assert direct.binding.codegen_action is CodegenAction.DIRECT_VALUE
    assert hidden.binding.codegen_action is CodegenAction.DIRECT_VALUE
    assert hidden.bridge.native_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert direct.bridge.native_result_role in function.available_roles
    assert hidden.bridge.native_result_role in function.available_roles


def test_multiple_scalar_results_lower_to_binding_tuple_and_one_bridge_function_call():
    artifacts = WrapperGenerator().generate(_multiple_result_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "int32_t bind_c_with_scalar(int32_t * n, int32_t * status);" in c_source
    assert "result = bind_c_with_scalar(&bound_n, &status);" in c_source
    assert "PyObject * result_0_obj = prik_int32_to_numpy(&result);" in c_source
    assert "PyObject * result_1_obj = prik_int32_to_numpy(&status);" in c_source
    assert "PyObject * result_obj = PyTuple_New(2);" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 0, result_0_obj);" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 1, result_1_obj);" in c_source
    assert "Py_DECREF(result_0_obj);" in c_source

    assert 'function bind_c_with_scalar(n, status) result(result) bind(c, name="bind_c_with_scalar")' in bridge_source
    assert "result = native_with_scalar(n, status)" in bridge_source
    assert "PyTuple" not in bridge_source


def test_multiple_scalar_result_validation_rejects_position_and_consumer_drift():
    plan = _multiple_result_plan()
    function = plan.namespaces[0].functions[0]
    _direct, hidden = function.results

    hidden.result_position = 0
    with pytest.raises(ValueError, match=r"duplicate-binding-result-position.*missing-binding-result-position"):
        WrapperGenerator().generate(plan)

    plan = _multiple_result_plan()
    function = plan.namespaces[0].functions[0]
    direct, _hidden = function.results
    function.results = (direct,)
    with pytest.raises(ValueError, match="unclaimed-native-result"):
        WrapperGenerator().generate(plan)

    plan = _multiple_result_plan()
    function = plan.namespaces[0].functions[0]
    direct, hidden = function.results
    duplicate = replace(hidden, owner_path=f"{hidden.owner_path}.duplicate", result_position=2)
    function.results = (direct, hidden, duplicate)
    with pytest.raises(ValueError, match="multiple-native-result-consumers"):
        WrapperGenerator().generate(plan)

    plan = _multiple_result_plan()
    function = plan.namespaces[0].functions[0]
    _direct, hidden = function.results
    hidden.native_call_slot = replace(hidden.native_call_slot)
    with pytest.raises(ValueError, match="inconsistent-function-result-slot"):
        WrapperGenerator().generate(plan)
