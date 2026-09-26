"""Direct-return plus hidden-output scalar aggregation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
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


def _four_result_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Addr, Arg, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("one", 1), Return("two", 2), Return("three", 3)])
def with_four_scalars(n: Int32) -> tuple[Int32, Int32, Int32, Int32]: ...
""",
        module_name="four_scalar_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_four_scalar_results_share_one_linear_failure_cleanup_suffix():
    artifacts = WrapperGenerator().generate(_four_result_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "if (result_1_obj == NULL) {\n        goto prik_output_cleanup_1;\n    }" in c_source
    assert "if (result_obj == NULL) {\n        goto prik_output_cleanup_4;\n    }" in c_source
    for position in range(4, 0, -1):
        assert f"prik_output_cleanup_{position}:" in c_source
        assert c_source.count(f"Py_XDECREF(result_{position - 1}_obj);") == 1
    assert "Py_DECREF(result_0_obj);" not in c_source


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
    hidden.projected_call_slot = replace(hidden.projected_call_slot)
    with pytest.raises(ValueError, match="inconsistent-function-result-slot"):
        WrapperGenerator().generate(plan)
