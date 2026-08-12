"""Direct-plan required scalar string-value input lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import CodegenAction, NativeBarrierAction, PythonBarrierAction
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArgumentHandoffMode, BridgeDataAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.planning.models import DatatypeFamily


def _string_input_module():
    module = parse_pyi_text(
        """
def fixed(text: String[8]) -> Int32: ...
def assumed(text: String) -> Int32: ...
""",
        module_name="string_inputs",
    )
    complete_semantic_policies(module)
    return module


def _string_input_plan():
    return WrapperPlanner().build(_string_input_module())


def test_required_string_values_reuse_argument_plan_with_character_handoff_facts():
    module = _string_input_module()
    plan = WrapperPlanner().build(module)
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    fixed = functions["fixed"].arguments[0]
    assumed = functions["assumed"].arguments[0]

    for function_name, argument in (("fixed", fixed), ("assumed", assumed)):
        assert argument.datatype_family is DatatypeFamily.STRING
        assert argument.binding.python_action is PythonBarrierAction.STRING_VALUE
        assert argument.bridge.native_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        assert argument.bridge.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
        assert argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        assert argument.bridge.copy_reason == (
            "materialize Fortran character storage from the binding UTF-8 byte buffer"
        )
        assert argument.native_call_slot.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
        assert argument.binding.length_handoff_role == argument.bridge.length_handoff_role
        assert argument.binding.length_handoff_role == f"{argument.owner_path}:length"
        assert argument.native_call_slot is functions[function_name].native_call_slots[0]
        assert argument.native_call_slot.codegen_action is CodegenAction.CALL_LOCAL_INPUT

    assert fixed.native_call_slot.character_length == 8
    assert assumed.native_call_slot.character_length is None


def test_required_string_values_dispatch_to_named_binding_and_bridge_lowering():
    artifacts = WrapperGenerator().generate(_string_input_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "#include <string.h>" in c_source
    assert "const char * bound_text = NULL;" in c_source
    assert "bound_text = PyUnicode_AsUTF8AndSize(bound_text_obj, &bound_text_length);" in c_source
    assert "strlen(bound_text) != bound_text_length" in c_source
    assert "bound_text_length != 8" in c_source
    assert "must encode to exactly 8 bytes" in c_source
    assert "bind_c_fixed(bound_text, (int64_t)bound_text_length)" in c_source
    assert "bind_c_assumed(bound_text, (int64_t)bound_text_length)" in c_source

    assert "type(c_ptr), value :: bound_text" in bridge_source
    assert "integer(c_int64_t), value :: text_length" in bridge_source
    assert "character(kind=c_char), pointer, dimension(:) :: text_bytes" in bridge_source
    assert "character(kind=c_char, len=text_length) :: text" in bridge_source
    assert "call c_f_pointer(bound_text, text_bytes, [text_length])" in bridge_source
    assert "text = transfer(text_bytes, text)" in bridge_source
    assert "native_fixed(text)" in bridge_source
    assert "native_assumed(text)" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-length", "missing-string-length-handoff"),
        ("wrong-handoff", "invalid-string-handoff"),
        ("wrong-copy", "invalid-string-data-action"),
    ],
)
def test_string_handoff_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _string_input_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    if edit == "missing-length":
        argument.binding.length_handoff_role = None
        argument.bridge.length_handoff_role = None
    elif edit == "wrong-handoff":
        argument.bridge.handoff_mode = ArgumentHandoffMode.TYPED_REFERENCE
    else:
        argument.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER
        argument.native_call_slot.bridge_data_action = BridgeDataAction.DIRECT_TRANSFER
        argument.bridge.copy_reason = None
        argument.native_call_slot.bridge_copy_reason = None

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
