"""Direct-plan fixed string result and hidden-output lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from prik.policy.ownership import (
    ObjectKind,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import BridgeDataAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _fixed_string_module():
    module = parse_pyi_text(
        """
def direct_label() -> String[8]: ...

@native_call([Return("label", 0)])
def hidden_label() -> String[8]: ...
""",
        module_name="fixed_string_results",
    )
    complete_semantic_policies(module)
    return module


def _fixed_string_plan():
    return WrapperPlanner().build(_fixed_string_module())


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-length", "invalid-result-character-length"),
        ("wrong-copy", "invalid-string-result-data-action"),
        ("slot-length-drift", "inconsistent-result-character-length"),
    ],
)
def test_fixed_string_result_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _fixed_string_plan()
    direct, hidden = (
        plan.namespaces[0].functions[0].results[0],
        plan.namespaces[0].functions[1].results[0],
    )
    if edit == "missing-length":
        direct.character_length = None
    elif edit == "wrong-copy":
        direct.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER
        direct.bridge.copy_reason = None
    else:
        hidden.projected_call_slot.character_length = 7

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_fixed_string_result_policy_uses_ordered_mixed_result_cleanup():
    module = parse_pyi_text(
        """
@native_call([Return("status", 1)])
def mixed() -> tuple[String[8], Int32]: ...
""",
        module_name="mixed_string_results",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    assert policy.blockers == ()
    assert policy.results[0].ownership.kind is ObjectKind.STRING
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    assert tuple(result.result_position for result in function.results) == (0, 1)

    c_source = next(source.text for source in WrapperGenerator().generate(plan).sources if source.path.suffix == ".c")
    assert "free(result);" in c_source
    assert "PyTuple_New(2)" in c_source
    assert "Py_DECREF(result_0_obj);" in c_source


def test_fixed_string_result_failure_releases_later_unpublished_native_results():
    module = parse_pyi_text(
        """
@native_call([Return("left", 0), Return("right", 1)])
def mixed() -> tuple[String[8], String[8]]: ...
""",
        module_name="multiple_string_results",
    )
    complete_semantic_policies(module)
    c_source = next(
        source.text
        for source in WrapperGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".c"
    )

    first_failure = c_source[c_source.index("if (left == NULL)") : c_source.index("result_0_obj =")]
    first_conversion_failure = c_source[
        c_source.index("if (result_0_obj == NULL)") : c_source.index("if (right == NULL)")
    ]
    assert "if (right != NULL) { free(right); right = NULL; }" in first_failure
    assert "if (right != NULL) { free(right); right = NULL; }" in first_conversion_failure


def test_fixed_string_result_policy_blocks_status_error_until_failure_release_is_planned():
    module = parse_pyi_text(
        """
@raises(status="status", success=0)
@native_call([Return("label", 0), Hidden("status", Int32)])
def label() -> String[8]: ...
""",
        module_name="string_result_with_status",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert "fixed string result with native status error requires planned failure-path release" in policy.blockers
    assert len(policy.results) == 1
    assert policy.results[0].ownership.kind is ObjectKind.STRING
