"""Default-logical scalar kind adaptation through completed wrapper plans."""

from prik import parse_fortran_file
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import BridgeDataAction, ScalarLogicalABI
from prik.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


SOURCE = """
module logical_args
contains
subroutine use_flags(input, output)
  logical, intent(in) :: input
  logical, intent(out) :: output
  output = .not. input
end subroutine use_flags
end module logical_args
"""


def _logical_function_plan():
    parsed_module = parse_fortran_file(SOURCE).modules[0]
    semantic_module = fortran_module_to_semantic_module(parsed_module)
    complete_semantic_policies(semantic_module)
    module_plan = WrapperPlanner().build(semantic_module)
    return module_plan, module_plan.namespaces[0].functions[0]


def test_policy_completes_default_logical_input_and_output_kind_copies():
    _module_plan, function = _logical_function_plan()
    input_plan = function.arguments[0]
    output_slot = function.results[0].native_call_slot

    assert input_plan.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY
    assert input_plan.scalar_native_type == "logical"
    assert input_plan.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
    assert output_slot.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY
    assert output_slot.scalar_native_type == "logical"
    assert output_slot.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION


def test_bridge_mechanically_lowers_completed_default_logical_kind_copies():
    module_plan, _function = _logical_function_plan()

    bridge_source = next(
        source.text for source in WrapperCodeGenerator().generate(module_plan).sources if source.path.suffix == ".f90"
    )

    assert "logical(c_bool), value :: input" in bridge_source
    assert "logical :: input_native" in bridge_source
    assert "input_native = input" in bridge_source
    assert "logical(c_bool) :: output" in bridge_source
    assert "logical :: output_value" in bridge_source
    assert "call native_use_flags(input_native, output_value)" in bridge_source
    assert "output = output_value" in bridge_source
