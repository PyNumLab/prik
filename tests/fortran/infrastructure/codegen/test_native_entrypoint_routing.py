"""Completed direct/adapted route handoffs across policy, plan, and lowering."""

from prik.parsers.fortran import parse_fortran_file
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import NativeGeneratedCodeGroupKind, WrapperPlanner
from prik.policy import complete_semantic_policies
from prik.policy.models import (
    EntrypointPassingConvention,
    EntrypointProjectionAction,
    NativeEntrypointAction,
)
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


def _plan(source: str):
    parsed = parse_fortran_file(source)
    module = fortran_module_to_semantic_module(parsed.modules[0])
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_direct_plan_keeps_one_projected_sequence_and_no_adapter_facets():
    plan = _plan(
        """
module direct_projection
  use iso_c_binding
contains
  real(c_double) function scale(value) bind(C, name="direct_scale") result(output)
    real(c_double), value, intent(in) :: value
    output = value
  end function scale
end module direct_projection
"""
    )
    function = plan.namespaces[0].functions[0]
    argument = function.arguments[0]
    slot = function.entrypoint.projected_slots[0]

    assert plan.bridge is None
    assert plan.native_generated_code_groups == ()
    assert function.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI
    assert function.entrypoint.symbol_name == "direct_scale"
    assert function.bridge is None
    assert argument.projected_call_slot is slot
    assert argument.bridge is None
    assert slot.adapter is None
    assert slot.projection_action is EntrypointProjectionAction.ARGUMENT_DEFAULT
    assert slot.passing is EntrypointPassingConvention.C_VALUE


def test_adapted_plan_attaches_one_narrow_adapter_to_the_shared_projection():
    plan = _plan(
        """
module adapted_projection
contains
  real(8) function scale(value) result(output)
    real(8), intent(in) :: value
    output = value
  end function scale
end module adapted_projection
"""
    )
    function = plan.namespaces[0].functions[0]
    argument = function.arguments[0]
    slot = function.entrypoint.projected_slots[0]

    assert plan.bridge is not None
    assert [group.kind for group in plan.native_generated_code_groups] == [
        NativeGeneratedCodeGroupKind.FORTRAN_ADAPTERS
    ]
    assert plan.native_generated_code_groups[0].member_keys == (function.owner_path,)
    assert function.entrypoint.action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    assert function.bridge is not None
    assert argument.projected_call_slot is slot
    assert slot.adapter is not None
    assert slot.passing is EntrypointPassingConvention.C_VALUE


def test_direct_and_mixed_lowering_emit_only_selected_fortran_membership():
    plan = _plan(
        """
module selective_lowering
  use iso_c_binding
contains
  integer(c_int) function direct_value(value) bind(C, name="native_direct_value") result(output)
    integer(c_int), value, intent(in) :: value
    output = value
  end function direct_value

  integer function adapted_value(value) result(output)
    integer, intent(in) :: value
    output = value
  end function adapted_value
end module selective_lowering
"""
    )
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")
    bridge = next(source.text for source in generated.sources if source.path.suffix == ".f90")

    assert "int32_t native_direct_value(int32_t value);" in binding
    assert "result = native_direct_value(bound_value);" in binding
    assert "bind_c_adapted_value" in bridge
    assert "native_adapted_value => adapted_value" in bridge
    assert "direct_value" not in bridge.casefold()
    assert [group.kind for group in generated.native_generated_code_groups] == [
        NativeGeneratedCodeGroupKind.FORTRAN_ADAPTERS
    ]
    assert generated.native_generated_code_groups[0].member_keys == ("selective_lowering.adapted_value",)


def test_direct_user_operation_and_fortran_support_own_separate_group_membership():
    plan = _plan(
        """
module support_only_lowering
  use iso_c_binding
  integer(c_int) :: counter = 1_c_int
contains
  integer(c_int) function direct_value(value) bind(C) result(output)
    integer(c_int), value, intent(in) :: value
    output = counter + value
  end function direct_value
end module support_only_lowering
"""
    )

    assert [group.kind for group in plan.native_generated_code_groups] == [NativeGeneratedCodeGroupKind.FORTRAN_SUPPORT]
    assert all("direct_value" not in key for key in plan.native_generated_code_groups[0].member_keys)

    generated = WrapperGenerator().generate(plan)
    bridge = next(source.text for source in generated.sources if source.path.suffix == ".f90")

    assert "bind_c_get_counter" in bridge
    assert "direct_value" not in bridge.casefold()


def test_all_direct_lowering_assembles_binding_and_header_without_fortran_source():
    generated = WrapperGenerator().generate(
        _plan(
            """
module all_direct_lowering
  use iso_c_binding
contains
  integer(c_int) function value(input) bind(C) result(output)
    integer(c_int), value, intent(in) :: input
    output = input
  end function value
end module all_direct_lowering
"""
        )
    )

    assert generated.bridge_sources == ()
    assert generated.required_link_languages == ("fortran",)
    assert [path.suffix for path in generated.source_paths] == [".c", ".h"]
